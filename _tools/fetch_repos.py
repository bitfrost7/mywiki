#!/usr/bin/env python3
"""
mywiki fetch_repos — Step 1 of the CodeNotes Pipeline
======================================================

Reads repo_config.yaml, clones/pulls repos to cache.
Completely independent of analysis logic — only Git operations.

Usage:
  python3 fetch_repos.py                            # All repos, incremental
  python3 fetch_repos.py --system privatelink       # One system
  python3 fetch_repos.py --system privatelink --repo apisvr  # Single repo
  python3 fetch_repos.py --force                    # Re-clone all
  python3 fetch_repos.py --system privatelink --force  # Force one system
  python3 fetch_repos.py --list                     # Show configured repos
  python3 fetch_repos.py --status                   # Show cached state

Pipeline interface:
  Step 1 (this tool): fetch_repos.py  → repos on disk + state file
  Step 2 (analyze):   reads disk → analysis data (JSON per repo)
  Step 3 (generate):  reads analysis → writes CodeNotes/*.md

  Contract between steps:
    - Repo cache:  ~/.cache/mywiki-repos/<name>/.git (HEAD commit)
    - State file:  ~/.cache/mywiki-repos/.state.json
    - Step 2 reads state file to know which repos to analyze.
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("ERROR: 需要 PyYAML（pip3 install pyyaml）", file=sys.stderr)
    sys.exit(1)


# ─── Paths ────────────────────────────────────────────────────────────

VAULT = Path.home() / "Documents/Code/work/mywiki"
TOOLS_DIR = Path(__file__).parent.resolve()
CACHE = Path.home() / ".cache/mywiki-repos"
STATE_FILE = CACHE / ".state.json"

# Config search order: vault root first, then _tools/
CONFIG_CANDIDATES = [
    VAULT / "repo_config.yaml",
    TOOLS_DIR / "repo_config.yaml",
]


# ─── Logging ──────────────────────────────────────────────────────────

def log(msg: str, indent: int = 0):
    prefix = "  " * indent
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{prefix}[{ts}] {msg}", flush=True)


def warn(msg: str):
    print(f"  ⚠  {msg}", file=sys.stderr, flush=True)


def err(msg: str):
    print(f"  ✗  {msg}", file=sys.stderr, flush=True)


# ─── Config ───────────────────────────────────────────────────────────

def find_config() -> Path:
    for p in CONFIG_CANDIDATES:
        if p.exists() and p.stat().st_size > 0:
            try:
                with open(p) as f:
                    content = yaml.safe_load(f)
                if content and "systems" in content:
                    log(f"使用配置: {p}")
                    return p
                else:
                    log(f"跳过空/无效配置: {p}")
            except yaml.YAMLError:
                log(f"跳过解析失败配置: {p}")
        else:
            log(f"配置不存在或为空: {p}")
    print("ERROR: 未找到有效的 repo_config.yaml", file=sys.stderr)
    sys.exit(1)


def load_config(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if not cfg or "systems" not in cfg:
        err("repo_config.yaml 结构无效: 缺少 systems")
        sys.exit(1)

    # Normalize systems to list-of-dicts format
    systems_raw = cfg["systems"]
    if isinstance(systems_raw, dict):
        # dict format: {name: {description, repos, analyzer, ...}}
        systems = []
        for name, info in systems_raw.items():
            entry = {"name": name, "description": info.get("description", ""), "repos": []}
            # Inherit system-level analyzer config
            sys_analyzer = info.get("analyzer", {})
            for repo_entry in info.get("repos", []):
                if isinstance(repo_entry, str):
                    repo = {"url": repo_entry, "analyzer": dict(sys_analyzer)}
                else:
                    repo = dict(repo_entry)
                    # Merge system analyzer into repo if not overridden
                    merged = dict(sys_analyzer)
                    merged.update(repo.get("analyzer", {}))
                    repo["analyzer"] = merged
                repo["name"] = _repo_name(repo["url"])
                repo["system"] = entry["name"]
                entry["repos"].append(repo)
            systems.append(entry)
        cfg["systems"] = systems
    elif isinstance(systems_raw, list):
        # list format: [{name, description, repos}]
        # Already normalized
        pass
    else:
        err("systems 格式不支持（需 dict 或 list）")
        sys.exit(1)

    # Set defaults
    defaults = cfg.get("defaults", {})
    git_defaults = defaults.get("git", {})
    branch = git_defaults.get("branch", "master")
    for sys_info in cfg["systems"]:
        for repo in sys_info.get("repos", []):
            repo.setdefault("branch", branch)
            # Extract name from URL if not set
            if "name" not in repo:
                repo["name"] = _repo_name(repo["url"])

    return cfg


def _repo_name(git_url: str) -> str:
    return git_url.rstrip("/").split("/")[-1].replace(".git", "")


# ─── State ────────────────────────────────────────────────────────────

STATE_VERSION = 2


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {"version": STATE_VERSION, "updated": "", "repos": {}}
    return {"version": STATE_VERSION, "updated": "", "repos": {}}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


# ─── Git operations ───────────────────────────────────────────────────

def run_git(args: List[str], cwd: Optional[Path] = None,
            timeout: int = 60) -> Tuple[str, str, int]:
    """Run a git command, return (stdout, stderr, returncode)."""
    try:
        r = subprocess.run(
            ["git"] + args,
            cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip(), r.stderr.strip(), r.returncode
    except subprocess.TimeoutExpired:
        return "", f"超时 ({timeout}s)", -1
    except FileNotFoundError:
        return "", "git 未安装", -1


def get_head_commit(repo_dir: Path) -> str:
    stdout, _, rc = run_git(["rev-parse", "HEAD"], cwd=repo_dir, timeout=10)
    return stdout if rc == 0 else ""


def get_remote_head(repo_dir: Path, branch: str) -> str:
    stdout, _, rc = run_git(
        ["rev-parse", f"origin/{branch}"], cwd=repo_dir, timeout=10
    )
    return stdout if rc == 0 else ""


def clone_repo(url: str, dest: Path, timeout: int = 120) -> bool:
    log(f"克隆: {dest.name} ← {url}")
    _, stderr, rc = run_git(["clone", url, str(dest)], timeout=timeout)
    if rc != 0:
        # Truncate stderr for readability
        short_err = stderr[:200].replace("\n", " ")
        err(f"克隆失败 [{dest.name}]: {short_err}")
        return False
    return True


def update_repo(repo_dir: Path, branch: str) -> bool:
    """Fetch origin and reset to latest. Returns True if HEAD changed."""
    name = repo_dir.name
    before = get_head_commit(repo_dir)

    # fetch
    _, stderr, rc = run_git(["fetch", "origin", "--quiet"], cwd=repo_dir, timeout=30)
    if rc != 0:
        short_err = stderr[:120].replace("\n", " ")
        warn(f"fetch 失败 [{name}]: {short_err} — 跳过")
        return False

    # Check if HEAD is already at origin/branch
    remote_head = get_remote_head(repo_dir, branch)
    if not remote_head:
        warn(f"获取远程 HEAD 失败 [{name}] — 可能分支 '{branch}' 不存在")
        return False

    if before == remote_head:
        return False  # Already up to date

    # Reset
    _, _, rc = run_git(["reset", "--hard", f"origin/{branch}"], cwd=repo_dir, timeout=30)
    if rc != 0:
        err(f"reset 失败 [{name}]")
        return False

    # Clean untracked files (generated artifacts, etc.)
    _, _, _ = run_git(["clean", "-fd"], cwd=repo_dir, timeout=10)

    after = get_head_commit(repo_dir)
    log(f"  更新: {before[:12]}..{after[:12]}", indent=1)
    return True


def ensure_repo(url: str, sys_name: str, repo_name: str, branch: str,
                force: bool) -> Optional[Path]:
    """Ensure a repo exists at CACHE/<sys_name>/<repo_name> at latest revision.
    Returns repo_path or None on failure.
    """
    repo_dir = CACHE / sys_name / repo_name

    if repo_dir.exists() and (repo_dir / ".git").exists():
        if force:
            log(f"强制更新: {sys_name}/{repo_name}")
        else:
            log(f"增量更新: {sys_name}/{repo_name}")
        ok = update_repo(repo_dir, branch)
        if not ok and not force:
            pass
        return repo_dir

    # Clone
    if repo_dir.exists():
        import shutil
        shutil.rmtree(repo_dir, ignore_errors=True)
    else:
        repo_dir.parent.mkdir(parents=True, exist_ok=True)

    ok = clone_repo(url, repo_dir)
    return repo_dir if ok else None


# ─── Main ─────────────────────────────────────────────────────────────

def list_repos(cfg: dict):
    """Print all configured repos grouped by system."""
    for sys_info in cfg["systems"]:
        sys_name = sys_info["name"]
        desc = sys_info.get("description", "")
        repos = sys_info.get("repos", [])
        print(f"\n{sys_name} — {desc} ({len(repos)} repos)")
        print("-" * 50)
        for repo in repos:
            name = repo["name"]
            url = repo["url"]
            branch = repo.get("branch", "master")
            analyzer = repo.get("analyzer", {})
            langs = analyzer.get("languages", ["go"])
            depth = analyzer.get("depth", "medium")
            print(f"  {name:25s} {langs!s:20s} {depth:8s} {branch:10s}")
            print(f"  {'':25s} {url}")

    total = sum(len(s["repos"]) for s in cfg["systems"])
    print(f"\n总计: {len(cfg['systems'])} systems, {total} repos")


def show_status(cfg: dict, state: dict):
    """Show which repos are cached vs missing."""
    cached = state.get("repos", {})
    print(f"\n缓存目录: {CACHE}")
    print(f"状态文件: {STATE_FILE}")
    if state.get("updated"):
        print(f"上次更新: {state['updated']}")
    print()

    for sys_info in cfg["systems"]:
        sys_name = sys_info["name"]
        repos = sys_info.get("repos", [])
        print(f"  {sys_name}:")

        for repo in repos:
            name = repo["name"]
            repo_key = f"{sys_name}/{name}"
            repo_state = cached.get(repo_key, {})
            cached_dir = CACHE / sys_name / name
            on_disk = cached_dir.exists() and (cached_dir / ".git").exists()
            head = get_head_commit(cached_dir) if on_disk else ""

            if on_disk and head:
                last_commit = repo_state.get("last_commit", "")
                match = "✓" if head == last_commit else "~"
                print(f"    {match} {name:25s} {head[:12]}")
            elif on_disk:
                print(f"    ? {name:25s} (已克隆，未追踪状态)")
            else:
                print(f"    · {name:25s} (未缓存)")

        print()


def run(cfg: dict, state: dict, systems_filter: List[str],
        repo_filter: Optional[str], force: bool, dry_run: bool) -> dict:
    """Execute the update. Returns summary dict."""
    summary = {
        "total": 0, "cloned": 0, "updated": 0, "unchanged": 0,
        "failed": 0, "skipped": 0,
    }
    results = []

    for sys_info in cfg["systems"]:
        sys_name = sys_info["name"]
        if systems_filter and sys_name not in systems_filter:
            continue

        repos = sys_info.get("repos", [])
        if not repos:
            continue

        # Filter by single repo
        if repo_filter:
            repos = [r for r in repos if r["name"] == repo_filter or r["url"] == repo_filter]
            if not repos:
                warn(f"系统 '{sys_name}' 中未找到仓库 '{repo_filter}'")
                continue

        print(f"\n{'─' * 50}")
        print(f"  {sys_name} ({len(repos)} repos)")
        print(f"{'─' * 50}")

        for repo in repos:
            name = repo["name"]
            sys_name = repo.get("system", sys_name)
            repo_key = f"{sys_name}/{name}"
            summary["total"] += 1

            if dry_run:
                repo_dir = CACHE / sys_name / name
                if repo_dir.exists() and (repo_dir / ".git").exists():
                    print(f"  · {repo_key} (已缓存，--dry-run 跳过)")
                else:
                    print(f"  · {repo_key} (需克隆，--dry-run 跳过)")
                summary["skipped"] += 1
                results.append({"name": repo_key, "status": "dry_run"})
                continue

            repo_dir = ensure_repo(
                repo["url"], sys_name, name,
                repo.get("branch", "master"), force,
            )
            if not repo_dir:
                summary["failed"] += 1
                results.append({"name": repo_key, "status": "failed"})
                continue

            # Get HEAD commit
            head = get_head_commit(repo_dir)

            # Check against state
            repo_state = state["repos"].get(repo_key, {})
            last_commit = repo_state.get("last_commit", "")

            if not last_commit:
                status = "cloned"
                summary["cloned"] += 1
            elif head != last_commit:
                status = "updated"
                summary["updated"] += 1
            else:
                summary["unchanged"] += 1
                results.append({"name": repo_key, "status": "unchanged"})
                icons = {"cloned": "+", "updated": "▲", "unchanged": "·"}
                print(f"  {icons['unchanged']} {repo_key:30s} {head[:12]} (unchanged)")
                continue

            # Save state
            state["repos"][repo_key] = {
                "last_commit": head,
                "last_fetch": datetime.now(timezone.utc).isoformat(),
                "system": sys_name,
                "url": repo["url"],
                "branch": repo.get("branch", "master"),
                "languages": repo.get("analyzer", {}).get("languages", ["go"]),
            }

            results.append({"name": repo_key, "status": status, "head": head[:12]})

            # Status icon
            icons = {"cloned": "+", "updated": "▲", "unchanged": "·"}
            icon = icons.get(status, "?")
            print(f"  {icon} {repo_key:30s} {head[:12]} ({status})")

            # Small delay between git ops to avoid SSH hammering
            time.sleep(0.3)

    return summary


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="mywiki fetch_repos — Step 1: 拉取/更新所有代码仓库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 fetch_repos.py                          # 增量更新全部
  python3 fetch_repos.py --system privatelink     # 只更新某个系统
  python3 fetch_repos.py -s privatelink -r apisvr # 单个仓库
  python3 fetch_repos.py --force                  # 强制重新拉取
  python3 fetch_repos.py --list                   # 查看配置
  python3 fetch_repos.py --status                 # 查看缓存状态
  python3 fetch_repos.py --dry-run                # 试运行（不执行）
        """,
    )
    parser.add_argument("--system", "-s", action="append", dest="systems",
                        help="只处理指定系统（可多次使用）")
    parser.add_argument("--repo", "-r", type=str,
                        help="只处理指定仓库名")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重新拉取已有仓库")
    parser.add_argument("--list", "-l", action="store_true",
                        help="列出所有配置的仓库")
    parser.add_argument("--status", action="store_true",
                        help="查看缓存状态")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="试运行（只打印计划，不执行）")
    parser.add_argument("--json", action="store_true",
                        help="以 JSON 格式输出结果")

    args = parser.parse_args()

    # ── Load config & state ──
    config_path = find_config()
    cfg = load_config(config_path)
    state = load_state() if not args.list else {}

    # ── Handle info commands ──
    if args.list:
        list_repos(cfg)
        return

    if args.status:
        show_status(cfg, state)
        return

    # ── Run ──
    summary = run(cfg, state, args.systems or [], args.repo,
                  args.force, args.dry_run)

    # ── Save state ──
    if not args.dry_run:
        save_state(state)

    # ── Summary ──
    total = summary["total"]
    changed = summary["cloned"] + summary["updated"]
    unchanged = summary["unchanged"]
    failed = summary["failed"]

    print(f"\n{'=' * 50}")
    if args.dry_run:
        print(f"  Dry-run: {summary['skipped']} repos 需操作")
    else:
        print(f"  总计: {total} | 新克隆: {summary['cloned']} | "
              f"更新: {summary['updated']} | 无变更: {unchanged} | "
              f"失败: {failed}")
    print(f"{'=' * 50}")

    # ── JSON output ──
    if args.json:
        print()
        print(json.dumps({
            "summary": summary,
            "state_path": str(STATE_FILE),
            "cache_path": str(CACHE),
        }, indent=2, ensure_ascii=False))

    # Exit with error if any failures
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
mywiki sync_code — 代码仓库同步 + Graphify AST 解析
=======================================================

读取 raw/config.yaml 的 code.repos 配置：
  1. 克隆/更新仓库到 raw/assets/repo/{group}/{name}
  2. 运行 graphify extract → AST 输出到 raw/assets/ast/{group}/{name}
  3. 追踪状态变更

支持 GitLab (SSH) 和 GitHub (SSH / HTTPS) 两种 URL 格式。

用法:
  python3 bin/sync_code.py                   # 同步全部，增量
  python3 bin/sync_code.py --repo apisvr     # 只同步某个 repo
  python3 bin/sync_code.py --force           # 强制重新克隆
  python3 bin/sync_code.py --skip-graphify   # 只拉代码，不跑 AST
  python3 bin/sync_code.py --status          # 查看缓存状态
  python3 bin/sync_code.py --dry-run         # 试运行
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import yaml
except ImportError:
    print("❌ 需要 PyYAML: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ── Paths ──────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent.resolve()
VAULT_ROOT = SCRIPT_DIR.parent
CONFIG_PATH = VAULT_ROOT / "raw" / "config.yaml"
REPO_CACHE = VAULT_ROOT / "raw" / "assets" / "repo"
AST_DIR = VAULT_ROOT / "raw" / "assets" / "ast"
STATE_FILE = AST_DIR / ".state.json"

# Graphify 命令路径（mise managed）
GRAPHIFY_CMD = os.environ.get(
    "GRAPHIFY_PATH",
    os.path.expanduser("~/.local/share/mise/installs/python/3.11/bin/graphify"),
)


# ── Logging ────────────────────────────────────────────────────────────

class Logger:
    def __init__(self, verbose: bool = False):
        self._verbose = verbose

    def info(self, msg: str, indent: int = 0):
        prefix = "  " * indent
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"{prefix}[{ts}] {msg}", flush=True)

    def ok(self, msg: str, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}✓ {msg}", flush=True)

    def warn(self, msg: str):
        print(f"  ⚠  {msg}", file=sys.stderr, flush=True)

    def err(self, msg: str, indent: int = 0):
        prefix = "  " * indent
        print(f"{prefix}✗ {msg}", file=sys.stderr, flush=True)

    def debug(self, msg: str):
        if self._verbose:
            print(f"  · {msg}", flush=True)


log = Logger()


# ── Config ─────────────────────────────────────────────────────────────

def _env_replace(m: re.Match) -> str:
    """Replace ${VAR} and ${VAR:-default} with env var values."""
    var = m.group(1)
    default = m.group(2)
    val = os.environ.get(var)
    if val is None:
        return default if default is not None else m.group(0)
    return val


def _resolve_env_vars(obj):
    """Recursively resolve ${VAR} references in string values."""
    if isinstance(obj, str):
        return re.sub(r'\$\{([^}:]+)(?::-(.+?))?\}', _env_replace, obj)
    elif isinstance(obj, dict):
        return {k: _resolve_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_resolve_env_vars(v) for v in obj]
    return obj


def load_config() -> dict:
    """Load raw/config.yaml with env var resolution."""
    if not CONFIG_PATH.exists():
        log.err(f"配置不存在: {CONFIG_PATH}")
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        raw = f.read()
    try:
        parsed: dict = yaml.safe_load(raw) or {}
    except yaml.YAMLError as e:
        log.err(f"config.yaml 格式错误: {e}")
        sys.exit(1)

    return _resolve_env_vars(parsed)  # type: ignore[return-value]


def get_code_repos(cfg: dict) -> List[dict]:
    """Extract and normalize code repo entries from config."""
    code = cfg.get("code", {})
    repos = code.get("repos", [])
    default_branch = code.get("default_branch", "master")

    for repo in repos:
        repo.setdefault("branch", default_branch)
        if "name" not in repo:
            repo["name"] = _repo_name_from_url(repo["url"])
        # Parse group from name
        parts = repo["name"].split("/", 1)
        repo["group"] = parts[0] if len(parts) > 1 else "_"
        repo["short_name"] = parts[-1]

    return repos


# ── URL parsing ─────────────────────────────────────────────────────────

def _repo_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].replace(".git", "")


def parse_repo_url(url: str) -> dict:
    """Parse a Git URL into {host, owner, repo, protocol}.

    Supports:
      git@git.ucloudadmin.com:group/repo.git   → GitLab SSH
      git@github.com:owner/repo.git            → GitHub SSH
      https://github.com/owner/repo.git        → GitHub HTTPS
      https://github.com/owner/repo            → GitHub HTTPS (no .git)
    """
    result = {"host": "", "owner": "", "repo": "", "protocol": ""}

    # SSH format: git@<host>:<path>.git
    m = re.match(r'git@([^:]+):(.+?)(?:\.git)?$', url)
    if m:
        result["host"] = m.group(1)
        result["protocol"] = "ssh"
        path = m.group(2)
        parts = path.split("/")
        if len(parts) >= 2:
            result["owner"] = "/".join(parts[:-1])
            result["repo"] = parts[-1]
        else:
            result["repo"] = parts[0]
        return result

    # HTTPS format: https://<host>/<path>.git
    m = re.match(r'https://([^/]+)/(.+?)(?:\.git)?$', url)
    if m:
        result["host"] = m.group(1)
        result["protocol"] = "https"
        path = m.group(2)
        parts = path.split("/")
        if len(parts) >= 2:
            result["owner"] = "/".join(parts[:-1])
            result["repo"] = parts[-1]
        else:
            result["repo"] = parts[0]
        return result

    # Unknown format — just store as-is
    result["host"] = "unknown"
    result["repo"] = _repo_name_from_url(url)
    return result


def is_github_url(url: str) -> bool:
    info = parse_repo_url(url)
    return "github" in info["host"].lower()


def is_gitlab_url(url: str) -> bool:
    info = parse_repo_url(url)
    return "ucloudadmin" in info["host"].lower() or "gitlab" in info["host"].lower()


# ── Git operations ─────────────────────────────────────────────────────

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


def clone_repo(url: str, dest: Path, branch: str, depth: int = 1,
               timeout: int = 120) -> bool:
    """Clone a repo with shallow depth."""
    log.info(f"克隆: {dest.name} ← {url}")
    cmd = ["clone", "--depth", str(depth), "--branch", branch, url, str(dest)]
    _, stderr, rc = run_git(cmd, timeout=timeout)
    if rc != 0:
        short_err = stderr[:200].replace("\n", " ")
        log.err(f"克隆失败 [{dest.name}]: {short_err}")
        return False
    return True


def update_repo(repo_dir: Path, branch: str, depth: int = 1) -> bool:
    """Fetch origin and reset to latest. Returns True if HEAD changed."""
    name = repo_dir.name
    before = get_head_commit(repo_dir)

    # Fetch (shallow since we cloned --depth 1)
    _, stderr, rc = run_git(
        ["fetch", "origin", branch, "--depth", str(depth)],
        cwd=repo_dir, timeout=30,
    )
    if rc != 0:
        short_err = stderr[:120].replace("\n", " ")
        log.warn(f"fetch 失败 [{name}]: {short_err}")
        return False

    # Check if HEAD is already at origin/branch
    remote_head = get_remote_head(repo_dir, branch)
    if not remote_head:
        log.warn(f"获取远程 HEAD 失败 [{name}] — 分支 '{branch}' 不存在?")
        return False
    if before == remote_head:
        return False  # Up to date

    _, _, rc = run_git(
        ["reset", "--hard", f"origin/{branch}"], cwd=repo_dir, timeout=30,
    )
    if rc != 0:
        log.err(f"reset 失败 [{name}]")
        return False

    _, _, _ = run_git(["clean", "-fd"], cwd=repo_dir, timeout=10)

    after = get_head_commit(repo_dir)
    log.info(f"  更新: {before[:12]}..{after[:12]}", indent=1)
    return True


def ensure_repo(repo: dict, force: bool, skip_clone: bool) -> Optional[Path]:
    """Clone or update a repo. Returns repo_dir or None on failure."""
    group = repo["group"]
    name = repo["short_name"]
    url = repo["url"]
    branch = repo.get("branch", "master")
    depth = repo.get("clone_depth", 1)

    repo_dir = REPO_CACHE / group / name

    if skip_clone:
        # Already provided externally — verify it exists
        if repo_dir.exists() and (repo_dir / ".git").exists():
            return repo_dir
        log.warn(f"仓库未找到（--skip-clone 模式下）: {repo_dir}")
        return None

    if repo_dir.exists() and (repo_dir / ".git").exists():
        if force:
            log.info(f"强制更新: {group}/{name}")
            shutil.rmtree(repo_dir, ignore_errors=True)
            repo_dir.parent.mkdir(parents=True, exist_ok=True)
            ok = clone_repo(url, repo_dir, branch, depth)
            return repo_dir if ok else None
        else:
            log.info(f"增量更新: {group}/{name}")
            ok = update_repo(repo_dir, branch, depth)
            return repo_dir  # Even if no change, repo is usable
    else:
        # Fresh clone
        if repo_dir.exists():
            shutil.rmtree(repo_dir, ignore_errors=True)
        repo_dir.parent.mkdir(parents=True, exist_ok=True)
        ok = clone_repo(url, repo_dir, branch, depth)
        return repo_dir if ok else None


# ── Graphify API key resolution ────────────────────────────────────────

def _resolve_graphify_api_key() -> str:
    """Try to find a usable API key for graphify's openai backend.

    Priority: OPENAI_API_KEY env var → Hermes config's model.api_key.
    """
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key
    # Fall back to Hermes config
    hermes_config = Path.home() / ".hermes" / "config.yaml"
    if hermes_config.exists():
        try:
            import yaml as _y
            cfg = _y.safe_load(hermes_config.read_text())
            if cfg and "model" in cfg and "api_key" in cfg["model"]:
                key = cfg["model"]["api_key"]
                log.debug(f"从 Hermes 配置读取 API key (len={len(key)})")
                return key
        except Exception:
            pass
    return ""


DEFAULT_GRAPHIFY_BACKEND = "openai"
DEFAULT_GRAPHIFY_MODEL = "deepseek-v4-flash"


def is_graphify_available() -> bool:
    return shutil.which(GRAPHIFY_CMD) is not None or os.path.isfile(GRAPHIFY_CMD)


def run_graphify_extract(repo_dir: Path, out_dir: Path,
                         backend: str = DEFAULT_GRAPHIFY_BACKEND,
                         model: str = DEFAULT_GRAPHIFY_MODEL,
                         timeout: int = 600) -> Tuple[bool, str]:
    """Run graphify extract on a repo directory.

    Auto-resolves API key from env or Hermes config.
    Returns (success, summary_or_error).
    """
    # Auto-set API key and base URL if using OpenAI-compatible backend
    if backend in ("openai", "deepseek"):
        if not os.environ.get("OPENAI_API_KEY"):
            key = _resolve_graphify_api_key()
            if key:
                os.environ["OPENAI_API_KEY"] = key
        if not os.environ.get("OPENAI_BASE_URL"):
            # Try Hermes config's base_url
            hermes_config = Path.home() / ".hermes" / "config.yaml"
            if hermes_config.exists():
                try:
                    import yaml as _y
                    cfg = _y.safe_load(hermes_config.read_text())
                    if cfg and "model" in cfg and "base_url" in cfg["model"]:
                        os.environ["OPENAI_BASE_URL"] = cfg["model"]["base_url"]
                        log.debug(f"从 Hermes 配置读取 BASE_URL")
                except Exception:
                    pass

    cmd = [
        GRAPHIFY_CMD, "extract", str(repo_dir),
        "--out", str(out_dir),
        "--backend", backend,
    ]
    if model:
        cmd.extend(["--model", model])

    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout,
        )
        out = r.stdout.strip()
        err = r.stderr.strip()
        if r.returncode != 0:
            short = (out + "\n" + err)[:500].replace("\n", " ")
            return False, short
        return True, out
    except subprocess.TimeoutExpired:
        return False, f"超时 ({timeout}s)"
    except FileNotFoundError:
        return False, "graphify 未安装或路径不存在"
    except Exception as e:
        return False, str(e)


def compute_ast_hash(ast_dir: Path) -> str:
    """Compute a content hash over the AST output directory for change detection."""
    if not ast_dir.exists():
        return ""
    hasher = hashlib.sha256()
    for root, dirs, files in os.walk(ast_dir):
        # Skip hidden files
        files = [f for f in files if not f.startswith(".")]
        for fname in sorted(files):
            fpath = Path(root) / fname
            try:
                rel = str(fpath.relative_to(ast_dir))
                data = fpath.read_bytes()
                hasher.update(rel.encode())
                hasher.update(data)
            except OSError:
                pass
    return hasher.hexdigest()[:16]


# ── State management ───────────────────────────────────────────────────

STATE_VERSION = 1


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {"version": STATE_VERSION, "updated": "", "repos": {}}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


# ── Main logic ──────────────────────────────────────────────────────────

def show_status(repos: list, state: dict):
    """Show sync and AST status for all configured repos."""
    print(f"\n代码仓库缓存: {REPO_CACHE}")
    print(f"AST 输出目录: {AST_DIR}")
    if state.get("updated"):
        print(f"上次同步:     {state['updated']}")
    print()

    for repo in repos:
        name = repo["name"]
        group = repo["group"]
        short = repo["short_name"]
        repo_dir = REPO_CACHE / group / short
        ast_dir = AST_DIR / group / short

        repo_key = name
        repo_state = state.get("repos", {}).get(repo_key, {})

        # Repo status
        on_disk = repo_dir.exists() and (repo_dir / ".git").exists()
        head = get_head_commit(repo_dir) if on_disk else ""
        last_commit = repo_state.get("last_commit", "")

        if on_disk and head:
            match = "✓" if head == last_commit else "~"
            repo_status = f"{match} {name:35s} {head[:12]}"
        elif on_disk:
            repo_status = f"? {name:35s} (已克隆，未追踪)"
        else:
            repo_status = f"· {name:35s} (未缓存)"

        # AST status
        ast_exists = ast_dir.exists() and any(ast_dir.iterdir())
        ast_hash = repo_state.get("ast_hash", "")
        if ast_exists:
            ast_status = f"✓ AST: {repo_state.get('ast_hash', '?')}"
        else:
            ast_status = "· AST: 未生成"

        print(f"  {repo_status}  |  {ast_status}")

    print()


def run_sync(repos: list, state: dict, repo_filter: Optional[str],
             force: bool, skip_graphify: bool, dry_run: bool,
             clone_depth: int, graphify_backend: str = DEFAULT_GRAPHIFY_BACKEND,
             graphify_model: str = DEFAULT_GRAPHIFY_MODEL) -> dict:
    """Execute the sync pipeline. Returns summary dict."""
    summary = {
        "total": 0, "cloned": 0, "updated": 0, "unchanged": 0,
        "failed": 0, "graphify_ok": 0, "graphify_skip": 0, "graphify_fail": 0,
    }

    for repo in repos:
        name = repo["name"]
        if repo_filter and repo_filter not in name:
            continue

        summary["total"] += 1
        group = repo["group"]
        short = repo["short_name"]
        repo_key = name
        print(f"\n{'─' * 60}")
        log.info(f"{name}")

        # ── Step 1: Clone/update repo ──
        repo_dir = REPO_CACHE / group / short
        ast_dir = AST_DIR / group / short

        if dry_run:
            on_disk = repo_dir.exists() and (repo_dir / ".git").exists()
            if on_disk:
                log.info(f"  需更新: {name}（--dry-run 跳过）", indent=1)
            else:
                log.info(f"  需克隆: {name}（--dry-run 跳过）", indent=1)
            summary["unchanged"] += 1
            continue

        repo_dir = ensure_repo(repo, force, skip_clone=False)
        if repo_dir is None:
            summary["failed"] += 1
            continue

        # Determine change status
        head = get_head_commit(repo_dir)
        repo_state = state.get("repos", {}).get(repo_key, {})
        last_commit = repo_state.get("last_commit", "")
        old_ast_hash = repo_state.get("ast_hash", "")

        if not last_commit:
            status = "cloned"
            summary["cloned"] += 1
        elif head != last_commit:
            status = "updated"
            summary["updated"] += 1
        else:
            status = "unchanged"
            summary["unchanged"] += 1

        # ── Step 2: Graphify AST extract ──
        need_graphify = True
        if skip_graphify:
            need_graphify = False
            summary["graphify_skip"] += 1
            log.info("  ─ AST: 跳过 (--skip-graphify)", indent=1)
        elif status == "unchanged":
            # Check if AST already exists and hash matches
            ast_exists = ast_dir.exists() and any(ast_dir.iterdir())
            if ast_exists and old_ast_hash:
                current_hash = compute_ast_hash(ast_dir)
                if current_hash == old_ast_hash:
                    need_graphify = False
                    log.ok(f"AST: 无变更 ({current_hash})", indent=1)

        if need_graphify and not dry_run:
            ast_dir.mkdir(parents=True, exist_ok=True)
            log.info(f"  → graphify extract ({graphify_backend}/{graphify_model}) ...", indent=1)
            ok, result = run_graphify_extract(repo_dir, ast_dir,
                                              backend=graphify_backend,
                                              model=graphify_model)

            if ok:
                ast_hash = compute_ast_hash(ast_dir)
                log.ok(f"AST: {ast_hash}", indent=1)
                summary["graphify_ok"] += 1
            else:
                log.err(f"AST 失败: {result[:200]}", indent=1)
                ast_hash = ""
                summary["graphify_fail"] += 1
        elif not dry_run and not need_graphify:
            ast_hash = compute_ast_hash(ast_dir) if (
                ast_dir.exists() and any(ast_dir.iterdir())
            ) else ""

        # ── Save state ──
        if not dry_run:
            state.setdefault("repos", {})
            state["repos"][repo_key] = {
                "last_commit": head or last_commit,
                "last_sync": datetime.now(timezone.utc).isoformat(),
                "url": repo["url"],
                "branch": repo.get("branch", "master"),
                "group": group,
                "ast_hash": compute_ast_hash(ast_dir) if (
                    ast_dir.exists() and any(ast_dir.iterdir())
                ) else (old_ast_hash or ""),
            }

        # Status icon
        icons = {"cloned": "+", "updated": "▲", "unchanged": "·"}
        icon = icons.get(status, "?")
        log.info(f"  {icon} HEAD: {head[:12]} ({status})", indent=1)

        time.sleep(0.2)

    return summary


def main():
    global log

    parser = argparse.ArgumentParser(
        description="mywiki sync_code — 代码仓库同步 + Graphify AST 解析",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
示例:
  python3 bin/sync_code.py                   # 同步全部代码仓库
  python3 bin/sync_code.py --repo apisvr     # 只同步某个 repo
  python3 bin/sync_code.py --force           # 强制重新克隆
  python3 bin/sync_code.py --skip-graphify   # 只拉代码，不跑 AST
  python3 bin/sync_code.py --status          # 查看缓存状态
  python3 bin/sync_code.py --dry-run         # 试运行
  python3 bin/sync_code.py --verbose         # 详细日志
        """,
    )
    parser.add_argument("--repo", "-r", type=str,
                        help="只处理指定仓库名（子串匹配）")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重新克隆已有仓库")
    parser.add_argument("--skip-graphify", action="store_true",
                        help="跳过 graphify AST 解析，只拉代码")
    parser.add_argument("--status", action="store_true",
                        help="查看缓存状态")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="试运行（只打印计划，不执行）")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细日志输出")
    parser.add_argument("--clone-depth", type=int, default=1,
                        help="Git 克隆深度（默认 1: 只拉最新提交）")
    parser.add_argument("--backend", type=str, default=DEFAULT_GRAPHIFY_BACKEND,
                        help=f"Graphify LLM backend (默认 {DEFAULT_GRAPHIFY_BACKEND})")
    parser.add_argument("--model", type=str, default=DEFAULT_GRAPHIFY_MODEL,
                        help=f"Graphify LLM model (默认 {DEFAULT_GRAPHIFY_MODEL})")

    args = parser.parse_args()
    log = Logger(verbose=args.verbose)

    # ── Load config ──
    cfg = load_config()
    repos = get_code_repos(cfg)

    if not repos:
        log.err("config.yaml 中未配置 code.repos")
        sys.exit(1)

    log.debug(f"找到 {len(repos)} 个代码仓库")
    if args.verbose:
        for r in repos:
            url_info = parse_repo_url(r["url"])
            host_type = "GitHub" if is_github_url(r["url"]) else "GitLab" if is_gitlab_url(r["url"]) else "其他"
            log.debug(f"  {r['name']:35s} → {host_type}  ({r['url']})")

    # ── Check graphify availability ──
    if not args.skip_graphify:
        if not is_graphify_available():
            log.warn(f"graphify 未找到 (尝试: {GRAPHIFY_CMD})")
            log.warn("将跳过 AST 解析，使用 --skip-graphify 可抑制此警告")
            args.skip_graphify = True

    # ── Load state ──
    state = load_state()

    # ── Handle status ──
    if args.status:
        show_status(repos, state)
        return

    # ── Run ──
    summary = run_sync(repos, state, args.repo, args.force,
                       args.skip_graphify, args.dry_run, args.clone_depth,
                       graphify_backend=args.backend,
                       graphify_model=args.model)

    # ── Save state ──
    if not args.dry_run:
        save_state(state)

    # ── Summary ──
    print(f"\n{'=' * 60}")
    if args.dry_run:
        print(f"  Dry-run 完成 — {summary['total']} repos 需操作")
    else:
        print(f"  总计: {summary['total']} "
              f"| 新克隆: {summary['cloned']} "
              f"| 更新: {summary['updated']} "
              f"| 无变更: {summary['unchanged']} "
              f"| 失败: {summary['failed']}"
              )
        if not args.skip_graphify:
            print(f"  AST: 成功 {summary['graphify_ok']} "
                  f"| 跳过 {summary['graphify_skip']} "
                  f"| 失败 {summary['graphify_fail']}"
                  )
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()

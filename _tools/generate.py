#!/usr/bin/env python3
"""
mywiki generate — Step 3 of the CodeNotes Pipeline
====================================================

Reads analysis JSON from Step 2 and generates Obsidian Markdown notes
in the CodeNotes/ vault directory.

Usage:
  python3 generate.py                              # All repos
  python3 generate.py --system privatelink         # One system
  python3 generate.py --system privatelink --repo apisvr  # Single repo
  python3 generate.py --force                      # Regenerate all
  python3 generate.py --status                     # Show generation status
  python3 generate.py --dir CodeNotes              # Output dir (default: CodeNotes)

Pipeline interface:
  Step 1: fetch_repos.py  → repos on disk
  Step 2: analyze.py      → analysis JSON per repo
  Step 3 (this tool):     → writes CodeNotes/<sys>/<repo>.md
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

# ─── Paths ────────────────────────────────────────────────────────────

CACHE = Path.home() / ".cache/mywiki-repos"
ANALYSIS_DIR = CACHE / "analysis"
STATE_FILE = CACHE / ".state.json"
GENERATED_STATE_FILE = CACHE / ".generated_state.json"

CACHE = Path.home() / ".cache/mywiki-repos"
VAULT = Path.home() / "Documents/Code/work/mywiki"

# ─── Helpers ──────────────────────────────────────────────────────────


def load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_json(state: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    state["_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


def get_module_name(file_path: str) -> str:
    """Extract top-level directory or file name for module grouping."""
    parts = file_path.split("/")
    if len(parts) >= 2:
        return parts[0]
    return parts[0] if parts else "root"


def escape_obsidian(text: str) -> str:
    """Escape special Obsidian characters."""
    return text.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def fmt_table_row(k: str, v: str) -> str:
    return f"| {escape_obsidian(k)} | {escape_obsidian(v)} |"


# ─── Front matter helpers ─────────────────────────────────────────────


def build_frontmatter(repo_key: str, info: dict,
                      analysis: dict) -> Dict[str, object]:
    system = info.get("system", "unknown")
    repo_name = repo_key.split("/")[-1]
    langs = info.get("languages", ["go"])
    return {
        "tags": [system, repo_name] + langs,
        "system": system,
        "source": info.get("url", ""),
        "status": "auto-generated",
    }


# ─── Markdown generators ──────────────────────────────────────────────


def gen_overview_table(info: dict, analysis: dict) -> str:
    """Generate project overview table."""
    rows = []
    rows.append(fmt_table_row("System", info.get("system", "?")))
    rows.append(fmt_table_row("Branch", info.get("branch", "?")))
    rows.append(fmt_table_row("Languages", ", ".join(info.get("languages", []))))
    rows.append(fmt_table_row("Files analyzed", str(analysis.get("files_analyzed", 0))))
    rows.append(fmt_table_row("Package", analysis.get("package", "?")))
    return "\n".join(rows)


def gen_structs_section(analysis: dict) -> str:
    """Generate struct/interface definitions section."""
    lines = []
    structs = [s for s in analysis.get("structures", [])
               if s["kind"] == "struct"]
    ifaces = [s for s in analysis.get("structures", [])
              if s["kind"] == "interface"]

    if structs:
        lines.append("\n### 数据结构\n")
        for s in sorted(structs, key=lambda x: x["name"]):
            fields_str = ""
            if s.get("fields"):
                # Show first few fields with a summary
                shown = []
                for f in s["fields"][:6]:
                    shown.append(f"`{f['name']}` `{f['type']}`")
                fields_str = ", ".join(shown)
                if len(s["fields"]) > 6:
                    fields_str += f", +{len(s['fields']) - 6} more"
            elif s.get("methods"):
                shown = []
                for m in s["methods"][:4]:
                    shown.append(f"`{m}()`")
                fields_str = ", ".join(shown)
                if len(s["methods"]) > 4:
                    fields_str += f", +{len(s['methods']) - 4} more"

            loc = f"`{s['file']}:{s['line']}`"
            if fields_str:
                lines.append(f"- ~~{s['name']}~~ — {loc} — {fields_str}")
            else:
                lines.append(f"- ~~{s['name']}~~ — {loc}")

    if ifaces:
        if not structs:
            lines.append("\n### 接口\n")
        else:
            lines.append("\n#### Interfaces\n")
        for s in sorted(ifaces, key=lambda x: x["name"]):
            methods = s.get("methods", [])
            shown = ", ".join(f"`{m}()`" for m in methods[:5])
            if len(methods) > 5:
                shown += f" +{len(methods) - 5} more"
            loc = f"`{s['file']}:{s['line']}`"
            if shown:
                lines.append(f"- ~~{s['name']}~~ — {loc} — {shown}")
            else:
                lines.append(f"- ~~{s['name']}~~ — {loc}")

    return "\n".join(lines)


def gen_routes_section(analysis: dict) -> str:
    """Generate HTTP routes section."""
    routes = analysis.get("routes", [])
    if not routes:
        return ""

    lines = ["\n### API 路由\n"]
    for r in sorted(routes, key=lambda x: (x["method"], x["path"])):
        handler = r["handler"]
        loc = f"`{r['file']}:{r['line']}`"
        lines.append(f"- `{r['method']}` `{r['path']}` → `{handler}` ({loc})")

    return "\n".join(lines)


def gen_functions_section(analysis: dict) -> str:
    """Generate key functions section."""
    funcs = analysis.get("functions", [])

    # Filter to exported and/or interesting functions
    exported = [f for f in funcs
                if f["name"][0].isupper()
                or f.get("kind") == "method"]

    if not exported:
        return ""

    # Group by file for compact display
    by_file: Dict[str, list] = {}
    for f in exported:
        by_file.setdefault(f["file"], []).append(f)

    lines = ["\n### 关键函数\n"]
    for file_path in sorted(by_file):
        func_list = by_file[file_path]
        lines.append(f"\n**`{file_path}`**")
        for f in sorted(func_list, key=lambda x: x["name"]):
            prefix = ""
            if f.get("receiver"):
                prefix = f"({f['receiver']})."
            lines.append(f"- `{prefix}{f['name']}` — `{f['signature'][:80]}`")

    return "\n".join(lines)


def gen_module_sections(analysis: dict) -> str:
    """Group structs/interfaces/funcs by directory module."""
    modules: Dict[str, dict] = {}

    for s in analysis.get("structures", []):
        mod = get_module_name(s["file"])
        modules.setdefault(mod, {"structs": [], "ifaces": [], "functions": []})
        if s["kind"] == "struct":
            modules[mod]["structs"].append(s)
        else:
            modules[mod]["ifaces"].append(s)

    for f in analysis.get("functions", []):
        mod = get_module_name(f["file"])
        modules.setdefault(mod, {"structs": [], "ifaces": [], "functions": []})
        modules[mod]["functions"].append(f)

    if not modules:
        return ""

    lines = ["\n## 核心模块\n"]
    for mod_name in sorted(modules):
        m = modules[mod_name]
        lines.append(f"\n### {mod_name}")
        counts = []
        if m["structs"]:
            counts.append(f"{len(m['structs'])} structs")
        if m["ifaces"]:
            counts.append(f"{len(m['ifaces'])} interfaces")
        if m["functions"]:
            counts.append(f"{len(m['functions'])} functions")
        # Check for routes in this module
        module_routes = [r for r in analysis.get("routes", [])
                        if r["file"].startswith(mod_name)]
        if module_routes:
            counts.append(f"{len(module_routes)} routes")

        if counts:
            lines.append(f"_{', '.join(counts)}_\n")

        # Show prominent structs (top 8 by fields count)
        top_structs = sorted(m["structs"], key=lambda x: -len(x.get("fields", [])))[:8]
        for s in top_structs:
            fields_str = ", ".join(
                f"`{f['name']}` `{f['type']}`"
                for f in s.get("fields", [])[:5]
            )
            if len(s.get("fields", [])) > 5:
                fields_str += " ..."
            if fields_str:
                lines.append(f"- ~~{s['name']}~~ — {{{fields_str}}}")
            else:
                lines.append(f"- ~~{s['name']}~~")

        # Routes in this module
        for r in module_routes[:5]:
            lines.append(f"- `{r['method']}` `{r['path']}` → `{r['handler']}`")

    return "\n".join(lines)


# ─── Repo note generation ─────────────────────────────────────────────


def generate_note(repo_key: str, info: dict,
                  analysis: dict) -> str:
    """Generate full Obsidian markdown note for a repo."""
    repo_name = repo_key.split("/")[-1]
    system = info.get("system", "unknown")

    # Build content
    lines = []

    # Frontmatter
    fm = build_frontmatter(repo_key, info, analysis)
    lines.append("---")
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    lines.append("")

    # Title
    lines.append(f"# {system} / {repo_name}")
    lines.append("")

    # Overview
    lines.append("## 概览")
    lines.append("")
    lines.append(gen_overview_table(info, analysis))
    lines.append("")

    # Routes (prominent if they exist)
    routes_section = gen_routes_section(analysis)
    if routes_section:
        lines.append(routes_section)
        lines.append("")

    # Module sections
    lines.append(gen_module_sections(analysis))
    lines.append("")

    # Structures
    structs_section = gen_structs_section(analysis)
    if structs_section:
        lines.append(structs_section)
        lines.append("")

    # Key functions
    funcs_section = gen_functions_section(analysis)
    # Only include if not too long
    func_count = len(analysis.get("functions", []))
    if funcs_section and func_count < 100:
        lines.append(funcs_section)
        lines.append("")

    return "\n".join(lines)


# ─── Main ──────────────────────────────────────────────────────────────


def run(systems_filter: List[str], repo_filter: str,
        force: bool, out_subdir: str) -> dict:
    """Run generation for matching repos."""
    state = load_json(STATE_FILE)
    repos = state.get("repos", {})
    if not repos:
        print("state 文件为空，先运行 fetch_repos.py")
        return {"total": 0, "generated": 0, "skipped": 0}

    gen_state = load_json(GENERATED_STATE_FILE)
    out_base = VAULT / out_subdir
    out_base.mkdir(parents=True, exist_ok=True)

    summary = {"total": 0, "generated": 0, "skipped": 0}

    matched = []
    for repo_key, info in sorted(repos.items()):
        if systems_filter and info.get("system", "") not in systems_filter:
            continue
        if repo_filter and repo_filter not in repo_key:
            continue
        matched.append((repo_key, info))

    summary["total"] = len(matched)
    if not matched:
        print("没有匹配的仓库")
        return summary

    print(f"\n{'─' * 50}")
    print(f"  生成 {len(matched)} 个仓库的 CodeNotes")
    print(f"{'─' * 50}")

    for repo_key, info in matched:
        repo_name = repo_key.split("/")[-1]
        system = info.get("system", "unknown")
        sys_dir = system

        # Load analysis JSON
        analysis_file = ANALYSIS_DIR / f"{repo_key}.json"
        if not analysis_file.exists():
            print(f"  · {repo_key:35s} ⚠ 无分析文件，跳过")
            summary["skipped"] += 1
            continue

        analysis = load_json(analysis_file)
        commit = analysis.get("commit", "")
        prev_gen = gen_state.get(repo_key, {})

        # Check if needs regeneration
        if not force and prev_gen.get("commit") == commit:
            print(f"  · {repo_key:35s} unchanged, 跳过")
            summary["skipped"] += 1
            continue

        # Generate
        note = generate_note(repo_key, info, analysis)

        # Write to obsidian vault
        out_file = out_base / sys_dir / f"{repo_name}.md"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        out_file.write_text(note)

        # Update state
        gen_state[repo_key] = {
            "commit": commit,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "path": str(out_file.relative_to(VAULT)),
        }

        n_files = analysis.get("files_analyzed", 0)
        total_structures = len(analysis.get("structures", []))
        print(f"  ✓ {repo_key:35s} {n_files:3d} files, "
              f"{total_structures:3d} structures, "
              f"→ {out_file.relative_to(VAULT)}")

        summary["generated"] += 1

    save_json(gen_state, GENERATED_STATE_FILE)
    return summary


def show_status(out_subdir: str):
    """Show generation status for all repos."""
    state = load_json(STATE_FILE)
    repos = state.get("repos", {})
    gen_state = load_json(GENERATED_STATE_FILE)
    out_base = VAULT / out_subdir

    for repo_key in sorted(repos):
        gen = gen_state.get(repo_key, {})
        analysis_file = ANALYSIS_DIR / f"{repo_key}.json"

        out_file = out_base / repo_key
        # guess the out file
        sys_name = repos.get(repo_key, {}).get("system", "unknown")
        repo_name = repo_key.split("/")[-1]
        out_file = out_base / sys_name / f"{repo_name}.md"

        analyzer_ok = "✓" if analysis_file.exists() else "·"
        gen_ok = "📄" if out_file.exists() else "·"
        gen_commit = gen.get("commit", "")[:12] if gen else "-"
        gen_at = gen.get("generated_at", "")[:19] if gen.get("generated_at") else "-"
        print(f"  {analyzer_ok}{gen_ok} {repo_key:35s} commit={gen_commit:12s} gen_at={gen_at}")


# ─── CLI ──────────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="mywiki generate — Step 3: 生成 CodeNotes Markdown",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 generate.py                            # 所有仓库
  python3 generate.py --system privatelink       # 单个系统
  python3 generate.py -s privatelink -r apisvr   # 单个仓库
  python3 generate.py --force                    # 强制重新生成
  python3 generate.py --status                   # 查看状态
  python3 generate.py --dir CodeNotes            # 指定输出目录
        """,
    )
    parser.add_argument("--system", "-s", action="append",
                        help="只处理指定系统")
    parser.add_argument("--repo", "-r", type=str,
                        help="只处理指定仓库")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重新生成")
    parser.add_argument("--status", action="store_true",
                        help="查看生成状态")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="试运行")
    parser.add_argument("--dir", type=str, default="CodeNotes",
                        help="输出子目录 (默认: CodeNotes)")

    args = parser.parse_args()

    if args.status:
        show_status(args.dir)
        return

    if args.dry_run:
        state = load_json(STATE_FILE)
        for repo_key in sorted(state.get("repos", {})):
            analysis_file = ANALYSIS_DIR / f"{repo_key}.json"
            status = "✓ analyzed" if analysis_file.exists() else "· pending"
            print(f"  · {repo_key:35s} {status}")
        return

    summary = run(args.system or [], args.repo or "",
                  args.force, args.dir)

    print(f"\n{'=' * 50}")
    print(f"  总计: {summary['total']} | "
          f"已生成: {summary['generated']} | "
          f"跳过(无变更): {summary['skipped']}")
    print(f"{'=' * 50}")


if __name__ == "__main__":
    main()

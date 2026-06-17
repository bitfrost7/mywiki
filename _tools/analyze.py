#!/usr/bin/env python3
"""
mywiki analyze — Step 2 of the CodeNotes Pipeline
==================================================

Reads repos from Step 1's cache, extracts structural code elements
(structs, interfaces, functions, routes) using tree-sitter.
Outputs per-repo analysis JSON for Step 3 (generate markdown).

Pluggable: add new language analyzers by registering a new handler.

Usage:
  python3 analyze.py                              # All repos, incremental
  python3 analyze.py --system privatelink         # One system
  python3 analyze.py --system privatelink --repo apisvr  # Single repo
  python3 analyze.py --force                      # Re-analyze all
  python3 analyze.py --status                     # Show analysis status
  python3 analyze.py --verbose                    # Detailed per-file logging

Pipeline interface:
  Step 1: fetch_repos.py  → repos on disk + .state.json (commit hashes)
  Step 2 (this tool):     → per-repo JSON to analysis/<sys>/<repo>.json
  Step 3: generate.py     → reads analysis JSON → writes CodeNotes/*.md

  Contract:
    - Reads:  ~/.cache/mywiki-repos/<sys>/<repo>/
    - Reads:  ~/.cache/mywiki-repos/.state.json
    - Writes: ~/.cache/mywiki-repos/analysis/<sys>/<repo>.json
    - Writes: ~/.cache/mywiki-repos/.analysis_state.json
"""

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ─── Paths ────────────────────────────────────────────────────────────

CACHE = Path.home() / ".cache/mywiki-repos"
STATE_FILE = CACHE / ".state.json"
ANALYSIS_DIR = CACHE / "analysis"
ANALYSIS_STATE_FILE = CACHE / ".analysis_state.json"

# ─── Logging ──────────────────────────────────────────────────────────

VERBOSE = False


def log(msg: str, indent: int = 0):
    prefix = "  " * indent
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{prefix}[{ts}] {msg}", flush=True)


def vlog(msg: str):
    if VERBOSE:
        log(msg)


def warn(msg: str):
    print(f"  ⚠  {msg}", file=sys.stderr, flush=True)


def err(msg: str):
    print(f"  ✗  {msg}", file=sys.stderr, flush=True)


# ─── State management ─────────────────────────────────────────────────

def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_state(state: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    state["_updated"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n")


# ─── Language registry ────────────────────────────────────────────────

# Analyzer returns: dict with keys: module, structures, functions, routes
_analyzer_registry = {}


def register_analyzer(lang: str):
    """Decorator to register a language analyzer function."""
    def wrapper(fn):
        _analyzer_registry[lang] = fn
        return fn
    return wrapper


def get_analysis(repo_dir: Path, languages: List[str],
                 commit: str, repo_key: str) -> dict:
    """Run analysis for a repo, dispatching to registered language analyzers."""
    result = {
        "repo_key": repo_key,
        "commit": commit,
        "analyzed_at": datetime.now(timezone.utc).isoformat(),
        "structures": [],
        "functions": [],
        "routes": [],
        "imports": [],
        "package": "",
        "files_analyzed": 0,
        "errors": [],
    }

    for lang in languages:
        lang = lang.lower()
        analyzer = _analyzer_registry.get(lang)
        if not analyzer:
            result["errors"].append(f"no analyzer for language: {lang}")
            continue
        try:
            lang_result = analyzer(repo_dir)
            # Merge
            for k in ("structures", "functions", "routes", "imports"):
                result.setdefault(k, []).extend(lang_result.get(k, []))
            result["files_analyzed"] += lang_result.get("files_analyzed", 0)
            result["errors"].extend(lang_result.get("errors", []))
            # Take the first package name found
            if not result["package"] and lang_result.get("package"):
                result["package"] = lang_result["package"]
        except Exception as e:
            result["errors"].append(f"[{lang}] {e}")

    return result


# ─── Go analyzer ──────────────────────────────────────────────────────

@register_analyzer("go")
def analyze_go(repo_dir: Path) -> dict:
    """Analyze Go source files using tree-sitter."""
    import tree_sitter_go
    from tree_sitter import Language, Parser

    LANG = Language(tree_sitter_go.language())
    parser = Parser(LANG)

    # Pre-compile queries
    q_package = LANG.query("(package_clause (package_identifier) @name)")
    q_imports = LANG.query("(import_declaration (import_spec (interpreted_string_literal) @path))")

    q_struct = LANG.query("""
        (type_declaration
          (type_spec
            name: (type_identifier) @name
            type: (struct_type) @body))
    """)
    q_struct_field = LANG.query("""
        (field_declaration
          name: (field_identifier) @fname
          type: (_) @ftype)
    """)

    q_iface = LANG.query("""
        (type_declaration
          (type_spec
            name: (type_identifier) @name
            type: (interface_type) @body))
    """)
    q_iface_method = LANG.query("(method_elem (field_identifier) @name)")

    q_func = LANG.query("""
        (function_declaration
          name: (identifier) @name) @node
    """)
    q_method = LANG.query("""
        (method_declaration
          name: (field_identifier) @name) @node
    """)
    q_method_receiver = LANG.query("(parameter_list . (parameter_declaration type: (_) @type))")

    # Gin-style routes: r.GET("/path", handler), r.POST(...), etc.
    q_route = LANG.query("""
        (call_expression
          function: (selector_expression
            field: (field_identifier) @method)
          arguments: (argument_list
            .
            (interpreted_string_literal) @path
            .
            [
              (identifier)
              (selector_expression)
            ] @handler))
    """)

    # Generic call expressions for non-standard route patterns (cnatapp, etc.)
    q_all_calls = LANG.query("(call_expression) @call")

    result = {
        "structures": [],
        "functions": [],
        "routes": [],
        "imports": [],
        "package": "",
        "files_analyzed": 0,
        "errors": [],
    }

    go_files = sorted(repo_dir.rglob("*.go"))
    go_files = [f for f in go_files if "vendor" not in str(f)]

    for fpath in go_files:
        try:
            code = fpath.read_bytes()
            tree = parser.parse(code)
            root = tree.root_node
        except Exception as e:
            result["errors"].append(f"{fpath.relative_to(repo_dir)}: {e}")
            continue

        rel_path = str(fpath.relative_to(repo_dir))
        result["files_analyzed"] += 1

        # Package
        if not result["package"]:
            for node in q_package.captures(root).get("name", []):
                result["package"] = get_text(code, node)

        # Imports (collect unique)
        for node in q_imports.captures(root).get("path", []):
            imp = get_text(code, node).strip("\"")
            if imp not in result["imports"]:
                result["imports"].append(imp)

        # Struct definitions
        for pat_idx, match in q_struct.matches(root):
            sname = ""
            sbody = None
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        sname = get_text(code, n)
                    elif tag_name == "body":
                        sbody = n

            if not sname:
                continue

            fields = []
            for _, fm in q_struct_field.matches(sbody):
                fname, ftype = "", ""
                for ftag, fnodes in fm.items():
                    for fn in fnodes:
                        if ftag == "fname":
                            fname = get_text(code, fn)
                        elif ftag == "ftype":
                            ftype = get_text(code, fn)
                if fname:
                    fields.append({"name": fname, "type": ftype})

            result["structures"].append({
                "kind": "struct",
                "name": sname,
                "file": rel_path,
                "line": sbody.start_point[0] + 1,
                "fields": fields,
            })

        # Interface definitions
        for pat_idx, match in q_iface.matches(root):
            iname = ""
            ibody = None
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        iname = get_text(code, n)
                    elif tag_name == "body":
                        ibody = n
            if not iname:
                continue

            methods = []
            for _, im in q_iface_method.matches(ibody):
                for itag, inodes in im.items():
                    for inn in inodes:
                        if itag == "name":
                            methods.append(get_text(code, inn))

            result["structures"].append({
                "kind": "interface",
                "name": iname,
                "file": rel_path,
                "line": ibody.start_point[0] + 1,
                "methods": methods,
            })

        # Functions
        for _, match in q_func.matches(root):
            fname = ""
            fnode = None
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        fname = get_text(code, n)
                    elif tag_name == "node":
                        fnode = n
            if fname and fnode:
                sig_start = fnode.start_byte
                sig_end = fnode.children[-1].start_byte if fnode.children else fnode.end_byte
                signature = code[sig_start:sig_end].decode()[:120]
                result["functions"].append({
                    "kind": "function",
                    "name": fname,
                    "file": rel_path,
                    "line": fnode.start_point[0] + 1,
                    "signature": signature,
                    "receiver": None,
                })

        # Methods
        for _, match in q_method.matches(root):
            mname = ""
            mnode = None
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        mname = get_text(code, n)
                    elif tag_name == "node":
                        mnode = n
            if not mname or not mnode:
                continue

            # Get receiver type from parameter list
            receiver = None
            params = mnode.child_by_field_name("receiver")
            if params:
                for _, rm in q_method_receiver.matches(params):
                    for rtag, rnodes in rm.items():
                        for rn in rnodes:
                            if rtag == "type":
                                receiver = get_text(code, rn)

            sig_start = mnode.start_byte
            sig_end = mnode.children[-1].start_byte if mnode.children else mnode.end_byte
            signature = code[sig_start:sig_end].decode()[:120]

            result["functions"].append({
                "kind": "method",
                "name": mname,
                "file": rel_path,
                "line": mnode.start_point[0] + 1,
                "signature": signature,
                "receiver": receiver,
            })

        # Routes (Gin-style)
        route_captures = q_route.captures(root)
        route_methods = route_captures.get("method", [])
        route_paths = route_captures.get("path", [])
        route_handlers = route_captures.get("handler", [])
        for i in range(len(route_methods)):
            rm = get_text(code, route_methods[i]).upper()
            rp = get_text(code, route_paths[i]) if i < len(route_paths) else ""
            rh = get_text(code, route_handlers[i]) if i < len(route_handlers) else ""
            HTTP_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
            if rm in HTTP_METHODS and rp and rh:
                result["routes"].append({
                    "method": rm,
                    "path": rp.strip("\""),
                    "handler": rh,
                    "file": rel_path,
                    "line": route_methods[i].start_point[0] + 1,
                })

        # Generic: collect all function calls for non-standard route detection
        # Future: cnatapp framework may use different patterns
        # We store them as potential calls for post-processing
        # (skipping for now — will add framework-specific queries later)

    return result


def get_text(code: bytes, node) -> str:
    return code[node.start_byte:node.end_byte].decode()


# ─── C analyzer (placeholder) ─────────────────────────────────────────

@register_analyzer("c")
def analyze_c(repo_dir: Path) -> dict:
    """Analyze C source files using tree-sitter.
    NOTE: Requires compatible tree-sitter-c grammar version.
    """
    result = {
        "structures": [],
        "functions": [],
        "routes": [],
        "imports": [],
        "package": "",
        "files_analyzed": 0,
        "errors": [],
    }

    try:
        import tree_sitter_c
        from tree_sitter import Language, Parser

        C_LANG = Language(tree_sitter_c.language())
        parser = Parser(C_LANG)
    except ImportError:
        result["errors"].append("tree-sitter-c not installed (pip3 install tree-sitter-c)")
        return result
    except ValueError as e:
        result["errors"].append(f"tree-sitter-c version incompatible: {e}")
        return result

    # Queries (C specific)
    q_struct = C_LANG.query("""
        (struct_specifier
          name: (type_identifier) @name
          body: (field_declaration_list) @body)
    """)
    q_func = C_LANG.query("""
        (function_definition
          declarator: (function_declarator
            declarator: (identifier) @name))
    """)

    c_files = sorted(repo_dir.rglob("*.c"))
    h_files = sorted(repo_dir.rglob("*.h"))
    sources = c_files + h_files

    for fpath in sources:
        try:
            code = fpath.read_bytes()
            tree = parser.parse(code)
            root = tree.root_node
        except Exception as e:
            result["errors"].append(f"{fpath.relative_to(repo_dir)}: {e}")
            continue

        rel_path = str(fpath.relative_to(repo_dir))
        result["files_analyzed"] += 1

        # Structs
        for pat_idx, match in q_struct.matches(root):
            sname = ""
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        sname = get_text(code, n)
            if sname:
                result["structures"].append({
                    "kind": "struct",
                    "name": sname,
                    "file": rel_path,
                    "line": 0,
                    "fields": [],
                })

        # Functions
        for pat_idx, match in q_func.matches(root):
            fname = ""
            for tag_name, nodes in match.items():
                for n in nodes:
                    if tag_name == "name":
                        fname = get_text(code, n)
            if fname:
                result["functions"].append({
                    "kind": "function",
                    "name": fname,
                    "file": rel_path,
                    "line": 0,
                    "signature": fname,
                    "receiver": None,
                })

    return result


# ─── Main analysis logic ──────────────────────────────────────────────

def needs_analysis(repo_key: str, commit: str, analysis_state: dict) -> bool:
    """Check if a repo needs (re-)analysis based on commit hash."""
    prev = analysis_state.get(repo_key, {})
    return prev.get("commit") != commit


def analyze_repo(repo_dir: Path, repo_key: str, repo_info: dict,
                 force: bool, analysis_state: dict) -> Optional[dict]:
    """Analyze a single repo. Returns result dict or None if skipped."""
    commit = repo_info.get("last_commit", "")
    if not commit:
        warn(f"{repo_key}: no commit info, skipping")
        return None

    if not force and not needs_analysis(repo_key, commit, analysis_state):
        return None  # Skipped

    languages = repo_info.get("languages", ["go"])

    vlog(f"分析: {repo_key} ({languages})")

    result = get_analysis(repo_dir, languages, commit, repo_key)

    # Write per-repo analysis file
    analysis_file = ANALYSIS_DIR / f"{repo_key}.json"
    analysis_file.parent.mkdir(parents=True, exist_ok=True)
    analysis_file.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    )

    # Update analysis state
    analysis_state[repo_key] = {
        "commit": commit,
        "analyzed_at": result["analyzed_at"],
        "status": "ok" if not result["errors"] else "partial",
        "errors": len(result["errors"]),
    }

    return result


def run(state: dict, systems_filter: List[str], repo_filter: Optional[str],
        force: bool, verbose: bool) -> dict:
    """Run analysis for matching repos."""
    global VERBOSE
    VERBOSE = verbose

    repos = state.get("repos", {})
    if not repos:
        warn("state file 中没有仓库信息，先运行 fetch_repos.py --status 检查")
        return {"total": 0, "analyzed": 0, "skipped": 0, "errors": []}

    analysis_state = load_state(ANALYSIS_STATE_FILE)

    summary = {"total": 0, "analyzed": 0, "skipped": 0, "errors": 0}
    results_by_repo = {}

    # Filter repos
    matched = []
    for repo_key, info in sorted(repos.items()):
        if systems_filter:
            sys_name = info.get("system", "")
            if sys_name not in systems_filter:
                continue
        if repo_filter and repo_filter not in repo_key:
            continue
        matched.append((repo_key, info))

    summary["total"] = len(matched)

    if not matched:
        warn("没有匹配的仓库")
        return summary

    print(f"\n{'─' * 50}")
    print(f"  分析 {len(matched)} 个仓库")
    print(f"{'─' * 50}")

    for repo_key, info in matched:
        repo_dir = CACHE / repo_key
        if not repo_dir.exists() or not (repo_dir / ".git").exists():
            warn(f"{repo_key}: 目录不存在，跳过（需要先 fetch）")
            summary["skipped"] += 1
            continue

        result = analyze_repo(repo_dir, repo_key, info, force, analysis_state)

        if result is None:
            # Skipped (unchanged)
            vlog(f"  · {repo_key} (unchanged)")
            summary["skipped"] += 1
            continue

        summary["analyzed"] += 1
        if result.get("errors"):
            summary["errors"] += len(result["errors"])

        # Print summary for this repo
        n_structs = sum(1 for s in result["structures"] if s["kind"] == "struct")
        n_ifaces = sum(1 for s in result["structures"] if s["kind"] == "interface")
        n_funcs = len(result["functions"])
        n_routes = len(result["routes"])
        n_files = result["files_analyzed"]
        pkg = result.get("package", "?")
        status = " ✓" if not result["errors"] else f" ⚠({len(result['errors'])} errs)"
        print(f"  {repo_key:30s} {n_files:3d} files  {pkg:15s} "
              f"{n_structs:3d} structs {n_ifaces:2d} ifaces "
              f"{n_funcs:3d} funcs {n_routes:2d} routes{status}")

        results_by_repo[repo_key] = result

    # Save analysis state
    save_state(analysis_state, ANALYSIS_STATE_FILE)

    return summary


def show_status(state: dict):
    """Show analysis status for all repos."""
    repos = state.get("repos", {})
    analysis_state = load_state(ANALYSIS_STATE_FILE)

    print(f"\n分析输出: {ANALYSIS_DIR}/")
    print(f"分析状态: {ANALYSIS_STATE_FILE}")
    if analysis_state.get("_updated"):
        print(f"上次分析: {analysis_state['_updated']}")
    print()

    for repo_key, info in sorted(repos.items()):
        commit = info.get("last_commit", "")[:12]
        sys_name = info.get("system", "?")
        state_entry = analysis_state.get(repo_key, {})
        prev_commit = state_entry.get("commit", "")[:12]
        analyzed_at = state_entry.get("analyzed_at", "")[:19] if state_entry.get("analyzed_at") else ""
        errors = state_entry.get("errors", 0)

        if state_entry:
            if commit == state_entry.get("commit", ""):
                status = "✓ analyzed"
            else:
                status = "~ outdated"
            if errors:
                status += f" ({errors} errs)"
        else:
            status = "· pending"

        analysis_file = ANALYSIS_DIR / f"{repo_key}.json"
        has_file = "📄" if analysis_file.exists() else "  "

        print(f"  {has_file} {repo_key:35s} {commit:12s} {status:22s} {analyzed_at}")


# ─── CLI ──────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="mywiki analyze — Step 2: 分析代码仓库提取结构信息",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python3 analyze.py                          # 分析所有变更的仓库
  python3 analyze.py --system privatelink     # 只分析某个系统
  python3 analyze.py -s privatelink -r apisvr # 单个仓库
  python3 analyze.py --force                  # 强制重新分析全部
  python3 analyze.py --status                 # 查看分析状态
  python3 analyze.py -v                       # 详细日志
        """,
    )
    parser.add_argument("--system", "-s", action="append", dest="systems",
                        help="只处理指定系统")
    parser.add_argument("--repo", "-r", type=str,
                        help="只处理指定仓库")
    parser.add_argument("--force", "-f", action="store_true",
                        help="强制重新分析已有仓库")
    parser.add_argument("--status", action="store_true",
                        help="查看分析状态")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细日志")
    parser.add_argument("--dry-run", "-n", action="store_true",
                        help="试运行（只打印计划）")

    args = parser.parse_args()

    state = load_state(STATE_FILE)
    if not state or "repos" not in state:
        err("state 文件为空或无效，先运行 fetch_repos.py 拉取仓库")
        sys.exit(1)

    if args.status:
        show_status(state)
        return

    if args.dry_run:
        repos = state.get("repos", {})
        matched = 0
        for repo_key, info in sorted(repos.items()):
            if args.systems and info.get("system", "") not in args.systems:
                continue
            if args.repo and args.repo not in repo_key:
                continue
            langs = info.get("languages", ["go"])
            print(f"  · {repo_key:35s} {langs}")
            matched += 1
        print(f"\nDry-run: {matched} repos 待分析")
        return

    summary = run(state, args.systems or [], args.repo, args.force, args.verbose)

    print(f"\n{'=' * 50}")
    print(f"  总计: {summary['total']} | 已分析: {summary['analyzed']} | "
          f"跳过(无变更): {summary['skipped']} | 错误: {summary['errors']}")
    print(f"{'=' * 50}")

    if summary["errors"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
mywiki extract — Step 1: 符号提取

从 Go 源码提取结构化符号表（symbols.jsonl），供 agent 精确搜索 + LLM 摘要生成。
纯 Python，零外部依赖，基于行级状态机解析 Go 语法。

用法:
  python3 extract.py                                          # 所有 repo
  python3 extract.py --system utraffic                        # 单个系统
  python3 extract.py --system utraffic --repo bandwidth_utraffic  # 单个 repo
  python3 extract.py --status                                 # 查看状态

输出: ~/.mywiki_pipeline/symbols/<repo_name>.jsonl
     ~/.mywiki_pipeline/dep_map.json       (跨 repo 依赖矩阵)
"""

import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

# ─── 路径 ────────────────────────────────────────────────────────

CACHE = Path.home() / ".cache/mywiki-repos"
WORK = Path.home() / "Documents/Code/work"
PIPELINE_DIR = Path.home() / ".mywiki_pipeline"
SYMBOLS_DIR = PIPELINE_DIR / "symbols"
CACHE_DIR = PIPELINE_DIR / "cache"
STATE_FILE = CACHE / ".state.json"

# ─── 导入语言特定提取器 ────────────────────────────────────────

from extract_c import extract_c_symbols

# ─── Go 符号提取 ────────────────────────────────────────────────

def extract_go_symbols(filepath: Path, repo_root: Path) -> List[dict]:
    """从单个 .go 文件提取符号，基于行级状态机，零正则魔法。"""
    try:
        lines = filepath.read_text(errors="replace").splitlines()
    except Exception:
        return []

    rel = str(filepath.relative_to(repo_root))
    symbols = []
    comment_block = []  # 当前注释块（// 行）
    in_struct = False   # 是否在 struct { ... } 内部
    struct_brace_depth = 0
    current_struct = None
    struct_fields = []

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        # ── 收集注释块 ──
        if stripped.startswith("//"):
            comment_block.append(stripped[2:].strip())
            i += 1
            continue
        elif stripped == "":
            comment_block = []  # 空行打断注释
            if in_struct:
                pass  # 空行在 struct 域内是合法的
            i += 1
            continue

        # ── 处理 struct body ──
        if in_struct:
            # 计算大括号深度变化
            for ch in line:
                if ch == "{":
                    struct_brace_depth += 1
                elif ch == "}":
                    struct_brace_depth -= 1

            if struct_brace_depth <= 1:  # 回到外层（struct body 结束）
                # 在闭合前提取最后一行的字段
                field_line = line.split("//")[0].strip()
                if field_line and field_line != "}" and re.match(r'^\w', field_line):
                    parts = field_line.split()
                    if len(parts) >= 2 and parts[0][0].islower():
                        struct_fields.append(f"{parts[0]} {parts[1]}")

                if struct_brace_depth == 0:
                    if current_struct:
                        current_struct["fields_sample"] = struct_fields[:10]
                        if len(struct_fields) > 10:
                            current_struct["fields_sample"].append(f"... +{len(struct_fields)-10} more")
                    in_struct = False
                    current_struct = None
                    struct_fields = []
                i += 1
                continue

            # 在 struct body 内提取字段
            field_line = line.split("//")[0].strip()
            if field_line and re.match(r'^\w', field_line):
                parts = field_line.split()
                if len(parts) >= 2:
                    struct_fields.append(f"{parts[0]} {parts[1]}")
            i += 1
            continue

        # ── type X struct 定义 ──
        type_match = re.match(r'^type\s+(\w+)\s+(struct|interface)\s*(\{?)', stripped)
        if type_match:
            name = type_match.group(1)
            kind = type_match.group(2)
            has_brace = type_match.group(3) == "{"
            line_num = i + 1  # 1-indexed

            if kind == "struct":
                if has_brace:
                    in_struct = True
                    struct_brace_depth = 1
                    current_struct = {
                        "kind": "struct",
                        "name": name,
                        "file": rel,
                        "line": line_num,
                        "comment": "\n".join(comment_block) if comment_block else "",
                        "fields_sample": [],
                    }
                    struct_fields = []
                else:
                    # 可能是单行 struct: type X struct { ... } 或 type X struct
                    # 检查同一行有没有 {
                    brace_pos = line.find("{")
                    if brace_pos >= 0:
                        # 同行有 {，但可能跨行
                        rest = line[brace_pos+1:]
                        if "}" in rest:
                            # 单行 struct: type X struct { Name string }
                            inner = rest.split("}")[0].strip()
                            fields = []
                            if inner:
                                # 多个字段可能用空格或分号
                                parts = re.findall(r'(\w+)\s+([\w.\[\]\*]+)', inner)
                                for fname, ftype in parts[:10]:
                                    fields.append(f"{fname} {ftype}")
                            symbols.append({
                                "kind": "struct",
                                "name": name,
                                "file": rel,
                                "line": line_num,
                                "comment": "\n".join(comment_block) if comment_block else "",
                                "fields_sample": fields,
                            })
                        else:
                            in_struct = True
                            struct_brace_depth = line.count("{") - line.count("}")
                            current_struct = {
                                "kind": "struct",
                                "name": name,
                                "file": rel,
                                "line": line_num,
                                "comment": "\n".join(comment_block) if comment_block else "",
                                "fields_sample": [],
                            }
                            struct_fields = []
                    else:
                        # type X struct — 下一行才 {
                        in_struct = True
                        struct_brace_depth = 0
                        current_struct = {
                            "kind": "struct",
                            "name": name,
                            "file": rel,
                            "line": line_num,
                            "comment": "\n".join(comment_block) if comment_block else "",
                            "fields_sample": [],
                        }
                        struct_fields = []
                comment_block = []
                i += 1
                continue

            elif kind == "interface":
                symbols.append({
                    "kind": "interface",
                    "name": name,
                    "file": rel,
                    "line": line_num,
                    "comment": "\n".join(comment_block) if comment_block else "",
                })
                comment_block = []
                i += 1
                continue

        # ── func 定义（函数或方法） ──
        func_match = re.match(r'^func\s', stripped)
        if func_match:
            # 提取完整签名（到 { 或行尾）
            sig_end = line.find(" {")
            if sig_end < 0:
                sig_end = len(line)
            # 可能跨行，拼接后续行直到找到 {
            sig = stripped[sig_end:]
            j = i
            while "{" not in sig and j + 1 < len(lines):
                j += 1
                sig = sig + " " + lines[j].strip()
                if "{" in sig:
                    sig_end = sig.find(" {")
                    if sig_end < 0:
                        sig_end = len(sig)
                    break
            if sig_end < 0:
                sig_end = len(stripped)

            # 提取 receiver（如果有）
            full_sig = stripped[5:sig_end].strip()
            receiver = None
            rcvr_match = re.match(r'^\((\w+\s+\*?\w+)\)\s+(\w+)', full_sig)
            if rcvr_match:
                receiver = rcvr_match.group(1)
                func_name = rcvr_match.group(2)
            else:
                # 普通函数
                fn_match = re.match(r'^(\w+)', full_sig)
                func_name = fn_match.group(1) if fn_match else full_sig.split("(")[0]

            symbols.append({
                "kind": "func",
                "name": func_name,
                "signature": full_sig[:200],
                "receiver": receiver,
                "file": rel,
                "line": i + 1,
                "comment": "\n".join(comment_block) if comment_block else "",
            })
            comment_block = []
            # 跳过这种一行式 type/const/var 声明
            i += 1
            continue

        # ── const / var 块级声明 ──
        cv_match = re.match(r'^(const|var)\s+\(', stripped)
        if cv_match:
            kw = cv_match.group(1)
            symbols.append({
                "kind": f"{kw}_block",
                "name": f"{kw} block",
                "file": rel,
                "line": i + 1,
                "comment": "\n".join(comment_block) if comment_block else "",
                "preview": f"{kw} (...) — 展开查看详细",
            })
            comment_block = []
            i += 1
            continue

        # ── 顶层 const/var 声明 ──
        cv_match = re.match(r'^(const|var)\s+(\w+)', stripped)
        if cv_match:
            kw = cv_match.group(1)
            name = cv_match.group(2)
            symbols.append({
                "kind": kw,
                "name": name,
                "file": rel,
                "line": i + 1,
                "comment": "\n".join(comment_block) if comment_block else "",
                "signature": stripped[:200],
            })
            comment_block = []
            i += 1
            continue

        # ── import 路径 ──
        imp_match = re.match(r'^import\s+["(]', stripped)
        if imp_match:
            # 只记位置
            symbols.append({
                "kind": "import_section",
                "name": "imports",
                "file": rel,
                "line": i + 1,
            })
            comment_block = []
            i += 1
            continue

        # 其他行，清空注释
        comment_block = []
        i += 1

    # 如果 struct 没有闭合（语法错误），仍然记录下来
    if current_struct:
        symbols.append(current_struct)

    return symbols


def extract_imports(repo_path: Path) -> List[str]:
    """从仓库中提取所有 import 路径（去重）。"""
    imports = set()
    for fpath in repo_path.rglob("*.go"):
        if any(p in fpath.parts for p in ("vendor", "third_party")):
            continue
        if fpath.name.endswith("_test.go") or fpath.name.endswith(".pb.go"):
            continue
        try:
            src = fpath.read_text(errors="replace")
        except Exception:
            continue
        # 提取 import "path" 和 import ( "path1" "path2" )
        for m in re.finditer(r'\n\s+["\u0060]([^"\u0060]+)["\u0060]', src):
            path = m.group(1)
            if not path.startswith("."):
                imports.add(path)
    return sorted(imports)


def get_go_module(repo_path: Path) -> Optional[str]:
    """读取 go.mod 获取模块名。"""
    gomod = repo_path / "go.mod"
    if gomod.exists():
        for line in gomod.read_text().splitlines():
            if line.startswith("module "):
                return line[7:].strip()
    return None


def get_readme(repo_path: Path) -> str:
    """读取 README（如果有）。"""
    for name in ("README.md", "README", "README.txt"):
        f = repo_path / name
        if f.exists():
            text = f.read_text(errors="replace")
            return text[:1500]
    return ""


# ─── 仓库处理 ────────────────────────────────────────────────────


def process_repo(repo_key: str, repo_path: Path, force: bool,
                 cache: dict) -> Optional[str]:
    """处理单个仓库，返回变更的 commit 或 None。"""
    repo_name = repo_key.split("/")[-1]
    
    # 检查 git commit
    git_dir = repo_path / ".git"
    if not git_dir.exists():
        print(f"  · {repo_key:35s} ⚠ 不是 git 仓库，跳过")
        return None

    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            print(f"  · {repo_key:35s} ⚠ git 错误，跳过")
            return None
        commit = result.stdout.strip()
    except Exception:
        print(f"  · {repo_key:35s} ⚠ git 异常，跳过")
        return None

    # 增量检查
    prev_commit = cache.get(repo_key, "")
    if not force and prev_commit == commit:
        return commit  # 无变更，返回 commit 但不标记变化

    # 提取符号
    all_symbols = []
    go_files = []
    c_files = []

    # Go 文件
    for fpath in sorted(repo_path.rglob("*.go")):
        if any(p in fpath.parts for p in ("vendor", "third_party")):
            continue
        if fpath.name.endswith("_test.go") or fpath.name.endswith(".pb.go"):
            continue
        go_files.append(fpath)
        all_symbols.extend(extract_go_symbols(fpath, repo_path))

    # C/C++ 文件
    for ext in ["*.c", "*.h", "*.cc", "*.cpp", "*.hpp"]:
        for fpath in sorted(repo_path.rglob(ext)):
            if any(p in fpath.parts for p in ("vendor", "third_party", "build")):
                continue
            c_files.append(fpath)
            all_symbols.extend(extract_c_symbols(fpath, repo_path))

    # 提取 imports
    imports = extract_imports(repo_path)
    module = get_go_module(repo_path)
    readme = get_readme(repo_path)

    # 写入 symbols.jsonl
    out_file = SYMBOLS_DIR / f"{repo_name}.jsonl"
    out_file.parent.mkdir(parents=True, exist_ok=True)

    with out_file.open("w") as f:
        # 先写 repo 头
        header = {
            "_type": "repo_meta",
            "repo": repo_key,
            "name": repo_name,
            "module": module or "",
            "lang": "go,c" if c_files else "go",
            "commit": commit,
            "files": len(go_files) + len(c_files),
            "files_go": len(go_files),
            "files_c": len(c_files),
            "symbols": len(all_symbols),
            "imports": imports,
            "readme_present": bool(readme),
        }
        f.write(json.dumps(header, ensure_ascii=False) + "\n")
        for s in all_symbols:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    print(f"  ✓ {repo_key:35s} {header['symbols']:4d} symbols → {out_file.name}")
    return commit


# ─── 依赖矩阵 ────────────────────────────────────────────────────


def build_dep_map(repos: dict) -> dict:
    """根据各 repo 的 import 路径构建跨 repo 依赖矩阵。"""
    # 所有已知 repo 的 import 前缀映射
    prefix_map = {}
    for repo_key in repos:
        repo_name = repo_key.split("/")[-1]
        sym_file = SYMBOLS_DIR / f"{repo_name}.jsonl"
        if not sym_file.exists():
            continue
        with sym_file.open() as f:
            first = json.loads(f.readline())
            module = first.get("module", "")
            if module:
                prefix_map[module] = repo_name

    dep_map = {}
    for repo_key in repos:
        repo_name = repo_key.split("/")[-1]
        sym_file = SYMBOLS_DIR / f"{repo_name}.jsonl"
        if not sym_file.exists():
            continue
        with sym_file.open() as f:
            first = json.loads(f.readline())
            imports = first.get("imports", [])

        internal_deps = []
        for imp in imports:
            for prefix, dep_name in prefix_map.items():
                if imp == prefix or imp.startswith(prefix + "/"):
                    if dep_name != repo_name:
                        internal_deps.append({"target": dep_name, "import": imp})
                        break  # 只匹配最精确的一个

        dep_map[repo_name] = {
            "module": first.get("module", ""),
            "depends_on": sorted(set(d["target"] for d in internal_deps)),
            "dep_imports": internal_deps,
        }

    return dep_map


# ─── Main ────────────────────────────────────────────────────────


def find_repo_path(repo_key: str) -> Optional[Path]:
    """查找 repo 本地路径（走缓存或工作目录）。"""
    # 先查缓存
    cache_path = CACHE / repo_key
    if cache_path.exists() and (cache_path / ".git").exists():
        return cache_path
    # 再查工作目录
    system, name = repo_key.split("/", 1)
    work_path = WORK / system / name
    if work_path.exists() and (work_path / ".git").exists():
        return work_path
    return None


def run(systems_filter: List[str], repo_filter: str, force: bool):
    """主流程。"""
    # 读取配置
    config_path = Path(__file__).parent / "repo_config.yaml"
    if not config_path.exists():
        print("❌ 找不到 repo_config.yaml")
        return

    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)

    repos = {}
    for sys_name, sys_cfg in config.get("systems", {}).items():
        if systems_filter and sys_name not in systems_filter:
            continue
        for repo_cfg in sys_cfg.get("repos", []):
            url = repo_cfg["url"]
            # 从 URL 提取 repo name
            name = url.rstrip("/").split("/")[-1].replace(".git", "")
            repo_key = f"{sys_name}/{name}"
            if repo_filter and repo_filter not in name and repo_filter not in repo_key:
                continue
            repos[repo_key] = {"system": sys_name, "url": url}

    if not repos:
        print("没有匹配的仓库")
        return

    # 加载缓存
    cache_file = CACHE_DIR / ".extract_cache.json"
    cache = {}
    if cache_file.exists():
        cache = json.loads(cache_file.read_text())

    print(f"\n{'─'*60}")
    print(f"  符号提取: {len(repos)} 个仓库")
    print(f"{'─'*60}\n")

    changed = False
    for repo_key in sorted(repos):
        repo_path = find_repo_path(repo_key)
        if not repo_path:
            print(f"  · {repo_key:35s} ⚠ 未找到本地路径，跳过")
            continue
        commit = process_repo(repo_key, repo_path, force, cache)
        if commit:
            cache[repo_key] = commit
            changed = True

    # 构建依赖矩阵
    dep_map = build_dep_map(repos)
    dep_file = PIPELINE_DIR / "dep_map.json"
    dep_file.parent.mkdir(parents=True, exist_ok=True)
    dep_file.write_text(json.dumps(dep_map, indent=2, ensure_ascii=False))
    print(f"\n  依赖矩阵: {len(dep_map)} repos → {dep_file}")

    # 写入缓存
    if changed:
        cache["_updated"] = datetime.now(timezone.utc).isoformat()
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps(cache, indent=2))


def show_status():
    """查看当前状态。"""
    sym_dir = SYMBOLS_DIR
    if not sym_dir.exists():
        print("还没有符号文件")
        return

    print(f"\n{'─'*60}")
    print(f"  符号索引状态")
    print(f"{'─'*60}\n")
    for f in sorted(sym_dir.glob("*.jsonl")):
        with f.open() as fh:
            first = json.loads(fh.readline())
            total = sum(1 for _ in fh) + 1
        print(f"  {f.stem:30s} {total:4d} symbols   commit={first.get('commit','')[:12]}")


# ─── CLI ─────────────────────────────────────────────────────────


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="mywiki extract — Step 1: 符号提取",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--system", "-s", action="append", help="只处理指定系统")
    parser.add_argument("--repo", "-r", type=str, help="只处理指定仓库")
    parser.add_argument("--force", "-f", action="store_true", help="强制重新提取")
    parser.add_argument("--status", action="store_true", help="查看状态")

    args = parser.parse_args()

    if args.status:
        show_status()
        return

    run(args.system or [], args.repo or "", args.force)


if __name__ == "__main__":
    main()

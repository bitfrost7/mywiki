#!/usr/bin/env python3
"""
mywiki generate_relationship — 生成服务关联关系图

基于 dep_map.json 分析跨 repo 依赖关系，生成:
1. Mermaid 流程图（可在 Markdown 中渲染）
2. JSON 格式的依赖数据
3. 系统级依赖关系文档

用法:
  python3 generate_relationship.py                    # 所有系统
  python3 generate_relationship.py --system privatelink  # 单个系统
  python3 generate_relationship.py --format mermaid    # 只生成 mermaid
  python3 generate_relationship.py --format all         # 生成所有格式
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional

# ─── 路径 ────────────────────────────────────────────────────────

VAULT = Path.home() / "Documents/Code/work/mywiki"
PIPELINE_DIR = Path.home() / ".mywiki_pipeline"
DEP_MAP_FILE = PIPELINE_DIR / "dep_map.json"
SYMBOLS_DIR = PIPELINE_DIR / "symbols"
OUTPUT_DIR = VAULT / "CodeNotes" / "_relationships"

# ─── 依赖分析 ────────────────────────────────────────────────────


def load_dep_map() -> Dict[str, dict]:
    """加载依赖矩阵。"""
    if not DEP_MAP_FILE.exists():
        print(f"✗ 依赖矩阵不存在: {DEP_MAP_FILE}")
        print("  请先运行: python3 extract.py")
        sys.exit(1)
    return json.loads(DEP_MAP_FILE.read_text())


def group_by_system(dep_map: Dict[str, dict]) -> Dict[str, List[str]]:
    """按系统分组 repo。"""
    systems: Dict[str, List[str]] = {}
    for repo_name, info in dep_map.items():
        # 从 module 路径推断系统
        module = info.get("module", "")
        if "privatelink" in module:
            system = "privatelink"
        elif "uver4" in module:
            system = "uver4"
        elif "utraffic" in module:
            system = "utraffic"
        elif "l4fwd" in module:
            system = "l4fwd"
        elif "cnat" in module:
            system = "cnat"
        else:
            system = "other"
        
        systems.setdefault(system, []).append(repo_name)
    
    return systems


def build_dependency_edges(dep_map: Dict[str, dict], repos: List[str]) -> List[dict]:
    """构建系统内的依赖边。"""
    edges = []
    repo_set = set(repos)
    
    for repo_name in repos:
        info = dep_map.get(repo_name, {})
        for dep in info.get("depends_on", []):
            if dep in repo_set:
                edges.append({
                    "from": repo_name,
                    "to": dep,
                    "imports": [imp["import"] for imp in info.get("dep_imports", []) if imp["target"] == dep]
                })
    
    return edges


def find_entry_points(dep_map: Dict[str, dict], repos: List[str]) -> List[str]:
    """找出入口服务（不被其他服务依赖的）。"""
    repo_set = set(repos)
    depended_by = {r: [] for r in repos}
    
    for repo_name in repos:
        info = dep_map.get(repo_name, {})
        for dep in info.get("depends_on", []):
            if dep in repo_set:
                depended_by[dep].append(repo_name)
    
    # 不被依赖的就是入口
    entry_points = [r for r in repos if not depended_by[r]]
    return entry_points


def find_core_libs(dep_map: Dict[str, dict], repos: List[str]) -> List[str]:
    """找出核心库（被最多服务依赖的）。"""
    repo_set = set(repos)
    depended_count = {r: 0 for r in repos}
    
    for repo_name in repos:
        info = dep_map.get(repo_name, {})
        for dep in info.get("depends_on", []):
            if dep in repo_set:
                depended_count[dep] += 1
    
    # 按被依赖次数排序
    return sorted(repos, key=lambda r: depended_count[r], reverse=True)[:5]


# ─── 生成 Mermaid 图 ────────────────────────────────────────────


def generate_mermaid(system: str, repos: List[str], edges: List[dict]) -> str:
    """生成 Mermaid 流程图。"""
    lines = [
        f"# {system} 服务依赖关系图",
        "",
        "```mermaid",
        "graph TD",
    ]
    
    # 节点样式定义
    entry_points = find_entry_points({r: {} for r in repos}, repos)
    core_libs = find_core_libs({r: {} for r in repos}, repos)
    
    for repo in repos:
        if repo in entry_points:
            lines.append(f"    {repo}[{repo}]:::entry")
        elif repo in core_libs:
            lines.append(f"    {repo}[{repo}]:::core")
        else:
            lines.append(f"    {repo}[{repo}]")
    
    lines.append("")
    
    # 边
    for edge in edges:
        from_repo = edge["from"]
        to_repo = edge["to"]
        lines.append(f"    {from_repo} --> {to_repo}")
    
    # 样式类
    lines.extend([
        "",
        "    classDef entry fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
        "    classDef core fill:#fff3e0,stroke:#e65100,stroke-width:2px",
        "```",
        "",
        "**图例**:",
        "- 🔵 蓝色: 入口服务（不被其他服务依赖）",
        "- 🟠 橙色: 核心库（被多个服务依赖）",
    ])
    
    return "\n".join(lines)


# ─── 生成依赖矩阵表 ─────────────────────────────────────────────


def generate_matrix_table(system: str, repos: List[str], edges: List[dict]) -> str:
    """生成依赖矩阵表格。"""
    lines = [
        f"## {system} 依赖矩阵",
        "",
        "| 服务 | 依赖 | 被依赖 | 说明 |",
        "|------|------|--------|------|",
    ]
    
    dep_map = load_dep_map()
    
    # 构建依赖关系
    repo_set = set(repos)
    depends_on = {r: [] for r in repos}
    depended_by = {r: [] for r in repos}
    
    for repo_name in repos:
        info = dep_map.get(repo_name, {})
        for dep in info.get("depends_on", []):
            if dep in repo_set:
                depends_on[repo_name].append(dep)
                depended_by[dep].append(repo_name)
    
    for repo in sorted(repos):
        deps = ", ".join(depends_on[repo]) or "-"
        depended = ", ".join(depended_by[repo]) or "-"
        
        # 获取简短说明
        info = dep_map.get(repo, {})
        module = info.get("module", "")
        desc = f"`{module.split('/')[-1]}`" if module else "-"
        
        lines.append(f"| {repo} | {deps} | {depended} | {desc} |")
    
    return "\n".join(lines)


# ─── 生成系统级文档 ─────────────────────────────────────────────


def generate_system_doc(system: str, repos: List[str], edges: List[dict]) -> str:
    """生成完整的系统依赖文档。"""
    dep_map = load_dep_map()
    
    entry_points = find_entry_points(dep_map, repos)
    core_libs = find_core_libs(dep_map, repos)
    
    mermaid = generate_mermaid(system, repos, edges)
    matrix = generate_matrix_table(system, repos, edges)
    
    lines = [
        "---",
        f"tags: [relationship, {system}, architecture]",
        f"system: {system}",
        f"updated: {datetime.now().strftime('%Y-%m-%d')}",
        "status: auto-generated",
        "---",
        "",
        f"# {system} 服务架构图",
        "",
        mermaid,
        "",
        "---",
        "",
        matrix,
        "",
        "---",
        "",
        "## 架构分析",
        "",
        "### 入口服务",
        "这些服务是系统的入口点，不被其他内部服务依赖：",
        "",
    ]
    
    for ep in entry_points:
        info = dep_map.get(ep, {})
        module = info.get("module", "")
        lines.append(f"- **{ep}** — `{module}`")
    
    lines.extend([
        "",
        "### 核心库",
        "这些库被多个服务依赖，是系统的核心基础设施：",
        "",
    ])
    
    for lib in core_libs:
        info = dep_map.get(lib, {})
        module = info.get("module", "")
        # 计算被依赖次数
        count = sum(1 for r in repos if lib in dep_map.get(r, {}).get("depends_on", []))
        lines.append(f"- **{lib}** — 被 {count} 个服务依赖 — `{module}`")
    
    lines.extend([
        "",
        "### 依赖热力",
        "",
    ])
    
    # 计算依赖热力
    if edges:
        dep_counts = {}
        for edge in edges:
            dep_counts[edge["to"]] = dep_counts.get(edge["to"], 0) + 1
        
        sorted_deps = sorted(dep_counts.items(), key=lambda x: x[1], reverse=True)
        
        lines.append("| 被依赖服务 | 依赖者数量 |")
        lines.append("|------------|------------|")
        for dep, count in sorted_deps[:10]:
            lines.append(f"| {dep} | {count} |")
    
    return "\n".join(lines)


# ─── 主流程 ─────────────────────────────────────────────────────


def generate_for_system(system: str, dep_map: Dict[str, dict], repos: List[str], fmt: str):
    """为单个系统生成关系文档。"""
    edges = build_dependency_edges(dep_map, repos)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if fmt in ("mermaid", "all"):
        mermaid = generate_mermaid(system, repos, edges)
        out_file = OUTPUT_DIR / f"{system}-diagram.md"
        out_file.write_text(mermaid)
        print(f"  ✓ {out_file.name}")
    
    if fmt in ("matrix", "all"):
        matrix = generate_matrix_table(system, repos, edges)
        out_file = OUTPUT_DIR / f"{system}-matrix.md"
        out_file.write_text(matrix)
        print(f"  ✓ {out_file.name}")
    
    if fmt in ("full", "all"):
        doc = generate_system_doc(system, repos, edges)
        out_file = OUTPUT_DIR / f"{system}-architecture.md"
        out_file.write_text(doc)
        print(f"  ✓ {out_file.name}")
    
    if fmt == "json":
        data = {
            "system": system,
            "repos": repos,
            "edges": edges,
            "entry_points": find_entry_points(dep_map, repos),
            "core_libs": find_core_libs(dep_map, repos),
        }
        out_file = OUTPUT_DIR / f"{system}-relationship.json"
        out_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"  ✓ {out_file.name}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="生成服务关联关系图")
    parser.add_argument("--system", "-s", help="只处理指定系统")
    parser.add_argument("--format", "-f", default="all", 
                        choices=["mermaid", "matrix", "full", "json", "all"],
                        help="输出格式")
    args = parser.parse_args()
    
    dep_map = load_dep_map()
    systems = group_by_system(dep_map)
    
    print(f"\n{'─'*60}")
    print(f"  服务关联关系生成")
    print(f"{'─'*60}\n")
    
    if args.system:
        if args.system not in systems:
            print(f"✗ 系统 '{args.system}' 不存在")
            print(f"  可用系统: {', '.join(systems.keys())}")
            sys.exit(1)
        repos = systems[args.system]
        print(f"[{args.system}] {len(repos)} 个服务")
        generate_for_system(args.system, dep_map, repos, args.format)
    else:
        for system, repos in sorted(systems.items()):
            print(f"\n[{system}] {len(repos)} 个服务")
            generate_for_system(system, dep_map, repos, args.format)
    
    print(f"\n{'─'*60}")
    print(f"  输出目录: {OUTPUT_DIR.relative_to(VAULT)}")
    print(f"{'─'*60}")


if __name__ == "__main__":
    main()

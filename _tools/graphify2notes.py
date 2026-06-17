#!/usr/bin/env python3
"""
mywiki graphify2notes — 将 Graphify graph.json 转为结构化 CodeNotes

用法:
  export PATH="$HOME/.local/share/mise/shims:$PATH"
  python3 graphify2notes.py <repo-path> --out <vault-codenotes-dir>

示例:
  python3 graphify2notes.py ~/Code/privatelink/apisvr \\
    --out ~/mywiki/CodeNotes/privatelink/apisvr
"""

import json
import os
import sys
import argparse
from pathlib import Path


def load_graph(repo_path: Path) -> dict:
    graph_path = repo_path / "graphify-out" / "graph.json"
    if not graph_path.exists():
        print(f"ERROR: {graph_path} not found. Run graphify extract first.")
        sys.exit(1)
    with open(graph_path) as f:
        g = json.load(f)
    # Normalize: ensure nodes is a dict keyed by id
    if isinstance(g.get("nodes"), list):
        nodes = {}
        for n in g["nodes"]:
            nid = n.get("id", "")
            nodes[nid] = n
        g["nodes"] = nodes
    if g.get("edges") is None and g.get("links"):
        g["edges"] = g["links"]
    return g


def load_report(repo_path: Path) -> str:
    report_path = repo_path / "graphify-out" / "GRAPH_REPORT.md"
    if report_path.exists():
        return report_path.read_text()
    return ""


def get_nodes(graph: dict) -> dict:
    return graph.get("nodes", {})


def extract_communities(graph: dict) -> list:
    """Extract community clusters from graph."""
    communities = {}
    for node_id, node in get_nodes(graph).items():
        comm_id = node.get("community")
        if comm_id is not None:
            communities.setdefault(comm_id, []).append(node)
    sorted_comms = sorted(communities.items(), key=lambda x: -len(x[1]))
    return [(cid, nodes, len(nodes)) for cid, nodes in sorted_comms]


def extract_god_nodes(graph: dict, top_n: int = 15) -> list:
    """Find most connected nodes (hubs)."""
    edge_count = {}
    for edge in graph.get("edges", []):
        if not isinstance(edge, dict):
            continue
        for k in ("source", "target"):
            edge_count.setdefault(edge.get(k, ""), 0)
            edge_count[edge[k]] += 1

    sorted_nodes = sorted(edge_count.items(), key=lambda x: -x[1])
    result = []
    for node_id, count in sorted_nodes[:top_n]:
        node = get_nodes(graph).get(node_id, {})
        result.append({
            "id": node_id,
            "label": node.get("label", node_id),
            "kind": node.get("kind", node.get("file_type", "")),
            "file": node.get("file", node.get("source_file", "")),
            "connections": count,
        })
    return result


def extract_api_endpoints(graph: dict) -> list:
    """Extract API handlers/routes from graph."""
    endpoints = []
    for node_id, node in get_nodes(graph).items():
        kind = node.get("kind", "")
        label = node.get("label", "")
        if kind in ("api", "route", "handler") or "Handler" in label or "handler" in label.lower():
            endpoints.append({
                "id": node_id,
                "label": label,
                "file": node.get("source_file", ""),
                "community": node.get("community"),
            })
    return endpoints


def extract_structs(graph: dict) -> list:
    """Extract struct/type definitions."""
    structs = []
    for node_id, node in get_nodes(graph).items():
        kind = node.get("kind", "")
        if kind in ("struct", "type", "interface"):
            structs.append({
                "id": node_id,
                "label": node.get("label", node_id),
                "kind": kind,
                "file": node.get("source_file", ""),
            })
    return structs


def generate_readme(repo_name: str, graph: dict, report: str, out_dir: Path):
    """Generate README.md with architecture overview."""
    god_nodes = extract_god_nodes(graph)
    communities = extract_communities(graph)
    structs = extract_structs(graph)
    endpoints = extract_api_endpoints(graph)

    total_nodes = len(graph.get("nodes", {}))
    total_edges = len(graph.get("edges", []))

    lines = [
        f"# {repo_name} — 代码知识图谱\n",
        f"> Graphify 自动分析 | {total_nodes} 节点 · {total_edges} 边 · {len(communities)} 社区\n",
    ]

    # Summary stats
    lines.extend([
        "---\n",
        "## 概览\n",
        f"| 指标 | 数值 |",
        f"|------|------|",
        f"| 节点数 | {total_nodes} |",
        f"| 边数 | {total_edges} |",
        f"| 社区数 | {len(communities)} |",
        f"| 结构体/类型 | {len(structs)} |",
        f"| API Handler | {len(endpoints)} |",
        "\n---\n",
    ])

    # God Nodes
    if god_nodes:
        lines.extend([
            "## 核心抽象（God Nodes）\n",
            "连接数最多的节点，代表系统的核心抽象：\n",
            "| 节点 | 连接数 | 类型 | 文件 |",
            "|------|--------|------|------|",
        ])
        for gn in god_nodes:
            lines.append(f"| `{gn['label']}` | {gn['connections']} | {gn['kind']} | `{gn['file']}` |")
        lines.append("")

    # Communities
    if communities:
        lines.extend([
            "---\n",
            "## 社区导航\n",
            "按大小排序的代码社区（功能模块）：\n",
            "| # | 社区 | 节点数 |",
            "|---|------|--------|",
        ])
        for i, (cid, nodes, size) in enumerate(communities[:15], 1):
            labels = [n.get("label", "") for n in nodes[:3]]
            desc = ", ".join(l for l in labels if l)[:80]
            lines.append(f"| {i} | {desc} | {size} |")
        lines.append("")

    # Key structs
    if structs:
        lines.extend([
            "---\n",
            "## 关键类型定义\n",
            f"共 {len(structs)} 个类型：\n",
        ])
        for s in structs[:20]:
            lines.append(f"- **`{s['label']}`** ({s['kind']}) — `{s['file']}`")
        if len(structs) > 20:
            lines.append(f"\n... 还有 {len(structs) - 20} 个类型（完整列表见 graph.html）")
        lines.append("")

    # API endpoints
    if endpoints:
        lines.extend([
            "---\n",
            "## API 接口\n",
            f"共 {len(endpoints)} 个 Handler：\n",
        ])
        for ep in endpoints[:30]:
            lines.append(f"- **{ep['label']}** — `{ep['file']}`")
        if len(endpoints) > 30:
            lines.append(f"\n... 还有 {len(endpoints) - 30} 个 Handler")
        lines.append("")

    # Interactive viz link
    lines.extend([
        "---\n",
        "## 交互式可视化\n",
        "\n打开 `graph.html` 浏览完整的代码知识图谱。\n",
    ])

    # Graph report excerpts
    if report:
        # Extract the graph report sections about surprising connections
        lines.extend([
            "---\n",
            "## Graphify 分析报告\n",
            "> 以下内容来自 graphify 的 GRAPH_REPORT.md\n",
        ])
        in_surprising = False
        for line in report.split("\n"):
            if line.startswith("# ") or line.startswith("## "):
                # Remove community sections (too granular)
                if "COMMUNITY" in line:
                    in_surprising = False
                    continue
                lines.append(f"\n{line}")
            elif line.strip() and not line.startswith("[["):
                lines.append(line)

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "README.md").write_text("\n".join(lines))
    print(f"  README.md — {len(lines)} lines")


def main():
    parser = argparse.ArgumentParser(description="Convert graphify output to CodeNotes")
    parser.add_argument("repo_path", help="Path to the analyzed repo (with graphify-out/)")
    parser.add_argument("--out", "-o", required=True, help="Output directory for CodeNotes")
    args = parser.parse_args()

    repo_path = Path(args.repo_path).resolve()
    out_dir = Path(args.out).resolve()
    repo_name = repo_path.name

    print(f"📦 {repo_name}")
    print(f"   Graph: {repo_path}/graphify-out/graph.json")
    print(f"   Output: {out_dir}")

    graph = load_graph(repo_path)
    report = load_report(repo_path)

    print(f"   节点: {len(graph.get('nodes', {}))}")
    print(f"   边: {len(graph.get('edges', []))}")
    print(f"   社区: {len(set(n.get('community') for n in graph.get('nodes', {}).values() if n.get('community') is not None))}")

    generate_readme(repo_name, graph, report, out_dir)

    # Copy interactive viz
    src_html = repo_path / "graphify-out" / "graph.html"
    if src_html.exists():
        import shutil
        shutil.copy2(src_html, out_dir / "graph.html")
        print(f"  graph.html — copied")

    print(f"\n✅ Done → {out_dir}/")
    print(f"   打开 {out_dir}/README.md 查看代码知识")


if __name__ == "__main__":
    main()

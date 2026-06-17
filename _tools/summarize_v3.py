#!/usr/bin/env python3
"""
mywiki summarize v3 — 语义索引优化版

目标：生成适合人类快速查阅 + AI 语义索引的文档
特点：
- 每层都有关键词标签，便于语义匹配
- 关键概念必须带精确行号
- 结构扁平，避免深度嵌套
- 增加"查询路径"章节，明示用户问题如何映射到代码

输出格式：CodeNotes/<system>/<repo>/<doc_type>.md
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

VAULT = Path.home() / "Documents/Code/work/mywiki"
PIPELINE_DIR = Path.home() / ".mywiki_pipeline"
CACHE_FILE = PIPELINE_DIR / "cache" / ".summarize_v3_cache.json"

REPO_SEARCH_PATHS = [
    Path.home() / "Documents/Code/work",
    Path.home() / ".cache/mywiki-repos",
]

# 关键目录优先级
KEY_DIRS = ["api", "factory", "db/model", "db", "server.go"]


def find_repo_path(repo_name: str) -> Optional[Path]:
    for base in REPO_SEARCH_PATHS:
        for subdir in base.iterdir() if base.exists() else []:
            if not subdir.is_dir():
                continue
            candidate = subdir / repo_name
            if candidate.exists() and (candidate / ".git").exists():
                return candidate
    return None


def read_go_files(repo_path: Path, max_file_size_kb: int = 512) -> List[Dict[str, str]]:
    files = []
    
    for go_file in repo_path.rglob("*.go"):
        rel_path = str(go_file.relative_to(repo_path))
        if any(p in rel_path for p in ("vendor/", ".git/", "third_party/")):
            continue
        if go_file.name.endswith("_test.go"):
            continue
        if ".pb.go" in go_file.name:
            continue
        
        size_kb = go_file.stat().st_size / 1024
        if size_kb > max_file_size_kb:
            files.append({
                "path": rel_path,
                "content": f"// File too large ({size_kb:.0f}KB), skipped\n",
                "priority": 99,
                "skipped": True,
            })
            continue
        
        try:
            content = go_file.read_text(errors="replace")
            priority = 99
            for i, key in enumerate(KEY_DIRS):
                if key in rel_path:
                    priority = i
                    break
            
            files.append({
                "path": rel_path,
                "content": content,
                "lines": len(content.splitlines()),
                "priority": priority,
                "size_kb": size_kb
            })
        except Exception as e:
            files.append({
                "path": rel_path,
                "content": f"// Error reading file: {e}\n",
                "priority": 99,
                "error": str(e)
            })
    
    files.sort(key=lambda x: (x["priority"], x["path"]))
    return files


def format_code_for_llm(files: List[Dict[str, str]], max_chars: int = 150000) -> str:
    chunks = []
    total_chars = 0
    
    for f in files:
        path = f["path"]
        content = f["content"]
        lines = f.get("lines", 0)
        
        numbered_content = "\n".join(
            f"{i+1:4d}| {line}" 
            for i, line in enumerate(content.splitlines())
        )
        
        chunk = f"=== {path} ({lines} lines) ===\n{numbered_content}\n"
        
        if total_chars + len(chunk) > max_chars:
            chunks.append(f"\n... [代码截断，剩余 {len(files) - len(chunks)} 个文件] ...")
            break
        
        chunks.append(chunk)
        total_chars += len(chunk)
    
    header = f"# Repository Code ({len(files)} files)\n\n"
    return header + "\n".join(chunks)


def call_llm(prompt: str, model: Optional[str] = None) -> Optional[str]:
    provider = os.environ.get("LLM_PROVIDER", "auto").lower()
    
    if provider == "auto":
        if os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY"):
            base = os.environ.get("ANTHROPIC_BASE_URL", "")
            if not base or "anthropic.com" in base:
                provider = "anthropic"
            else:
                provider = "openai"
        else:
            provider = "openai"
    
    api_key = (os.environ.get("LLM_API_KEY")
               or os.environ.get("ANTHROPIC_AUTH_TOKEN")
               or os.environ.get("ANTHROPIC_API_KEY"))
    if not api_key:
        print(" ⚠ API key 未设置")
        return None
    
    base_url = (os.environ.get("LLM_BASE_URL")
                or os.environ.get("ANTHROPIC_BASE_URL"))
    
    if model is None:
        model = os.environ.get("LLM_MODEL", "deepseek-ai/DeepSeek-V3.2")
    
    try:
        if provider == "anthropic":
            import anthropic
            client = anthropic.Anthropic(api_key=api_key, base_url=base_url or None)
            msg = client.messages.create(
                model=model,
                max_tokens=8000,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text
        else:
            from openai import OpenAI
            if base_url and not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"
            client = OpenAI(api_key=api_key, base_url=base_url or "https://api.openai.com/v1")
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=8000,
                temperature=0.1,  # 更低温度，更确定性
            )
            return resp.choices[0].message.content
    except Exception as e:
        print(f" ⚠ LLM 错误: {e}")
        return None


# ─── 优化后的 Prompt ───────────────────────────────────────────

DOC_TYPES = {
    "architecture": {
        "title": "架构设计",
        "keywords": ["路由", "Factory", "分层", "调用链", "初始化"],
        "query_paths": [
            "入口在哪里？ -> 路由模式 + 分发逻辑",
            "怎么调用外部服务？ -> Factory 6客户端",
            "创建Endpoint流程？ -> CreateVPCEndpoint 10步调用链",
            "配置怎么加载？ -> Config 嵌套结构 + VerifyParams",
        ]
    },
    "api": {
        "title": "API文档",
        "keywords": ["Action", "请求结构", "校验规则", "错误码", "路由"],
        "query_paths": [
            "有哪些接口？ -> 19个Action列表",
            "请求参数怎么校验？ -> validate tag规则",
            "错误码有哪些？ -> ErrCodeDefine 映射",
            "怎么新增接口？ -> Action常量 + handle switch-case + 处理器函数",
        ]
    },
    "db": {
        "title": "数据库设计",
        "keywords": ["表结构", "字段含义", "GORM", "关联", "软删除"],
        "query_paths": [
            "有哪些表？ -> 6张表及用途",
            "字段什么意思？ -> 核心字段业务含义",
            "表之间什么关系？ -> ER关联图",
            "怎么查白名单？ -> GetServicesWhiteListRecordsByServiceIDAndCompanyIDs",
        ]
    },
    "integration": {
        "title": "外部依赖",
        "keywords": ["Factory", "VPC", "LB", "L4", "计费", "账号", "ZK"],
        "query_paths": [
            "怎么调VPC？ -> VPC.AllocateIPv4 等",
            "怎么调计费？ -> UBill.BuyEndpointPostPaidResource",
            "怎么查公司信息？ -> UAccount.FetchCompanyInfosByCompanyIDs",
            "L4怎么发现？ -> L4APISvrZKPath + ZooKeeper",
        ]
    },
    "config": {
        "title": "配置文档",
        "keywords": ["配置项", "必填", "默认值", "验证", "DSN"],
        "query_paths": [
            "哪些配置必填？ -> VerifyParams 检查的4项",
            "默认值是什么？ -> SetDefaultValue 设置",
            "Region在哪里配？ -> APIConfig.RegionID",
            "数据库怎么配？ -> DBConfig.DSN",
        ]
    }
}


def build_prompt(doc_type: str, repo_name: str, code: str, system_name: str = "") -> str:
    doc_info = DOC_TYPES.get(doc_type, DOC_TYPES["architecture"])
    keywords = ", ".join(doc_info["keywords"])
    query_paths = "\n".join(f"  - {p}" for p in doc_info["query_paths"])
    
    return f"""你是资深软件架构师。根据以下 Go 源代码，生成**{doc_info['title']}**文档。

【核心目标】
文档要同时服务两个场景：
1. 人类快速查阅：一眼看到核心概念和关键流程
2. AI 语义索引：通过关键词/问题能快速定位代码位置

【源代码】
{code}

【输出要求】

## 1. 一句话概述
用 1-2 句话概括这个服务的核心职责和关键特点。

## 2. 核心概念索引（必须带行号）
列出 5-10 个核心概念，每个包含：
- 概念名称
- 一句话解释
- 关键代码位置 [文件:行号]

示例格式：
- **统一 Action 分发**: 所有请求 POST 到 `/`，通过 `Action` 字段路由，非 RESTful。位置 [api/api.go:130-210]
- **Factory 模式**: 6 个外部客户端封装，依赖注入给 API 层。位置 [factory/factory.go:13-20]

关键词覆盖：{keywords}

## 3. 查询路径（QA映射）
列出用户常见问题到代码的映射：
{query_paths}

每个路径必须给出精确的代码位置 [文件:行号]。

## 4. 关键实现细节（扁平列表）
用 bullet list 列出最重要的实现点，每项格式：
- 要点描述 [文件:行号]
- 子要点（如参数说明、条件分支）

禁止长段落，必须扁平化。

## 5. 涉及文件清单
列出本主题涉及的关键文件及其作用。

【格式规则】
1. 行号格式：`[file.go:12]` 或 `[file.go:12-34]`
2. 代码中的行号格式是 `  12| content`，直接引用数字部分
3. 禁止废话：每句话必须有信息增量
4. 禁止编造：不确定的内容标注"未在代码中体现"
"""


def generate_doc(repo_name: str, repo_path: Path, doc_type: str,
                 system_name: str, force: bool = False) -> bool:
    cache = {}
    if CACHE_FILE.exists():
        cache = json.loads(CACHE_FILE.read_text())
    
    cache_key = f"{repo_name}:{doc_type}"
    
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_path, capture_output=True, text=True, timeout=10
        )
        commit = result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        commit = "unknown"
    
    prev = cache.get(cache_key, {})
    if not force and prev.get("commit") == commit:
        print(f"    · {doc_type}.md: unchanged")
        return True
    
    print(f"    → 读取代码...", end="", flush=True)
    files = read_go_files(repo_path)
    total_lines = sum(f.get("lines", 0) for f in files if "lines" in f)
    print(f" {len(files)} files, {total_lines} lines")
    
    code = format_code_for_llm(files)
    
    prompt = build_prompt(doc_type, repo_name, code, system_name)
    
    print(f"    → {doc_type}.md LLM 生成...", end="", flush=True)
    content = call_llm(prompt)
    if not content:
        print(" ✗ 失败")
        return False
    
    output_dir = VAULT / "CodeNotes" / system_name / repo_name
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 提取关键词用于 frontmatter
    doc_info = DOC_TYPES.get(doc_type, DOC_TYPES["architecture"])
    keywords_str = ", ".join(doc_info["keywords"])
    
    frontmatter = f"""---
tags: [codenotes, {repo_name}, {doc_type}, {keywords_str}]
system: {system_name}
repo: {repo_name}
doc_type: {doc_type}
keywords: [{keywords_str}]
commit: {commit[:12]}
updated: {datetime.now().strftime('%Y-%m-%d')}
status: auto-generated-v3-index
code_files: {len(files)}
code_lines: {total_lines}
---

"""
    
    out_file = output_dir / f"{doc_type}.md"
    out_file.write_text(frontmatter + content)
    print(f" ✓ [{len(content)} chars]")
    
    cache[cache_key] = {
        "commit": commit,
        "generated_at": datetime.now().isoformat()
    }
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))
    
    return True


def generate_all_docs(repo_name: str, system_name: str,
                      target_doc: Optional[str] = None,
                      force: bool = False):
    repo_path = find_repo_path(repo_name)
    if not repo_path:
        print(f"  ✗ {repo_name}: 未找到 repo")
        return False
    
    print(f"\n  [{repo_name}] {repo_path}")
    
    doc_types = [target_doc] if target_doc else list(DOC_TYPES.keys())
    
    success = 0
    for doc_type in doc_types:
        if generate_doc(repo_name, repo_path, doc_type, system_name, force):
            success += 1
    
    return success == len(doc_types)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="mywiki summarize v3 — 语义索引优化版")
    parser.add_argument("--system", "-s", help="指定系统")
    parser.add_argument("--repo", "-r", help="指定仓库（必需）")
    parser.add_argument("--doc", "-d", choices=list(DOC_TYPES.keys()),
                        help="只生成特定文档类型")
    parser.add_argument("--force", action="store_true", help="强制重新生成")
    args = parser.parse_args()
    
    if not args.repo:
        print("✗ 请指定 --repo")
        sys.exit(1)
    
    system = args.system or "unknown"
    
    print(f"\n{'─'*60}")
    print("  mywiki summarize v3 — 语义索引优化版")
    print(f"{'─'*60}")
    
    generate_all_docs(args.repo, system, args.doc, args.force)
    
    print(f"\n{'─'*60}")
    print("  完成")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()

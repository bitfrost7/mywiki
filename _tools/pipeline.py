#!/usr/bin/env python3
"""
mywiki Pipeline — 代码→知识库文档生成流程

架构：
  原始代码 → 结构提取 → 语义分块 → LLM分层生成 → 索引 → 知识库文档

依赖：
  - Python 3.10+ (标准库)
  - ollama (本地嵌入服务)
  - 外部 API: DeepSeek-V3.2 (代码理解)

用法：
  python3 pipeline.py --system privatelink --repo apisvr    # 单仓库
  python3 pipeline.py --system privatelink                   # 单系统
  python3 pipeline.py                                        # 全量
  python3 pipeline.py --index-only                           # 仅更新索引
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import urllib.request
import urllib.error

# ─── 配置 ────────────────────────────────────────────────────────

VAULT = Path.home() / "Documents/Code/work/mywiki"
TOOLS_DIR = VAULT / "_tools"
CONFIG_FILE = VAULT / "config.yaml"

# 工作目录
CACHE_DIR = Path.home() / ".cache/mywiki-repos"
WORK_DIR = Path.home() / ".mywiki_pipeline"
SYMBOLS_DIR = WORK_DIR / "symbols"
EMBED_DIR = WORK_DIR / "embeddings"
STATE_FILE = WORK_DIR / "pipeline_state.json"

# Ollama 配置
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_EMBED_MODEL = "nomic-embed-text:latest"

# ─── 核心数据模型 ────────────────────────────────────────────────

class CodeChunk:
    """代码语义块 - Pipeline 的核心数据单元"""

    def __init__(self, repo: str, file: str, lines: tuple, code: str,
                 chunk_type: str, symbols: List[str], context: str = ""):
        self.repo = repo           # 仓库名
        self.file = file           # 相对文件路径
        self.lines = lines         # (start, end) 行号
        self.code = code           # 代码内容（已截断）
        self.type = chunk_type     # architecture | api | db | integration | config
        self.symbols = symbols     # 包含的符号名列表
        self.context = context     # 上下文描述（来自父级结构）

        # 生成的字段
        self.doc: Optional[str] = None      # 生成的人类可读文档
        self.embedding: Optional[List[float]] = None  # 语义向量
        self.doc_path: Optional[str] = None # 输出文档路径

    def source_ref(self) -> str:
        """返回源代码引用标记，如 `internal/api/handler.go:42-56`"""
        return f"`{self.file}:{self.lines[0]}-{self.lines[1]}`"

    def to_prompt(self, max_chars: int = 8000) -> str:
        """转换为 LLM Prompt 格式"""
        header = f"【{self.type.upper()}】{self.file}:{self.lines[0]}-{self.lines[1]}"
        if self.context:
            header += f"\n上下文: {self.context}"
        if len(self.code) > max_chars:
            code = self.code[:max_chars] + f"\n... (truncated, total {len(self.code)} chars)"
        else:
            code = self.code
        return f"{header}\n\n```go\n{code}\n```"

    def to_dict(self) -> dict:
        return {
            "repo": self.repo,
            "file": self.file,
            "lines": self.lines,
            "type": self.type,
            "symbols": self.symbols,
            "context": self.context,
            "source_ref": self.source_ref(),
        }


class RepoKnowledge:
    """单个仓库的知识库 - 包含分层文档"""

    def __init__(self, system: str, repo: str):
        self.system = system
        self.repo = repo
        self.chunks: List[CodeChunk] = []

        # 分层生成的文档
        self.overview: Optional[str] = None      # 第1层：项目概览
        self.architecture: Optional[str] = None  # 第2层：架构设计
        self.modules: Dict[str, str] = {}        # 第3层：模块详情 (模块名 → 文档)
        self.apis: Optional[str] = None          # API 文档
        self.db: Optional[str] = None            # 数据库文档
        self.relationships: Optional[str] = None # 第4层：模块关系图

    def add_chunk(self, chunk: CodeChunk):
        self.chunks.append(chunk)

    def get_chunks_by_type(self, chunk_type: str) -> List[CodeChunk]:
        return [c for c in self.chunks if c.type == chunk_type]


# ─── 阶段 1: 结构提取 ──────────────────────────────────────────────

class StructureExtractor:
    """从源码提取结构化信息，生成 CodeChunk"""

    KEY_PATTERNS = {
        "api": [
            r"func.*Handler.*\(", r"func.*Controller.*\(", r"func.*API.*\(", r"gin\.(GET|POST|PUT|DELETE)",
            r"http\.Handle", r"mux\.Handle", r"echo\.(GET|POST)", r"fiber\.(Get|Post)",
        ],
        "db": [
            r"type.*Model.*struct", r"func.*TableName\(\)", r"gorm:", r"sql\.",
            r"CREATE TABLE", r"ALTER TABLE", r"type.*DAO.*struct",
        ],
        "config": [
            r"type.*Config.*struct", r"viper\.", r"yaml:", r"json:\"", r"env:\"",
            r"const.*=.*\(", r"var.*=.*\(", r"func init\(\)",
        ],
        "integration": [
            r"factory\.", r"client\.", r"grpc\.", r"http\.Client", r"rpc\.",
            r"kafka\.", r"redis\.", r"db\.",
        ],
    }

    def __init__(self, max_file_size_kb: int = 512):
        self.max_file_size = max_file_size_kb * 1024

    def extract_repo(self, repo_path: Path, repo_name: str) -> List[CodeChunk]:
        """提取整个仓库的代码块"""
        chunks = []

        for go_file in sorted(repo_path.rglob("*.go")):
            # 跳过测试文件、vendor、生成代码
            if self._should_skip(go_file, repo_path):
                continue

            file_chunks = self._extract_file(go_file, repo_path, repo_name)
            chunks.extend(file_chunks)

        return chunks

    def _should_skip(self, filepath: Path, repo_root: Path) -> bool:
        """判断文件是否应该跳过"""
        rel = str(filepath.relative_to(repo_root))

        skip_patterns = [
            "_test.go", "vendor/", "third_party/", "generated/",
            ".pb.go", ".pb.gw.go", ".mock.go", "_gen.go",
            "node_modules/", "dist/", "build/",
        ]

        if any(p in rel for p in skip_patterns):
            return True

        # 文件大小检查
        try:
            if filepath.stat().st_size > self.max_file_size:
                return True
        except:
            return True

        return False

    def _extract_file(self, filepath: Path, repo_root: Path, repo_name: str) -> List[CodeChunk]:
        """从单个 Go 文件提取代码块"""
        chunks = []
        rel_path = str(filepath.relative_to(repo_root))

        try:
            content = filepath.read_text(errors="replace")
            lines = content.splitlines()
        except:
            return chunks

        # 简单状态机提取顶级定义
        current_block = []
        block_start = 0
        in_block = False
        brace_count = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # 检测代码块开始（函数、类型定义）
            if not in_block and self._is_block_start(stripped):
                in_block = True
                block_start = i
                current_block = [line]
                brace_count = line.count("{") - line.count("}")
            elif in_block:
                current_block.append(line)
                brace_count += line.count("{") - line.count("}")

                # 块结束
                if brace_count <= 0 and line.strip() == "}":
                    code = "\n".join(current_block)
                    chunk_type = self._classify_chunk(code)
                    symbols = self._extract_symbols(code)

                    chunk = CodeChunk(
                        repo=repo_name,
                        file=rel_path,
                        lines=(block_start + 1, i + 1),
                        code=code,
                        chunk_type=chunk_type,
                        symbols=symbols,
                        context=self._extract_context(lines, block_start)
                    )
                    chunks.append(chunk)

                    in_block = False
                    current_block = []

        return chunks

    def _is_block_start(self, line: str) -> bool:
        """判断是否是代码块开始"""
        return bool(re.match(r"^(func|type|const|var)\s+", line))

    def _classify_chunk(self, code: str) -> str:
        """根据代码内容分类"""
        code_lower = code.lower()

        for chunk_type, patterns in self.KEY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, code, re.IGNORECASE):
                    return chunk_type

        # 默认根据内容判断
        if "interface" in code_lower:
            return "architecture"
        if re.search(r"func\s+\w+.*\(.*http\.", code):
            return "api"

        return "integration"  # 默认归类为集成

    def _extract_symbols(self, code: str) -> List[str]:
        """提取代码中的符号名"""
        symbols = []

        # 函数名
        func_match = re.search(r"func\s+(?:\([^)]+\)\s*)?(\w+)", code)
        if func_match:
            symbols.append(func_match.group(1))

        # 类型名
        type_match = re.search(r"type\s+(\w+)", code)
        if type_match:
            symbols.append(type_match.group(1))

        return symbols

    def _extract_context(self, lines: List[str], block_start: int) -> str:
        """提取块上方的注释作为上下文"""
        context_lines = []
        for i in range(block_start - 1, max(-1, block_start - 10), -1):
            line = lines[i].strip()
            if line.startswith("//"):
                context_lines.insert(0, line[2:].strip())
            elif line == "" or line == "*/":
                continue
            else:
                break

        return " ".join(context_lines) if context_lines else ""


# ─── 阶段 2: 语义嵌入 ──────────────────────────────────────────────

class EmbeddingIndexer:
    """使用 Ollama nomic-embed-text 生成语义向量"""

    def __init__(self, host: str = OLLAMA_HOST, model: str = OLLAMA_EMBED_MODEL):
        self.host = host
        self.model = model

    def embed(self, text: str) -> Optional[List[float]]:
        """调用 Ollama 生成嵌入向量"""
        try:
            payload = json.dumps({
                "model": self.model,
                "input": text[:8192]  # nomic-embed-text 最大输入
            }).encode()

            req = urllib.request.Request(
                f"{self.host}/api/embed",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
                # Ollama 返回格式: {"embeddings": [[...]]}
                if "embeddings" in result and result["embeddings"]:
                    return result["embeddings"][0]
                return None

        except Exception as e:
            print(f"Embedding failed: {e}")
            return None

    def embed_chunks(self, chunks: List[CodeChunk], cache_path: Optional[Path] = None) -> bool:
        """批量嵌入代码块，支持缓存"""
        print(f"Generating embeddings for {len(chunks)} chunks...")

        for i, chunk in enumerate(chunks):
            # 生成嵌入文本（代码 + 上下文）
            embed_text = f"{chunk.type}: {chunk.file}\n{chunk.context}\n{chunk.code[:2000]}"
            chunk.embedding = self.embed(embed_text)

            if i % 10 == 0:
                print(f"  Progress: {i}/{len(chunks)}")

        # 保存缓存
        if cache_path:
            self._save_embeddings(chunks, cache_path)

        return True

    def _save_embeddings(self, chunks: List[CodeChunk], path: Path):
        """保存嵌入到本地缓存"""
        data = {
            "model": self.model,
            "timestamp": datetime.now().isoformat(),
            "chunks": [
                {
                    "repo": c.repo,
                    "file": c.file,
                    "lines": c.lines,
                    "type": c.type,
                    "symbols": c.symbols,
                    "embedding": c.embedding,
                }
                for c in chunks if c.embedding is not None
            ]
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2))

    def load_embeddings(self, path: Path) -> Dict[str, List[float]]:
        """加载缓存的嵌入"""
        if not path.exists():
            return {}

        data = json.loads(path.read_text())
        return {
            f"{c['file']}:{c['lines'][0]}-{c['lines'][1]}": c["embedding"]
            for c in data.get("chunks", [])
        }


# ─── 阶段 3: LLM 文档生成 ──────────────────────────────────────────

class LLMDocGenerator:
    """调用 DeepSeek-V3.2 生成分层知识库文档"""

    # 分层生成 Prompt 模板

    PROMPT_OVERVIEW = """你是一个资深软件架构师，需要为代码仓库生成项目概览文档。

【任务】基于以下代码片段，生成简洁的项目概览（中文）：

{chunks}

【输出要求】
1. 项目名称和一句话描述
2. 核心职责（2-3 点）
3. 技术栈（语言、框架、关键依赖）
4. 目录结构简述

【格式】Markdown，使用二级标题，控制在 300 字以内。
"""

    PROMPT_ARCHITECTURE = """基于以下代码信息，生成架构设计文档。

【项目】{repo}
【代码片段】
{chunks}

【任务】分析并输出：
1. 整体架构模式（如分层架构、微服务、DDD）
2. 核心模块划分及职责
3. 关键接口/抽象定义
4. 数据流概览

【格式要求】
- 使用 Markdown 三级标题组织
- 每个模块用表格列出：模块名 | 文件位置 | 职责
- 关键接口标注代码来源，如 `internal/api/handler.go:42`
"""

    PROMPT_MODULE = """为以下代码模块生成详细文档。

【模块】{module_name}
【所属】{repo}
【代码】
```go
{code}
```

【任务】输出：
1. 模块职责（一句话）
2. 主要类型/函数清单（表格：名称 | 类型 | 功能简述 | 行号）
3. 关键实现逻辑（2-3 段描述）
4. 外部依赖（调用了哪些其他模块）

【格式】Markdown，简洁明了，避免大段代码粘贴。
"""

    PROMPT_API = """分析以下 HTTP/gRPC 接口代码，生成 API 文档。

【代码片段】
{chunks}

【输出格式】
| 接口路径 | 方法 | 处理函数 | 文件位置 |
|---------|------|---------|----------|
| /api/v1/... | GET | GetUser | handler.go:45 |

【附加说明】对每个关键接口，用 1 句话描述其业务含义。
"""

    PROMPT_DB = """分析以下数据库模型代码，生成数据模型文档。

【代码片段】
{chunks}

【输出格式】
| 表名/模型 | 字段 | 类型 | 说明 | 文件位置 |
|----------|------|------|------|----------|

【附加】列出关键 SQL 操作或 DAO 方法。
"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config = self._load_config(config_path)
        self.base_url = self.config.get("llm", {}).get("base_url", "")
        self.api_key = os.getenv("ANTHROPIC_AUTH_TOKEN", "")
        self.model = self.config.get("llm", {}).get("default_model", "deepseek-ai/DeepSeek-V3.2")

    def _load_config(self, path: Path) -> dict:
        """加载 YAML 配置"""
        try:
            import yaml
            return yaml.safe_load(path.read_text())
        except:
            # 基础默认配置
            return {
                "llm": {
                    "base_url": "https://api.modelverse.cn",
                    "default_model": "deepseek-ai/DeepSeek-V3.2"
                },
                "generation": {
                    "max_tokens": 8000,
                    "temperature": 0.2
                }
            }

    def generate(self, prompt: str, max_tokens: int = 8000) -> str:
        """调用 LLM API 生成文档"""
        try:
            payload = json.dumps({
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.2,
            }).encode()

            req = urllib.request.Request(
                f"{self.base_url}/v1/chat/completions",
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=120) as resp:
                result = json.loads(resp.read().decode())
                return result["choices"][0]["message"]["content"]

        except Exception as e:
            return f"生成失败: {e}"

    def generate_overview(self, knowledge: RepoKnowledge) -> str:
        """第1层：生成项目概览"""
        # 选取代表性代码块（最多 5 个）
        chunks = knowledge.chunks[:5]
        chunks_text = "\n\n---\n\n".join([c.to_prompt(2000) for c in chunks])

        prompt = self.PROMPT_OVERVIEW.format(chunks=chunks_text)
        return self.generate(prompt, max_tokens=2000)

    def generate_architecture(self, knowledge: RepoKnowledge) -> str:
        """第2层：生成架构文档"""
        # 按类型选取关键代码块
        arch_chunks = knowledge.get_chunks_by_type("architecture")[:10]
        api_chunks = knowledge.get_chunks_by_type("api")[:5]

        all_chunks = arch_chunks + api_chunks
        chunks_text = "\n\n---\n\n".join([c.to_prompt(1500) for c in all_chunks])

        prompt = self.PROMPT_ARCHITECTURE.format(
            repo=knowledge.repo,
            chunks=chunks_text
        )
        return self.generate(prompt, max_tokens=4000)

    def generate_module_docs(self, knowledge: RepoKnowledge) -> Dict[str, str]:
        """第3层：为每个模块生成详细文档"""
        # 按文件分组，每个文件作为一个模块
        file_chunks: Dict[str, List[CodeChunk]] = {}
        for c in knowledge.chunks:
            file_chunks.setdefault(c.file, []).append(c)

        module_docs = {}
        for file_path, chunks in list(file_chunks.items())[:10]:  # 限制前10个文件
            module_name = Path(file_path).stem
            code_sample = chunks[0].code[:3000] if chunks else ""

            prompt = self.PROMPT_MODULE.format(
                module_name=module_name,
                repo=knowledge.repo,
                code=code_sample
            )
            module_docs[module_name] = self.generate(prompt, max_tokens=3000)

        return module_docs

    def generate_api_doc(self, knowledge: RepoKnowledge) -> str:
        """生成 API 汇总文档"""
        api_chunks = knowledge.get_chunks_by_type("api")[:15]
        if not api_chunks:
            return "无 API 代码"

        chunks_text = "\n\n---\n\n".join([c.to_prompt(1000) for c in api_chunks])
        prompt = self.PROMPT_API.format(chunks=chunks_text)
        return self.generate(prompt, max_tokens=3000)

    def generate_db_doc(self, knowledge: RepoKnowledge) -> str:
        """生成数据库文档"""
        db_chunks = knowledge.get_chunks_by_type("db")[:15]
        if not db_chunks:
            return "无数据库模型代码"

        chunks_text = "\n\n---\n\n".join([c.to_prompt(1000) for c in db_chunks])
        prompt = self.PROMPT_DB.format(chunks=chunks_text)
        return self.generate(prompt, max_tokens=3000)


# ─── 阶段 4: 文档组装与输出 ───────────────────────────────────────

class DocAssembler:
    """将生成的内容组装成最终知识库文档"""

    def __init__(self, vault_path: Path = VAULT):
        self.vault_path = vault_path

    def assemble(self, knowledge: RepoKnowledge) -> List[Path]:
        """组装并写入所有文档"""
        output_dir = self.vault_path / "CodeNotes" / knowledge.system / knowledge.repo
        output_dir.mkdir(parents=True, exist_ok=True)

        generated_files = []

        # 1. 主文档 README.md
        main_doc = self._build_main_doc(knowledge)
        main_path = output_dir / "README.md"
        main_path.write_text(main_doc)
        generated_files.append(main_path)

        # 2. 分类型文档
        if knowledge.architecture:
            arch_path = output_dir / "architecture.md"
            arch_path.write_text(knowledge.architecture)
            generated_files.append(arch_path)

        if knowledge.apis:
            api_path = output_dir / "api.md"
            api_path.write_text(knowledge.apis)
            generated_files.append(api_path)

        if knowledge.db:
            db_path = output_dir / "db.md"
            db_path.write_text(knowledge.db)
            generated_files.append(db_path)

        # 3. 模块详情（子目录）
        modules_dir = output_dir / "modules"
        modules_dir.mkdir(exist_ok=True)
        for module_name, doc in knowledge.modules.items():
            # 清理文件名
            safe_name = re.sub(r'[^\w\-]', '_', module_name)
            mod_path = modules_dir / f"{safe_name}.md"
            mod_path.write_text(doc)
            generated_files.append(mod_path)

        return generated_files

    def _build_main_doc(self, knowledge: RepoKnowledge) -> str:
        """构建主文档"""
        lines = [
            f"# {knowledge.repo}",
            "",
            f"所属系统: [[{knowledge.system}]]",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "## 文档索引",
            "",
            "| 文档 | 说明 |",
            "|------|------|",
        ]

        if knowledge.architecture:
            lines.append(f"| [架构设计](./architecture.md) | 整体架构与模块划分 |")
        if knowledge.apis:
            lines.append(f"| [API 文档](./api.md) | 接口清单与说明 |")
        if knowledge.db:
            lines.append(f"| [数据模型](./db.md) | 数据库表结构 |")
        if knowledge.modules:
            lines.append(f"| [模块详情](./modules/) | 各模块详细文档 ({len(knowledge.modules)} 个) |")

        lines.extend([
            "",
            "## 项目概览",
            "",
            knowledge.overview or "（待生成）",
            "",
            "---",
            "",
            "*由 mywiki Pipeline 自动生成*",
        ])

        return "\n".join(lines)


# ─── 主控 Pipeline ────────────────────────────────────────────────

class Pipeline:
    """代码→知识库文档完整 Pipeline"""

    def __init__(self):
        self.extractor = StructureExtractor(max_file_size_kb=512)
        self.embedder = EmbeddingIndexer()
        self.generator = LLMDocGenerator()
        self.assembler = DocAssembler()

    def run(self, system: Optional[str] = None, repo: Optional[str] = None,
            skip_embed: bool = False, skip_generate: bool = False) -> List[Path]:
        """
        运行完整 Pipeline

        Args:
            system: 指定系统名，None 表示所有系统
            repo: 指定仓库名，None 表示所有仓库
            skip_embed: 跳过嵌入阶段
            skip_generate: 跳过 LLM 生成（仅做结构提取）
        """
        print("=" * 60)
        print("mywiki Pipeline — 代码→知识库文档生成")
        print("=" * 60)

        # 1. 获取仓库列表
        repos = self._get_target_repos(system, repo)
        print(f"\n目标仓库: {len(repos)} 个")

        all_generated = []

        for system_name, repo_name, repo_path in repos:
            print(f"\n--- 处理: {system_name}/{repo_name} ---")

            knowledge = RepoKnowledge(system_name, repo_name)

            # 阶段 1: 结构提取
            print("[1/4] 提取代码结构...")
            chunks = self.extractor.extract_repo(repo_path, repo_name)
            for c in chunks:
                knowledge.add_chunk(c)
            print(f"      提取 {len(chunks)} 个代码块")

            # 阶段 2: 语义嵌入
            if not skip_embed:
                print("[2/4] 生成语义嵌入 (Ollama)...")
                embed_cache = EMBED_DIR / f"{system_name}_{repo_name}.json"
                self.embedder.embed_chunks(chunks, embed_cache)
                print(f"      嵌入已缓存: {embed_cache}")

            # 阶段 3: LLM 生成
            if not skip_generate:
                print("[3/4] 生成知识库文档 (DeepSeek-V3.2)...")
                print("      - 生成项目概览...")
                knowledge.overview = self.generator.generate_overview(knowledge)

                print("      - 生成架构文档...")
                knowledge.architecture = self.generator.generate_architecture(knowledge)

                print("      - 生成 API 文档...")
                knowledge.apis = self.generator.generate_api_doc(knowledge)

                print("      - 生成 DB 文档...")
                knowledge.db = self.generator.generate_db_doc(knowledge)

                print("      - 生成模块详情...")
                knowledge.modules = self.generator.generate_module_docs(knowledge)

            # 阶段 4: 组装输出
            print("[4/4] 写入知识库文档...")
            files = self.assembler.assemble(knowledge)
            for f in files:
                print(f"      ✓ {f.relative_to(VAULT)}")
            all_generated.extend(files)

        print(f"\n{'=' * 60}")
        print(f"Pipeline 完成，共生成 {len(all_generated)} 个文档")
        print(f"知识库位置: {VAULT}/CodeNotes/")
        print("=" * 60)

        return all_generated

    def _get_target_repos(self, system: Optional[str], repo: Optional[str]):
        """获取目标仓库列表"""
        repos = []

        # 加载配置
        try:
            import yaml
            config = yaml.safe_load((TOOLS_DIR / "repo_config.yaml").read_text())
        except:
            config = {"systems": {}}

        for sys_name, sys_config in config.get("systems", {}).items():
            if system and sys_name != system:
                continue

            for repo_info in sys_config.get("repos", []):
                repo_url = repo_info if isinstance(repo_info, str) else repo_info.get("url")
                repo_name = repo_url.split("/")[-1].replace(".git", "")

                if repo and repo_name != repo:
                    continue

                repo_path = CACHE_DIR / repo_name
                if repo_path.exists():
                    repos.append((sys_name, repo_name, repo_path))

        return repos


# ─── CLI ────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(description="mywiki Pipeline — 代码→知识库文档")
    parser.add_argument("--system", help="指定系统名")
    parser.add_argument("--repo", help="指定仓库名")
    parser.add_argument("--skip-embed", action="store_true", help="跳过嵌入阶段")
    parser.add_argument("--skip-generate", action="store_true", help="跳过 LLM 生成")
    parser.add_argument("--index-only", action="store_true", help="仅更新索引（同 --skip-generate）")

    args = parser.parse_args()

    if args.index_only:
        args.skip_generate = True

    pipeline = Pipeline()
    pipeline.run(
        system=args.system,
        repo=args.repo,
        skip_embed=args.skip_embed,
        skip_generate=args.skip_generate
    )


if __name__ == "__main__":
    main()

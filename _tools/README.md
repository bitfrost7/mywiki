# _tools — CodeNotes Pipeline

mywiki 代码笔记 Pipeline 工具集。从 GitLab 拉取代码、提取符号、生成结构化的 CodeNotes。

---

## 推荐：新版 LLM Pipeline

使用 DeepSeek-V3.2 + Ollama 嵌入的完整代码→知识库文档流程：

```bash
# 一键运行完整流程（提取 + 嵌入 + 生成）
python3 pipeline.py --system privatelink --repo apisvr
```

架构：

```
原始代码
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段 1: 结构提取 (StructureExtractor)                   │
│  - 解析 Go 源码，提取函数/类型/接口                        │
│  - 按语义分类: api | db | config | integration            │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段 2: 语义嵌入 (Ollama nomic-embed-text)              │
│  - 本地生成语义向量                                       │
│  - 建立代码块的语义索引                                   │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段 3: LLM 分层生成 (DeepSeek-V3.2)                    │
│  第1层: 项目概览 (overview)                              │
│  第2层: 架构设计 (architecture)                          │
│  第3层: 模块详情 (modules)                               │
│  专项: API 文档 (api) | 数据模型 (db)                     │
└─────────────────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│ 阶段 4: 文档组装 (DocAssembler)                         │
│  - 整合为可读 Markdown                                   │
│  - 输出到 CodeNotes/<system>/<repo>/                     │
└─────────────────────────────────────────────────────────┘
```

---

## 旧版 Pipeline（维护中）

```
Step 1: fetch_repos.py     →  从 GitLab 拉取/更新代码到 ~/.cache/mywiki-repos/
Step 2: extract.py         →  提取 Go/C 符号表 → ~/.mywiki_pipeline/symbols/
Step 3: summarize_v3.py    →  生成结构化笔记 → ~/mywiki/CodeNotes/
```

---

## 脚本说明

### 新版 Pipeline

| 脚本 | 作用 | 输入 | 输出 |
|------|------|------|------|
| `pipeline.py` | **主控脚本：代码→知识库完整流程** | 源码目录 | `~/mywiki/CodeNotes/**/*.md` |
| `prompts/` | LLM Prompt 模板目录 | - | 可定制的生成模板 |

### 旧版脚本

| 脚本 | 作用 | 输入 | 输出 |
|------|------|------|------|
| `fetch_repos.py` | 拉取/更新代码仓库 | `repo_config.yaml` | `~/.cache/mywiki-repos/` |
| `extract.py` | Go 代码符号提取 | 源码目录 | `~/.mywiki_pipeline/symbols/*.jsonl` |
| `extract_c.py` | C 代码符号提取 | 源码目录 | 被 extract.py 调用 |
| `analyze.py` | 代码依赖分析 | 符号表 | 依赖矩阵、调用图 |
| `summarize_v3.py` | 生成 CodeNotes Markdown | 符号表 + 源码 | `~/mywiki/CodeNotes/**/*.md` |
| `generate.py` | 批量生成笔记入口 | 配置 | 调用 summarize_v3 |
| `generate_relationship.py` | 生成模块关系图 | 依赖矩阵 | Mermaid 关系图 |

---

## 配置

### repo_config.yaml

定义要拉取的系统和仓库列表，支持：
- 系统分组（如 privatelink, utraffic）
- 每系统/仓库的分析器配置（语言、排除模式等）

```yaml
systems:
  privatelink:
    analyzer:
      languages: [go]
    repos:
      - url: git@git.example.com:team/repo.git
```

---

## 使用

### 新版 Pipeline（推荐）

```bash
cd /Users/user/Documents/Code/work/mywiki/_tools

# 完整流程：单仓库
python3 pipeline.py --system privatelink --repo apisvr

# 处理整个系统
python3 pipeline.py --system privatelink

# 跳过 LLM 生成（仅做结构提取和嵌入）
python3 pipeline.py --system privatelink --skip-generate

# 仅更新索引（已有文档，重新生成嵌入）
python3 pipeline.py --system privatelink --index-only
```

### 旧版 Pipeline

```bash
cd /Users/user/Documents/Code/work/mywiki/_tools

# Step 1: 拉取所有代码
python3 fetch_repos.py

# Step 2: 提取符号（Go）
python3 extract.py --system privatelink

# Step 3: 生成笔记
python3 summarize_v3.py --system privatelink --repo apisvr
```

### 增量更新

```bash
# 只更新有变化的仓库
python3 fetch_repos.py
python3 extract.py
python3 summarize_v3.py
```

### 单系统/单仓库

```bash
python3 fetch_repos.py --system privatelink
python3 extract.py --system privatelink --repo apisvr
python3 summarize_v3.py --system privatelink --repo apisvr
```

---

## 目录约定

| 路径 | 用途 |
|------|------|
| `~/.cache/mywiki-repos/` | 代码仓库缓存 |
| `~/.mywiki_pipeline/symbols/` | 符号表（JSONL） |
| `~/.mywiki_pipeline/cache/` | 状态缓存 |
| `~/mywiki/CodeNotes/<system>/<repo>/` | 生成的笔记 |

---

## 依赖

### 新版 Pipeline

- Python 3.10+（标准库，无外部依赖）
- [Ollama](https://ollama.com)（本地嵌入服务）
  - 模型：`nomic-embed-text:latest`
  - 启动：`ollama serve`
- API 访问：DeepSeek-V3.2（或 config.yaml 中配置的其他模型）
  - 需要设置 `ANTHROPIC_AUTH_TOKEN` 环境变量

### 旧版脚本

- Python 3.10+
- 标准库（无外部依赖）
- 可选：ollama（用于 LLM 摘要增强）

---

## 状态文件

- `~/.cache/mywiki-repos/.state.json` — 仓库拉取状态
- `~/.mywiki_pipeline/cache/.summarize_v3_cache.json` — 生成缓存

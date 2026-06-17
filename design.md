# mywiki — 个人知识库设计方案

---

## 目录

- [1. 核心理念](#1-核心理念)
- [2. 完整调研生态](#2-完整调研生态)
- [3. 架构总览](#3-架构总览)
- [4. 七层详解](#4-七层详解)
  - [Layer 0：Obsidian Vault](design.md#layer-0obsidian-vault--唯一数据源)
  - [Layer 1：笔记格式层 — obsidian-skills](design.md#layer-1笔记格式层--obsidian-skills)
  - [Layer 2：内容采集层 — chubbyskills（可选）](design.md#layer-2内容采集层--chubbyskills可选)
  - [Layer 3：代码知识提取 — Graphify](design.md#layer-3代码知识提取--graphify)
  - [Layer 4：Wiki 编译层 — LLM Wiki 模式](design.md#layer-4wiki-编译层--llm-wiki-模式新增)
  - [Layer 5：语义检索层 — LightRAG / gbrain](design.md#layer-5语义检索层--lightrag--gbrain)
  - [Layer 6：Agent 记忆层 — open-second-brain](design.md#layer-6agent-记忆层--open-second-brain)
  - [Layer 7：Hermes mywiki Skill](design.md#layer-7hermes-mywiki-skill)
- [5. 数据流](#5-数据流)
- [6. Vault 目录约定](#6-vault-目录约定)
- [7. 技术选型对比](#7-技术选型对比)
- [8. 实施路线图](#8-实施路线图)
- [9. 关键原则](#9-关键原则)

---

## 1. 核心理念

```
┌───────────────────────────────────────────────────────┐
│           你写进 vault → agent 能搜到、用到            │
│           agent 学到 → 写回 vault Brain/               │
│           知识在同一个地方不断叠加                       │
└───────────────────────────────────────────────────────┘
```

**三条铁律：**

1. **Obsidian vault 是唯一数据源** — 所有外部索引（gbrain、LightRAG、Brain/ 状态）都可以推倒重建，但 vault 里的 .md 文件不会丢。
2. **人和 agent 读同一个东西** — 不存在"这是给 agent 看的"和"这是给人看的"两套数据。一篇笔记，两个读者。
3. **知识是提炼的，不是搬运的** — 代码存摘要不存原文，网页转笔记不存截图，会议讨论提炼要点不存逐字稿。vault 里是高质量理解性知识，不是原始数据 dump。

---

## 2. 完整调研生态

### 2.1 第一轮调研（方案基线）

| 项目 | Stars | 作者 | 角色 |
|---|---|---|---|
| [kepano/obsidian-skills](https://github.com/kepano/obsidian-skills) | 35,881 ⭐ | Obsidian CEO | Agent 笔记格式标准 |
| [itechmeat/open-second-brain](https://github.com/itechmeat/open-second-brain) | 74 ⭐ | 社区 | Hermes 原生记忆层 |
| [garrytan/gbrain](https://github.com/garrytan/gbrain) | 10k+ ⭐ | Garry Tan (YC) | 本地向量+知识图谱 |
| [fxa3bah/OneBrain](https://github.com/fxa3bah/OneBrain) | 25 ⭐ | 社区 | gbrain 运维包装 |
| [chubbyguan/chubbyskills](https://github.com/chubbyguan/chubbyskills) | 390 ⭐ | 社区 | 中文内容采集 |
| [DeepWiki (Cognition)](https://deepwiki.com) | — | Cognition/Devin | 代码→Wiki（参考思路） |
| [AsyncFuncAI/deepwiki-open](https://github.com/AsyncFuncAI/deepwiki-open) | 16.9k ⭐ | 社区 | DeepWiki 开源复刻 |

### 2.2 第二轮调研（LLM Wiki + 个人知识库生态）

#### 核心发现：Karpathy LLM Wiki 模式已成为主流

Andrej Karpathy 在 2024 年提出的 [LLM Wiki 思路](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 已被整个社区验证和实现。核心思想：

> **不要等到查询时再做 RAG。而是每次新资料入库时，让 LLM 编译成持久的 wiki 页面。知识像利息一样复利增长。**

```
传统 RAG：                 chunk → embed → 查询时搜索 + LLM 合成
LLM Wiki（复利模式）：      原始资料 → LLM 编译 → wiki 页面 → 持久化 → 下次查询直接回答
```

这个模式有 3 个关键优势：
1. **知识复利** — 每个新资料不是独立 chunk，而是被整合进已有的知识体系中
2. **人类可读** — wiki 页面是 markdown，你和 agent 读同一个东西
3. **零查询延迟** — 知识已经编译好了，不需要每次搜索+合成

#### 第二轮调研发现的生态全景

| 项目 | Stars | 类型 | 一句话 |
|---|---|---|---|
| [AgriciDaniel/claude-obsidian](https://github.com/AgriciDaniel/claude-obsidian) | **6,976 ⭐** | AI Second Brain | 最流行的自组织第二大脑。15 个 skill，支持 LYT/PARA/Zettelkasten 方法学模式，自主研究循环，10 原则思维框架 |
| [xerrors/Yuxi（语析）](https://github.com/xerrors/Yuxi) | **5,614 ⭐** | 知识库平台 | LightRAG + 知识图谱 + 多租户 Agent Harness。中文开发，支持 MinerU 文档解析 |
| [raphaelmansuy/edgequake](https://github.com/raphaelmansuy/edgequake) | **2,003 ⭐** | GraphRAG 引擎 | Rust 实现的高性能 GraphRAG，受 LightRAG 启发 |
| [Astro-Han/karpathy-llm-wiki](https://github.com/Astro-Han/karpathy-llm-wiki) | **1,138 ⭐** | Agent Skill | Karpathy LLM Wiki 的 Agent Skills 实现。纯 skill，无额外依赖 |
| [1517005260/graph-rag-agent](https://github.com/1517005260/graph-rag-agent) | **2,226 ⭐** | GraphRAG 工具 | 融合 GraphRAG、LightRAG、Neo4j 知识图谱 |
| [nduckmink/arkon](https://github.com/nduckmink/arkon) | **994 ⭐** | 企业 MCP 知识库 | 自托管企业知识库 MCP Server。MRP 管线（Map→Reduce→Plan→Refine→Verify→Commit），部门隔离，RBAC |
| [lewislulu/llm-wiki-skill](https://github.com/lewislulu/llm-wiki-skill) | **587 ⭐** | Agent Skill | Karpathy LLM Wiki 的另一个 Agent Skills 实现 |
| [swarmclawai/swarmvault](https://github.com/swarmclawai/swarmvault) | **571 ⭐** | LLM Wiki CLI | **生产级 LLM Wiki**：npm CLI，三层架构（raw/wiki/schema），tree-sitter 代码感知，知识图谱，混合搜索（FTS5+语义），MCP Server，30+ 输入格式 |
| [NicholasSpisak/second-brain](https://github.com/NicholasSpisak/second-brain) | **400 ⭐** | Agent Skill | Karpathy 模式的 Obsidian PKB，4 个 Agent Skills |
| [olafgeibig/knowledge-mcp](https://github.com/olafgeibig/knowledge-mcp) | **54 ⭐** | MCP + LightRAG | 基于 LightRAG 的 MCP Server。Python，`uvx` 启动，支持多知识库 |
| [Lamarre707/LLM-Wiki-on-Hermes](https://github.com/Lamarre707/LLM-Wiki-on-Hermes) | 1 ⭐ | Hermes Wiki | **在 Hermes 上实现的 LLM Wiki**！工作记忆/语义记忆/情景记忆三层，SQLite FTS5 索引，Hermes memory provider |

### 2.3 关键趋势总结

**趋势 1：LLM Wiki 模式正在代替纯 RAG**
- 社区共识：持久 wiki 页面 > 查询时动态合成
- swarmvault 把 Karpathy 的 gist 变成了生产级 CLI（30+ 输入格式、tree-sitter 代码感知、MCP）
- claude-obsidian (6,976⭐) 验证了模式的普适性

**趋势 2：三层架构成为标准**
```
raw/   ← 原始资料（不可变输入，git 管理）
wiki/  ← LLM 编译的持久页面（实体、概念、综合、索引）
schema/← 领域约定（结构和规则，agent 和你共同进化）
```

**趋势 3：MCP 是知识库的通用接口**
- Hermes / Claude Code / Codex / Cursor 都通过 MCP 连接同一个知识库
- gbrain (80+ 工具)、knowledge-mcp (LightRAG)、swarmvault 都提供 MCP Server
- Arkon 把 MCP 做到了企业级（部门隔离、审批流程、审计日志）

**趋势 4：中文生态已成熟**
- Yuxi（语析）5,614⭐ — 多租户知识库 + LightRAG + 知识图谱
- chubbyskills 390⭐ — 全中文平台采集
- MinerU + PaddleX 做中文文档解析

### 2.4 对 mywiki 方案的启示

| 启示 | 来源 | 对方案的影响 |
|---|---|---|
| 用 LLM Wiki 模式编译知识 | swarmvault / claude-obsidian / karpathy-llm-wiki | 新增 Layer 4：Wiki 编译层 |
| LightRAG 可替代 ChromaDB 做图RAG | knowledge-mcp / Yuxi | Layer 5 可选 LightRAG 作为 gbrain 替代 |
| 代码需要 tree-sitter 感知 | swarmvault (tree-sitter AST) | Layer 3 代码 pipeline 可参考 |
| 已有 Hermes 上的 LLM Wiki 实现 | LLM-Wiki-on-Hermes | Layer 7 Skill 可直接借鉴其模式 |
| 方法学模式（LYT/PARA）可选 | claude-obsidian | 未来可选扩展 |

---

## 3. 架构总览

```ascii
┌──────────────────────────────────────────────────────────────────────────┐
│                       Obsidian Vault — ~/mywiki/                          │
│   你学的、写的、做过的都在这里 · git 版本管理 · 图视图 / 反向链接           │
│                                                                          │
│   ┌────────┐ ┌───────────┐ ┌───────────┐ ┌─────┐ ┌──────┐ ┌──────┐    │
│   │Knowledge│ │  CodeNotes│ │ Learnings │ │Daily│ │Brain │ │Wiki/ │    │
│   │业务/领域 │ │ 代码摘要   │ │ 学习总结   │ │     │ │记忆  │ │编译页 │    │
│   │  文档   │ │           │ │ + 读书心得 │ │     │ │      │ │面    │    │
│   └───┬────┘ └─────┬─────┘ └─────┬─────┘ └──┬──┘ └──┬──┘ └───┬───┘    │
│       │            │             │          │       │        │        │
│       └────────────┼─────────────┼──────────┼───────┴────────┘        │
│                    │             │          │                          │
└────────────────────┼─────────────┼──────────┼──────────────────────────┘
                     │             │          │
          ┌──────────┘             │          └──────────────┐
          ▼                        ▼                        ▼
┌───────────────────┐   ┌───────────────────┐   ┌────────────────────┐
│ Layer 3: Pipeline │   │ Layer 4: Wiki     │   │ Layer 5: 语义检索  │
│ 代码提取+清洗+摘要│──▶│ Compilation       │──▶│ gbrain / LightRAG │
│ + 网页/文档入库   │   │ (LLM Wiki 编译)   │   │ (MCP Server)      │
│ → CodeNotes/      │   │ → Wiki/ 概念/实体  │   │ 向量+知识图谱搜索 │
└───────────────────┘   └───────────────────┘   └────────┬───────────┘
                                                         │
                                  ┌──────────────────────┘
                                  ▼
                   ┌──────────────────────────────┐
                   │ Layer 6: Agent 记忆层        │
                   │ open-second-brain            │
                   │ Brain/ 信号 → dream → 偏好    │
                   │ Hermes memory provider        │
                   └────────────┬─────────────────┘
                                │
                                ▼
                   ┌──────────────────────────────┐
                   │ Layer 7: Hermes mywiki Skill │
                   │ + obsidian-skills (Layer 1)  │
                   │ 统一入口：搜知识/写笔记/总结   │
                   └────────────┬─────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
              ┌──────────┐          ┌──────────────┐
              │  Hermes  │          │ Claude Code  │
              │ (主入口)  │          │ Codex/Cursor │
              │ mywiki S │          │ (MCP 客户端)  │
              └──────────┘          └──────────────┘
```

### Layer 0：Obsidian Vault — 唯一数据源

**设计原则**：所有知识最终都是 .md 文件，你拥有、你管理、你 grep。

**Vault 路径**：`~/mywiki/`

```
~/mywiki/
├── Knowledge/                    # 知识领域文档（业务系统、领域研究、项目文档）
│   ├── 系统A/
│   │   ├── README.md
│   │   └── architecture.md
│   ├── 领域B/
│   │   └── research-notes.md
│   └── ...
├── CodeNotes/                    # 代码库摘要（pipeline 自动生成）
│   ├── 系统A/
│   │   ├── repo1.md
│   │   └── repo2.md
│   └── 系统B/
│       └── ...
├── Learnings/                    # 学习总结、读书笔记、技术调研、教程
├── Daily/                        # 日报/周报（agent 辅助生成）
├── Wiki/                         # LLM Wiki 编译页面（概念、实体、跨领域综合）
│   ├── Concepts/
│   └── index.md
├── Brain/                        # agent 记忆（open-second-brain 管理）
│   ├── active.md                 # 注入到 Hermes system prompt
│   ├── preferences/              # 确认的用户偏好
│   ├── signals/                  # 原始信号（dream 前）
│   └── audit/                    # 变更日志
├── .obsidian/                    # Obsidian 配置
└── .git/
```

**版本管理**：git 入 GitLab 私有仓库，`gitignore` 排除 `.obsidian/` 本地配置。

---

### Layer 1：笔记格式层 — obsidian-skills

**目的**：agent 写笔记时使用规范的 Obsidian 语法，保证你读的笔记和 agent 写的笔记格式一致。

**安装**：

```bash
hermes skills install github.com/kepano/obsidian-skills
```

**加载到会话**：

```
/skill obsidian-markdown   # wikilinks, callouts, properties
/skill obsidian-bases      # 数据库表格 (.base)
/skill json-canvas         # 画布 (.canvas)
/skill defuddle            # 网页 → 干净 markdown
```

**效果**：
- agent 写笔记时自动用 `[[wikilink]]` 做关联，用 `> [!NOTE]` callout 做重点标注，用 `---` 做 metadata
- 你读笔记时能看到 Obsidian 图视图中的链接关系
- agent 从网页抓资料时用 defuddle 去噪，产出干净的 markdown

---

### Layer 2：内容采集层 — chubbyskills（可选）

**目的**：如果你经常看中文技术文章（公众号、B站、小红书、X），丢个链接进去自动转成 markdown 笔记入 vault。

**安装**：

```bash
git clone https://github.com/chubbyguan/chubbyskills ~/.hermes/skills/chubbyskills
bash ~/.hermes/skills/chubbyskills/setup.sh
```

**用法**：在 Hermes 中说「帮我把这篇公众号文章存到 mywiki」— agent 加载对应 skill 自动完成。

**注意**：不是必须的。如果你的业务文档和代码已经够用，可以跳过这层。

---

### Layer 3：代码知识提取 — Graphify

**工具**：Graphify（AST + Claude 语义分析，无需自建 Pipeline）

**处理流程**：

```
代码仓库
    │
    ▼
Pass 1: Tree-sitter AST 提取（免费）
  · 函数、类型、接口、常量定义
  · 调用关系、文件级溯源
    │
    ▼
Pass 2: Whisper 本地摘要（可选）
  · 复杂函数体的自然语言描述
    │
    ▼
Pass 3: Claude 语义分析（付费，但极省 token）
  · 识别社区聚类（Community Detection）
  · 提取 God Nodes（高连接核心抽象）
  · 标记 surprising connections（跨模块调用）
    │
    ▼
输出到 vault ~/mywiki/CodeNotes/<repo>/
  · GRAPH_REPORT.md — 人可读的分析报告
  · graph.html — 交互式可视化（浏览器打开）
  · graph.json — 机器可查询的知识图谱
```

**输出示例**（GRAPH_REPORT.md 结构）：

```markdown
# Graph Report: apisvr

## 概览
- 节点: 1220
- 边: 2215
- 社区: 83
- 边类型: 95% EXTRACTED (确定性事实) / 5% INFERRED

## 社区导航
1. **VPC Endpoint Service Creation** — 服务端点创建流程
2. **API Request Handling** — HTTP 请求处理链
3. **Database Connection Management** — DB 连接池管理
...

## God Nodes（核心抽象）
| 节点 | 连接数 | 类型 | 说明 |
|------|--------|------|------|
| Logger | 47 | struct | 日志门面 |
| tConnectInfoDo | 45 | struct | 连接信息数据对象 |
| Database | 42 | struct | 数据库连接管理 |

## Surprising Connections（跨模块调用）
- `NewServer()` → `InitFactory()` @ cmd/server/main.go:47
  （启动时初始化工厂模式，影响所有服务实例）
```

**更新节奏**：项目有重大变更时重新运行 `graphify <repo>`，或按需更新。

**目录结构**：

```
~/mywiki/CodeNotes/privatelink-apisvr/
├── graph.json           # 完整知识图谱（NetworkX 格式）
├── GRAPH_REPORT.md      # 人可读的分析报告
├── graph.html           # 交互式可视化（浏览器打开）
└── 2026-06-17/          # 历史备份（语义版本）
    └── graph.json
```

---

### Layer 4：Wiki 编译层 — LLM Wiki 模式（新增）

**目的**：代码 Pipeline（Layer 3）产出 CodeNotes/摘要，你手动写 Knowledge/ 和 Learnings/ 笔记后，进一步将这些内容用 **LLM Wiki 模式**编译成交叉引用的持久 wiki 页面。知识不只是独立文件，而是整合进已有的知识体系。

**核心模式**（来自 Karpathy LLM Wiki）：

```
原始资料 → LLM 编译 → wiki 页面 → 持久化 → 下次查询直接回答
```

不是等查询时做 RAG，而是每次新资料入库时做一次编译。

**流程**：

```
你手动写 Knowledge/README.md、Learnings/ 读书笔记
  或 agent 从网页抓文档
        │
        ▼
LLM 读取已有 wiki 页面 → 理解上下文
        │
        ▼
创建或更新 wiki 页面：
  · 实体页面（概念、系统、服务、人）
  · 综合页面（跨领域对比、知识关联）
  · index.md 自动更新链接
        │
        ▼
写入 vault 的 Wiki/ 目录（补充 Knowledge/、CodeNotes/、Learnings/）
        │
        ▼
语义检索层（Layer 5）索引整个 vault → 查询时走语义搜索
```

**与传统 RAG 对比**：

| 维度 | 传统 RAG | LLM Wiki（本方案） |
|---|---|---|
| 入库时 | chunk → 向量化 | LLM 编译为 wiki 页面 |
| 查询时 | 向量搜索 + LLM 合成 | 搜索 wiki 页面 + 直接回答 |
| 知识复利 | ❌ 每次重新合成 | ✅ 页面不断积累和交叉引用 |
| 人类可读 | ❌ 只有向量 | ✅ 完整的 markdown 页面 |
| 可编辑性 | ❌ 不能手工改 chunk | ✅ 手动编辑 wiki 页面即生效 |

**如何实现**：

方案 A（推荐）：用 Hermes 的 mywiki Skill 内置编译能力 — 写一条指令「编译 Systems/ 的新文档到 wiki」，Hermes 自动完成。

方案 B（可选）：安装 `karpathy-llm-wiki` skill 或 `swarmvault` CLI 作为补充工具：
```bash
# swarmvault 方式（全自动管线）
npm install -g @swarmvaultai/cli
cd ~/mywiki && swarmvault scan --schedule

# 或 Agent Skill 方式
# 在会话中加载 karpathy-llm-wiki 后运行 /wiki-ingest
```

**输出目录**：

```
~/mywiki/Wiki/                  # LLM 编译的 wiki 页面（新增）
├── Knowledge/
│   ├── 系统A-architecture.md   # 领域知识综合页面
│   └── 领域B-overview.md
├── Concepts/
│   ├── auth-flow.md            # 跨领域的知识概念
│   ├── timeout-strategy.md
│   └── ...
├── index.md                    # 所有 wiki 页面的自动索引
└── log.md                      # 编译操作日志
```

**更新策略**：每次新增/修改 Knowledge/、Learnings/ 或 CodeNotes/ 后，可通过 mywiki skill 触发编译。不需要定时，由事件驱动。

---

### Layer 5：语义检索层 — gbrain / LightRAG

**目的**：当 vault 里累积了成百上千篇笔记后，用语义搜索而非全文字符串匹配找到相关内容。

**核心**：gbrain 定时索引整个 vault，构建 PGLite 索引 + nomic-embed-text 嵌入 + 知识图谱，暴露 80+ MCP 工具。

**安装**：

```bash
# 1. 安装 gbrain
git clone https://github.com/garrytan/gbrain ~/Code/gbrain
cd ~/Code/gbrain && bun install

# 2. 安装 Ollama 和嵌入模型
brew install ollama
ollama pull nomic-embed-text

# 3. 首次索引 vault
cd ~/Code/gbrain && bun run src/cli.ts sync --repo "$HOME/mywiki"

# 4. 启动 MCP 服务（HTTP，端口 3131）
bun run src/cli.ts serve
```

> 或用 OneBrain 的 install.sh 一键装好 LaunchAgent + 定时同步：
> ```bash
> git clone https://github.com/fxa3bah/OneBrain ~/Code/OneBrain
> cp ~/Code/OneBrain/.env.example ~/.secrets/.env
> # 编辑 ~/.secrets/.env 填入 OBSIDIAN_VAULT_PATH 和 GBRAIN_REPO
> cd ~/Code/OneBrain && bash install.sh
> ```

**Hermes 配置**（`~/.hermes/config.yaml`）：

```yaml
mcp_servers:
  gbrain:
    url: http://127.0.0.1:3131/mcp
    headers:
      Authorization: "Bearer <your-token>"
```

**效果**：
- 问「支付系统的超时逻辑」→ 语义匹配到 `Systems/支付系统/超时处理.md`
- 问「上次讨论的部署方案」→ 匹配最近的 Daily/ 或 Learnings/ 笔记
- 知识图谱自动发现笔记之间的关联

**更新**：每次 vault 有变化后重新 sync：
```bash
cd ~/Code/gbrain && bun run src/cli.ts sync --repo "$HOME/mywiki"
```

可配 cron 每 30 分钟自动 sync，或在 CodeNotes pipeline 跑完后触发一次。

---

### Layer 6：Agent 记忆层 — open-second-brain

**目的**：Hermes 记得你的偏好和上下文，并且**你能在 Obsidian 里看到 agent 记住了什么**。

**原理**：open-second-brain 作为 Hermes 原生 memory provider，把 agent 的每次交互信号写入 vault 的 `Brain/` 目录，每晚 `dream` 合并重复信号为确认偏好。

**安装**：

```bash
# 1. 装插件
hermes plugins install itechmeat/open-second-brain --enable
hermes gateway restart

# 2. 装 CLI
~/.hermes/plugins/open-second-brain/scripts/o2b install-cli

# 3. 初始化 vault
o2b init --vault ~/mywiki --name "mywiki" --agent-name "hermes"
o2b brain init --vault ~/mywiki --primary-agent "hermes"

# 4. 启用 memory provider
hermes memory setup
# 选 open-second-brain，或在 config.yaml 中直接设置
```

**配置**（`~/.hermes/config.yaml`）：

```yaml
memory:
  provider: open-second-brain
```

**验证**：

```bash
o2b doctor --vault ~/mywiki
hermes memory status
# 应有 Provider: open-second-brain, available ✓
```

**效果**：
- 每次 Hermes 会话开始时，`Brain/active.md` 注入到 system prompt
- 你的每次纠正（"不要用内部缩写"）→ Brain/signals/ → 下次 dream → Brain/preferences/
- 你早上打开 Obsidian，点开 `Brain/preferences/pref-no-internal-abbrev.md`，能看到 agent 昨天学了什么
- 跨 Agent：Claude Code、Codex 通过 MCP 读同一个 Brain

---

### Layer 7：Hermes mywiki Skill

**目的**：一个 Hermes Skill，把所有层串起来，让 Hermes 知道怎么用这个知识库。

**安装**：写入 `~/.hermes/skills/mywiki/SKILL.md`，会话中 `/skill mywiki` 加载。

```markdown
---
name: mywiki
description: 个人知识库 mywiki — 结合 Obsidian vault、gbrain 语义搜索、open-second-brain 记忆
---

# mywiki Skill

## 当用户问业务/代码问题时：

1. 先用 gbrain MCP 工具做语义搜索（`search` / `ask`）
2. 命中 CodeNotes/ 的摘要 → 先读摘要定位 → 再搜具体文件
3. 引用时标注来源文件 + 行号
4. 回答后写一条 signal 到 Brain/signals/（open-second-brain）

## 当用户写新文档时：

1. 加载 obsidian-markdown skill
2. 用 Obsidian 规范语法：`[[wikilink]]`、`> [!note]` callout、`---` metadata
3. 根据内容类型写到 Knowledge/、Learnings/ 或 Daily/
4. 关联已有笔记（加反向链接）
5. 自动触发 Wiki 编译（Layer 4）更新概念页面和 index.md

## 当用户要求总结时：

1. 扫描 Knowledge/、Learnings/、CodeNotes/ 近期变更
2. 分析 gbrain 图谱中的热点主题
3. 生成日报/周报 → 写到 Daily/
4. 在 vault 里更新索引页（MOC - Map of Content）

## 定期任务：

- 每晚：检查 open-second-brain dream 结果
- 每 2 周：提醒用户跑代码 pipeline
- 每次 vault sync 后：通知 gbrain 重新索引
```

---

## 5. 数据流

```
知识入库                                   知识出库（Agent 查询）
─────────                                  ─────────────────

你写笔记 → Knowledge/                     用户提问 → Hermes
  或文档 → Learnings/                          │
  或读书 → Learnings/                          ├→ mywiki skill → 选择策略
  或代码 → CodeNotes/                          │
  或链接 → chubbyskills（可选）                 ├→ 策略 1：直接搜 wiki 页面
      │                                         │   (Layer 4 编译页面)
      ▼                                         │
  ┌──────────┐                                  ├→ 策略 2：语义搜索整个 vault
  │ Layer 4  │← 自动触发                         │   (Layer 5: gbrain / LightRAG)
  │ Wiki 编译│                                  │   跨越 Knowledge/ CodeNotes/
  │ → Wiki/  │                                  │   Learnings/ Daily/ 全部内容
  └────┬─────┘                                  │
       │                                         ├→ 策略 3：读命中文件的完整内容
       ▼                                         │
  人读 Obsidian 图视图                            ▼
  或 Wiki/ 浏览页面                          Hermes 组织回答 + 来源引用
       │                                          │
       ▼                                          ▼
  gbrain/LightRAG sync                     写 Brain/signals/
  → 更新向量索引 + 知识图谱                   （记录什么有用）
       │                                          │
       ▼                                          ▼
  open-second-brain dream                  下次 dream → 优化检索权重
  → Brain/preferences/
```

---

## 6. Vault 目录约定

| 目录 | 内容 | 维护者 | 格式要求 |
|---|---|---|---|
| `Knowledge/` | 知识领域文档（业务系统、领域研究、项目架构） | 你手动维护 | 标准 markdown + wikilinks |
| `CodeNotes/` | 代码库摘要（按系统/项目分组） | pipeline 自动生成 | 固定模板格式 |
| `Wiki/` | LLM Wiki 编译页面（概念、实体、跨领域综合） | agent 自动编译 | 交叉引用 + index.md |
| `Learnings/` | 学习总结、读书笔记、技术调研、教程 | 你写 + agent 辅助 | 自由格式 |
| `Daily/` | 日报、周报、想法记录 | agent 辅助生成 | `YYYY-MM-DD.md` |
| `Brain/` | Agent 记忆 | open-second-brain 管理 | 自动格式 |

**笔记命名约定**：
- 知识领域：`领域名-模块名.md`，如 `payment-timeout.md`
- 代码摘要：`repo-name.md`，如 `auth-service.md`
- 学习总结：`主题-日期.md`，如 `go-generics-202606.md`

**每条笔记的 metadata**（YAML frontmatter）：

```yaml
---
tags: [系统A, payment, 架构]
created: 2026-06-17
updated: 2026-06-17
source: ./internal/payment/handler.go
status: draft   # draft | reviewed | archived
---
```

---

## 7. 技术选型对比

| 组件 | 选择方案 | 替代方案 | 选择理由 |
|---|---|---|---|
| 数据源 | Obsidian vault (.md) | ChromaDB / 任何数据库 | 人类可读、git 管理、Obsidian 生态、零 vendor lock |
| 语义搜索 | gbrain (PGLite + Ollama) | LightRAG + bge-small-zh | gbrain 80+ MCP 工具、知识图谱、全离线、跟 vault 原生对齐；LightRAG 是 Python 生态替代（更易扩展） |
| 知识编译 | **LLM Wiki 模式** (Hermes agent 内置) | swarmvault CLI / karpathy-llm-wiki skill | 事件驱动，不需要单独守护进程；swarmvault 是全自动管线备选 |
| Agent 记忆 | open-second-brain | 自写 MCP / Hermes 内置 memory | 原生 Hermes 插件、确定性 dream 算法、0 维护 |
| 笔记格式 | obsidian-skills | 自写规则 | CEO 维护、35.8k ⭐、Agent Skills 开放标准 |
| 中文内容 | chubbyskills | 自写爬虫 | 14 个现成 skill、涵盖全平台 |
| 代码摘要 | 自定义 pipeline | 纯向量塞原始代码 | 摘要比原始代码更有价值、人类可读、无噪音 |
| 协议 | MCP (标准) | Hermes Plugin | 跨 Agent 共享、不锁死 Hermes 生态 |

### 为什么不用 ChromaDB 了？

原计划用 ChromaDB + bge-small-zh。调研后发现 **gbrain 更优**：

| 维度 | ChromaDB | gbrain |
|---|---|---|
| 角色 | 纯向量数据库 | 向量 + 知识图谱 + 全文索引 + 80+ MCP 工具 |
| 嵌入 | 需自建 pipeline | 内嵌 Ollama + nomic-embed-text |
| 知识图谱 | ❌ | ✅ 自动构建 |
| MCP 工具 | 需自写 | 80+ 现成 |
| Obsidian 集成 | ❌ | ✅ 原生支持 |
| 代码量 | 几千行自写 | 直接安装即可 |

### 为什么用 open-second-brain 而非自写记忆层？

- 确定性 dream 算法（不是 LLM 来管理记忆，不幻觉）
- 原生 Hermes 插件，`memory.provider` 一行配置
- 跨 Agent 共享（MCP bridge）
- 自带 `o2b` CLI：init / doctor / brain init / rollback / hygiene 齐全

---

## 8. 实施路线图

### Phase 1：基础 Vault + Hermes 集成（~30min）

```
[ ] 建 ~/mywiki/ vault，git init，push 到 GitLab
[ ] hermes plugins install itechmeat/open-second-brain --enable
[ ] o2b init + o2b brain init
[ ] memory.provider: open-second-brain
[ ] hermes skills install github.com/kepano/obsidian-skills
[ ] 写 ~/.hermes/skills/mywiki/SKILL.md
```

**验收**：`hermes memory status` 显示 Provider: open-second-brain ✓

### Phase 2：代码知识提取 — Graphify（~30min）

使用 Graphify 替代旧的 pipeline_v2，三阶段处理（AST 提取 → Whisper 摘要 → Claude 语义分析）。

```
[ ] 安装: pipx install graphify 或 mise use graphify
[ ] 首次运行: graphify ~/Code/your-repo --obsidian ~/mywiki/CodeNotes/your-repo
[ ] 浏览器打开 graphify-out/graph.html 验证可视化
[ ] 观察 GRAPH_REPORT.md 中的 God Nodes 和社区聚类
```

**配置**（添加到 `~/.mywiki/config.yaml`）:
```yaml
graphify:
  backend: openai
  base_url: https://api.modelverse.cn/v1
  model: deepseek-ai/DeepSeek-V3.2
  output_format: obsidian  # 或 wiki 用于 swarmvault 集成
```

**验收**：`~/mywiki/CodeNotes/your-repo/` 下有可读的 `GRAPH_REPORT.md` 和交互式 `graph.html`

### Phase 2b：长期知识库 — SwarmVault（可选，~30min）

如需将 Graphify 产出纳入持续维护的个人知识库：

```
[ ] 安装: npm install -g @swarmvaultai/cli
[ ] 初始化: swarmvault init ~/mywiki --format=obsidian
[ ] 将 Graphify 的 graph.json 复制到 ~/mywiki/raw/codenotes/
[ ] 运行编译: swarmvault build
[ ] 验证 Wiki/ 目录下生成带交叉引用的 markdown
```

**验收**：`~/mywiki/Wiki/` 有编译出的概念页面，agent 能基于 wiki 直接回答

### Phase 3：语义检索（~30min）

```
[ ] git clone gbrain ~/Code/gbrain + bun install
[ ] brew install ollama + ollama pull nomic-embed-text
[ ] 首次 sync：bun run src/cli.ts sync --repo ~/mywiki
[ ] 启动 serve：配 LaunchAgent 或手动启动
[ ] 配 Hermes MCP config：mcp_servers.gbrain
[ ] 验证：在 Hermes 中用自然语言搜 vault
```

**验收**：问「支付超时逻辑」正确返回 Systems/ 和 CodeNotes/ 中的相关笔记

### Phase 4：学习闭环（~30min）

```
[ ] 建 Daily/ 目录 + 日报模板
[ ] 配 Hermes cron job：每晚生成日报（`0 22 * * *`）
[ ] 配 cron job：Graphify 更新代码笔记（项目有更新时手动/自动触发）
[ ] 配 cron job：gbrain sync 每 30 分钟（`*/30 * * * *`）
[ ] 验证 open-second-brain dream 自动运行
```

**验收**：早上打开 Obsidian 能看到昨天的 Daily/ 和 Brain/ 更新

---

### 方案演进记录：从 pipeline_v2 到 Graphify + SwarmVault

> **日期**: 2025-06-17  
> **背景**: 测试 apisvr 代码知识提取，发现 pipeline_v2 产出质量不达标

#### pipeline_v2 问题根因分析

| 问题 | 表现 | 根因 | 位置 |
|------|------|------|------|
| **骨架正确，细节缺失严重** | 所有请求/响应结构都标「需确认」 | `_build_action_api_prompt` 接收 `handlers` 参数但**从未使用**，只把 routes 传给 LLM | `prompt_builder.py:202-271` |
| **内部接口遗漏** | `IDeleteVPCEndpoint` 等 2 个接口完全丢失 | `extract_action_constants` 遇到 `const(...)` 块直接返回 `None` | `prompt_builder.py:263-268` |
| **文件位置错误** | 4 个 handler 指向 `db/db.go` | 索引逻辑「保留首次出现、跳过后续」，导致后面的 `api/*.go` 被忽略 | `prompt_builder.py:56-75` |
| **Struct 字段丢失** | 只有 `[fact_type] name @ location` | `_format_facts` 丢弃了 `metadata['fields']` | `prompt_builder.py:355-374` |

#### Graphify 验证结果

```bash
OPENAI_API_KEY=$KEY OPENAI_BASE_URL=https://api.modelverse.cn/v1 \
  graphify ~/Documents/Code/work/privatelink/apisvr \
  --backend=openai --model=deepseek-ai/DeepSeek-V3.2
```

| 指标 | 数值 |
|------|------|
| 节点 | 1220 |
| 边 | 2215 |
| 社区 | 83 |
| EXTRACTED (确定性事实) | 95% |
| INFERRED (LLM 推理) | 5% |
| 成本 | ~$0.0045 (2600 tokens in / 2178 out) |

**关键发现**：
- **God Nodes 自动识别**: `Logger`(47边)、`tConnectInfoDo`(45边)、`Database`(42边) —— 真正的核心抽象
- **内部接口补全**: 「Endpoint Deletion Internal」「Service Configuration Deletion Internal」都被提取
- **调用链完整**: `runServer() → NewServer() → NewAPI()/NewDatabase()/InitFactory()`
- **文件级溯源**: 每个连接都带精确文件位置

#### 新架构决策：双工具策略

```
┌─────────────────────────────────────────────────────────────────────┐
│                         工具分工                                     │
├─────────────────────────────────────────────────────────────────────┤
│  Graphify          │  代码仓库分析                                  │
│  (AST + Claude)    │  • 新项目 onboarding                          │
│                    │  • Code review 前预习                         │
│                    │  • 架构分析 / 依赖梳理                         │
│                    │  ──→ 产出: graph.json + GRAPH_REPORT.md       │
├─────────────────────────────────────────────────────────────────────┤
│  SwarmVault        │  长期个人知识库                                │
│  (npm CLI)         │  • Karpathy LLM Wiki 持续编译                 │
│                    │  • 知识复利增长                               │
│                    │  • MCP Server 供所有 Agent 访问               │
│                    │  • Obsidian 导出 (可选)                       │
├─────────────────────────────────────────────────────────────────────┤
│  关系              │  Graphify 产出 → 作为 SwarmVault `raw/` 的上游 │
└─────────────────────────────────────────────────────────────────────┘
```

**废弃决定**: 不再维护 pipeline_v2，后续代码分析需求统一使用 Graphify。

---

### Total 投入

| Phase | 时间 | 产出 |
|---|---|---|
| 1 | ~30min | Hermes 能读写 vault，记忆生效 |
| 2 | ~30min | Graphify 分析代码，生成知识图谱 |
| 2b | ~30min | SwarmVault 长期知识库（可选） |
| 3 | ~30min | 语义搜索可用 |
| 4 | ~30min | 知识库自动更新 |

---

## 9. 关键原则

1. **Vault 永远在** — 所有外部索引（gbrain 的 PGLite、Brain/ 状态）都可以推倒重建，但 `~/mywiki/*.md` 不会丢。
2. **知识是提炼的，不是搬运的** — 代码存摘要不存原文，网页转笔记不存截图，会议讨论提炼要点不存逐字稿。vault 里是高质量理解性知识，不是原始数据 dump。
3. **人和 agent 读同一个东西** — Agent 搜到 `Knowledge/payment/timeout.md`，你也在 Obsidian 里点开同一份文件。不存在"给 agent 看的数据"和"给人看的数据"两套。
4. **增量建设** — Phase 1 今晚就能跑起来，后面按需叠加。不要求一次性建完。
5. **跨 Agent** — MCP 协议确保 Claude Code、Codex、Cursor 等也能用同一个知识库。Hermes 是主入口但不是唯一入口。

---

> **参考链接**
>
> ### 核心组件
> - open-second-brain: https://github.com/itechmeat/open-second-brain
> - obsidian-skills: https://github.com/kepano/obsidian-skills
> - chubbyskills: https://github.com/chubbyguan/chubbyskills
> - gbrain: https://github.com/garrytan/gbrain
> - OneBrain: https://github.com/fxa3bah/OneBrain
>
> ### LLM Wiki 生态（本轮新增）
> - Karpathy LLM Wiki 原始思路: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
> - claude-obsidian (6,976⭐): https://github.com/AgriciDaniel/claude-obsidian
> - swarmvault (571⭐): https://github.com/swarmclawai/swarmvault
> - karpathy-llm-wiki (1,138⭐): https://github.com/Astro-Han/karpathy-llm-wiki
> - NicholasSpisak/second-brain (400⭐): https://github.com/NicholasSpisak/second-brain
> - LLM-Wiki-on-Hermes: https://github.com/Lamarre707/LLM-Wiki-on-Hermes
>
> ### 语义检索备选
> - LightRAG (20k+⭐): https://github.com/HKUDS/LightRAG
> - knowledge-mcp (LightRAG MCP Server): https://github.com/olafgeibig/knowledge-mcp
> - Yuxi（语析，5,614⭐）: https://github.com/xerrors/Yuxi
>
> ### 企业级 / MCP
> - Arkon (994⭐): https://github.com/nduckmink/arkon
>
> ### 其他
> - Agent Skills spec: https://agentskills.io
> - DeepWiki: https://deepwiki.com

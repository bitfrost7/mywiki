# mywiki — 个人知识库设计方案 v2

> 基于 v1 设计 + 对抗式多 Agent 分析 + 置信度体系 + 业务层级

---

## 目录

- [1. 核心理念](#1-核心理念)
- [2. 七层架构](#2-七层架构)
  - [Layer 0：Obsidian Vault](#layer-0obsidian-vault--唯一数据源)
  - [Layer 1：笔记格式层 — obsidian-skills](#layer-1笔记格式层--obsidian-skills)
  - [Layer 2：内容采集层 — chubbyskills（可选）](#layer-2内容采集层--chubbyskills可选)
  - [Layer 3：代码知识提取 — Graphify + 多 Profile 编译](#layer-3代码知识提取--graphify--多-profile-编译)
  - [Layer 4：Wiki 编译层 — LLM Wiki 模式](#layer-4wiki-编译层--llm-wiki-模式)
  - [Layer 5：语义检索层 — gbrain / LightRAG](#layer-5语义检索层--gbrain--lightrag)
  - [Layer 6：Agent 记忆层 — open-second-brain](#layer-6agent-记忆层--open-second-brain)
  - [Layer 7：Hermes mywiki Skill](#layer-7hermes-mywiki-skill)
- [3. 文档置信度体系](#3-文档置信度体系)
  - [3.1 来源分层与初始置信度](#31-来源分层与初始置信度)
  - [3.2 置信度调整规则](#32-置信度调整规则)
  - [3.3 领域置信度聚合](#33-领域置信度聚合)
  - [3.4 反馈获取](#34-反馈获取)
  - [3.5 修复流程](#35-修复流程)
- [4. Vault 目录约定](#4-vault-目录约定)
- [5. 数据流](#5-数据流)
- [6. 技术选型](#6-技术选型)
- [7. 实施路线图](#7-实施路线图)

---

## 1. 核心理念

```
┌────────────────────────────────────────────────────────────────────────┐
│          你写进 vault → agent 能搜到、用到                               │
│          agent 学到 → 写回 vault Brain/                                 │
│          知识在同一个地方不断叠加                                         │
│          文档有置信度 → 不靠谱的不进回答 → 反馈修正闭环                    │
└────────────────────────────────────────────────────────────────────────┘
```

**四条铁律：**

1. **Obsidian vault 是唯一数据源** — 所有外部索引都可以推倒重建，但 vault 里的 .md 文件不会丢。
2. **人和 agent 读同一个东西** — 一篇笔记，两个读者。
3. **知识是提炼的，不是搬运的** — 代码存摘要不存原文，网页转笔记不存截图。
4. **代码事实落地靠源码，Graphify 是索引不是结论** — 语义分析和文档生成由多 Agent 对抗式完成。

---

## 2. 七层架构

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       Obsidian Vault — ~/mywiki/                          │
│   你学的、写的、做过的都在这里 · git 版本管理 · 图视图 / 反向链接           │
│                                                                          │
│   ┌────────┐ ┌───────────┐ ┌───────────┐ ┌─────┐ ┌──────┐ ┌──────┐    │
│   │Knowledge│ │  CodeNotes│ │ Learnings │ │Daily│ │Brain │ │Wiki/ │    │
│   │高置信度  │ │ 代码编译   │ │学习/外部  │ │ 偏好│ │记忆  │ │编译页 │    │
│   │ 手动写   │ │ 多profile  │ │ draft→review│ │     │ │      │ │面    │    │
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
│ Graphify + 多Pro  │──▶│ Compilation       │──▶│ gbrain / LightRAG  │
│ file 对抗式编译   │   │ (LLM Wiki 编译)    │   │ (MCP Server)      │
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
                   │ 统一入口：搜知识/写笔记/查询    │
                   └──────────────────────────────┘
```

---

### Layer 0：Obsidian Vault — 唯一数据源

**Vault 路径**：`~/mywiki/`

**Vault 目录结构（v2 完整版）：**

```
~/mywiki/
├── Knowledge/                    # 业务/领域知识文档（用户手动写，高置信度）
│   ├── privatelink/
│   │   ├── overview.md
│   │   ├── architecture.md
│   │   └── deployment.md
│   └── go-patterns/
├── CodeNotes/                    # 代码库编译文档（按业务→服务→子仓库组织）
│   ├── privatelink/              # 〈业务线〉
│   │   ├── apisvr/               # 〈服务〉
│   │   │   ├── go/               # 〈子仓库〉
│   │   │   │   ├── README.md
│   │   │   │   ├── interfaces.md         # 对外接口 + 外部依赖
│   │   │   │   ├── interfaces/           # 接口多时拆分
│   │   │   │   ├── persistence.md        # DB/Redis/ZK
│   │   │   │   ├── data-flow.md          # 业务数据流
│   │   │   │   ├── modules/              # 模块级功能（内容多时再分）
│   │   │   │   │   ├── vpc-endpoint.md
│   │   │   │   │   └── connection.md
│   │   │   │   ├── graph-report.md
│   │   │   │   └── graph.json
│   │   │   ├── web/
│   │   │   │   └── README.md
│   │   │   └── migration/
│   │   ├── authsvr/
│   │   └── controllersvr/
│   └── ueip_ops/
│       └── apisvr/
├── Learnings/                    # 学习总结、读书笔记（初始 draft，review 后 reviewed）
│   └── go-generics-202606.md
├── Wiki/                         # LLM Wiki 编译页面（概念、实体、跨领域综合）
│   ├── Concepts/
│   ├── Knowledge/
│   └── index.md
├── Daily/                        # 日报（cron 生成，不入 wiki 编译）
│   └── 2026-06-19.md
├── Brain/                        # Agent 记忆（o2b 管理）
│   └── ...
└── .obsidian/
```

**版本管理**：git 入 GitLab 私有仓库。

---

### Layer 1：笔记格式层 — obsidian-skills

与 v1 相同。加载 `obsidian-markdown` / `obsidian-bases` / `json-canvas` / `defuddle`。

---

### Layer 2：内容采集层 — chubbyskills（可选）

与 v1 相同。非必须。

---

### Layer 3：代码知识提取 — Graphify + 多 Profile 编译

**核心变化（v1 → v2）：**

| | v1 | v2 |
|---|---|---|
| 语义分析 | 单 LLM 一次调用 | 多 profile Kanban Swarm 对抗式 |
| 产出 | 简要代码摘要 | 接口/持久化/数据流/模块功能全量文档 |
| 大服务 | 一个文件 | 自动检测量级，超阈值自动拆子文件 |
| 事实来源 | 依赖 Graphify 推断 | Graphify 提供骨架，源码是事实锚点 |

#### 3.1 工具分工

```
Graphify（AST 骨架提取）
  功能：函数/类型/接口/调用关系/社区检测
  产出：graph.json（机器可读）+ GRAPH_REPORT.md（人可读摘要）
  成本：极低（~$0.005/次）
  特点：95% 确定性事实，5% 推断
        只提供调用关系和模块实体依赖，不做语义文档

多 Profile 编译（LLM 层，本层核心）
  功能：读取源码 + graph.json → 编译为完整文档
  方式：Kanban Swarm 对抗式（generator → adversary → synthesis）
  产出：interfaces.md / persistence.md / data-flow.md / modules/*
  事实锚点：源码（代码行号引用）+ graph.json 调用链
```

#### 3.2 多 Profile 对抗式流程

```
                                    ┌──────────────────────────────┐
                                    │ Stage 1: Generator           │
                                    │ Profile: code-analyzer       │
                                    │ 输入：源码路径 + graph.json  │
                                    │ 输出：初步文档（含源码引用）  │
                                    └──────────┬───────────────────┘
                                               │
                                               ▼
                                    ┌──────────────────────────────┐
                         ┌──────────┤ Stage 2: Adversary           │
                         │          │ Profile: code-adversary      │
                         │          │ 任务：                      │
                         │          │  · 挑刺遗漏                  │
                         │          │  · 标记幻觉                  │
                         │          │  · 指出过度推断              │
                         │          │ 输出：挑刺意见 + 证据引用     │
                         │          └──────────┬───────────────────┘
                         │                     │
                         ▼                     ▼
                    ┌──────────────────────────────────────┐
                    │ Stage 3: Synthesis                    │
                    │ Profile: code-synthesizer             │
                    │ 输入：初步文档 + 挑刺意见              │
                    │ 输出：修正后文档 → reviewed 状态       │
                    └──────────────────────────────────────┘
```

**实现方式 — Kanban Swarm：**

```bash
hermes kanban swarm "编译 apisvr 持久化层文档" \
  --worker hermes:生成持久化文档初稿:code-analyzer \
  --worker hermes:对抗审查初稿:code-adversary \
  --verifier hermes:合并修正 \
  --synthesizer hermes
```

**关于 L 点（引入错误性熵增）：** Stage 1 的 Generator 被指示产出一个 deliberately noisy 的版本——多角度、多候选、不过滤。Adversary 的任务不是否定全部，而是**区分信号和噪音**。结果会比「一次求稳」的版本更全面地覆盖边缘情况。

#### 3.3 输出内容

每个 CodeNotes 服务目录产出 **4 类文档**：

**interfaces.md** — 对外接口 + 外部依赖
- 提供接口列表（gRPC / REST / 内部 RPC）
- 外部依赖清单（其他服务、中间件、第三方）
- 接口→Handler 映射
- 当接口数量多时分拆到 `interfaces/` 子目录

**persistence.md** — 持久化
- DB 表结构 + 对应实体对象
- Redis key 模式 + 含义
- ZK 注册路径 + 用途
- 缓存的层级和失效策略

**data-flow.md** — 业务数据/流量流转
- 核心业务流程时序
- 关键路径的请求→处理→响应链条
- 状态机 / 状态流转

**modules/** — 各模块内部功能
- 按模块分文件（vpc-endpoint.md、connection.md 等）
- 内容量决定是否要继续分目录

#### 3.4 大服务拆分策略

每次编译时，orchestrator 先评估内容量级：

```python
如果 接口数 > 20 或 预估行数 > 200:
    自动拆分: interfaces.md → interfaces/vpc-endpoint.md + ...
    在 interfaces.md 里保留索引/大纲
否则:
  写单个文件
```

---

### Layer 4：Wiki 编译层 — LLM Wiki 模式

与 v1 相同，但增加了一条关键限制：

**只针对 `reviewed` 状态的文档进行编译。**

| 来源 | 进入 Wiki 编译 |
|------|:-------------:|
| CodeNotes（reviewed 后） | ✅ |
| Learnings（reviewed 后） | ✅ |
| Knowledge（直接） | ✅ |
| Daily | ❌（走 o2b） |
| Brain/ | ❌（独立流程） |

---

### Layer 5：语义检索层 — gbrain / LightRAG

与 v1 基本相同。但检索策略需结合置信度：

```
查询命中多篇文档 → 按置信度排序
领域平均置信度 < 阈值（如 4.0）→ 不走该领域的 wiki 检索
                         → 标记为"需要修复"→ 触发修复流程
```

---

### Layer 6：Agent 记忆层 — open-second-brain

与 v1 相同。

---

### Layer 7：Hermes mywiki Skill

在 v1 基础上增加：

```
## 当用户查询知识时：

1. 先查 Wiki/ 和 CodeNotes/（按置信度排序）
2. 回答后追加反馈入口：「这个回答有用吗？[👍/👎]」
3. 记录反馈到文档的 confidence_log

## 当置信度异常的文档被命中时：

不要拒绝回答，而是在回答前标注：
「以下信息来自 CodeNotes/interfaces.md（置信度 5/10），可能有偏差」
```

---

## 3. 文档置信度体系

### 3.1 来源分层与初始置信度

每篇文档 metadata 增加以下字段：

```yaml
---
source: codenotes                        # codenotes | learnings | knowledge | wiki | daily
confidence: 6                            # 0-10，根据来源初始赋值
confidence_log:
  - date: 2026-06-19
    action: create                       # create | review-pass | query-feedback | repair
    score: 6
    reason: "CodeNotes 初版，经 2 轮 profile 审查"
  - date: 2026-06-20
    action: query-feedback
    score: 7
    reason: "用户反馈"很有用"
---
```

**各来源初始置信度：**

| 来源 | 初始置信度 | 原因 |
|------|:---------:|------|
| **Knowledge**（用户手动写） | 8 | 高可信度 |
| **CodeNotes**（AI 编译 + 多 profile 审查） | 6 | AI 生成但有源码事实兜底 |
| **Learnings**（学习总结，reviewed 后） | 6 | 人工 review 通过 |
| **Learnings**（学习总结，draft） | 3 | 未审核，质量不确定 |
| **Wiki/**（编译页） | 继承来源置信度 | 不独立赋值 |
| **Daily** | — | 不入本体系，走 o2b |

### 3.2 置信度调整规则

| 事件 | 调整 | 说明 |
|:----|:----:|:-----|
| 创建（AI 生成，draft） | 初始 3 | CodeNotes/Learnings 初版 |
| 创建（用户手动写） | 初始 8 | Knowledge 基线 |
| 多 profile 对抗式审查通过 | +2 | 每轮 adversary→synthesis 通过 |
| 用户手动 review → reviewed 状态 | +3 | 最大单次增益 |
| 用户查询后正面反馈（👍） | +1 | 认为有用 |
| 用户查询后负面反馈（👎） | -2 | 内容不对 / 不完整 / 过时 |
| 检测到代码变更但文档未更新 | -3 | 代码已变，文档可能过时 |
| AI 自动修复并重新审查通过 | +1 | 自动修复增益较小 |

### 3.3 领域置信度聚合

按领域聚类计算**加权平均置信度**，权重按查询频率：

```
领域 "privatelink/apisvr"
  ├── go/interfaces.md          conf=7    qps=12
  ├── go/persistence.md         conf=6    qps=5
  ├── go/modules/vpc.md         conf=8    qps=8
  └── go/graph-report.md        conf=5    qps=2
  ──────────────────────────────────────────
  领域加权平均 ≈ 7.0
```

当领域平均置信度低于阈值（默认 4.0）时：
1. 查询不走该领域 wiki 检索
2. cron job 标记为「领域需修复」
3. 触发修复流程

### 3.4 反馈获取

```
用户问：apisvr 的 VPC Endpoint 是怎么创建的？

Hermes 回答（引用 go/modules/vpc-endpoint.md，conf=8）
  ↓
追加一行：这个回答对你有帮助吗？[👍/👎]
  ↓
如果 👎：弹输入框「哪里不对？（选填）」
       记录到 confidence_log（action: query-feedback, score: -2）
```

反馈数据同时记录到 Brain/log/，供后续分析热区问题。

### 3.5 修复流程

#### 按来源分支

```
发现问题（置信度低 / 用户反馈 / 代码变更检测）
    │
    ▼
┌──────────────────┐
│  来源是什么？     │
└──────┬───────────┘
       │
  ┌────┴──────────────────────────┐
  │ codenotes                     │
  │  1. 重新拉最新代码            │
  │  2. 重新跑 Graphify           │
  │  3. 多 profile 再编译一次     │
  │  4. diff 新旧文档 → 产生更新    │
  └────┬──────────────────────────┘
       │
  ┌────┴──────────────────────────┐
  │ learnings / knowledge         │
  │  1. 状态降为 draft            │
  │  2. 通知用户人工 review        │
  │  3. 出修复草案（见下文）        │
  └────┬──────────────────────────┘
       │
       ▼
  标记 fixed 或等用户确认
```

#### AI 差异分析 + 修复草案

当用户反馈「这个文档不对」或代码变更被检测到时：

```
1. 读同领域其他文档的相同主题 → 找出矛盾点
2. 读源码对应模块 → 事实核实
3. 读最近 git diff → 是否有变更但文档没更新
4. AI 输出差异报告 + 修复草案
   格式：【问题位置】→ 【当前内容】→ 【建议修正】→ 【证据来源】

输出不是直接改文档，而是生成修复草案 →
  如果是 codenotes：自动走 review 流程
  如果是 learnings/knowledge：通知用户确认
```

---

## 4. Vault 目录约定

| 目录 | 内容 | 维护者 | 初始置信度 | 格式要求 | 进入 Wiki 编译 |
|------|------|:------:|:--------:|:-------:|:-------------:|
| `Knowledge/` | 业务文档/领域知识 | 用户手动 | 8 | 标准 markdown + wikilinks | ✅ 直接 |
| `Knowledge/<业务>/<服务>/` | 业务层级 | 用户手动 | 8 | 同知识 domain | ✅ |
| `CodeNotes/` | 代码编译文档 | pipeline | 6（审查后） | 固定模板 | ✅（reviewed） |
| `CodeNotes/<业务>/<服务>/<子仓库>/` | 业务层级 | pipeline | 6（审查后） | 4 类模板 | ✅（reviewed） |
| `CodeNotes/<业务>/` | 业务入口 | pipeline | — | 索引 | ✅ |
| `Learnings/` | 学习总结 | 用户+AI | 3(draft)/6(reviewed) | 自由格式 | ✅（reviewed） |
| `Wiki/` | 编译页 | AI 编译 | 继承源 | 交叉引用 | — |
| `Daily/` | 日报 | cron AI | — | YYYY-MM-DD.md | ❌ 走 o2b |
| `Brain/` | Agent 记忆 | o2b 管理 | — | 自动格式 | ❌ |

---

## 5. 数据流

```
知识入库                                   知识出库（Agent 查询）
─────────                                  ─────────────────

产生新源码变更                              用户提问 → Hermes
  │                                              │
  ▼                                              ├→ mywiki skill
Graphify AST 提取 → skeleton                       │
  │                                              ├→ 查置信度
  ▼                                              │   命中领域 conf > 4.0 → 走检索
多 profile 对抗式编译                               │   conf ≤ 4.0 → 标记修复，不走 wiki
  │                                              │
  ▼                                              ▼
CodeNotes/<业务>/<服务>/<子仓库>/              检索命中多篇文档
  interfaces.md                                 │
  persistence.md                                ├→ 按置信度排序
  data-flow.md                                  │
  modules/*                                     ├→ 回答（标注来源+置信度）
  │                                              │
  ▼                                              ▼
reviewed + confidence=N                        追加「有用吗？[👍/👎]」
  │                                              │
  ▼                                              ▼
Layer 4 Wiki 编译                               confidence_log 更新
  → Wiki/Concepts/                              ← 用户反馈
  → Wiki/Knowledge/                             
  → Wiki/index.md                              
```

---

## 6. 技术选型

| 组件 | v2 方案 | 对比 v1 |
|------|---------|:-------:|
| 数据源 | Obsidian vault (.md) | 不变 |
| 代码骨架提取 | Graphify（AST + community detection） | 不变 |
| **代码语义编译** | **多 profile Kanban Swarm（hermes kanban swarm）** | **新增** |
| **对抗式审查** | **code-analyzer + code-adversary + code-synthesizer 三 profile** | **新增** |
| 语义搜索 | gbrain (PGLite + Ollama) 或 LightRAG | 不变 |
| 知识编译 | LLM Wiki（Hermes agent 内置） | 不变 |
| 记忆层 | open-second-brain | 不变 |
| 笔记格式 | obsidian-skills | 不变 |
| **置信度体系** | **metadata.confidence + confidence_log + 领域聚合** | **新增** |
| **反馈闭环** | **query 后追加 👍/👎 + 置信度调整** | **新增** |
| **修复流程** | **按来源分支 + AI 差异分析出草案** | **新增** |
| **业务层级** | **CodeNotes/<业务>/<服务>/<子仓库>/** | **新增** |

---

## 7. 实施路线图

### Phase 1：目录重构 + 置信度基础（~30min）

```
[ ] Vault 目录从扁平改为业务层级
[ ] metadata 模板增加 source / confidence / confidence_log
[ ] 写初始置信度赋值脚本
[ ] 更新 hermes cron job（每日统计置信度）
[ ] git push 新结构
```

**验收**：`CodeNotes/privatelink/apisvr/go/interfaces.md` 等新路径可用

### Phase 2：多 Profile 对抗式分析（~1h）

```
[ ] 创建 code-analyzer / code-adversary / code-synthesizer 三个 Hermes profile
[ ] 配各自的 role skill（gen 激进 / adv 挑刺 / syn 合并）
[ ] 写 kanban swarm 模板脚本
[ ] 首次运行：对抗式编译 apisvr 的持久化层
[ ] 对比单 LLM 产出和质量差异
```

**验收**：`hermes kanban swarm "编译..."` 一次跑通，产出 4 类文档

### Phase 3：置信度闭环（~1h）

```
[ ] 在 mywiki skill 中加入回答后反馈入口
[ ] confidence_log 记录逻辑
[ ] 领域置信度聚合 + 阈值检查 cron
[ ] 修复流程脚本（按来源分支 + AI 差异分析）
[ ] 配置阈值低于 4.0 时走修复
```

**验收**：问一个问题 → 回答 → 点 👎 → 置信度下降 → cron 检测到异常 → 触发修复流程

### Phase 4：持续改进

```
[ ] 统计热区文档（查询频率高但置信度低）
[ ] 优化权重算法（是否按时间衰减？）
[ ] 扩展 wiki 编译的领域范围
[ ] 接入更多业务线的代码
```

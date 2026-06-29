# mywiki — 个人知识库设计方案 v3

> 综合 v2 设计 + 流程文档的实践细节，统一 Kanban 模式、置信度体系、Wiki 分层

---

## 目录

- [1. 核心理念](#1-核心理念)
- [2. 八层架构](#2-八层架构)
  - [L0：Obsidian Vault](#l0obsidian-vault)
  - [L1：笔记格式层](#l1笔记格式层)
  - [L2：内容采集层](#l2内容采集层)
  - [L3：代码知识提取 — Kanban 统一管线](#l3代码知识提取--kanban-统一管线)
  - [L4：文档知识入库](#l4文档知识入库)
  - [L5：Wiki 编译层](#l5wiki-编译层)
  - [L6：语义检索层](#l6语义检索层)
  - [L7：Agent 记忆层 — open-second-brain](#l7agent-记忆层--open-second-brain)
  - [L8：Hermes mywiki Skill](#l8hermes-mywiki-skill)
- [3. 知识处理管线](#3-知识处理管线)
  - [3.1 代码型知识处理](#31-代码型知识处理)
  - [3.2 文档型知识处理](#32-文档型知识处理)
- [4. Kanban 统一模式](#4-kanban-统一模式)
  - [4.1 仓库级文档（Stage 1）](#41-仓库级文档stage-1)
  - [4.2 业务级聚合（Stage 2）](#42-业务级聚合stage-2)
  - [4.3 修复流程（Stage 3）](#43-修复流程stage-3)
- [5. 文档产出规范](#5-文档产出规范)
- [6. 置信度体系](#6-置信度体系)
  - [6.1 来源分层与初始置信度](#61-来源分层与初始置信度)
  - [6.2 置信度调整规则](#62-置信度调整规则)
  - [6.3 时间衰减](#63-时间衰减)
  - [6.4 领域置信度聚合](#64-领域置信度聚合)
  - [6.5 反馈获取](#65-反馈获取)
  - [6.6 修复触发条件](#66-修复触发条件)
- [7. Vault 目录约定](#7-vault-目录约定)
- [8. 数据流](#8-数据流)
- [9. 技术选型](#9-技术选型)
- [10. 实施路线图](#10-实施路线图)

---

## 1. 核心理念

```
┌────────────────────────────────────────────────────────────────────────┐
│  你写进 vault → agent 能搜到、用到                                       │
│  agent 学到 → 写回独立 Brain vault                                        │
│  知识在同一个地方不断叠加                                                 │
│  文档有置信度 → 不靠谱的不进回答 → 反馈修正闭环                            │
└────────────────────────────────────────────────────────────────────────┘
```

**四条铁律：**
1. **Obsidian vault 是唯一数据源** — 所有外部索引可以推倒重建，vault 里的 `.md` 不会丢。
2. **人和 agent 读同一个东西** — 一篇笔记，两个读者。
3. **知识是提炼的，不是搬运的** — 代码存摘要不存原文，网页转笔记不存截图。
4. **代码事实落地靠源码，Graphify 是索引不是结论** — 语义分析和文档生成由多 Agent 对抗式完成。

**知识分类两条轴：**
- **来源轴**：内部（企业代码库 / 个人学习）vs 外部（公众号 / 博客 / 官方文档 / GitHub 开源）
- **类型轴**：代码型（经过编译测试的代码，置信度高）vs 文档型（人总结编写，需校验）

---

## 2. 八层架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Obsidian Vault — ~/mywiki/                             │
│                                                                             │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐ ┌──────────┐            │
│  │Knowledge │ │CodeNotes │ │Learnings │ │ Wiki │ │   docs   │            │
│  │ 手动知识  │ │ 代码编译  │ │ AI 总结  │ │编译页│ │ 内外部文档│            │
│  └────┬────┘ └─────┬────┘ └────┬─────┘ └──┬───┘ └────┬─────┘            │
│       │            │           │          │          │                   │
│       └────────────┼───────────┼──────────┼──────────┘                   │
│                    │           │          │                               │
└────────────────────┼───────────┼──────────┼─────────────────────────────────┘
                     │           │          │
          ┌──────────┘           │          └──────────────┐
          ▼                      ▼                        ▼
┌────────────────────┐ ┌──────────────────────┐ ┌──────────────────────┐
│ L3: 代码编译管线   │ │ L4: 文档入库         │ │ L5: Wiki 编译层      │
│ Graphify → Kanban  │ │ Kanban → MR → 审查   │ │ personal/biz/public  │
│ 多profile 对抗式   │ │                      │ │ 仅 reviewed 文档进入  │
└─────────┬──────────┘ └──────────┬───────────┘ └─────────┬────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ L6: 语义检索          │
                    │ gbrain / LightRAG    │
                    │ 结合置信度排序        │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────────┐
                    │ L7: Agent 记忆           │
                    │ open-second-brain        │
                    │ → 独立 vault (~/brain/)  │
                    └──────────┬───────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ L8: Hermes mywiki    │
                    │ Skill 统一入口       │
                    └──────────────────────┘
```

### L0：Obsidian Vault

**Vault 路径**：`~/mywiki/`

唯一数据源，git 入 GitLab 私有仓库。所有文档都是 `.md` 文件，人和 agent 共享同一视图。

### L1：笔记格式层

加载 `obsidian-markdown` / `obsidian-bases` / `json-canvas` / `defuddle`，确保 agent 能正确读写 Obsidian 格式。

### L2：内容采集层

非必须。通过 chubbyskills 或其他采集脚本将外部内容转化为 markdown 存入 vault。

### L3：代码知识提取 — Kanban 统一管线

**这是 v3 的核心变化**，综合了 design-v2 的对抗式三阶段和 流程.md 的并行写作+迭代审查模式。

详见 [第 4 节 Kanban 统一模式](#4-kanban-统一模式)。

### L4：文档知识入库

处理文档型知识（公众号、博客、内部文档等）的入库流程。见 [3.2 文档型知识处理](#32-文档型知识处理)。

### L5：Wiki 编译层

LLM Wiki 模式，将 `reviewed` 状态的文档编译为交叉引用的概念/实体页面。

**Wiki 分三层**：
- `personal` — 个人文档（学习总结、读书笔记等）
- `biz` — 公司项目和业务文档
- `public` — 外源性知识（公众号、GitHub 提炼等）

### L6：语义检索层

gbrain / LightRAG 作为 MCP Server，提供向量+知识图谱混合检索。

检索策略结合置信度：按置信度排序结果，低于阈值的领域走修复流程。

### L7：Agent 记忆 — open-second-brain（独立 vault）

独立于 `~/mywiki/` 的 Brain 体系，运行在 `~/brain/`。信号→dream→偏好流程。与知识库置信度体系隔离。

### L8：Hermes mywiki Skill

统一入口 skill，整合 L3-L7 的调用流程。

---

## 3. 知识处理管线

### 3.1 代码型知识处理

```
┌────────────────────────────────────────────────────────────────┐
│  Stage 1: 仓库级文档                                            │
│  ─────────────────────                                          │
│  输入：源码仓库（某服务的子仓库，如 apisvr/go）                     │
│  输出：README / architecture / modules/* / dataflow/* / interfaces.md │
│  工具：Graphify AST 提取 → Kanban 多 profile 编译               │
│  (详见第 4 节)                                                    │
│                                                                │
│  Stage 2: 业务级聚合                                            │
│  ─────────────────────                                          │
│  输入：同一业务下各服务仓库的 Stage 1 产出                         │
│  输出：architecture.md（服务间关系）+ dataflow.md（跨服务请求流转） │
│  工具：Kanban（架构师 profile 阅读各服务文档 → 提炼 → 审查）       │
│                                                                │
│  Stage 3: 修复                                                  │
│  ─────────────────────                                          │
│  触发条件：置信度低于阈值 / 用户反馈 / 代码变更检测                 │
│  修复：重新拉代码 → 重新 Graphify → 多 profile 再编译 → diff 更新  │
│                                                                │
│  状态说明：                                                      │
│  ─────────                                                      │
│  Kanban 完成后 → pending-review（等待人类 review）                 │
│  人类 review 通过 → reviewed                                    │
│  仅 reviewed 文档进入 Wiki 编译和语义检索                          │
└────────────────────────────────────────────────────────────────┘
```

### 3.2 文档型知识处理

```
原始文档（公众号 / 博客 / 内部文档 / 官方文档）
          │
          ▼
┌──────────────────────────────────────────────┐
│  Kanban 编译（同 Stage 1 结构，但无 Graphify） │
│  ──────────────────────────────────────────── │
│  Writer × 2-4 并行理解原文 + 提取知识点         │
│  ├─ 纠正原文逻辑错误（标注原文 vs 修正）         │
│  ├─ 与已有知识库交叉校验（防止矛盾/重复）         │
│  └─ 给出知识归并意见（合并到哪个目录/文件）       │
│                                              │
│  Adversary 审查                               │
│  ├─ 挑刺遗漏、理解偏差                          │
│  └─ 标记与已有知识的冲突                        │
│                                              │
│  Reviewer 迭代 → 直到无意见                     │
│                                              │
│  Polisher 润色                                │
└───────────────────────────┬──────────────────┘
                            │
                            ▼
                    ┌──────────────────────┐
                    │ 发起 Merge Request   │
                    │ 产出 → 请求人类审批   │
                    └──────────┬───────────┘
                               │
                          ┌────┴────┐
                          │ 人类    │
                          │ Review  │
                          └────┬────┘
                          ├───────┘
                     ┌────┴────┐
                     │ approved│
                     └─────────┘
                          │
                          ▼
                  知识入库 Knowledge/
                  或 Learnings/reviewed/
                  state: reviewed, confidence=8
```

**实现方式**：设计为一个 Hermes Skill，用户在对话中提出「把这篇知识库化」时运行上述 Kanban 流程，最后发 Merge Request 等人审批。

---

## 4. Kanban 统一模式

综合 design-v2 和 流程.md 两种 Kanban 模式，v3 采用**三阶段渐进式 Kanban**：

### 4.1 仓库级文档（Stage 1）

```
┌─────────────────────────────────────────────────────────────────┐
│                  Orchestrator（调度器）                           │
│  ├─ 评估内容量级：接口数 > 20 或 预估行数 > 200 → 自动拆分文件    │
│  ├─ 分配任务给 Writer × N（N=2-4，按模块/文档类型分）              │
│  └─ 收集产出 → 进入审查循环                                      │
└─────────────────────────────────────────────────────────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           ▼                    ▼                    ▼
    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │ Writer 1     │   │ Writer 2     │   │ Writer N     │
    │ inputs:      │   │ inputs:      │   │ inputs:      │
    │ AST graph    │   │ AST graph    │   │ AST graph    │
    │ 源码        │   │ 源码        │   │ 源码        │
    │ README      │   │ README      │   │ README      │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
           │                  │                  │
           └──────────┬───────┴─────────┬────────┘
                      ▼                 ▼
           ┌──────────────────┐  ┌──────────────────────┐
           │ Adv Profile      │  │ 迭代循环（可选多次）   │
           │ 对抗式审查       │  │ Reviewer 挑刺          │
           │ 挑刺遗漏         │──┤ Writer 修改            │
           │ 标记幻觉         │  │ 直到无意见             │
           │ 指出过度推断     │  └──────────────────────┘
           └────────┬─────────┘
                    │
                    ▼
           ┌──────────────────┐
           │ Polisher         │
           │ 排序、润色       │
           │ 不改变逻辑       │
           │ 增强可读性       │
           └──────────────────┘
                    │
                    ▼
           ┌────────────────────────────────────────────┐
           │ 文档进入 pending-review 状态               │
           │ 初始置信度 7（代码型）                     │
           │ 等待人类 review → reviewed 后进入 Wiki 编译 │
           └────────────────────────────────────────────┘
```

**要点：**
- **并行写作**：2-4 个 Writer 根据 orchestrator 分配的模块和 prompt，同时生成不同部分的文档
- **对抗式审查**：Adversary profile 对 Writer 产出进行挑刺，事实来源是源码和 AST 图
- **迭代审查**：Reviewer 的意见加入 prompt 让 Writer 修改，直到没有意见——**设计 v2 的 gen→adv→syn 的单轮对抗和 流程.md 的 reviewer 迭代循环可以并存**：先跑一轮对抗式审查（故意 noisy → 挑刺 → 修正），再跑迭代审查直到零意见
- **润色**：不改变逻辑的情况下对文档进行排序、加入过渡词使文档更易读

### 4.2 业务级聚合（Stage 2）

```
              各服务仓库的 Stage 1 产出
                        │
                        ▼
             ┌─────────────────────┐
             │ 架构师 Profile      │
             │ 阅读各服务文档      │
             │ 提炼出架构和流转    │
             └─────────┬───────────┘
                       │
                       ▼
             ┌─────────────────────┐
             │ 产出草案：          │
             │ architecture.md     │
             │ dataflow.md         │
             └─────────┬───────────┘
                       │
                       ▼
             ┌─────────────────────┐
             │ Reviewer            │
             │ 根据代码事实审查    │
             │ 迭代直到无意见      │
             └─────────┬───────────┘
                       │
                       ▼
             ┌─────────────────────┐
             │ Polisher 润色       │
             └─────────────────────┘
```

### 4.3 修复流程（Stage 3）

```
发现置信度问题 / 用户反馈 / 代码变更
        │
        ▼
┌──────────────────┐
│  来源是什么？     │
└──────┬───────────┘
       │
  ┌────┴──────────────────────────────┐
  │ codenotes                         │
  │ 1. 重新拉最新代码                  │
  │ 2. 重新跑 Graphify                │
  │ 3. 多 profile 再编译（Stage 1）    │
  │ 4. diff 新旧文档 → 更新            │
  └────┬──────────────────────────────┘
       │
  ┌────┴──────────────────────────────┐
  │ learnings / knowledge             │
  │ 1. 状态降为 draft                 │
  │ 2. 通知用户人工确认               │
  │ 3. AI 出修复草案：问题位置→当前内容 │
  │    →建议修正→证据来源              │
  │ 4. 人类审批后修复                 │
  │ 5. Reviewer 对比事实验证          │
  └────┬──────────────────────────────┘
       │
       ▼
  文档置信度更新，标记 fixed 或待确认
```

---

## 5. 文档产出规范

### 仓库级文档（每个子仓库一组）

| 文件 | 目的 | 回答的问题 | 事实锚点 |
|------|------|-----------|:--------:|
| **README.md** | 项目概览 | 这是一个什么项目？做什么的？ | Graphify + 源码 |
| **architecture.md** | 架构图景 | 项目分几层？各层模块做什么？ | 源码调用链 |
| **modules/<module>.md** | 模块细节 | 某模块的输入输出、功能是什么？ | 源码行号 |
| **dataflow/{api-path}.md** | API 流转 | 某个接口来了之后是怎么被处理的？ | 源码行号 |
| **dataflow/{data-path}.md** | 数据流转 | 数据入口→解析层→处理层→转发层的流转？ | 源码行号 |
| **interfaces.md** | 接口清单 | 对外提供了哪些接口？依赖哪些外部服务？ | Graphify 调用图 |

**分拆策略**：接口数 > 20 或预估行数 > 200 时自动拆分到子目录。

### 业务级文档（跨服务聚合）

| 文件 | 目的 | 回答的问题 |
|------|------|-----------|
| **architecture.md** | 整体业务架构 | 这个业务的服务间是什么关系？ |
| **dataflow.md** | 跨服务流转 | 一个业务请求的完整流转路径？ |

---

## 6. 置信度体系

### 6.1 来源分层与初始置信度

每篇文档 metadata：

```yaml
---
source: codenotes                       # codenotes | learnings | knowledge | wiki
confidence: 7                           # 0-10
state: pending-review                   # draft | pending-review | reviewed | needs-fix
confidence_log:
  - date: 2026-06-22
    action: create
    score: 7
    reason: "CodeNotes 初版，经 Kanban 编译通过"
  - date: 2026-06-23
    action: human-review
    score: 8
    reason: "人类 review 通过"
---
```

| 来源 | 初始置信度 | 初始状态 | 原因 |
|------|:---------:|:--------:|------|
|| **Knowledge**（用户手动写，长期维护） | 8 | reviewed | 用户手动写的领域知识 |
|| **CodeNotes**（Kanban 编译完成） | 7 | pending-review | 源码兜底，多轮审查，等人 review |
|| **CodeNotes**（初版 draft） | 3 | draft | 待审核 |
|| **Learnings**（reviewed 后） | 7 | reviewed | 使用过程中 AI 生成的总结，人工审核通过 |
|| **Learnings**（draft） | 3 | draft | AI 生成的初稿 |
|| **Docs**（原始文档直接入库） | 8 | reviewed | 下载的内外部文档，本身完整无需编译 |
|| **文档型入库**（Kanban 编译 → MR → 人类 review 通过） | 8 | reviewed | 经历了 Kanban 编译 + 人工审批 |
|| **Wiki/**（编译页） | 继承源置信度 | — | 不独立赋值 |

### 6.2 置信度调整规则

| 事件 | 调整 | 说明 |
|:----|:----:|:-----|
| 创建（AI 生成，draft） | 初始 3 | CodeNotes/Learnings 初版 |
| 创建（用户手动写） | 初始 8 | Knowledge |
| Kanban 仓库级(Stage 1)审查通过 | 初始 7 | Writer×N + 对抗式 + 迭代审查 + 润色全部通过 → pending-review |
| Kanban 业务级(Stage 2)审查通过 | 初始 7 | 架构师提炼 + 审查 → pending-review |
| Kanban 文档型入库审查通过 | 初始 8 | 文档型 Kanban 编译 + 逻辑校验 → 发出 MR |
| **人类 review → reviewed 状态** | **+2** | **最核心的增益——无论代码型还是文档型，人类 review 通过后加 2 分** |
| 用户查询后正面反馈（👍） | +1 | 认为有用 |
| 用户查询后负面反馈（👎） | -2 | 内容不对 / 不完整 / 过时 |
| 检测到代码变更但文档未更新 | -3 | 代码已变，文档可能过时 |
| 修复后重新 Kanban 审查通过 | +1 | 自动修复增益较小 |

### 6.3 时间衰减

**每周衰减 1 分**，从最近修改日起算。

- 衰减下限：3 分（低于此强制触发修复）
- 衰减暂停条件：90 天内收到过正面反馈
- 衰减可通过 cron job 统一计算，批量更新 `confidence` 字段

### 6.4 领域置信度聚合

按路径前缀聚类计算**加权平均置信度**，权重按查询频率：

```
领域 "privatelink/apisvr/go"
  ├── README.md              conf=7  qps=3
  ├── interfaces.md           conf=7  qps=12
  ├── persistence.md          conf=6  qps=5
  ├── modules/vpc.md          conf=8  qps=8
  └── architecture.md         conf=7  qps=4
  ────────────────────────────────────
  领域加权平均 ≈ 7.0
```

当领域平均置信度低于阈值（默认 4.0）时：
1. 查询不走该领域 wiki 检索
2. cron job 标记为「领域需修复」
3. 触发修复流程（Stage 3）

### 6.5 反馈获取

```
用户问：apisvr 的 VPC Endpoint 是怎么创建的？

Hermes 回答（引用 modules/vpc-endpoint.md，conf=8）
  ↓
追加一行：这个回答对你有帮助吗？[👍/👎]
  ↓
如果 👎：弹输入框「哪里不对？（选填）」
       记录到 confidence_log（action: query-feedback, score: -2）
```

反馈数据记录到 confidence_log，供后续分析热区问题。

### 6.6 修复触发条件

满足以下任一条件即触发修复：
1. 领域聚合置信度 < 4.0
2. 单文档置信度 < 3.0（含时间衰减后）
3. 用户连续 2 次负面反馈（同一文档）
4. 代码变更检测到文档过时（git diff 提示对应文件变更）

---

## 7. Vault 目录约定

```
~/mywiki/
├── Knowledge/                        # 业务/领域知识（用户手动写）
│   ├── privatelink/
│   │   ├── overview.md
│   │   ├── architecture.md
│   │   └── deployment.md
│   └── go-patterns/
│
├── CodeNotes/                        # 代码编译文档
│   ├── privatelink/                  # 〈业务线〉
│   │   ├── apisvr/                   # 〈服务〉
│   │   │   ├── go/                   # 〈子仓库〉（Go 项目）
│   │   │   │   ├── README.md
│   │   │   │   ├── architecture.md
│   │   │   │   ├── interfaces.md
│   │   │   │   ├── modules/
│   │   │   │   ├── dataflow/
│   │   │   │   └── graph.json
│   │   │   ├── web/                  # 〈子仓库〉（前端）
│   │   │   │   └── README.md
│   │   │   └── migration/
│   │   ├── authsvr/
│   │   │   └── go/
│   │   ├── controllersvr/
│   │   │   └── go/
│   │   └── architecture.md           # 业务级聚合文档
│   │   └── dataflow.md
│   └── ueip_ops/
│       └── apisvr/
│           └── go/
│
├── Learnings/                        # 使用过程中 AI 生成的总结（draft → reviewed）
│   ├── draft/                        # AI 生成的初稿，未审核
│   │   └── go-generics-202606.md
│   └── reviewed/                     # 人工审核通过
│       ├── rest-api-design.md
│       └── go-slices.md
│
├── Wiki/                             # LLM 编译页面
│   ├── personal/                     # 个人知识
│   ├── biz/                          # 公司项目和业务
│   │   └── privatelink/
│   │       └── vpc-endpoint-overview.md
│   └── public/                       # 外源性知识
│
├── docs/                             # 下载的内外部文档（原始文档直接入库）
│   └── go-1.21-release-notes.md
│
├── Templates/                        # 模板
│
├── Assets/                           # 附件
│
└── .obsidian/                        # Obsidian 配置
```

| 目录 | 内容 | 维护者 | 初始状态 | 初始置信度 | 进入 Wiki 编译 |
|------|------|:------:|:--------:|:--------:|:-------------:|
| `Knowledge/` | 业务/领域知识 | 用户手动 | reviewed | 8 | ✅ 直接 |
| `CodeNotes/<业务>/<服务>/<子仓库>/` | 代码编译文档 | pipeline | pending-review | 7 | ✅（reviewed 后） |
| `Learnings/reviewed/` | AI 生成的总结，已审核 | 用户+AI | reviewed | 7 | ✅ |
| `Learnings/draft/` | AI 生成的总结，初稿 | AI | draft | 3 | ❌ |
| `docs/` | 下载的内外部文档 | 用户手动 | reviewed | 8 | ✅ 直接 |
| `Wiki/{personal,biz,public}/` | 编译页 | AI 编译 | — | 继承源 | — |

---

## 8. 数据流

```
知识入库                                   知识出库（Agent 查询）
─────────                                  ─────────────────

代码型：                                   用户提问 → Hermes
  │                                              │
  ▼                                              ├→ mywiki skill
Graphify AST 提取 → graph.json                    │
  │                                              ├→ 查领域置信度
  ▼                                              │   命中领域 conf > 4.0 → 走检索
Kanban Stage 1（仓库级文档）                        │   conf ≤ 4.0 → 标记修复
  ├─ 2-4 Writer 并行                              │
  ├─ 对抗式 + 迭代审查                              ▼
  └─ Polisher 润色                             检索命中多篇文档
  │                                              ├→ 按置信度排序
  ▼                                              ├→ 回答（标注来源+置信度）
CodeNotes/<业务>/<服务>/<子仓库>/                   │
  README + architecture + modules/*               ▼
  + dataflow/* + interfaces.md                追加「有用吗？[👍/👎]」
  │                                              │
  ▼                                              │
pending-review + confidence=7               confidence_log 更新
  │                                              ← 用户反馈
  ▼                                              │
人类 review → reviewed（+2）                       ├→ 无问题 → 结束
  │                                              │
  ├─ 通过 → Stage 2 业务级聚合                     ├→ 👎 → 触发修复流程
  │         Architecture Profile                  │
  │         → cross-service docs                  ├→ 代码变更检测
  │         → pending-review → 人类 review        │
  │                                              ▼
  ├─ 通过 → Wiki 编译                        Stage 3 修复
  │         → Wiki/personal/                      │
  │         → Wiki/biz/                          ├→ codenotes：自动修复
  │         → Wiki/public/                       └→ learnings/knowledge：出草案→人批
  │
  └─ 所有 reviewed 文档 → 语义检索索引更新
            gbrain / LightRAG


文档型：
原始文档（公众号/博客/内部文档）
  │
  ▼
Kanban 编译（同结构，无 Graphify）
  ├─ Writer × 2-4 理解原文 + 提取知识点
  │   ├─ 纠正逻辑错误（标注原文 vs 修正）
  │   ├─ 与已有知识库交叉校验
  │   └─ 给出知识归并意见
  ├─ Adversary 审查
  └─ Reviewer 迭代 → 无意见
  │
  ▼
发起 Merge Request → 请求人类审批
  │
  ▼
人类 review
  ├─ approved → 入 Knowledge/ 或 Learnings/reviewed/
  │             state: reviewed, confidence=8
  └─ rejected → 退回修改
```

---

## 9. 技术选型

| 组件 | 方案 |
|------|------|
| 数据源 | Obsidian vault (`.md`) |
| 代码骨架提取 | Graphify（AST + community detection） |
| 代码语义编译 | **Kanban 统一管线（Hermes kanban swarm + workflow.yaml）** |
| 对抗式审查 | **Adversary Profile（源码 + AST 图锚定事实）** |
| 迭代审查 | **Reviewer Profile（多轮修正直到零意见）** |
| 文档格式化 | obsidian-skills |
| 语义搜索 | gbrain (PGLite + Ollama) 或 LightRAG |
| 知识编译 | LLM Wiki（Hermes agent 内置） |
| 记忆层 | open-second-brain |
| 文档入库管线 | Hermes Skill（对话驱动） |
| 代码仓库源 | 内部 GitLab + GitHub |
| 版本管理 | git |

---

## 10. 实施路线图

### Phase 1：目录重构（~30min）

```
[ ] Vault 目录从扁平改为业务层级（Knowledge/<业务>/<服务>/ 等）
[ ] metadata 模板增加 source / confidence / confidence_log
[ ] 写初始置信度赋值脚本
[ ] 更新 hermes cron job（每日统计置信度 + 时间衰减计算）
[ ] git push 新结构
```

**验收**：`CodeNotes/privatelink/apisvr/go/interfaces.md` 等路径可用

### Phase 2：仓库级 Kanban（~1.5h）

```
[ ] 创建 3 个 Profile：
    - code-writer (Stage 1 写作)
    - code-adversary (对抗式审查)
    - code-synthesizer (合并 + 迭代审查)
[ ] 配各自的 prompt / role skill
[ ] 写 workflow.yaml 定义 Kanban 流程
    - Writer × 2-4 并行 → Adversary 审查 → Synthesis 修正 → Polisher 润色
[ ] 首次运行：编译 apisvr/go 的持久化层
[ ] 对比单 LLM 产出和质量差异
```

**验收**：`hermes kanban ...` 一次跑通，产出完整文档，状态为 `pending-review`

### Phase 3：人类 review 流程（~30min）

```
[ ] 定义 CodeNotes review 的标准操作流程
    - 人类如何批阅 pending-review 文档
    - review 通过 → state 改为 reviewed, confidence += 2
    - review 不通过 → 退回 kanban 重新编译
[ ] 定义文档型入库的 merge request 格式
[ ] 首次 review 已编译的 apisvr/go 文档
```

**验收**：Kanban 产出的文档经人类 review 后进入 reviewed 状态

### Phase 4：业务级聚合（~1h）

```
[ ] 创建 architect Profile（Stage 2）
[ ] 写聚合 kanban 脚本
[ ] 首次运行：聚合 privatelink 业务线的跨服务文档
[ ] 迭代：Reviewer 根据代码事实审查聚合文档
```

**验收**：`CodeNotes/privatelink/architecture.md` 和 `dataflow.md` 可用

### Phase 5：置信度闭环（~1h）

```
[ ] 在 mywiki skill 中加入回答后反馈入口
[ ] confidence_log 记录逻辑
[ ] 领域置信度聚合 + 阈值检查 cron
[ ] 时间衰减 cron（每周 -1）
[ ] 修复流程（按来源分支 + AI 分析出草案）
```

**验收**：问问题 → 回答 → 👎 → 置信度下降 → cron 检测异常 → 触发修复

### Phase 6：文档入库管线（~1h）

```
[ ] 创建 doc-ingest skill
[ ] 实现 Kanban 编译流程（Writer × N → Adversary → Reviewer → Polisher）
[ ] 实现 Merge Request 发起逻辑
[ ] 设计 prompt 模板（逻辑校验 + 交叉校验 + 归并意见）
[ ] 测试：对一篇公众号文章跑入库
```

**验收**：对话中说「把这篇知识库化」→ 跑通 Kanban 编译 → 发出 MR

### Phase 7：Wiki 编译 + 持续改进

```
[ ] Wiki 编译仅对 reviewed 文档进行
[ ] Wiki 分 personal / biz / public 三层
[ ] 统计热区文档（高频查询 + 低置信度）
[ ] 权重算法优化（是否按时间衰减衰减因子？）
[ ] 扩展更多业务线
```

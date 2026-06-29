# mywiki v4 — 个人知识库设计方案

> 简化多层架构，元信息 SQLite 化，OSB sig→dream 闭环驱动知识修复

---

## 目录

- [1. v4 核心变化](#1-v4-核心变化)
- [2. 架构总览](#2-架构总览)
- [3. Vault 目录约定](#3-vault-目录约定)
- [4. SQLite 元信息层](#4-sqlite-元信息层)
- [5. 知识处理管线](#5-知识处理管线)
  - [5.1 代码型知识](#51-代码型知识)
  - [5.2 文档型知识](#52-文档型知识)
  - [5.3 个人笔记](#53-个人笔记)
- [6. Wiki 页面规范](#6-wiki-页面规范)
- [7. 置信度体系](#7-置信度体系)
- [8. OSB sig→dream→fix 修复闭环](#8-osb-sigdreamfix-修复闭环)
- [9. 实体与关系层](#9-实体与关系层)
- [10. 技术选型](#10-技术选型)
- [11. 实施路线图](#11-实施路线图)

---

## 1. v4 核心变化

| 变化 | v3 | v4 |
|------|:--:|:--:|
| 目录结构 | CodeNotes/ + Knowledge/ + Learnings/ + Wiki/ 四层 | **Wiki/** 单层，按领域分子目录 |
| 编译链路 | 底层 → Kanban → 三级目录 → Wiki 编译 | **源码/文档 → Kanban → Wiki（直接产出）** |
| 元信息 | 嵌在 markdown frontmatter | **SQLite（mywiki.db）** |
| 修复流程 | 手动 review，无自动化 | **OSB sig→dream → cron→fix pipeline** |
| 知识缺口检测 | 无 | **agent 使用中自动积累 sig → dream → fix** |

---

## 2. 架构总览

```
┌────────────────────────────────────────────────────────────────────┐
│                          Obsidian Vault                             │
│                          ~/mywiki/                                 │
│                                                                     │
│   Wiki/                     mywiki.db           raw/                │
│   ├─ privatelink/           (元信息)             ├─ articles/       │
│   ├─ ucloud/                                    ├─ papers/         │
│   ├─ personal/                                  └─ assets/         │
│   └─ concepts/                                                      │
└──────────────────────────┬─────────────────────────────────────────┘
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │ Kanban 编译  │ │ OSB MCP │ │ gbrain MCP  │
    │ (生产页面)   │ │ (sig→   │ │ (语义检索)   │
    │             │ │ dream)  │ │              │
    └──────────────┘ └──────────┘ └──────────────┘
                           │
                           ▼
                    ┌──────────────┐
                    │ mywiki.db   │
                    │ cron 维护   │
                    │ (置信度衰减) │
                    │ (修复触发)  │
                    └──────────────┘
```

### 分层

| 层 | 组件 | 职责 |
|----|------|------|
| L0 | Obsidian Vault | 唯一数据源，git 管理 |
| L1 | Wiki/ 目录 | 纯 markdown 页面，无 frontmatter，按领域分目录 |
| L2 | **mywiki.db** | 所有元信息（状态、置信度、来源、反馈、缺口） |
| L3 | Kanban 编译 | Graphify + 多 profile 对抗式编译，直接产出 Wiki 页面 |
| L4 | 语义检索 | gbrain / LightRAG MCP Server |
| L5 | **OSB sig→dream** | 使用中积累信号 → 夜间合并 → 触发修复 |
| L6 | cron 维护 | 置信度衰减、修复检测、缺口通知 |
| L7 | Hermes mywiki Skill | 统一入口，整合 L1-L6 |

---

## 3. Vault 目录约定

```
~/mywiki/
├── Wiki/                           # 唯一的知识文档目录
│   ├── privatelink/                # 按业务/领域分子目录
│   │   ├── unetfe-overview.md
│   │   ├── unetfe-api-flow.md
│   │   ├── eip-service.md
│   │   └── gateway-architecture.md
│   ├── ucloud/                     # UCloud 相关
│   │   └── region-id-map.md
│   ├── personal/                   # 个人学习总结
│   │   ├── go-patterns.md
│   │   └── k8s-notes.md
│   ├── concepts/                   # 跨领域概念
│   │   └── rbac-model.md
│   └── index.md                    # Wiki 内容索引（手动维护或自动生成）
│
├── raw/                            # 原始资料（只读，git 管理）
│   ├── articles/                   # 网页文章
│   ├── papers/                     # PDF / 论文
│   └── assets/                     # 图片、附件
│
├── Wiki/
│   └── projects/                   # ⚠️ 软链接或子模块指向具体代码仓库路径
│       └── privatelink → /Users/user/Code/privatelink
│
├── mywiki.db                       # SQLite 元信息库
├── .gitignore
└── README.md
```

### Wiki/ 目录规则

- **无 frontmatter** — 页面纯 markdown 内容。元信息全部在 mywiki.db
- **文件名** — 小写连字符，如 `unetfe-api-flow.md`
- **内容** — 使用 Obsidian 标准语法：`[[wikilink]]`、`> [!NOTE]` callout、代码块
- **页面顶端可选三行摘要** — 方便你直接阅读时快速了解

---

## 4. SQLite 元信息层

### 4.1 表结构

```sql
-- 页面主表
CREATE TABLE wiki_pages (
    id          TEXT PRIMARY KEY,          -- Wiki/privatelink/unetfe-overview（vault 相对路径）
    title       TEXT NOT NULL,             -- 页面标题
    type        TEXT NOT NULL DEFAULT 'concept',  -- concept | entity | comparison | reference
    dir         TEXT NOT NULL,             -- Wiki/privatelink/（目录，用于领域聚合）
    state       TEXT NOT NULL DEFAULT 'draft',    -- draft | pending-review | reviewed | needs-fix
    confidence  REAL NOT NULL DEFAULT 3.0,        -- 0.0 - 10.0
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now')),
    compiled_at TEXT,                      -- 最近一次编译时间（代码型知识）
    graphify_hash TEXT                     -- 最近一次 Graphify 产出 hash，用于判断代码是否变更
);

-- 来源表
CREATE TABLE wiki_sources (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id     TEXT NOT NULL REFERENCES wiki_pages(id),
    source_type TEXT NOT NULL,             -- code | document | manual | web
    source_uri  TEXT NOT NULL,             -- 仓库路径 / URL / 原始文件路径
    summary     TEXT,                      -- 来源描述（如 "从 privatelink/apisvr 源码编译"）
    hash        TEXT                       -- 内容 hash（用于代码型判断变更）
);

-- 置信度变更流水
CREATE TABLE wiki_confidence_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id     TEXT NOT NULL REFERENCES wiki_pages(id),
    old_conf    REAL,
    new_conf    REAL NOT NULL,
    reason      TEXT NOT NULL,             -- create | human-review | decay | feedback-up | feedback-down | code-change | fix
    detail      TEXT,                      -- 补充说明
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- OSB signal 关联（sig→page 的映射）
CREATE TABLE wiki_signals (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id     TEXT NOT NULL REFERENCES wiki_pages(id),
    signal_id   TEXT NOT NULL,             -- OSB signal file id（如 sig-2026-06-23-unetfe-fix）
    topic       TEXT NOT NULL,             -- 匹配的 OSB topic
    signal_type TEXT NOT NULL,             -- positive | negative
    summary     TEXT,                      -- signal 内容概要
    status      TEXT NOT NULL DEFAULT 'pending', -- pending | fix-triggered | fixed | dismissed
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 知识缺口（待修复/新增）
CREATE TABLE wiki_gaps (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    page_id     TEXT,                      -- 关联页面（可空，新增知识时为空）
    gap_type    TEXT NOT NULL,             -- fix | new
    topic       TEXT NOT NULL,             -- 领域/话题
    description TEXT NOT NULL,             -- 问题描述
    fix_type    TEXT,                      -- code-recompile | ai-edit | ask-human
    evidence    TEXT,                      -- 事实依据（引用置信度高的 wiki 页面或其他来源）
    status      TEXT NOT NULL DEFAULT 'open', -- open | in-progress | mr-created | fixed | ignored
    priority    INTEGER DEFAULT 3,         -- 1-5，5 最高
    signal_ids  TEXT,                      -- 关联的 signal id 列表
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    fixed_at    TEXT
);

-- myskill_meta（版本 / 最后 cron 执行时间等）
CREATE TABLE wiki_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### 4.2 索引

```sql
CREATE INDEX idx_pages_state ON wiki_pages(state);
CREATE INDEX idx_pages_dir ON wiki_pages(dir);
CREATE INDEX idx_pages_confidence ON wiki_pages(confidence);
CREATE INDEX idx_confidence_log_page ON wiki_confidence_log(page_id);
CREATE INDEX idx_signals_page ON wiki_signals(page_id);
CREATE INDEX idx_signals_status ON wiki_signals(status);
CREATE INDEX idx_gaps_status ON wiki_gaps(status);
CREATE INDEX idx_sources_page ON wiki_sources(page_id);
```

### 4.3 常用查询

```sql
-- 所有待修复页面（置信度低于阈值）
SELECT id, title, confidence FROM wiki_pages
WHERE state = 'reviewed' AND confidence < 4.0
ORDER BY confidence ASC;

-- 某个领域的平均置信度
SELECT dir, AVG(confidence) as avg_conf FROM wiki_pages
WHERE state = 'reviewed' GROUP BY dir;

-- 某个页面的所有 negative sig
SELECT s.summary, sig.signal_id FROM wiki_signals sig
JOIN wiki_pages p ON sig.page_id = p.id
WHERE p.id = 'Wiki/privatelink/unetfe-overview' AND sig.signal_type = 'negative';

-- 待处理的知识缺口
SELECT * FROM wiki_gaps WHERE status = 'open' ORDER BY priority DESC;

-- 置信度变更流水
SELECT * FROM wiki_confidence_log WHERE page_id = 'Wiki/privatelink/unetfe-overview'
ORDER BY created_at DESC LIMIT 10;
```

---

## 5. 知识处理管线

### 5.1 代码型知识

源码仓库直接编译为 Wiki 页面，不再经过 CodeNotes/ 中转。

```
源码仓库（某服务子仓库）
    │
    ├─ Graphify AST 提取 → graph.json
    │
    ├─ Kanban 多 Profile 对抗式编译
    │   ├─ Orchestrator：评估内容量级，分配任务
    │   ├─ Writer × 2-4：并行生成 Wiki 页面
    │   ├─ Adversary：对抗式审查
    │   ├─ Reviewer：迭代直到零意见
    │   └─ Polisher：排序润色
    │
    ├─ 产出直接写入
    │   Wiki/privatelink/unetfe-overview.md
    │   Wiki/privatelink/unetfe-api-flow.md
    │   ...
    │
    ├─ SQLite 写入来源信息：
    │   wiki_sources: source_type='code', source_uri='privatelink/apisvr'
    │   wiki_pages: state='pending-review', confidence=7
    │
    └─ 人类 review → state='reviewed', confidence+=2
```

**分仓库编译说明：**

不同代码仓库的编译结果写入 Wiki/ 下对应的业务领域目录。例如：

| 代码仓库 | 产出目录 | 说明 |
|----------|---------|------|
| `privatelink/apisvr` | `Wiki/privatelink/apisvr-*.md` | API 服务相关 |
| `privatelink/gateway` | `Wiki/privatelink/gateway-*.md` | 网关相关 |
| `ucloud/console` | `Wiki/ucloud/console-*.md` | 控制台相关 |

**交叉引用**：Kanban 编译时，agent 会先读取同一领域下已有的 Wiki 页面，确保新页面用 `[[wikilink]]` 交叉引用已有知识。

### 5.2 文档型知识

外部文档（公众号、博客、内部文档、官方文档）直接编译为 Wiki 页面。

```
原始文档 / URL / PDF
    │
    ├─ defuddle / Jina Reader → 纯文本
    │
    ├─ Kanban 编译（无 Graphify）
    │   ├─ Writer × 2-4：理解 + 提取知识 + 逻辑纠错 + 交叉校验
    │   ├─ Adversary 审查
    │   └─ Reviewer 迭代
    │
    ├─ 产出直接写入
    │   Wiki/privatelink/gateway-architecture.md
    │
    ├─ SQLite：source_type='document' or 'web'
    │   state='pending-review', confidence=8
    │
    └─ 人类 review → state='reviewed', confidence+=2
```

原始文档保留在 `raw/articles/` 或 `raw/papers/`。

### 5.3 个人笔记

手动写的笔记直接创建 Wiki 页面，SQLite 写入 state='reviewed', confidence=8。

---

## 6. Wiki 页面规范

### 6.1 内容格式

Wiki 页面是纯 markdown，**无 frontmatter**。元信息全部在 mywiki.db。

```markdown
# UNetFe 服务概览

UNetFe 是一个 EIP API 网关服务，通过 ... 对外提供接口。

## 架构

- 接入层：处理 ...
- 业务层：处理 ...
- 数据层：访问 ...

## 关键接口

- `CreateEndpoint`：...
- `DeleteEndpoint`：...

## 相关页面

- [[apisvr-architecture]]
- [[gateway-overview]]
```

### 6.2 页面顶端规范

为了你在 Obsidian 直接阅读时能快速定位，页面顶端保留四行简短元信息（markdown 注释，不进入 SQLite 但仍保留 git）：

```markdown
%% state: pending-review | confidence: 7 | type: concept | sources: privatelink/apisvr %%

# UNetFe 服务概览
...
```

这样你在 obsidian 里看一眼就知道文档状态，不需要查数据库。

---

## 7. 置信度体系

### 7.1 初始置信度

| 来源 | 初始置信度 | 初始状态 |
|------|:---------:|:--------:|
| 代码 Kanban 编译 | 7 | pending-review |
| 文档 Kanban 编译 | 8 | pending-review |
| 手动写笔记 | 8 | reviewed |
| AI 修复/新增（draft） | 3 | draft |
| 人类 review 通过 | +2 | reviewed |

### 7.2 调整规则

| 事件 | 调整 |
|:-----|:----:|
| 人类 review 通过 | +2 |
| 用户👍 | +1 |
| 用户👎 | -2 |
| 检测到代码变更 | -3 |
| 修复后重审通过 | +1 |
| 时间衰减 | -1/周（下限 3） |

### 7.3 领域聚合

按 `dir` 前缀聚类，计算加权平均置信度。低于 4.0 的领域触发修复。

---

## 8. OSB sig→dream→fix 修复闭环

### 8.1 信号来源

```
agent 使用知识库过程中
    │
    ├─ 人类纠正："不对，UNetFe 不是直连 EIP"
    │   → brain_feedback(topic="Wiki/privatelink/unetfe-overview",
    │                     signal="negative",
    │                     principle="UNetFe 不直连 EIP，中间有 Gateway")
    │
    ├─ 用户👎回答
    │   → brain_feedback(topic="Wiki/privatelink/unetfe-api-flow",
    │                     signal="negative",
    │                     principle="回答中 UNetFe 接口描述不准确")
    │
    ├─ agent 发现代码事实与 wiki 矛盾
    │   → brain_feedback(topic="Wiki/privatelink/eip-service",
    │                     signal="negative",
    │                     principle="代码中 eip 模块新增了 auth 校验，wiki 未更新")
    │
    └─ agent 发现 wiki 未覆盖某个概念
        → brain_feedback(topic="Wiki/privatelink/middleware",
                          signal="negative",
                          principle="privatelink 存在 middleware 层，wiki 无此页面")
            │
            ▼
    OSB 积累 sig → wiki_signals 表同步插入（agent 在 brain_feedback 后同步写 mywiki.db）
```

### 8.2 Dream 后的 fix 触发

```
OSB dream 合并 sig → 生成修复类 pref（如 pref-mywiki-fix-unetfe）

cron（每天凌晨）检测：
  │
  ├─ 查 OSB：brain_query(topic="Wiki/privatelink/unetfe-overview")
  │
  ├─ 查 mywiki.db：SELECT * FROM wiki_gaps WHERE status='open'
  │
  ├─ 如果缺口持续存在且有足够多的 negative sig：
  │
  └─ 触发 fix pipeline
```

### 8.3 Fix Pipeline

```
检测到某个 Wiki 页面需修复（sig 积累 3+ / 置信度 < 3.0 / 人工标记）
    │
    ├─ ① 读 sources
    │   SELECT * FROM wiki_sources WHERE page_id = 'Wiki/privatelink/unetfe-overview'
    │
    ├─ ② 判断修复类型
    │   │
    │   ├─ code 类型
    │   │   ├─ 检查 graphify_hash 是否匹配最新代码
    │   │   ├─ 不匹配 → 重拉代码 + Graphify + Kanban → 重写 Wiki 页面
    │   │   └─ 匹配但知识不全 → 标记为 knowledge-gap，需 AI 补充
    │   │
    │   ├─ document 类型
    │   │   ├─ 重新读取原始文档
    │   │   ├─ AI 生成修正草案
    │   │   └─ 产出待 review 的 MR
    │   │
    │   └─ manual 类型
    │       ├─ 直接 AI 修文案
    │       └─ 在 wiki_gaps 标记待 review
    │
    ├─ ③ 构建事实依据
    │   从同一领域下 confidence >= 8 的页面提取事实
    │   （"经常命中且置信度高"的页面 = 可靠事实来源）
    │
    ├─ ④ AI 生成修复/新增草案
    │   参考事实依据 + sig 里的意见
    │   写入 Wiki/ 对应路径
    │   state='draft', confidence=3
    │
    ├─ ⑤ 发出 MR（git branch + commit）
    │
    └─ ⑥ 等待人类 review
        ├─ 通过 → confidence +2, state='reviewed'
        └─ 拒绝 → wiki_gaps.status='open', 重新排队
```

### 8.4 知识缺口检测

除了修复已有页面，还要**检测缺失的知识**：

```
agent 连续多次查询某个 topic 但命中率低
  → brain_feedback(topic="knowledge-gap", signal="negative", ...)
  → wiki_gaps.insert({gap_type: 'new', topic: 'privatelink-middleware', ...})
  → AI 判断是否有事实依据（源码、文档）
  → 有 → 生成草案 → MR
  → 无 → 标记为 "需人工补充"，待你处理
```

### 8.5 Cron 维护任务

```yaml
# 置信度衰减（每周一）
cron:
  name: mywiki-confidence-decay
  schedule: "0 0 * * 1"
  prompt: |
    执行 mywiki 置信度衰减：
    UPDATE wiki_pages SET confidence = MAX(3.0, confidence - 1),
    updated_at = datetime('now')
    WHERE state = 'reviewed' AND julianday('now') - julianday(updated_at) > 7;

# 修复检测（每天凌晨）
cron:
  name: mywiki-fix-check
  schedule: "0 3 * * *"
  prompt: |
    1. 查 OSB：brain_query(topic="Wiki/privatelink/*") 获取待处理的 sig
    2. 查 mywiki.db：SELECT * FROM wiki_gaps WHERE status='open'
    3. 查低置信度页面：SELECT id FROM wiki_pages WHERE confidence < 4.0
    4. 汇总为报告，触发 fix pipeline 处理

# 领域健康报告（每天早 8 点）
cron:
  name: mywiki-health-report
  schedule: "0 8 * * *"
  prompt: |
    报告 mywiki 健康状态：
    - 各领域平均置信度
    - 待修复页面数
    - 待处理知识缺口
    - 累计未 review 的 MR 数
```

---

## 9. 实体与关系层

除了 Wiki 页面，还有一个实体注册表，用于管理**人、系统、服务、概念**的规范名称和别名。

通过 OSB 的实体管理工具维护：

```bash
# 注册实体
o2b brain entity add --name "UNetFe" --category "service" --alias "unetfe" --alias "unet-fe"

# 建立关系
o2b brain entity relate --from "UNetFe" --relation "depends-on" --to "EIP"

# 列出实体
o2b brain entity list --category "service"
```

实体和 Wiki 页面通过 `[[wikilink]]` 建立关联，不需要在 SQLite 中维护关系表。

---

## 10. 技术选型

| 组件 | 方案 | 说明 |
|------|------|------|
| Vault | Obsidian | 唯一数据源 |
| 元信息 | **SQLite**（mywiki.db） | 通过 Python 脚本读写 |
| 代码 AST | Graphify | 确定性事实提取 |
| 文档编译 | Hermes Kanban + delegate_task | 多 profile 对抗式 |
| 语义检索 | gbrain / LightRAG MCP | 待定，不阻塞 v4 实施 |
| Agent 记忆 | **OSB** | sig→dream→preference |
| 定时任务 | Hermes cron | 置信度衰减 + 修复检测 |
| 修复触发 | cron + mywiki db 检查 | 自动调度 fix pipeline |
| MR 审批 | GitLab / GitHub | 等待人类 review |

---

## 11. 实施路线图

### P0（本周）

```
① 创建 mywiki.db schema 和初始化脚本
② 更新 mywiki skill：Kanban 产出直接写 Wiki/ 目录 + mywiki.db
③ 迁移现有页面元信息从 frontmatter 到 SQLite
```

### P1（下周）

```
④ OSB sig → mywiki.db wiki_signals 的同步 bridge
⑤ 置信度衰减 cron job（第一条）
⑥ 修复检测 cron job（检测 + 报告）
```

### P2（下月）

```
⑦ fix pipeline 实现（AI 生成修复草案 → MR）
⑧ 知识缺口检测（agent 使用中自动 sig）
⑨ gbrain / LightRAG MCP 集成
```

---

## 关键原则

1. **Wiki 是编译产物，不是编辑目标。** 修代码/文档 → 重新编译 Wiki，不直接改 Wiki。
2. **SQLite 是元信息，不是内容。** Wiki/ 的 .md 文件永远可读、可 grep、可 git diff。
3. **sig 不直接触发 fix。** dream 合并确认后才触发 cron 检查，避免一有 negative 就修。
4. **事实锚定。** AI 修复必须基于置信度 >= 8 的 Wiki 页面或源码事实，不能凭空生成。
5. **知识缺口不是 bug。** 没覆盖到的领域是正常的，AI 检测到缺口后走新增流程，不是修复。

---

> 参考：`design.md`（v1）、`design-v2.md`（v2）、`design-v3.md`（v3）、`流程.md`（初期流程设计）

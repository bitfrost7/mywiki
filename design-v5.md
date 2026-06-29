# mywiki v5 — gbrain 驱动的个人知识库

> 以 gbrain 为核心引擎，完成从文档入库到大脑自进化的一体化闭环。
> v23.9K ⭐ 生产级大脑（146K 页 / 24K 人 / 5K 公司 / YC 总裁自用）

---

## 目录

- [1. v5 核心理念](#1-v5-核心理念)
- [2. v5 相对 v4 的核心变化](#2-v5-相对-v4-的核心变化)
- [3. 架构总览](#3-架构总览)
- [4. 基础设施搭建](#4-基础设施搭建)
- [5. 文档入库管线](#5-文档入库管线)
- [6. 知识处理管线](#6-知识处理管线)
- [7. 闭环：搜索→反馈→修复→进化](#7-闭环搜索反馈修复进化)
- [8. 状态检查与评估](#8-状态检查与评估)
- [9. OSB 的保留角色](#9-osb-的保留角色)
- [10. 与现有流程的融合](#10-与现有流程的融合)
- [11. 技术选型](#11-技术选型)
- [12. 实施路线图](#12-实施路线图)
- [13. 关键原则](#13-关键原则)

---

## 1. v5 核心理念

```
写文档（Obsidian Wiki/）
      ↓
gbrain import（自动索引）
      ↓
gbrain think（搜索→合成回答）
      ↓
发现问题（capture 纠正 / 修源文件）
      ↓
autopilot dream（自动聚合→修复→进化）
      ↑
      └────────── 此循环永不停歇 ─────────┘
```

**一切从文件开始，回到文件结束。** Wiki/ 是唯一数据源，gbrain 是检索和推理引擎，autopilot 是持续进化的动力。你只需要写笔记和偶尔 review。

---

## 2. v5 相对 v4 的核心变化

| 变化 | v4 | v5 |
|------|:--:|:--:|
| 核心引擎 | OSB sig→dream + SQLite mywiki.db | **gbrain**（Postgres + 混合搜索 + 图谱 + 合成） |
| 元信息存储 | SQLite mywiki.db（自定义表） | **gbrain PGLite**（内置 schema + 向量索引） |
| 知识图谱 | OSB entity 注册，手动维护 | **gbrain 自构建**，零 LLM 调用，自动 typed edges |
| 语义检索 | gbrain/LightRAG（待定） | **gbrain 混合搜索**（向量+BM25+图谱+RRF+reranker） |
| 合成回答 | 无 | **gbrain think**（带引用和缺口分析） |
| 反馈机制 | OSB brain_feedback → sig → dream | **capture 纠正 + 修源 + autopilot dream 自动聚合** |
| 修复闭环 | cron + OSB dream → fix pipeline | **autopilot 自动完成**（sync→extract→synthesize→consolidate→embed） |
| 知识评分 | 自定义置信度体系（0-10） | **gbrain takes**（correct/incorrect/partial/unresolvable） |
| 类型系统 | 无 | **schema packs**（person/company/concept/deal 等类型） |
| 评估框架 | 无 | gbrain eval（LongMemEval, NamedThingBench, contradiction） |
| 子任务 | Hermes delegate_task | **gbrain Minions**（崩溃安全的两阶段队列） |

---

## 3. 架构总览

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Obsidian Vault ~/mywiki/                          │
│                                                                          │
│  Wiki/（唯一数据源）                raw/（原始资料）                       │
│  ├─ privatelink/                    ├─ articles/                          │
│  │   ├─ unetfe-overview.md          ├─ papers/                            │
│  │   ├─ apisvr-architecture.md      └─ assets/                            │
│  │   └─ gateway-overview.md                                               │
│  ├─ ucloud/                                                                │
│  ├─ personal/                                                              │
│  └─ concepts/                                                              │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ gbrain sync（文件变更 → 增量导入）
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    gbrain Engine（PGLite / Postgres）                      │
│                                                                          │
│  混合检索层                              知识图谱层                        │
│  ├─ 向量索引 (HNSW pgvector)             ├─ 类型化边 (works_at,           │
│  ├─ BM25 关键词索引                        founded, invested_in…)          │
│  ├─ 图谱信号 (graph signals)             ├─ 实体解析 (人物/公司/概念)      │
│  └─ ZeroEntropy Reranker                 └─ 多跳图遍历 (graph-query)       │
│                                                                          │
│  合成回答层                              评估层                            │
│  ├─ gbrain think（答案+引用+缺口分析）    ├─ LongMemEval                   │
│  └─ find_trajectory（实体时间线）         ├─ NamedThingBench               │
│                                           └─ suspected-contradictions      │
│                                                                          │
│  调度层                                schema 层                          │
│  ├─ autopilot（24/7 循环）              ├─ schema packs (mywiki-base)     │
│  ├─ Minions 队列（崩溃安全子任务）       └─ auto-detect 类型匹配            │
│  ├─ dream cycle（12 个阶段）                                                 │
│  └─ cron 定时                                                              │
└──────────────────────────┬───────────────────────────────────────────────┘
                           │ MCP 协议（30+ 工具）
                           ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                        Hermes Agent                                      │
│                                                                          │
│  gbrain MCP（30+ 工具）            OSB（保留：行为偏好）                   │
│  ├─ gbrain_search/think            ├─ brain_feedback（agent 行为规则）    │
│  ├─ gbrain_capture/put_page        ├─ brain_apply_evidence                │
│  ├─ graph_query                    ├─ brain_pinned_context                │
│  ├─ find_trajectory                └─ pref-xxx（偏好系统）                 │
│  ├─ submit_job (Minions)                                                  │
│  └─ ...                                                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

### 分层

| 层 | 组件 | 职责 |
|----|------|------|
| L0 | **Obsidian Vault** `~/mywiki/` | 唯一数据源，Git 管理。Wiki/ 是纯 markdown |
| L1 | **gbrain import/sync** | 文件变更检测 → 增量导入 → 分块 → 向量嵌入 |
| L2 | **gbrain Postgres** | 存储所有元信息（向量索引、知识图谱、时间线、takes） |
| L3 | **gbrain 检索+合成** | 混合搜索 + think 合成回答 + graph-query 图遍历 |
| L4 | **gbrain dream/autopilot** | 自动维护（同步→提取→合成→合并→评分→报告） |
| L5 | **gbrain feedback** | capture 纠正 + 修源 + dream 聚合 → 闭环 |
| L6 | **OSB（保留子集）** | Agent 行为偏好（不涉及知识内容） |
| L7 | **Hermes mywiki skill** | 统一入口，协调 L1-L6 |

---

## 4. 基础设施搭建

### 4.1 当前状态（已就绪）

```bash
bun install -g github:garrytan/gbrain    # gbrain v0.42.52.0 ✅
gbrain init --pglite                      # 2 秒启动 PGLite ✅
gbrain sources add default ~/mywiki       # 源指向 mywiki  ✅
gbrain import --all                       # 91 页已导入 ✅
hermes mcp add gbrain -- gbrain serve     # MCP 注册 ✅

# 查看状态
gbrain doctor                             # 健康检查
gbrain status                             # 同步状态
gbrain sources list                       # 源列表
```

### 4.2 首次激活（需执行一次）

```bash
# 1. 同步最新内容
gbrain sync --all

# 2. 升级 schema 包（从 gbrain-base → gbrain-base-v2）
gbrain onboard --check --explain
gbrain schema use gbrain-base-v2

# 3. 运行首次完整 dream（构建知识图谱+时间线+评分）
gbrain dream --source default

# 4. 安装 autopilot（之后全自动）
gbrain autopilot --install --repo ~/mywiki
```

### 4.3 日常操作

```bash
# 写 wiki → 自动同步（autopilot 每 30 分钟检测变更）
# 啥也不用做，autopilot 负责 sync → extract → embed → dream

# 手动触发同步（想立即可见时）
gbrain sync --source default

# 手动跑 dream
gbrain dream --source default

# 查询
gbrain search "UNetFe 超时问题"
gbrain think "UNetFe 和 EIP 之间的网络拓扑"
```

---

## 5. 文档入库管线

### 5.1 代码型知识（Kanban → Wiki）

```
源码仓库（某服务子仓库）
    │
    ├─ Graphify AST 提取 → graph.json + GRAPH_REPORT.md
    │
    ├─ Kanban 多 Profile 对抗式编译
    │   ├─ Orchestrator：评估内容量级，分配任务
    │   ├─ Writer × 2-4：并行生成 Wiki 页面
    │   ├─ Adversary：对抗式审查
    │   ├─ Reviewer：迭代直到零意见
    │   └─ Polisher：排序润色
    │
    ├─ 产出写入 Wiki/privatelink/apisvr-*.md
    │
    ├─ gbrain 自动检测到新文件 → 增量导入
    │   （autopilot sync 每 30 分钟检测，或手动 gbrain sync）
    │
    └─ gbrain 自动：
        ├─ 分块 + 向量嵌入
        ├─ 提取 [[wikilink]] → 知识图谱边
        ├─ 创建时间线条目
        └─ synthesize_concepts 检测是否需合并已有知识
```

### 5.2 文档型知识（Kanban → Wiki）

```
原始文档（公众号/博客/内部文档/官方文档）
    │
    ├─ defuddle / Jina Reader → 纯文本
    │
    ├─ Kanban 编译（无 Graphify）
    │   ├─ Writer × 2-4：理解 + 提取知识 + 逻辑纠错 + 交叉校验
    │   ├─ Adversary 审查
    │   └─ Reviewer 迭代
    │
    ├─ 产出写入 Wiki/ 对应目录
    │   原始文档保留在 raw/articles/
    │
    └─ gbrain 同上自动导入
```

### 5.3 个人笔记

```
手动在 Obsidian 中写 Wiki/personal/x.md
    │
    └─ autopilot 检测变更 → 自动导入 → 立即可搜索
```

### 5.4 快速 capture（inbox 式）

```
随手想法 / 会议记录 / 纠正
    │
    ├─ gbrain capture "想法内容"
    │   → 写入 inbox/YYYY-MM-DD-<hash>.md
    │   → autopilot dream 时自动分拣到合适的 Wiki/ 目录
    │
    └─ 或直接在 Obsidian 中创建 Wiki/inbox/ 文件
```

---

## 6. 知识处理管线

### 6.1 gbrain dream 循环（12 阶段）

每次 dream 跑一个完整的 12 阶段循环。这是 gbrain 的核心进化引擎：

```
Phase 1:  lint                   检查基础知识健康
Phase 2:  backlinks              提取 [[wikilink]] → 知识图谱 typed edges
Phase 3:  sync                   从文件系统导入新/变更内容
Phase 4:  synthesize             跨页面的初步合成
Phase 5:  extract                提取实体、时间线
Phase 6:  extract_facts          提取正式的事实声明
Phase 7:  extract_atoms          提取知识原子
Phase 8:  resolve_symbol_edges   解析符号引用
Phase 9:  embed                  向量嵌入（新/变更页面）
Phase 10: synthesize_concepts    全局概念聚合（类 OSB dream 的 sig 合并）
Phase 11: consolidate            事实聚类合并 + takes 生成
Phase 12: propose_takes + grade  提议新事实 + 评分已有事实
```

autopilot 模式下这些阶段自动按依赖顺序执行。

### 6.2 知识图谱构建（全自动）

```
你写：UNetFe 是一个 [[EIP]] 网关服务，[[Alice]] 是该团队负责人
    │
    └─ gbrain backlinks 阶段自动提取：
        ├─ entity: "UNetFe" ← type: concept
        ├─ entity: "EIP"   ← type: concept
        ├─ entity: "Alice" ← type: person
        ├─ edge: UNetFe -[related_to]-> EIP
        ├─ edge: UNetFe -[owned_by]-> Alice
        └─ edge: Alice -[works_at]-> 未定义（有新页面则自动创建）
```

```bash
# 查询图谱
gbrain graph-query "谁和 UNetFe 有关？"
gbrain think "Alice 参与过哪些项目？"
```

### 6.3 实体时间线（自动）

每次文档更新自动记录：

```
gbrain find_trajectory "UNetFe"
# → 返回：
#   2026-06-01: 创建 UNetFe 概览文档
#   2026-06-15: 更新 Gateway 层架构
#   2026-06-20: 新增超时处理策略
```

---

## 7. 闭环：搜索→反馈→修复→进化

这是 v5 的核心——一个完整的自愈循环：

```
        ① 你搜索/think
              │
              ▼
        ② gbrain 返回结果（含引用和知识缺口标注）
              │
         ┌────┴────┐
         │         │
    结果正确    结果有问题
         │         │
         │    ┌────┴────┐
         │    │         │
         │  ③a 修源    ③b capture 纠正
         │  编辑 Wiki/  gbrain capture
         │  中的 .md    "纠正：..."
         │         │
         │         ▼
         │  ④ gbrain sync（增量导入变更）
         │         │
         └────┬────┘
              │
        ⑤ autopilot dream 自动聚合：
           ├─ detect contradictions
           ├─ consolidate 事实
           ├─ synthesize_concepts
           ├─ propose_takes + grade
           └─ embed → 下次搜索即生效
              │
        ⑥ gbrain doctor 报告健康状态
              │
              └──→ 回到①
```

### 7.1 反馈的具体操作

#### 场景 A：think 回答有误

```bash
# 你的操作（任选一种）：
# 选项 1：修源文件（推荐）
vim ~/mywiki/Wiki/privatelink/unetfe-overview.md  # 改正确
gbrain sync --source default                       # 同步

# 选项 2：capture 纠正（快速）
gbrain capture "纠正：UNetFe 不直连 EIP，中间经过 Gateway 层" \
  --type correction --slug corrections/unetfe-gateway

# 两个选项都会触发 autopilot dream 自动聚合处理
```

#### 场景 B：搜索结果不理想

```bash
# 调整搜索模式
gbrain search "UNetFe" --mode tokenmax    # 召回优先
gbrain search "UNetFe" --mode balanced    # 平衡

# 诊断为什么没搜到
gbrain search diagnose "UNetFe" --target Wiki/privatelink/unetfe-overview
```

#### 场景 C：发现知识矛盾

```bash
# gbrain 自动检测（autopilot 内建的）
gbrain eval suspected-contradictions --top-k 5

# 或手动标记
gbrain capture "矛盾：页面 A 说 UNetFe 直连 EIP，
  页面 B 说中间有 Gateway。请核实。" --type flag
```

### 7.2 什么是「修复闭环」

```
碎片化反馈（修源、capture、矛盾标记）
    │
    ▼
autopilot dream cycle 自动处理：
    │
    ├─ sync: 导入新内容
    ├─ extract: 提取实体/时间线
    ├─ backlinks: 更新知识图谱
    ├─ consolidate: 聚类相关事实
    ├─ synthesize_concepts: 合并概念
    ├─ propose_takes: 提议新事实声明
    └─ embed: 嵌入 → 搜索立即可见
    │
    ▼
你不需要做任何事情——下次 gbrain think 时结果已自动更新。
```

**gbrain 与 OSB 的反馈模型对比：**

```
OSB 模式：                    gbrain 模式：
brain_feedback("不对")        capture 纠正 / 修源文件
    ↓                              ↓
sig-xxx 文件堆积               inbox/ 页面堆积
    ↓                              ↓
dream 合并 sig → pref         dream cycle → consolidate + synthesize
    ↓                              ↓
需要配置 cron 触发 fix           autopilot 自动处理
    ↓                              ↓
手动或 cron 执行修复             dream cycle 内建修复（backlinks/
                                  extract/synthesize/consolidate）
```

### 7.3 知识缺口检测

gbrain 的 `think` 命令内建知识缺口分析——它返回的答案末尾自动标注：

```
"UNetFe 的架构包含三层..."
...
⚠️ 注意：关于 Gateway 的熔断机制，大脑中没有找到相关信息。
   建议补充 Wiki/privatelink/gateway-circuit-breaker.md。
```

这是 gbrain 原生的能力（`think` 的 gap analysis），不需要额外配置。

---

## 8. 状态检查与评估

### 8.1 健康检查

```bash
# 一键健康检查
gbrain doctor

# 关注指标：
# - sync_freshness: 同步是否及时（建议 < 1h）
# - embed_coverage: 嵌入覆盖率（100% = 完美）
# - brain_score: 综合分数（目标 90+/100）
# - graph_coverage: 实体链接覆盖率
# - contradictions: 矛盾声明数

# 大脑深度评估
gbrain status
# 显示：页面数、同步状态、上次 dream 时间、autopilot 状态
```

### 8.2 搜索质量评估

```bash
# 跑基准测试
gbrain eval longmemeval              # LongMemEval 基准
gbrain eval retrieval-quality        # NamedThingBench

# 比较搜索模式
gbrain search modes --explain

# 诊断特定页面是否可检索
gbrain search diagnose "UNetFe" --target Wiki/privatelink/unetfe-overview
```

### 8.3 矛盾检测

```bash
# 自动发现矛盾声明
gbrain eval suspected-contradictions --top-k 10

# 每次 autopilot dream 后自动检查
# 有矛盾时 doctor 会有告警
```

---

## 9. OSB 的保留角色

OSB 不再负责**知识内容**（那已是 gbrain 的职责），但保留**Agent 行为偏好**：

| 保留 | OSB 功能 | 用途举例 |
|------|----------|---------|
| ✅ | brain_feedback | "下次这类问题先用 agent-search"、"这类问题不要百度" |
| ✅ | brain_apply_evidence | 记录某个偏好是否被遵守 |
| ✅ | brain_pinned_context | 当前 session 的临时工作状态 |
| ✅ | brain_search (pref 搜索) | 搜索 agent 规则（不是知识） |
| ❌ | sqlite mywiki.db | 已由 gbrain PGLite 替代 |
| ❌ | sig→dream→fix 管线 | 已由 gbrain dream cycle 替代 |
| ❌ | brain_entity | 已由 gbrain 知识图谱替代 |
| ❌ | confidence 体系 | 已由 gbrain takes + dream consolidate 替代 |

---

## 10. 与现有流程的融合

### 10.1 Kanban 编译产出 → gbrain 自动导入

现有的 Kanban 编译管线不变。唯一变化是产出后不需要写 mywiki.db：

```
Kanban 编译 → Wiki/privatelink/apisvr-*.md
                       │
                       ├─ [旧] 写入 mywiki.db + 状态标记
                       ├─ [新] gbrain sync 自动检测新文件
                       ├─ [新] gbrain 自动嵌入 + 建图谱
                       └─ [新] 立即可查询（人类 review 前就是 pending-review）
```

### 10.2 现有 Wiki 页面迁移到 gbrain

```
# 一步到位（已经完成）：
gbrain import ~/mywiki/Wiki/
# → 91 页已导入，PGLite 数据库已构建

# 后续新增：
# 在 Obsidian 写完新页面 → autopilot sync 自动检测 → 导入
```

### 10.3 Hermes session 中使用

```
# 在 Hermes 中直接使用 gbrain 能力
# 不需要退出 Hermes，gbrain MCP 工具自动可用

gbrain think "UNetFe 和 EIP 的关系"       # 合成回答
gbrain search "Gateway 架构"              # 检索
gbrain capture "记一下这个想法"            # 快速录入
```

---

## 11. 技术选型

| 组件 | v4 方案 | v5 方案 | 说明 |
|------|---------|---------|------|
| Vault | Obsidian | Obsidian | 不变 |
| 数据库 | SQLite mywiki.db | **gbrain PGLite** | v4 的自定义 schema 全部由 gbrain 内置替代 |
| 搜索 | 手动 FTS / 语义检索待定 | **gbrain 混合搜索** | 向量+BM25+图谱+RRF+reranker，P@5 49.1% |
| 知识图谱 | OSB entity（手动） | **gbrain 自构建** | 自动 typed edges，零 LLM 调用 |
| 合成回答 | 无 | **gbrain think** | 带引用+缺口分析 |
| Agent 记忆 | OSB sig→dream | OSB（行为偏好子集） | 两套分工：知识走 gbrain，行为走 OSB |
| 反馈模型 | brain_feedback | **修源 + capture** | 更自然的知识修复方式 |
| 大脑维护 | Hermes cron | **gbrain autopilot** | 24/7 自动，崩溃安全 |
| 子任务 | Hermes delegate_task | **gbrain Minions** | 崩溃安全队列 |
| 评估 | 无 | **gbrain eval** | LongMemEval, NamedThingBench |
| Schema | 无 | **gbrain schema packs** | 自动类型检测 |
| 检索入口 | Hermes Session | **gbrain MCP** (30+ 工具) | 给任何客户端用 |

---

## 12. 实施路线图

### Phase 0（已完成）

```
✅ bun + gbrain 安装
✅ gbrain init --pglite（2 秒 PGLite）
✅ gbrain import ~/mywiki/Wiki/（91 页）
✅ hermes mcp add gbrain（MCP 注册，Hermes 中可用）
```

### Phase 1（立即执行，30 分钟）

```
① gbrain sync --all                    # 同步最新内容
② gbrain schema use gbrain-base-v2     # 升级 schema 包
③ gbrain dream --source default        # 首次 dream（建图谱+时间线+takes）
④ gbrain doctor                        # 验证健康
```

### Phase 2（本周）

```
⑤ gbrain autopilot --install --repo ~/mywiki
   # 之后大脑自动维护，不再需要手动操作

⑥ 更新 mywiki skill
   # 整合 gbrain 操作指南到 Hermes 技能中
   # 确保 agent 知道用 gbrain 而非 OSB 搜知识

⑦ gbrain eval run-all 或 gbrain eval longmemeval
   # 建立评估基线
```

### Phase 3（持续）

```
⑧ 日常使用 gbrain think/search 替代手动查笔记
⑨ 通过修源或 capture 反馈问题，观察 autopilot 自动修复
⑩ 定期 gbrain doctor 检查大脑健康
⑪ 必要时运行 gbrain eval suspected-contradictions
```

### 激活命令对照

```
之前要做的（v4）                      现在要做的（v5）
────────────────────────────────────────────────
hermes cron create ...               gbrain autopilot --install
（配置置信度衰减 cron）              （全自动，不用配置）

手动写 brain_feedback                gbrain capture "纠正" 或修源
（每次反馈一条 sig）                 （更自然的操作）

手动检查 wiki_gaps                   gbrain think 自动带缺口分析
（查 mywiki.db 的 SQL）              （内建功能，零配置）

手动写 OSB entity                    gbrain 自动提取实体+建图谱
（o2b brain entity add ...）         （写 [[wikilink]] 就够了）
```

---

## 13. 关键原则

1. **Wiki/ 是唯一数据源。** 所有知识从 `~/mywiki/Wiki/` 的 markdown 文件来。gbrain 只是索引和推理引擎，不取代源文件。

2. **gbrain 管理元信息，不管理内容。** Wiki/ 的 .md 文件在 Obsidian/git 中永远可读。gbrain 的 PGLite 是只读缓存，被删除可以重建。

3. **修源 = 修结果。** 发现错误，编辑对应的 .md 文件，gbrain sync 自动覆盖旧数据。不需要额外的投票/评分操作。

4. **反馈碎片化不可怕。** 随手 capture 纠正，随手修源文件。autopilot dream 会自动聚合、去重、合并。不需要你组织反馈。

5. **知识缺口不是 bug。** gbrain think 的 gap analysis 是产品特性。没覆盖到的知识自动出现在答案末尾的建议中。

6. **OSB 管行为，gbrain 管知识。** 不要混用。agent 行为规则走 brain_feedback，知识内容走 gbrain。

7. **autopilot 是一切自动化的基础。** 不装 autopilot，gbrain 就只是一个更快的搜索引擎。装了 autopilot，它才是自进化的知识大脑。

---

## 附录：常用命令速查

```bash
# === 日常操作 ===
gbrain sync --all                       # 同步最新文件
gbrain search "关键词"                  # 搜索
gbrain think "问题"                     # 合成回答
gbrain capture "想法"                   # 快速录入
gbrain graph-query "关系查询"            # 知识图谱查询
gbrain find_trajectory "实体名"          # 实体时间线

# === 维护 ===
gbrain doctor                           # 健康检查
gbrain status                           # 状态概览
gbrain dream                            # 手动 dream
gbrain autopilot --install              # 安装 autopilot

# === 评估 ===
gbrain eval longmemeval dataset         # 跑基准
gbrain eval suspected-contradictions    # 矛盾检测
gbrain search diagnose "q" --target p   # 诊断页面可检索性
gbrain takes list                       # 查看待评事实

# === 高级 ===
gbrain schema use gbrain-base-v2        # 升级 schema
gbrain onboard --check --explain        # 检查可升级项
gbrain jobs submit --type agent ...     # 提交子任务
```

---

> 参考：`design-v4.md`（v4）、`design-v3.md`（v3）、`design-v2.md`（v2）、`design.md`（v1）
> gbrain: https://github.com/garrytan/gbrain（23.9K ⭐, MIT）
> 本文档 v1 | 2026-06-24

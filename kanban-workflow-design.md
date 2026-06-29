# Hermes Kanban 流程设计: L1 + L2 编译管线

> 适用项目: mywiki — 从 Go 源码 AST 自动生成知识文档
> 角色分布: `orchestrator`(本session) → `analyst` + `writer` + `synthesizer` + `reviewer`

---

## 总体架构

```
┌──────────────────────────────────────────────────────┐
│  L1 编译: 单服务源码 → 文档                            │
│  ┌────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  Analyst   │───▶│ Writer × N  │───▶│ Reviewer │  │
│  │ (独立profile)│   │ (接口+模块)  │    │ (审查)   │  │
│  └────────────┘    └──────────────┘    └──────────┘  │
├──────────────────────────────────────────────────────┤
│  L2 编译: 多服务综合 → 业务文档                        │
│  ┌────────────┐    ┌──────────────┐    ┌──────────┐  │
│  │  Analyst   │───▶│ Synthesizer  │───▶│ Reviewer │  │
│  │ (独立profile)│   │ (跨服务合成)  │    │ (终验)   │  │
│  └────────────┘    └──────────────┘    └──────────┘  │
└──────────────────────────────────────────────────────┘
```

**四大 profile**: `analyst`、`writer`、`synthesizer`、`reviewer` — 各司其职，无重叠。

---

## 编译管线全景

```
L0 ── sync_code.py ───────── AST 提取（bin/ 脚本，非 kanban）
         │
L1 ── analyst → writer (×N) → reviewer ── 单服务文档
         │                                    (接口页+模块页+流程页)
L2 ── analyst → synthesizer → reviewer ── 跨服务业务合成
         │                                    (总览+架构+数据流+索引)
L3 ── analyst → reviewer (gbrain) ──── 语义入库
                                              (概念关联+跨服务检索)
```

---

## 四大 Profile 职责

### 🔍 `analyst`
> 模型: `Qwen/Qwen3-Max`（最强推理，理解代码结构）
> SOUL.md 关键原则: 「只分析不写文档，创建子卡让 writer/synthesizer 去写」
> 工作目录: `~/.../mywiki/raw/`

| 职责 | L1 场景 | L2 场景 |
|------|---------|---------|
| 读 graph.json | 解析 AST 节点结构 | — |
| 枚举 | 列出所有接口 (actions) 和模块 (modules) | 列出业务组下的所有服务 |
| 业务理解 | 读入口源码，理解业务语义 | 确认各服务 L1 已通过 review |
| 创建子卡 | 创建 writer 卡（interface/module/architecture） | 创建 synthesizer 卡 |
| 分组/关联 | actions 按功能分组，modules 关联到功能 | — |
| 完成 | `kanban_complete(summary="...N个接口, M个模块")` | `kanban_complete(summary="...")` |

**不代劳**: 分析完就退出，不碰产出文件，不写文档正文。

---

### ✍️ `writer`
> 模型: `deepseek-ai/DeepSeek-V3.2`（高翻译质量文档模型）
> 工作技能: `interface-sk`、`module-sk`、`flow-sk`、`architecture-sk`、`fix-sk`
> 工作目录: `~/.../mywiki/raw/`
> 核心约束: 每个声明标注源码行号，不脑补

| 技能 | 产出物 | 文件后缀 | 说明 |
|------|--------|---------|------|
| `interface-sk` | `interfaces/<action>.md.bak` | `.bak` | 读源码 + 模板 → 接口详情页 |
| `module-sk` | `modules/<module>.md.bak` | `.bak` | 读源码 + 模板 → 模块详解页 |
| `flow-sk` | `flows/<flow>.md.bak` | `.bak` | 跨接口组合 → 业务流程文档 |
| `architecture-sk` | `overview.md.bak` + `architecture.md.bak` + `interfaces-index.md.bak` | `.bak` | 顶层合成（依赖全部 interface/module） |
| `fix-sk` | 修改已有 `.bak` 文件 | `.bak` | 按 reviewer 意见逐条修复 |

**工作流**: 写完 → `kanban_create(reviewer)` → `kanban_block("waiting: review")`

---

### 🔗 `synthesizer`
> 模型: `deepseek-ai/DeepSeek-V3.2`
> 工作技能: `synthesis-sk`
> 工作目录: `~/.../mywiki/raw/`

| 职责 | 说明 |
|------|------|
| 读 L1 正式文档 | 读取多个服务已通过 review 的 `.md`（interfaces/ + modules/ + flows/) |
| 写 overview | `Wiki/<group>/<group>-overview.md` — 业务全景、服务定位 |
| 写 architecture | `Wiki/<group>/<group>-architecture.md` — 跨服务架构、分层调用链 |
| 写 dataflow | `Wiki/<group>/<group>-dataflow.md` — 核心请求的跨服务时序 |
| 写 index | `Wiki/<group>/<group>-index.md` — 服务目录 + 关键词索引 |
| 输出直写 `.md` | 不走 bak 流程，产出即为正式文件 |
| 交叉引用 | 每个声明标注来源 L2 页面（`[[Wiki/<group>/<service>/...]]`） |

**约束**: 不编造跨服务调用关系，环断则非法。

---

### ✅ `reviewer`
> 模型: `deepseek-ai/DeepSeek-V3.2`
> 工作技能: `review-sk`（入口）、`review-accuracy-sk`、`review-completeness-sk`、`review-crossref-sk`、`review-format-sk`、`verifier-role`

| 技能 | 职责 |
|------|------|
| `review-sk`（入口） | 读父卡 `.bak` → 对照源码审查 → 通过则 `cp .bak .md` + `kanban_unblock()` |
| `review-accuracy-sk` | 事实准确性 — 源码有的事实才写，无源码的声明标记怀疑 |
| `review-completeness-sk` | 完整性 — 不缺页、不缺字段、不缺行号引用 |
| `review-crossref-sk` | 交叉引用 — `[[wikilink]]` 是否指向真实存在的页面 |
| `review-format-sk` | 格式规范 — `%%metadata%%` 完整、YAML frontmatter 正确、模板一致 |
| `verifier-role` | L2 终验 — 检查 4 页完整性 + gbrain 导入验证 |

#### Reviewer 分档标准

不同文档类型适用不同的审查标准 — reviewer 加载卡时根据 `doc_type` 参数执行对应审查：

| 文档类型 | `doc_type` | 审查标准 |
|----------|-----------|---------|
| 接口页 | `interface` | **accuracy**（原文对照）+ **format**（metadata 完整）+ **crossref**（行号可追溯） |
| 模块页 | `module` | **accuracy** + **completeness**（覆盖全部关键 struct/func）+ **format** |
| 流程页 | `flow` | **crossref**（引用接口是否存在）+ **accuracy**（步骤是否合理） |
| L2 总览/架构 | `synthesis` | **completeness**（4 页不缺）+ **crossref**（跨服务引用正确）+ gbrain 验证 |
| — | 未指定 | 全量审查（accuracy + completeness + crossref + format） |

每个审查子 skill 结束时调用 `kanban_complete()` 或创建 fix 卡。入口 `review-sk` 汇总判断是否整体通过。

---

## Profile 配置总览

| 属性 | `analyst` | `writer` | `synthesizer` | `reviewer` |
|------|-----------|----------|--------------|-----------|
| 模型 | Qwen/Qwen3-Max | DeepSeek-V3.2 | DeepSeek-V3.2 | DeepSeek-V3.2 |
| provider | custom | custom | custom | custom |
| base_url | api.modelverse.cn/v1 | 同上 | 同上 | 同上 |
| max_turns | 200 | 150 | 150 | 150 |
| kanban.in_progress | 3 | 3 | 3 | 3 |
| cwd | `~/.../mywiki/raw/` | `~/.../mywiki/raw/` | `~/.../mywiki/raw/` | `~/.../mywiki/raw/` |

---

## L1 编译 — 单服务文档管线

### 触发方式

```bash
# 完整流程 (推荐)
./bin/kanban-l1.sh <service-name>

# 示例
./bin/kanban-l1.sh apisvr
./bin/kanban-l1.sh unetfe

# 预览(不创建卡片)
./bin/kanban-l1.sh apisvr --dry-run

# 只写接口页(跳过模块)
./bin/kanban-l1.sh apisvr --interfaces-only
```

### 流程步骤

```
T1 [analyst profile]       ─ 读 graph.json，枚举接口和模块
    │                           analyst 独立成卡，kanban 调度
    │
    ├── T2..Tn [writer-interface-sk]  并行写接口详情页
    │    └── 每个 Action 一张卡，goal_mode: 6 轮
    │    └── 依赖 T1
    │
    ├── Tn+1..Tm [writer-module-sk]   并行写模块详解页
    │    └── 依赖前 3 张 interface 卡（信号: 等 interface 都做完）
    │    └── goal_mode: 5 轮
    │
    ├── T_top [writer-architecture-sk] 写顶层文档
    │    └── overview + architecture + interfaces 索引
    │    └── 依赖 全部 interface + module 卡
    │    └── goal_mode: 8 轮
    │
    └── T_rev [reviewer-review-sk]    审查
         └── 依赖 T_top
         └── 通过 → kanban_complete()
         └── 发现问题 → kanban_block() + kanban_comment()
```

### 角色-Profile 映射

| 角色 | Profile | Skill | 模型 | 职责 |
|------|---------|-------|------|------|
| analyst | `analyst` | `analyst-sk` | `Qwen/Qwen3-Max` | 枚举接口和模块 |
| interface writer | `writer` | `interface-sk` | `DeepSeek-V3.2` | 写 Action 接口详情页 |
| module writer | `writer` | `module-sk` | `DeepSeek-V3.2` | 写模块详解页 |
| architecture writer | `writer` | `architecture-sk` | `DeepSeek-V3.2` | 写 overview/architecture/interfaces 索引 |
| reviewer | `reviewer` | `review-sk` | `DeepSeek-V3.2` | 审查全部文档（按 doc_type 分标准） |

### 卡依赖关系

```
T_analyst ────┐
    │          │
    ├── T_interface_1 ─┐
    ├── T_interface_2 ─┤
    ├── T_interface_3 ─┤      ┌────────────────┐
    │   ...            ├─────▶│ T_top          │────▶ T_rev
    ├── T_module_1     ├─────▶│ (architecture) │
    ├── T_module_2     ─┤     └────────────────┘
    ├── T_module_3     ─┤
    │   ...            ─┘
    └── [T_arch] ───────┘  (全部接口+模块 done 后触发)
```

注意: `module` 卡依赖前 3 张 `interface` 卡（等所有 interface 做完才触发）；`T_top` 依赖全部 interface + module 卡；`T_rev` 依赖 `T_top`。

### 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| goal_mode | `True` | 每张卡允许多轮迭代 |
| goal_max_turns | interface=6, module=5, architecture=8, review=8 | 防止无限循环 |
| timeout | 180s | 调用超时 |

---

## L2 编译 — 多服务业务文档管线

### 触发方式

```bash
# 完整流程
./bin/kanban-l2.sh <business-group>

# 示例
./bin/kanban-l2.sh privatelink
```

### 流程步骤

```
T0 [analyst profile]          ─ 枚举服务列表，确认 L1 就绪
    │                               analyst 独立成卡
    │
    ├── T_syn [synthesizer + synthesis-sk]  4 页 L3 合成
    │    └── overview + architecture + dataflow + index
    │    └── goal_mode: 10 轮
    │
    └── T_ver [reviewer + verifier-role]   终验
         └── 检查 L3 4 页完整性
         └── gbrain import + search 验证
         └── 依赖 T_syn
```

### 角色-Profile 映射

| 角色 | Profile | Skill | 模型 | 职责 |
|------|---------|-------|------|------|
| analyst | `analyst` | `analyst-sk` | `Qwen/Qwen3-Max` | 枚举服务、确认 L1 就绪 |
| synthesizer | `synthesizer` | `synthesis-sk` | `DeepSeek-V3.2` | 跨服务合成 4 页 L3 |
| verifier | `reviewer` | `verifier-role` | `DeepSeek-V3.2` | 终验 + gbrain 导入 |

### L3 页面清单

| 页面 | path | 说明 |
|------|------|------|
| overview | `Wiki/<group>/<group>-overview.md` | 业务全景、服务定位 |
| architecture | `Wiki/<group>/<group>-architecture.md` | 跨服务架构、调用链 |
| dataflow | `Wiki/<group>/<group>-dataflow.md` | 核心请求的跨服务时序 |
| index | `Wiki/<group>/<group>-index.md` | 服务目录、关键词索引 |

---

## 生命周期管理

### 正常流程

```text
todo ──(parent done)──▶ ready ──(dispatcher)──▶ in_progress ──▶ done
                                                      │
                                                      ▼
                                                   block (发现问题)
                                                      │
                                                   unblock ──▶ in_progress ──▶ done
```

### 卡状态说明

| 状态 | 触发条件 | 说明 |
|------|----------|------|
| `todo` | 刚创建，有未完成 parent | 等待上游 |
| `ready` | 无 parent 或所有 parent done | dispatcher 60s 轮询 |
| `in_progress` | dispatcher 分配 | worker 正在工作 |
| `done` | 调用 `kanban_complete()` | 完成 |
| `block` | 调用 `kanban_block()` | reviewer 发现问题，需要人工处理 |

### 恢复流程

```bash
# 查看卡状态
hermes kanban list

# 跟踪特定卡
hermes kanban tail <task_id>

# 查看详情
hermes kanban show <task_id>

# 如果 worker 卡住 → reclaim
hermes kanban reclaim <task_id>

# 如果 profile 不对 → reassign
hermes kanban reassign <task_id> writer --reclaim

# 如需重新触发 dispatch
hermes kanban dispatch
```

---

## Profile 编辑工作流

Profile 文件应当纳入版本管理（mywiki repo），不在 `~/.hermes/profiles/` 下直接编辑。

### 标准工作流

```bash
# 1. 在项目仓库中编辑 profile 文件
# 目录结构:
#   profiles/
#     analyst/
#       config.yaml
#       SOUL.md
#       skills/analyst-sk/SKILL.md
#     writer/
#       config.yaml
#       SOUL.md
#       skills/interface-sk/SKILL.md
#       skills/module-sk/SKILL.md
#       ...
#     synthesizer/
#       ...
#     reviewer/
#       ...

# 2. 将编辑后的目录安装/更新到系统 profile
hermes profile install ~/Documents/Code/work/mywiki/profiles/analyst --name analyst --force

# 3. 查看 distribution 源确认
hermes profile info analyst
# → 显示 Source: file:///Users/user/Documents/Code/work/mywiki/profiles/analyst

# 4. 后续只需重复编辑 → 更新
cd ~/Documents/Code/work/mywiki
# 编辑 profiles/analyst/SOUL.md
# 编辑 profiles/analyst/skills/analyst-sk/SKILL.md
hermes profile update analyst --yes
```

### 命令参考

| 命令 | 场景 |
|------|------|
| `hermes profile install <dir> --name <name> --force` | **首次安装**新 profile 或**整体覆盖**已存在 profile |
| `hermes profile update <name> -y` | **增量更新** — 从已记录的 source 目录重新拉取 |
| `hermes profile info <name>` | 查看 profile 信息（版本、source、需求） |
| `hermes profile list` | 列出所有已安装 profile |
| `hermes profile show <name>` | 查看 profile 详情 |

### 注意事项

- `hermes profile install --force` 会保留用户数据（memories、sessions、auth），只覆盖 `SOUL.md`、`skills/`、`cron/`、`mcp.json`
- `hermes profile update` 同理，但额外默认保留 `config.yaml`（除非传 `--force-config`）
- `distribution.yaml` 是 profile 分发的清单文件，可选的。如果没有，直接 `install` 也能工作

---

## 需要创建的组件

### 1. `verifier-role` skill (reviewer profile 下)

作用: 给 reviewer profile 加载 L2 终验角色

```bash
mkdir -p ~/.hermes/profiles/reviewer/skills/verifier-role/
cat > ~/.hermes/profiles/reviewer/skills/verifier-role/SKILL.md << 'VERIFIER_EOF'
---
name: verifier-role
description: L3 终验 — 检查完整性 + gbrain 导入验证
---

# Verifier 角色

你收到终验 L3 跨服务文档的任务。

## 工作流程

1. **读 card body** — 了解要验证哪个 group
2. **检查 4 页存在** — `overview.md`, `architecture.md`, `dataflow.md`, `index.md`
3. **检查 metadata** — 每页有 `%%metadata%%` 且 type/agent 完整
4. **gbrain 导入** — 运行 `gbrain import ~/Documents/Code/work/mywiki/Wiki/<group>/ --fresh`
5. **gbrain 搜索验证** — 搜索新建内容确认可命中
6. **页面可读** — 尝试打开每个页面
7. **决策**
   - 全部通过 → `kanban_complete(summary="L3 终验通过")`
   - 发现问题 → `kanban_comment()` + `kanban_block(reason="...")`
VERIFIER_EOF
```

---

## 执行路径图

### L1: 单服务

```bash
# 1. 准备: 提取 AST
python3 bin/sync_code.py --repo privatelink/<service>

# 2. 启动管线
./bin/kanban-l1.sh <service>

# 3. 监控
hermes kanban list | grep "<service>"
```

### L2: 多服务

```bash
# 前提: 所有服务的 L1 管线已完成且通过 review
# 启动:
./bin/kanban-l2.sh <business-group>

# 监控:
hermes kanban list | grep "synthesize\|verify"
```

---

## 监控清单

日常运维所需的命令:

```bash
# 查看所有活跃卡
hermes kanban list

# 查看 dispatcher 状态
hermes gateway status

# 查看网关日志
tail -f ~/.hermes/logs/gateway.log

# 查看 worker 日志 (writer profile)
tail -f ~/.hermes/logs/gateway.error.log
```

---

## 常见问题（Pitfalls）

1. **Dispatacher 未运行** — gateway 必须 running，否则卡永远在 `ready`
   - 修复: `hermes gateway start`

2. **Profile 不存在** — 引用不存在的 profile 名，卡永远在 `ready`
   - 可用: `analyst`, `writer`, `synthesizer`, `reviewer`
   - 不要使用 `default` 或 `dev` 跑文档管线

3. **Skill 缺失** — worker 加载了 profile 但没有技能，不知道做什么
   - `analyst` 下必须有: `analyst-sk`
   - `writer` 下必须有: `interface-sk`, `module-sk`, `flow-sk`, `architecture-sk`, `fix-sk`
   - `synthesizer` 下必须有: `synthesis-sk`
   - `reviewer` 下必须有: `review-sk`, `review-accuracy-sk`, `review-completeness-sk`, `review-crossref-sk`, `review-format-sk`, `verifier-role`

4. **Card body 遗漏路径信息** — writer/synthesizer 需要绝对路径才能工作
   - body 必须包含: `graph.json` 路径、`output` 路径、`source` 路径、`service` 名

5. **--goal 模式轮次耗尽** — 默认 20 轮，接口卡设 6 轮
   - 耗尽后卡自动 block，人工 review 后 `/unblock`

6. **Tenant 隔离** — 必须传 `tenant` 参数，否则多 tenant 共用 kanban 会混乱
   - L1/L2 脚本已继承 `HERMES_TENANT`

7. **Profile 编辑未同步** — 改了 profiles/ 下的文件但没跑 `install` 或 `update`
   - 修改后必须执行 `hermes profile install --force` 或 `hermes profile update` 才能生效

8. **Reviewer 标准混淆** — reviewer 卡没有传 `doc_type`，使用默认全量审查
   - 如果只想要单项审查（如只检查格式），在卡 body 中传: `doc_type=interface` 或 `review_mode=format-only`

---

## 附录: Graph.json 字段说明

| 字段 | 说明 |
|------|------|
| `nodes` | Go 源码 AST 节点数组 |
| `nodes[].source_file` | 源文件相对路径 |
| `nodes[].label` | 节点标签（结构体名/函数名） |
| `nodes[].community` | Louvain 社区编号 |
| `links` | 调用/引用关系 |

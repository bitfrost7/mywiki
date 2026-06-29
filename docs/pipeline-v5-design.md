# mywiki Pipeline v5 Design

> 当前状态：workspace_kind=dir 验证通过，管线待迭代
> 最后更新：2026-06-29

## Architecture Overview

```
kanban-l1.sh
    ↓  创建 analyst 卡
[analyst profile] — 分析代码 → init discuss → add-doc
    ↓  (用 CLI 或 kanban_create 创建子卡)
[writer profile]  — 读源码 → 写 *.md → add-doc → 创建 review 卡
    ↓
[reviewer profile] — 审查 *.md → bin/discuss add 提讨论 / 通过
    ↓  如果有 .bak：cp .bak→.md, rm .bak
[fix writer profile] — 读 discuss_ids → cp *.md *.md.bak → 修复 → discuss fix → 创建 re-review 卡
    ↓
[reviewer (re-review)] — 审查 *.md.bak → 通过/打回
```

## Profile 结构

```
profiles/
├── analyst/       SOUL.md + skills/analyst-sk/SKILL.md
├── writer/        SOUL.md + skills/interface-sk + module-sk + flow-sk + fix-sk
├── reviewer/      SOUL.md + skills/review-sk (+ completeness/format/crossref/accuracy)
├── synthesizer/   SOUL.md + skills/synthesis-sk
```

## bin/discuss — 讨论管理系统

### 命令

```bash
bin/discuss init <数据路径> <服务名>
bin/discuss add-doc <数据路径> <文档路径>
bin/discuss add <数据路径> <文档路径> <描述> [--source SRC] [--hint HINT]
bin/discuss fix <数据路径> <讨论ID>
bin/discuss resolve <数据路径> <讨论ID>
bin/discuss list <数据路径>
bin/discuss verify <数据路径>
```

### 讨论生命周期

```
open → (writer: fix) → fixed → (reviewer: resolve) → resolved
```

### 权限（$HERMES_PROFILE 控制）

| 命令 | writer | reviewer | analyst |
|------|--------|----------|---------|
| init | | | ✅ |
| add-doc | ✅ | | ✅ |
| add | | ✅ | |
| fix | ✅ | | |
| resolve | | ✅ | |
| list | ✅ | ✅ | ✅ |
| verify | | | ✅ |

### 编译

- Go 1.25.5 + 纯标准库（crypto/aes + AES-256-GCM）
- 源码在 `/tmp/discuss/`
- 重新编译：`cd /tmp/discuss && go build -o ~/Documents/Code/work/mywiki/bin/discuss .`
- 已 gitignore

---

## Kanban Worker 环境（重要！2026-06-29 verified）

### Worker profile 可用工具

| 工具 | 可用性 |
|------|--------|
| `terminal` | ✅ 可执行 shell 命令 |
| `read_file` | ✅ 可读任意文件 |
| `write_file` | ✅ 可写任意文件 |
| `kanban_create` | ✅ 创建子卡 |
| `kanban_complete` | ✅ 完成当前卡 |
| `kanban_show` | ✅ 查看卡详情 |
| `kanban_block` / `kanban_heartbeat` / `kanban_comment` / `kanban_link` | ✅ |
| 总共约 35 个工具 | ✅ |

### Worker 环境变量

| 变量 | 值示例 |
|------|--------|
| `PWD` | `/Users/user/.hermes/kanban/workspaces/t_xxx` |
| `HERMES_PROFILE` | `writer` / `reviewer` |
| `HERMES_KANBAN_TASK` | 当前任务 ID |
| `HERMES_KANBAN_BOARD` | `default` |

### kanban_create() 参数（共 16 个）

| 参数 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| `title` | string | ✅ | 任务标题 |
| `assignee` | string | ✅ | 执行者 profile 名 |
| `body` | string | | 任务正文（结构化 key=value 格式） |
| `skills` | **string array** | | 技能名，如 `["interface-sk"]` |
| `parents` | string array | | 父任务 ID 列表 |
| `board` | string | | 看板标识 |
| `goal_mode` | boolean | | 目标模式开关 |
| `goal_max_turns` | integer | | 目标模式轮次上限 |
| `initial_status` | enum | | "running" / "blocked" |
| `priority` | integer | | 优先级 |
| `tenant` | string | | 租户命名空间 |
| `triage` | boolean | | 分类模式 |
| `workspace_kind` | enum | | "scratch" / "dir" / "worktree" |
| `workspace_path` | string | | 工作区路径 |
| `max_runtime_seconds` | integer | | 运行时间上限 |
| `idempotency_key` | string | | 幂等键 |

### CLI vs Tool 参数名对比

| 功能 | CLI (`hermes kanban create`) | Tool (`kanban_create()`) |
|------|------------------------------|--------------------------|
| 技能 | `--skill interface-sk` | `skills=["interface-sk"]` |
| 父卡 | `--parent t_xxx` | `parents=["t_xxx"]` |
| 返回 id | JSON key `"id"` | dict key `"task_id"` |

**注意！** 模型在 worker 中创建子卡时，可能用 `kanban_create()` tool（Python 接口）
也可能用 `terminal("hermes kanban create ...")`（CLI 接口）。两者参数名不同。

---

## 已知问题

### 问题 1: analyst 不按 SKILL.md 执行

表现：
- 不执行 `discuss init`
- 创建 writer 卡时不传 `skills` 参数
- 创建 writer 卡 body 是自然语言而非 key=value
- 倾向合并 actions 而非每接口一张卡

**根因：模型不遵循指令，不是工具限制。**

尝试的方案（均无效）：
1. SKILL.md 写更详细的步骤 → 无效
2. SKILL.md 写 `kanban_create(skills=["interface-sk"])` 示例 → 无效
3. 让 analyst 用 `terminal()` 绕开 `kanban_create()` 工具 → 无效

### 问题 2: discuss init 没有被调用

根因同上。修复方向：把 `discuss init` 移出 analyst-sk，放到 `kanban-l1.sh` 里。

### 问题 3: writer 未收到结构化上下文

analyst 创建的 writer 卡 body 是自由文本，不含 `output_dir=`、`discuss_path=` 等。
writer 无法知道输出路径和 discuss 路径。

### 问题 4: 没有 --skill 的 writer 卡

writer 卡创建时未传 `skills=["interface-sk"]`，导致 writer 只加载了 kanban lifecycle，没有加载 role skill。

---

## 已验证的成果

### workspace_kind=dir 测试通过 (2026-06-29)

通过 `--workspace "dir:/Users/user/Documents/Code/work/mywiki"` 设置后：

| 探测项 | 结果 |
|--------|------|
| Worker PWD | `/Users/user/Documents/Code/work/mywiki` ✅ |
| `ls bin/discuss` | 存在且可执行 ✅ |
| `$HERMES_PROFILE` | `writer` ✅ |
| `bin/discuss` 运行 | 正常 ✅ |

**结论：** 使用 `workspace_kind="dir"` + `workspace_path="..."` 可以让 worker 直接在 mywiki 根目录工作，`bin/discuss` 相对路径有效。

### kanban CLI workspace 参数格式

```bash
--workspace scratch                   # 默认，scratch 目录
--workspace "dir:/absolute/path"      # 指定绝对路径目录
--workspace worktree                  # git worktree
--workspace "worktree:/path"          # 指定路径的 worktree
```

### kanban_create() tool 的 workspace 参数

tool 接口对应 `workspace_kind` + `workspace_path` 两个参数：
```python
kanban_create(title="...",
    workspace_kind="dir",
    workspace_path="/Users/user/Documents/Code/work/mywiki",
    ...)
```

## 下一步

1. 把 `discuss init` 和 writer 卡创建移到 `kanban-l1.sh`（shell 脚本确定性强）
2. analyst 只做分析 + add-doc
3. 在 `kanban-l1.sh` 中用 `--workspace "dir:..."` 传工作目录参数
4. 在 analyst-sk 中用 `workspace_kind="dir"` 创建子卡
5. body 用结构化 key=value 格式
6. `kanban_create()` 正确传 `skills=["interface-sk"]`

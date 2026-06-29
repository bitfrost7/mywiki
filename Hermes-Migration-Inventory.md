# Hermes Agent 配置迁移清单

> 目标：将本机所有 Hermes Agent 相关配置用 GitHub 管理，搬迁到另一台主机。
> 生成日期：2026-06-28

---

## 1. 概述

| 项目 | 值 |
|------|-----|
| **版本** | Hermes Agent v0.17.0 (2026.6.19, commit c93b9f90) |
| **安装方式** | 脚本安装 (bootstrap-cache) |
| **Python** | 3.11.15 (via uv) |
| **~/.hermes 总大小** | ~4.4 GB (含缓存、日志、node_modules 等运行时) |
| **~/.hermes 是否 git 仓库** | ❌ 不是 |
| **技能库** | 98 个技能，symlink → `~/Documents/Code/work/brain/Brain/skills` |
| **活跃网关** | qqbot (connected) + feishu (connected) |
| **MCP 服务器** | gbrain (gbrain serve), open-second-brain (o2b mcp) |
| **内存提供者** | open-second-brain (plugin) |

---

## 2. 配置核心文件 (需复制 + 模板化)

### 2.1 主配置

| 文件 | 大小 | 是否含 Secret | 说明 |
|------|------|--------------|------|
| `~/.hermes/config.yaml` | 18 KB | ✅ `api_key` (Modelverse API Key) | 核心配置文件，含 model/provider/gateway/mcp 等全部配置 |
| `~/.hermes/.env` | 24 KB | ✅ 多个 secret | API keys, QQ bot token, Feishu secret, GitLab token |
| `~/.hermes/auth.json` | 1.7 KB | ✅ 含 credential pool tokens | OAuth tokens 和 credential pools |
| `~/.hermes/channel_directory.json` | 976 B | ❌ | Gateway channel mapping (gateway 启动时重建) |
| `~/.hermes/gateway_state.json` | 540 B | ❌ | 运行时状态 (迁移后重建) |

### 2.2 需要模板化的 Secrets

```
.env:
  GITLAB_PERSONAL_ACCESS_TOKEN
  QQ_APP_ID
  QQ_CLIENT_SECRET
  OPENROUTER_API_KEY
  FEISHU_APP_ID
  FEISHU_APP_SECRET

config.yaml:
  model.api_key = MODELVERSE_API_KEY
  custom_providers[0].api_key = MODELVERSE_API_KEY

auth.json:
  credential_pool[0].token (custom:api.modelverse.cn)
  credential_pool[1].token (copilot)
  credential_pool[2].token (openrouter)
```

### 2.3 人格文件

| 文件 | 大小 | 说明 |
|------|------|------|
| `~/.hermes/SOUL.md` | 848 B | 当前 session 的 agent persona (已在此会话加载) |

---

## 3. 技能 (Skills)

### 3.1 主技能库

| 元数据 | 值 |
|--------|-----|
| **路径** | `~/.hermes/skills/` → symlink → `~/Documents/Code/work/brain/Brain/skills/` |
| **技能数量** | 98 |
| **大小** | 54 MB |
| **是否需迁移** | ✅ symlink 指向的 Brain skills 需完整复制 (含子目录) |
| **排除** | `.bundled_manifest`, `.curator_backups`, `.curator_state`, `.hub`, `.usage.json`, `.usage.json.lock` |

> **注意**: 技能库 symlink 指向外部的 brain 仓库 (不在 ~/.hermes 内)。
> 迁移时需要确保 brain 仓库同步或技能目录完整独立。

### 3.2 技能备份

`~/.hermes/skills.bak/` — 12 MB 的技能备份，迁移时无需携带。

---

## 4. 配置文件 (Profiles)

### 4.1 Profile 列表

| Profile | 模型 | Provider | Gateway 状态 | 分布来源 |
|---------|------|----------|-------------|---------|
| **default** | deepseek-v4-flash | custom:api.modelverse.cn | stopped | — (built-in) |
| **analyst** | Qwen/Qwen3-Max | custom:api.modelverse.cn | stopped | mywiki/profiles/analyst |
| **dev** | deepseek-v4-flash | custom:api.modelverse.cn | stopped | — (本地创建) |
| **reviewer** | deepseek-ai/DeepSeek-V3.2 | custom:api.modelverse.cn | stopped | mywiki/profiles/reviewer |
| **synthesizer** | deepseek-ai/DeepSeek-V3.2 | custom:api.modelverse.cn | stopped | mywiki/profiles/synthesizer |
| **writer** | deepseek-ai/DeepSeek-V3.2 | custom:api.modelverse.cn | stopped | mywiki/profiles/writer |

### 4.2 需要迁移的 Profile 文件

| Profile | 需迁移文件 | 排除项 |
|---------|-----------|--------|
| **analyst** | `config.yaml`, `SOUL.md`, `distribution.yaml` | state.db, cache/, logs/ sessions/, home/, pairing/, skills/, skins/, plans/, audio_cache/, image_cache/, models_dev_cache.json, ollama_cloud_models_cache.json, .skills_prompt_snapshot.json, .update_check, auth.lock |
| **dev** | `config.yaml`, `SOUL.md`, `profile.yaml` | 同上 |
| **reviewer** | `config.yaml`, `SOUL.md`, `distribution.yaml` | 同上 |
| **synthesizer** | `config.yaml`, `SOUL.md`, `distribution.yaml` | 同上 |
| **writer** | `config.yaml`, `SOUL.md`, `distribution.yaml` | 同上 |

> **注意**: dev profile 没有 distribution.yaml (本地创建，非分布部署)。
> analyst/reviewer/synthesizer/writer 的源文件在 `~/Documents/Code/work/mywiki/profiles/`。

### 4.3 Profile 本地 .env 文件

reviewer/synthesizer/writer 三个 profile 的 `.env` 与主 `.env` 内容相同 (内含所有 secret)。
迁移时需模板化处理。

---

## 5. 定时任务 (Cron Jobs)

| 名称 | 调度 | 模式 | 交付目标 | 状态 |
|------|------|------|---------|------|
| **mywiki-draft-review** | `30 18 * * *` (每天 18:30) | Agent | local | error (timeout) |
| **每日早报** | `0 7 * * *` (每天 07:00) | Agent | qqbot | error (broken pipe) |
| **OSB Skills Cleanup Report** | `0 9 1 * *` (每月1号) | No-agent (script) | local | scheduled |
| **review-sync-mr470** | `0 * * * *` (每小时) | No-agent (script) | local | error (glab not found) |

**存储**: `~/.hermes/cron/jobs.json` (468 KB) — 需完整迁移

---

## 6. 脚本 (Scripts)

### 6.1 自定义脚本

| 文件 | 路径 | 大小 | 说明 |
|------|------|------|------|
| review-sync-mr470.py | `~/.hermes/scripts/review-sync-mr470.py` | 459 B | MR review 同步 |
| setup-webhook-route.py | `~/.hermes/scripts/setup-webhook-route.py` | 1.9 KB | Webhook 路由设置 |
| skill-cleanup-report.py | `~/.hermes/scripts/skill-cleanup-report.py` | 2.7 KB | OSB 技能清理报告 |
| start-proxy | symlink → prompt-logger | — | 代理脚本 |
| toggle-proxy | symlink → prompt-logger | — | 代理开关 |
| view-prompt | symlink → prompt-logger | — | 查看 prompt |

> **外部依赖**: start-proxy/toggle-proxy/view-prompt 指向 `~/Documents/Code/prompt-logger/`

---

## 7. 内存 (Memories)

| 文件 | 大小 | 说明 |
|------|------|------|
| `~/.hermes/memories/MEMORY.md` | 1.1 KB | Hermes 内存 (OSB 工具选择指南) |
| `~/.hermes/memories/USER.md` | 0 B | 用户 profile (空) |

---

## 8. MCP 服务器

| 名称 | 命令 | 状态 | 说明 |
|------|------|------|------|
| **gbrain** | `gbrain serve` | enabled | gbrain MCP server |
| **open-second-brain** | `o2b mcp --vault ~/Documents/Code/work/brain` | enabled | OSB 内存/AI 工具 |

---

## 9. 插件 (Plugins)

| 名称 | 版本 | 状态 | 类型 |
|------|------|------|------|
| **open-second-brain** | 1.17.0 | ✅ enabled | git 安装 (memory provider) |

其他 40+ 插件均为未启用 (bundled)。

---

## 10. 运行时数据 (排除项 — 无需迁移)

| 目录/文件 | 大小 | 原因 |
|-----------|------|------|
| `state.db` (+ -shm, -wal) | ~141 MB | SQLite 会话历史 (机器特定) |
| `hermes-agent/` (源码) | ~1.5 GB | `hermes update`/重新安装后重建 |
| `logs/` | ~23 MB | 日志 (新机器重建) |
| `node/` | ~188 MB | Node.js 运行时 |
| `lsp/` | ~102 MB | LSP 服务 |
| `plugins/open-second-brain/` | ~91 MB | `hermes plugins install` 重建 |
| `kanban/` + `kanban.db*` | ~18 MB | Kanban board 状态 (机器特定) |
| `skills.bak/` | ~12 MB | 技能备份 (不是主技能库) |
| `sessions/` | ~4.7 MB | 请求 dumps (机器特定) |
| `heapdumps/` | ~1.6 GB | 调试 dump (无需迁移) |
| `cache/` | ~324 KB | 模型等缓存 |
| `spawn-trees/` | ~240 KB | 子进程状态 |
| `bootstrap-cache/` | ~240 KB | 安装缓存 |
| `image_cache/`, `audio_cache/`, `pastes/`, `pending/`, `sandboxes/` | 小 | 运行时/缓存 |
| `state-snapshots/` | ~141 MB | 检查点快照 |
| `bin/` (tirith, uv, uvx) | ~56 MB | 工具二进制 (hermes 依赖自带) |
| `hooks/` | 0 B | 无内容 |
| `.hermes_history`, `.skills_prompt_snapshot.json`, `.update_check` | — | UI 状态 |
| `gateway_state.json`, `processes.json` | — | 运行时状态 |

---

## 11. 外部数据引用 (需单独处理)

| 引用 | 路径 | 说明 |
|------|------|------|
| Brain 技能库 | `~/Documents/Code/work/brain/Brain/skills/` | skills symlink 的源 |
| OSB Vault | `~/Documents/Code/work/brain/` | o2b mcp 的 vault 参数 |
| Profile 源 | `~/Documents/Code/work/mywiki/profiles/` | 4 个 profile 的源文件 |
| prompt-logger | `~/Documents/Code/prompt-logger/` | 脚本 symlink 依赖 |
| Brain 日志 | `~/Documents/Code/work/brain/Brain/log/` | brain_feedback 等写入 |

---

## 12. 迁移步骤概览

### 12.1 创建迁移 git 仓库

```bash
mkdir ~/Documents/Code/hermes-config
cd ~/Documents/Code/hermes-config
git init
```

### 12.2 复制并模板化

按 [hermes-agent skill 的 config-migration 指南](https://hermes-agent.nousresearch.com/docs/references/config-migration) 执行：

1. **config.yaml + .env** — 复制到 repo，替换 secret 为 `{{VAR_NAME}}`
2. **skills/** — 完整复制 (含 brain symlink 跳转)，排除运行时文件
3. **profiles/** — 只复制 `config.yaml`, `SOUL.md`, `distribution.yaml`, `profile.yaml` (dev)
4. **cron/jobs.json** — 完整复制
5. **memories/** — 复制 MEMORY.md + USER.md
6. **scripts/** — 完整复制自定义脚本
7. **SOUL.md** — 完整复制
8. **.env.template** — 从 `mywiki/profiles/` 已有模板扩展

### 12.3 编写 setup.sh

按 config-migration 模板生成 setup.sh，包含：
- 交互式 secret 输入
- `sed` 模板替换
- 文件部署到 `~/.hermes/`
- 备份已有的 skills

### 12.4 目标机器后置步骤

```bash
# 1. 验证配置
hermes doctor

# 2. 安装 MCP 服务器
hermes mcp install open-second-brain
# gbrain: 单独安装

# 3. 启用 profiles (基于 distribution.yaml)
hermes profile on analyst
hermes profile on reviewer
hermes profile on synthesizer
hermes profile on writer

# 4. Cron jobs 自动加载
# 5. 启动网关
hermes gateway start
```

### 12.5 机器特定设置 (不能同步)

- **Hermes 二进制**: `curl -fsSL https://hermes-agent.nousresearch.com/install | bash`
- **bun**: `curl -fsSL https://bun.sh/install | bash`
- **o2b**: 按 OSB repo 安装指南
- **Node.js / 开发工具**: 机器特定
- **QQ bot token / Feishu secret**: 在 setup.sh 交互式输入
- **gateway channel directory**: 在 gateway 启动时重建

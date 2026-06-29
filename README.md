# mywiki v4 — 个人知识库

一个由源码、文档和个人总结驱动的 Wiki 知识库。

## Vault 路径

`~/Documents/Code/work/mywiki/`

## 目录

| 目录 | 用途 |
|------|------|
| `Wiki/` | 知识页面（唯一的知识文档目录，按领域分） |
| `raw/articles/` | 外部文章原始资料 |
| `raw/docs/` | 内部文档原始资料 |
| `raw/assets/` | 代码仓库（软链接或克隆） |
| `raw/config.yaml` | 数据源配置 |
| `Brain/` | Agent 确定性记忆（open-second-brain 管理） |
| `_archive/` | 旧版设计文档 |
| `mywiki.db` | 页面元信息（状态、置信度、来源、反馈） |

## 核心流程

```
源码/文档/文章 → Kanban 编译 → Wiki/ 页面 → 使用中反馈 → OSB sig→dream → 修复/新增
```

## 设计文档

最新方案：`design-v4.md`
历史方案：`_archive/`

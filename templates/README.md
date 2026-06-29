# mywiki 文档模板规范

所有模板文件位于 `templates/` 目录。agent 必须严格按模板输出。

## Frontmatter 格式

每个 `.md` 文件顶部必须包含 YAML frontmatter，用 `---` 包裹：

```yaml
---
title: <页面标题>
type: api|module|flow|overview|architecture|interfaces
tags:
  - privatelink/<service>
  - L1|L2|L3
  - <type>
confidence: 1-10
agent: analyst|writer|reviewer
created: YYYY-MM-DD
---
```

| 字段 | 必须 | 说明 |
|------|:----:|------|
| `title` | ✅ | 页面标题 |
| `type` | ✅ | `api` / `module` / `flow` / `overview` / `architecture` / `interfaces` |
| `tags` | ✅ | 至少包含 service + 层级 + type |
| `confidence` | ✅ | 1-10 |
| `agent` | ✅ | 产出 agent 名 |
| `created` | ❌ | YYYY-MM-DD |

## 交叉引用

- 用 `[[privatelink/<service>/<path>]]` 格式
- 只引用确实存在的页面

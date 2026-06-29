---
title: <Service> 架构
type: architecture
tags:
  - privatelink/<service>
  - L2
  - architecture
confidence: 7
agent: writer
created: <YYYY-MM-DD>
---

# 架构 — <service>

## 分层

| 层 | 组件 | 职责 |
|-------|------|------|
| API | Gin | 接口层 |
| Logic | ... | 业务逻辑 |
| Data | ... | 数据访问 |

## 启动链

```
1. main.go → <初始化>
```

## 相关页面

- [[privatelink/<service>/overview]]

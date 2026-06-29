---
name: review-accuracy-sk
description: 终审 — 事实准确性
---

读所有正式文档 vs graph.json + 源码，检查事实是否准确。

通过 → `kanban_complete(summary="准确性通过")`
不通过 → `kanban_comment()` + `kanban_create("fix-accuracy", assignee="writer", skill="fix-sk", parents=[current])`

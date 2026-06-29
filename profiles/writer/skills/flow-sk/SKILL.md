---
name: flow-sk
description: 写 flows/<name>.md → add-doc → 创建 reviewer 卡
---

# Flow Writer

## 流程

1. 从 body 取 `flow_name`、`output_dir`、`source_dir`、`templates_dir`、`discuss_path`
   - 所有路径都是绝对路径（如 `/Users/user/Documents/Code/work/mywiki/Wiki/...`）
2. 读模板 `templates/flow.md`
3. 读相关源码，理解业务流程：

**不要预设 flow 是 API 调用链。** 一个 flow 可以是：

- **接口调用链** — 请求经过 入口→业务→数据 的路径
- **数据流转** — 数据在不同模块/组件之间的流动（异步队列、状态机、事件驱动）
- **网络包转发** — 入站→解析→转发→响应 的路径
- **定时任务/后台流程** — cron 触发的批量处理、清理、同步

从 graph.json 和源码推断：

- 该 flow 涉及哪些入口（Action/handler）
- 调用的中间模块
- 最终读写哪些资源（DB/cache/网络）
- 错误路径和边界条件
4. 写 `output_dir/flows/<flow_name>.md`
   - 业务概念表 + 流程步骤
   - 每步标注调用的接口 wikilink
5. 注册文档到 discuss：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss add-doc <discuss_path> flows/<flow_name>.md
```

6. 创建 review 卡：

```bash
kanban_create(title="review:flows/<flow_name>", assignee="reviewer",
  skill="review-sk",
  body="doc_file=flows/<flow_name>.md\ndiscuss_path=<discuss_path>")
```

7. 完成：

```bash
kanban_complete(summary="流程: <flow_name>")
```

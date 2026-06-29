---
name: interface-sk
description: 写 interfaces/<Action>.md → add-doc → 创建 reviewer 卡
---

# Interface Writer

## 流程

1. 从 body 取 `action`、`output_dir`、`source_dir`、`templates_dir`、`discuss_path`、`src_file`
   - 所有路径都是绝对路径（如 `/Users/user/Documents/Code/work/mywiki/Wiki/...`）
2. 读模板 `templates/interface.md`
3. 读接口定义文件（从 body 的 `src_file` 定位），提取：
   - Req 结构体及其字段、类型、json tag
   - Resp 结构体及其字段、类型
   - handler 函数的注释（如果有）
   - 从 Go import 推断调用的下游（service/layer/dao）
   - 从 handler 方法体推断业务逻辑步骤
4. 写 `output_dir/interfaces/<Action>.md`
   - 格式遵循 `wiki/schema-standard.md`
   - 字段表必须覆盖所有 Req/Resp 字段
   - 业务逻辑步骤从 handler 函数体推断
5. 注册文档到 discuss：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss add-doc <discuss_path> interfaces/<Action>.md
```

6. 创建 review 卡：

```bash
kanban_create(title="review:interfaces/<Action>", assignee="reviewer",
  skill="review-sk",
  body="doc_file=interfaces/<Action>.md\ndiscuss_path=<discuss_path>")
```

7. 完成：

```bash
kanban_complete(summary="接口: <Action>")
```

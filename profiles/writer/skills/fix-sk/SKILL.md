---
name: fix-sk
description: 按 discuss 意见修复文档，标记 fixed
---

# Fix Writer

## 流程

1. 从 body 取 `doc_file`、`discuss_ids`、`discuss_path`
   - 所有路径都是绝对路径（如 `/Users/user/Documents/Code/work/mywiki/Wiki/...`）
2. 拆分 `discuss_ids`（逗号分隔）得 ID 列表
3. 对每个 ID，创建 base 副本（如果还没有 .bak）：

```bash
terminal("cp <output_dir>/<doc_file> <output_dir>/<doc_file>.bak")
```

4. 读 `.md.bak` 文件
5. 逐一修复每个 discuss 指出的问题，在 `.md.bak` 中修改
6. 修复完后，标记每个 discuss 为 fixed：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss fix <discuss_path> dsc_001
/Users/user/Documents/Code/work/mywiki/bin/discuss fix <discuss_path> dsc_002
```

7. 完成：

```bash
kanban_complete(summary="修复: <doc_file>, <N> 个 discuss")
```

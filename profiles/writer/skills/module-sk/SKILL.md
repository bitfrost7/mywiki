---
name: module-sk
description: 写 modules/<name>.md → add-doc → 创建 reviewer 卡
---

# Module Writer

## 流程

1. 从 body 取 `module`、`output_dir`、`source_dir`、`templates_dir`、`discuss_path`
   - 所有路径都是绝对路径（如 `/Users/user/Documents/Code/work/mywiki/Wiki/...`）
2. 读模板 `templates/module.md`
3. 读源码 `<module>/` 目录下的 `.go` 文件，提取：
   - 包名和 import
   - 核心 struct 定义（字段、方法）
   - 该模块的接口（被 api/ 层调用的公开函数）
4. 写 `output_dir/modules/<module>.md`
   - 格式遵循 `wiki/schema-standard.md`
   - 核心结构表必须包含所有 struct/interface
   - 关键流程写 1-3 个核心业务场景
5. 注册文档到 discuss：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss add-doc <discuss_path> modules/<module>.md
```

6. 创建 review 卡：

```bash
kanban_create(title="review:modules/<module>", assignee="reviewer",
  skill="review-sk",
  body="doc_file=modules/<module>.md\ndiscuss_path=<discuss_path>")
```

7. 完成：

```bash
kanban_complete(summary="模块: <module>")
```

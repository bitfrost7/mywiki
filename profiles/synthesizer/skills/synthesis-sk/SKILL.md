---
name: synthesis-sk
description: 读所有已通过文档 → write_file 总览/架构/索引
---

# Synthesis

## 流程

1. 从 body 取 `output_dir`、`templates_dir`
2. `search_files(pattern="*.md", path=output_dir + "/interfaces/")` — 读所有已通过接口页
3. 同样读 modules/ 和 flows/
4. `read_file(templates_dir + "/overview.md")`
5. `read_file(templates_dir + "/architecture.md")`
6. `read_file(templates_dir + "/interfaces-index.md")`
7. 写 3 个文件（直接写 `.md`，不写 bak）:
   - `output_dir + "/overview.md"`
   - `output_dir + "/architecture.md"`
   - `output_dir + "/interfaces.md"`
8. `kanban_complete(summary="synthesis 完成")`

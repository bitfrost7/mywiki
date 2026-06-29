---
name: analyst-sk
description: 读 graph.json → 分任务 → 写 task.json
---

# Analyst

## 第1步：读参数

从 body 取：
```
service=apisvr
graph_json=/Users/user/Documents/Code/work/mywiki/raw/assets/ast/privatelink/apisvr/graphify-out/graph.json
output_dir=/Users/user/Documents/Code/work/mywiki/Wiki/privatelink/apisvr
source_dir=/Users/user/Documents/Code/work/mywiki/raw/assets/repo/privatelink/apisvr
discuss_path=/Users/user/Documents/Code/work/mywiki/raw/assets/privatelink/apisvr/discuss
```

## 第2步：读 graph.json

用 `read_file()` 读 graph.json，分析代码结构：

1. 按 `source_file` 分组，看 top-level 目录
2. 从目录名和文件内容（Go package name、struct 定义、import）推断：
   - 哪些文件是接口入口（含 Req/Resp、handler、controller）
   - 哪些目录是业务逻辑层
   - 哪些目录是数据层
3. 不要预设目录名（不一定是 `api/`、`service/`、`db/`），从 import 和 struct 关系推断

## 第3步：写 task.json

路径：`/Users/user/Documents/Code/work/mywiki/raw/assets/privatelink/<service>/task.json`

```json
{
  "tasks": [
    {
      "id": "t_1",
      "title": "interfaces/CreateVPCEndpoint",
      "skill": "interface-sk",
      "actions": ["CreateVPCEndpoint"],
      "modules": [],
      "doc_files": ["interfaces/CreateVPCEndpoint.md"],
      "source_files": ["api/CreateVPCEndpoint.go"]
    },
    {
      "id": "t_2",
      "title": "modules/db",
      "skill": "module-sk",
      "actions": [],
      "modules": ["db"],
      "doc_files": ["modules/db.md"],
      "source_files": []
    }
  ]
}
```

用 `write_file()` 写入。

## 第4步：完成

```python
kanban_complete(summary=f"分析完成: {N} 个任务")
```

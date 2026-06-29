---
name: review-sk
description: 审查文档 → discuss add（不通过）或 cp .bak + resolve（通过）
---

# Review

从卡 body 取 `doc_file`、`discuss_path`，可能还有 `fix_base_path`（表示有 .bak 需要比较）。

## 判断是否 re-review

如果 body 中有 `fix_base_path`：
- base 对应原始 `.md`，fix 对应 `.md.bak`
- 比较 base 和 fix 的差异，确认修复是否正确
- 审查焦点：fixer 是否有针对前面每个 discuss 的问题做了修复
- 读 `fix_base_path`（.bak）作为当前版本

如果没有 `fix_base_path`：
- 初版审查
- 读 `doc_file`（.md）作为当前版本

## 审查内容

对照源代码审查每篇文档：

1. **接口文档**（interfaces/）：
   - 字段表是否覆盖所有 Req/Resp 字段，无遗漏
   - 字段类型是否正确（string/int/bool 等）
   - 业务逻辑描述是否准确
   - 调用链是否正确（api → service → db）
   - 错误处理是否覆盖

2. **模块文档**（modules/）：
   - 职责描述是否准确
   - 核心 struct 是否覆盖
   - 关键流程是否正确

3. **流程文档**（flows/）：
   - 业务概念是否准确
   - 流程步骤是否完整
   - 接口 wikilink 是否指向存在的页面

## 发现问题 → 提 discuss

对每个问题：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss add <discuss_path> <doc_file> "问题描述" --source "<源文件:行号>" --hint "<修复建议>"
```

记录返回的 ID（如 `dsc_001`）。所有问题提完后，收集所有 discuss ID。

创建 fix 卡：

```bash
kanban_create(title="fix:<doc_file>", assignee="writer",
  skill="fix-sk",
  body="doc_file=<doc_file>\ndiscuss_ids=dsc_001,dsc_002\ndiscuss_path=<discuss_path>")
```

创建 re-review 卡（等 fix 完成才调度）：

```bash
kanban_create(title="re-review:<doc_file>", assignee="reviewer",
  skill="review-sk",
  body="doc_file=<doc_file>\ndiscuss_path=<discuss_path>\nfix_base_path=<doc_file>.bak\ndiscuss_ids=dsc_001,dsc_002",
  parents=[<fix_id>])
```

完成当前审查卡：

```bash
kanban_complete(summary="打回: N 个问题")
```

## 全通过 → 收尾

如果没有问题（re-review 场景下所有 discuss 已修复）：
- 如果有 `.bak`：`terminal("cp <doc>.md.bak <doc>.md && rm <doc>.md.bak")`
- 对所有 `discuss_ids` 中的 ID（如果 body 传了）：

```bash
/Users/user/Documents/Code/work/mywiki/bin/discuss resolve <discuss_path> dsc_001
/Users/user/Documents/Code/work/mywiki/bin/discuss resolve <discuss_path> dsc_002
```

```bash
kanban_complete(summary="通过: <doc_file>")
```

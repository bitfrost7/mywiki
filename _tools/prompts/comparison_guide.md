# 对比测试指南

## 目的

对比 `pipeline.py` 自动生成与其他 SWE1.6 agent 手动生成的文档质量。

## 测试对象

- **目标仓库**: privatelink/apisvr
- **代码路径**: `~/.cache/mywiki-repos/apisvr` 或 `~/Documents/Code/work/privatelink/apisvr`

## 测试方法

### 方法 1: 使用相同提示词

将 `full_pipeline_prompt.md` 的内容直接发送给其他 agent，让其生成文档。

### 方法 2: 让 agent 自主分析

只告诉 agent："为 privatelink/apisvr 生成知识库文档，包含概览、架构、API、DB、模块详情"，不提供详细格式要求。

## 对比维度

| 维度 | pipeline.py | 其他 agent | 评分 (1-5) |
|------|-------------|------------|------------|
| **完整性** | 是否覆盖所有 5 类文档 | | |
| **准确性** | 代码位置标注是否正确 | | |
| **结构化** | 表格使用是否规范 | | |
| **可读性** | 表达是否简洁清晰 | | |
| **一致性** | 格式是否统一 | | |
| **深度** | 是否理解设计意图 | | |
| **速度** | 生成耗时 | | |
| **成本** | Token 消耗 | | |

## 输出对比

### pipeline.py 输出
位置: `~/Documents/Code/work/mywiki/CodeNotes/privatelink/apisvr/`

### 其他 agent 输出
位置: `~/Documents/Code/work/mywiki/CodeNotes/privatelink/apisvr_agent/`

## 具体对比项

### 1. 项目概览 (README.md)

- [ ] 项目描述准确性
- [ ] 技术栈识别完整度
- [ ] 目录结构描述清晰度
- [ ] 字数控制（300 字以内）

### 2. 架构设计 (architecture.md)

- [ ] 架构模式识别正确性
- [ ] 模块划分合理性
- [ ] 关键抽象是否列出
- [ ] 数据流描述清晰
- [ ] 代码位置标注准确

### 3. API 文档 (api.md)

- [ ] 接口清单完整性
- [ ] 路由提取准确性
- [ ] 参数推断正确性
- [ ] 关键接口详情深度

### 4. 数据模型 (db.md)

- [ ] 表结构识别完整
- [ ] 字段类型推断准确
- [ ] 索引提取正确
- [ ] DAO 方法清单完整

### 5. 模块详情 (modules/)

- [ ] 模块职责描述准确
- [ ] 符号清单完整性
- [ ] 实现逻辑理解深度
- [ ] 外部依赖识别正确

## 记录模板

```markdown
## 对比结果

### pipeline.py 优点
- ...
- ...

### pipeline.py 缺点
- ...
- ...

### 其他 agent 优点
- ...
- ...

### 其他 agent 缺点
- ...
- ...

### 关键差异
1. ...
2. ...

### 改进建议
- ...
```

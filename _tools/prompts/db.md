# Prompt: 数据库模型文档生成

## 角色
DBA / 后端开发，需要理解数据存储结构

## 任务
从 Go 结构体 + SQL 代码中提取数据模型

## 输入
代码片段:
{chunks}

## 输出要求

### 数据模型表格

| 表名/模型名 | 字段 | 类型 | 约束 | 说明 | Go 定义位置 |
|------------|------|------|------|------|------------|
| User | id | int64 | PK, auto | 用户 ID | model/user.go:15 |
| User | name | varchar(64) | - | 用户名 | model/user.go:16 |
| User | created_at | datetime | - | 创建时间 | model/user.go:17 |
| ... | ... | ... | ... | ... | ... |

### 关键索引
```markdown
| 表名 | 索引名 | 字段 | 类型 |
|------|--------|------|------|
| User | idx_name | name | UNIQUE |
| ... | ... | ... | ... |
```

### DAO 方法清单
列出数据访问对象的关键方法：

| 方法 | 功能 | 文件位置 |
|------|------|----------|
| GetByID | 按 ID 查询 | dao/user.go:34 |
| Create | 插入记录 | dao/user.go:56 |
| ... | ... | ... |

### 关联关系
如果有外键或关联，用文本描述：

```markdown
User 1:N Order — 一个用户有多个订单
Order N:1 Product — 每个订单关联一个商品
```

### 约束
- 字段类型优先从 Gorm tag (`gorm:"type:varchar(64)"`) 或 SQL DDL 提取
- 如果没有明确类型，从 Go 字段类型推断（如 `string` → `varchar`）
- 每个模型必须标注 Go 定义位置

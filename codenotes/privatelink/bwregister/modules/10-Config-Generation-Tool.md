# 模块: Config Generation Tool

> 社区 #10 — 4 节点 · 凝聚力 0.80

---

## 概述

配置生成工具是一个独立的 Go 命令行工具（`cmd/tools/mysqlgen`），基于 `gorm.io/gen` 库自动从 MySQL 数据库表结构生成 ORM 模型代码和查询代码。这是 bwregister 开发时的代码生成器，不参与运行时。

---

## 文件索引

**`cmd/tools/mysqlgen/main.go`** — 代码生成工具（L1-77）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Config` | `:16` | 工具配置（DSN, OutPath, ModelPath, Tables） |
| `main()` | `:23` | 入口：加载配置 → 生成代码 |
| `loadConfig()` | `:43` | 读取 JSON 配置文件 |
| `genOut()` | `:55` | 核心：连接 MySQL + 调用 gorm gen 生成代码 |

---

## 使用方式

```bash
go run cmd/tools/mysqlgen/main.go -c conf/gen.json
```

## 配置示例（`conf/gen.json`）

```json
{
  "DSN": "user:pass@tcp(host:port)/dbname?...",
  "OutPath": "db/query",
  "ModelPath": "db/model",
  "Tables": ["t_service", "t_user_config", "t_vpc_endpoint"]
}
```

---

## 生成流程

**`genOut()` 在 `cmd/tools/mysqlgen/main.go:55-77`**：

```
1. gorm.Open(mysql.Open(DSN))           → 连接 MySQL
2. gen.NewGenerator(Config{...})        → 创建生成器
   ├── OutPath = "db/query"             → 查询代码输出路径
   ├── ModelPkgPath = "db/model"        → 模型代码路径
   ├── Mode = WithQueryInterface        → 生成查询接口
   └── FieldSignable/FieldNullable = true
3. g.UseDB(gormdb)                      → 绑定数据库
4. 遍历 Tables:
   └── g.GenerateModel(table)           → 为每张表生成模型
5. g.ApplyBasic(models...)              → 应用基础生成
6. g.Execute()                          → 执行生成
```

---

## 生成产物

| 表名 | 模型文件 | 查询文件 | 行数 |
|------|----------|----------|------|
| `t_service` | `db/model/t_service.gen.go` | `db/query/t_service.gen.go` | 41 + 自动生成 |
| `t_user_config` | `db/model/t_user_config.gen.go` | `db/query/t_user_config.gen.go` | 28 + 自动生成 |
| `t_vpc_endpoint` | `db/model/t_vpc_endpoint.gen.go` | `db/query/t_vpc_endpoint.gen.go` | 39 + 自动生成 |

此外还自动生成 `db/query/gen.go`（查询入口/事务管理）。

---

## gorm gen 配置说明

- `gen.WithoutContext`（已设置）：生成的查询方法不强制接收 context 参数
- `gen.WithQueryInterface`（已设置）：生成 `ITXxxDo` 接口供依赖注入
- `FieldSignable: true`：使字段支持泛型操作
- `FieldNullable: true`：处理 NULL 字段

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| 生成的模型文件 | Service Table Schema (C11) | `t_service.gen.go` |
| 生成的模型文件 | User Config Table Schema (C12) | `t_user_config.gen.go` |
| 生成的模型文件 | VPC Endpoint Table Schema (C13) | `t_vpc_endpoint.gen.go` |
| 生成的查询文件 | Database Transaction Context (C3) | `gen.go` |
| 生成的查询文件 | Database Connection Manager (C8) | 在 `db/db.go` 中使用 |

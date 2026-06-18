# billinsert - module 07: Main Configuration (Code Generation Tool)

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 13** (4 nodes, 凝聚力 0.80)
> **验证状态**: ✓ | **来源文件**: `cmd/tools/mysqlgen/main.go`, `cmd/tools/mysqlgen/conf/gen.json`

---

## 1. 模块职责

Main Configuration 模块是一个独立的 **GORM 代码生成工具**（`mysqlgen`），负责：

- **自动生成 ORM 代码**：根据 MySQL 数据库表结构，自动生成 `db/model/*.gen.go` 和 `db/query/*.gen.go`
- **配置驱动**：通过 JSON 配置文件指定目标数据库、输出路径和需要处理的表

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Config` | `cmd/tools/mysqlgen/main.go:16-21` | 结构体 | 代码生成配置（DSN, OutPath, ModelPath, Tables） |
| `main()` | `cmd/tools/mysqlgen/main.go:23-41` | 函数 | 入口：解析配置 → 执行生成 |
| `loadConfig()` | `cmd/tools/mysqlgen/main.go:43-53` | 函数 | 从 JSON 文件加载配置 |
| `genOut()` | `cmd/tools/mysqlgen/main.go:55-77` | 函数 | 核心：连接数据库 → 生成代码 |

## 3. 关键实现逻辑

### 3.1 代码生成流程（`cmd/tools/mysqlgen/main.go:55-77`）

```
genOut(conf)
  │
  ├─1. gorm.Open(mysql.Open(conf.DSN))
  │
  ├─2. g := gen.NewGenerator(gen.Config{
  │       OutPath:      conf.OutPath,     // db/query
  │       ModelPkgPath: conf.ModelPath,   // db/model
  │       Mode:         gen.WithoutContext | gen.WithQueryInterface,
  │       FieldSignable: true,
  │       FieldNullable: true,
  │     })
  │
  ├─3. g.UseDB(gormDB)
  │
  ├─4. for _, table := range conf.Tables {
  │       models = append(models, g.GenerateModel(table))
  │     }
  │
  ├─5. g.ApplyBasic(models...)
  │
  └─6. g.Execute()
```

### 3.2 生成模式

| 模式 | 说明 |
|------|------|
| `gen.WithoutContext` | Query 对象不自动携带 context（billinsert 手动通过 `WithContext()` 传递） |
| `gen.WithQueryInterface` | 生成查询接口（`ITServiceDo`、`ITTrafficInfoDo` 等） |
| `FieldSignable: true` | 字段支持有符号类型 |
| `FieldNullable: true` | 字段支持 nullable |

### 3.3 配置示例（`cmd/tools/mysqlgen/conf/gen.json`）

```json
{
    "DSN": "user:password@tcp(host:port)/dbname?...",
    "OutPath": "../../../db/query",
    "ModelPath": "../../../db/model",
    "Tables": [
        "t_service",
        "t_vpc_endpoint",
        "t_traffic_info"
    ]
}
```

**注意**：配置中只指定了 3 张表，但 `db/model/` 和 `db/query/` 目录下包含了 5 张表的生成文件（多了 `t_service_snatips` 和 `t_service_whitelist`）。这表明代码生成可能分多次执行，或者配置文件有过变更。

## 4. 使用方法

```bash
cd cmd/tools/mysqlgen
# 编辑 conf/gen.json 配置
go run main.go -c conf/gen.json
# 执行后会在 db/model/ 和 db/query/ 生成对应代码
```

## 5. 输出文件

| 生成文件 | 说明 |
|----------|------|
| `db/model/t_service.gen.go` | TService 结构体（映射 t_service 表） |
| `db/model/t_vpc_endpoint.gen.go` | TVpcEndpoint 结构体（映射 t_vpc_endpoint 表） |
| `db/model/t_traffic_info.gen.go` | TTrafficInfo 结构体（映射 t_traffic_info 表） |
| `db/model/t_service_snatips.gen.go` | TServiceSnatip 结构体（映射 t_service_snatips 表） |
| `db/model/t_service_whitelist.gen.go` | TServiceWhitelist 结构体（映射 t_service_whitelist 表） |
| `db/query/gen.go` | Query 门面（Use, ReadDB, WriteDB, Transaction） |
| `db/query/t_service.gen.go` | tService 查询对象 |
| `db/query/t_vpc_endpoint.gen.go` | tVpcEndpoint 查询对象 |
| `db/query/t_traffic_info.gen.go` | tTrafficInfo 查询对象 |
| `db/query/t_service_snatips.gen.go` | tServiceSnatip 查询对象（未在 Use() 中注册） |
| `db/query/t_service_whitelist.gen.go` | tServiceWhitelist 查询对象（未在 Use() 中注册） |

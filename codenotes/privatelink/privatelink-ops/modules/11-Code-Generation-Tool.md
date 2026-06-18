# 模块: 代码生成工具

> 社区 #15 — 5 节点 · Config Generation

---

## 概述

本模块实现基于 `gorm.io/gen` 的数据库模型和查询代码生成工具。通过读取 MySQL 数据库的表结构，自动生成 `db/model/*.gen.go`（结构体模型）和 `db/query/*.gen.go`（查询对象）代码，减少手写 ORM 代码的工作量。

---

## 文件索引

**`cmd/tools/mysqlgen/main.go:1-77`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Config` | `:16` | 生成配置：`DSN`（数据库地址）、`OutPath`（查询代码输出路径）、`ModelPath`（模型代码输出路径）、`Tables`（目标表名列表） |
| `main()` | `:23` | 入口：加载配置文件 → 调用 `genOut()` |
| `loadConfig()` | `:43` | 读取 JSON 配置文件（默认 `conf/gen.json`） |
| `genOut()` | `:55` | **核心生成逻辑**：连接数据库 → 配置 Generator → 生成代码 |

---

## 生成逻辑

**`cmd/tools/mysqlgen/main.go:55-77`** — `genOut()`

```go
func genOut(conf *Config) error {
    gormdb, err := gorm.Open(mysql.Open(conf.DSN))     // :56 — 连接数据库

    g := gen.NewGenerator(gen.Config{
        OutPath:       conf.OutPath,                    // 查询代码输出路径
        ModelPkgPath:  conf.ModelPath,                  // 模型代码输出路径
        Mode:          gen.WithoutContext | gen.WithQueryInterface,
        FieldSignable: true,                            // 字段支持有符号类型
        FieldNullable: true,                            // 字段支持可空
    })
    g.UseDB(gormdb)

    models := make([]interface{}, 0, len(conf.Tables))
    for _, table := range conf.Tables {
        models = append(models, g.GenerateModel(table)) // :72 — 逐个表生成
    }
    g.ApplyBasic(models...)                              // :74 — 应用基础生成
    g.Execute()                                          // :75 — 执行生成
    return nil
}
```

---

## 配置示例

配置文件（默认路径 `conf/gen.json`）：

```json
{
    "DSN": "user:password@tcp(host:3306)/privatelink?charset=utf8mb4",
    "OutPath": "../../db/query",
    "ModelPath": "../../db/model",
    "Tables": [
        "t_service",
        "t_user_config",
        "t_vpc_endpoint",
        "t_service_whitelist",
        "t_service_snatips"
    ]
}
```

---

## 使用方法

根据 **`README.md:15-24`** 的说明：

```bash
cd cmd/tools/mysqlgen
# 如有必要，修改 conf/gen.json 配置
go run main.go
```

---

## 生成的文件

执行后生成 5 个模型文件和 5 个查询文件：

| 表名 | 模型文件 | 查询文件 |
|------|----------|----------|
| `t_service` | `db/model/t_service.gen.go` | `db/query/t_service.gen.go` |
| `t_user_config` | `db/model/t_user_config.gen.go` | `db/query/t_user_config.gen.go` |
| `t_vpc_endpoint` | `db/model/t_vpc_endpoint.gen.go` | `db/query/t_vpc_endpoint.gen.go` |
| `t_service_whitelist` | `db/model/t_service_whitelist.gen.go` | `db/query/t_service_whitelist.gen.go` |
| `t_service_snatips` | `db/model/t_service_snatips.gen.go` | `db/query/t_service_snatips.gen.go` |

以及核心查询聚合文件 `db/query/gen.go`。

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `gen.GenerateModel()` | Database Models (M07) | 自动生成表结构模型 |
| `gen.Execute()` | Database Query Layer (M05) | 自动生成查询对象和 gen.go |

---

## 设计要点

- **全自动生成**：基于数据库实际表结构，无需手动编写 ORM 映射代码
- **配置驱动**：通过 JSON 配置文件指定目标表、输出路径，灵活适应数据库结构变更
- **不参与运行时**：本工具仅在开发阶段使用，生成的代码编译进二进制，工具本身不包含在运行镜像中

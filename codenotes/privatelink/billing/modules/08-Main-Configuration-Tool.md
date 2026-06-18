# billing — module_08_Main_Configuration_Tool

> 自动生成文档 | 社区 13 | 系统: billing | 时间: 2026-06-18

---

# Main Configuration Tool — 数据库模型代码生成工具

## 1. 模块职责

本模块是一个**独立的代码生成工具**，用于从 MySQL 数据库表结构自动生成 GORM Model 和 Query 代码。位于 `cmd/tools/mysqlgen/` 目录下，通过 `go run main.go` 执行，**不参与服务运行时**。

## 2. 主要函数/类型清单

| 函数/类型 | 代码位置 | 说明 |
|-----------|----------|------|
| `Config` | `cmd/tools/mysqlgen/main.go:16-21` | 生成配置：DSN、输出路径、表名列表 |
| `main` | `cmd/tools/mysqlgen/main.go:23-41` | 入口：加载配置 → genOut → 生成代码 |
| `loadConfig` | `cmd/tools/mysqlgen/main.go:43-53` | 读取 `conf/gen.json` 配置文件 |
| `genOut` | `cmd/tools/mysqlgen/main.go:55-65` | 调用 GORM Gen 生成代码 |

## 3. 关键实现逻辑

`genOut()`（`cmd/tools/mysqlgen/main.go:55-77`）

```go
func genOut(cfg *Config) {
    g := gen.NewGenerator(gen.Config{
        OutPath:  cfg.OutPath,   // Query 代码输出目录
        ModelPkgPath: cfg.ModelPkgPath,  // Model 包路径
    })
    g.UseDB(cfg.DB())  // 使用 MySQL 连接
    g.GenerateModel(cfg.Tables...)  // 按表名生成 Model
    g.Execute()  // 执行生成
}
```

### 3.2 配置示例

配置文件位于 `cmd/tools/mysqlgen/conf/gen.json`（根据 `gen.json` 文件路径推测）：

```json
{
  "DSN": "user:password@tcp(host:port)/dbname?charset=utf8mb4",
  "OutPath": "../../db/query",
  "ModelPkgPath": "../../db/model",
  "Tables": ["t_billing_info", "t_connect_info", "t_service", "t_traffic_info", "t_vpc_endpoint"]
}
```

## 4. 涉及的源文件

`cmd/tools/mysqlgen/main.go`（77 行）是一个代码生成工具
- `cmd/tools/mysqlgen/conf/gen.json`（配置，约 10 行）

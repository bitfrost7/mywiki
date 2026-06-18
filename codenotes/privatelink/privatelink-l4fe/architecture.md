# 架构文档

## 整体架构

`privatelink-l4fe` 是一个**轻量级、单体的 gRPC 数据服务**，采用分层架构设计：

```
┌─────────────────────────────────────────────────┐
│                  CLI Layer                       │
│          cmd/privatelinkl4fe/main.go             │
│           (命令分发: start/gen/dumpcfg)           │
├─────────────────────────────────────────────────┤
│              Server Bootstrap                    │
│              server.go / Config                  │
│           (初始化 App, gRPC, DB, API)             │
├─────────────────────────────────────────────────┤
│              gRPC API Layer                      │
│           api/grpc_api.go / GrpcAPI              │
│        (ListL4Gw 业务逻辑 + 数据聚合)               │
├─────────────────────────────────────────────────┤
│           Database Query Layer                   │
│           mygorm/db/gen.go / Query               │
│      (Use/Transaction/WithContext/读写分离)         │
├───────────┬──────────┬──────────┬────────────────┤
│Service    │VPC Endp  │SNAT IP   │Whitelist       │
│Data Access│Data Acc  │Data Acc  │Data Access     │
│t_service  │t_vpc_end │t_service_│t_service_      │
│.gen.go    │point.gen │snatips.  │whitelist.gen.go│
│           │.go       │gen.go    │                │
├───────────┴──────────┴──────────┴────────────────┤
│          Data Models (model/)                    │
│      TService / TVpcEndpoint / TServiceSnatip    │
│      / TServiceWhitelist / Data (聚合)           │
├─────────────────────────────────────────────────┤
│                  MySQL DB                        │
│    t_service / t_vpc_endpoint / t_service_snatips│
└─────────────────────────────────────────────────┘
```

## 数据流

### 正向请求流

```
gRPC Client
    │
    ▼
ListL4Gw(request{object_ids: [...serviceIDs]})
    │
    ▼
GrpcAPI.ListL4Gw()                       [api/grpc_api.go:26]
    │
    ▼
GrpcAPI.getDataFromDB()                  [api/grpc_api.go:201]
    │
    ├─► Query.Transaction()              [mygorm/db/gen.go:87]
    │      │
    │      ├─► tVpcEndpoint.Find()       [db/t_vpc_endpoint.gen.go:344]
    │      │     WHERE service_id IN (...) AND connect_status=1 AND delete_time=0
    │      │
    │      ├─► tService.Find()           [db/t_service.gen.go:348]
    │      │     WHERE service_id IN (...) AND delete_time=0
    │      │
    │      └─► tServiceSnatip.Find()     [db/t_service_snatips.gen.go:308]
    │            WHERE service_id IN (...) AND delete_time=0
    │
    ▼
数据聚合：按 ServiceID 组装 Data 结构    [model/privatelink.go:8]
    │
    ▼
构建 L4GwView (foreIPs/fnatips/Groups/Rules)  [api/grpc_api.go:32-191]
    │
    ▼
返回 ListL4GwReply
```

## 核心设计决策

### 1. 单事务查询

`getDataFromDB()` 使用 `Query.Transaction()` 确保三张表的查询在同一个数据库连接/事务上下文中执行，保证数据一致性。

### 2. 代码生成 (GORM gen)

- `mygorm/database.go:NewGen()`（行 54-73）通过 gorm/gen 读取 MySQL 表结构自动生成 DAO 和 Model 代码
- `cmd/privatelinkl4fe/main.go:gen()`（行 47-58）提供 CLI 命令来触发代码生成
- 生成的代码位于 `mygorm/db/` 和 `mygorm/model/` 目录

### 3. 读写分离支持

`mygorm/db/gen.go:ReadDB()`（行 53-55）和 `WriteDB()`（行 57-59）通过 `dbresolver.Read/Write` clause 支持读写分离。

### 4. 健康检查

`mygorm/db/gen.go:Available()`（行 41）提供数据库连接可用性检查。

### 5. FullNAT 转发模型

`ListL4Gw` 返回的配置采用了 **FullNAT 转发模型**：
- **Fore (前端)**：VPC Endpoint 的 IP，外部流量到达这些 IP
- **Backend (后端)**：Service 自身的 IP，流量最终转发到这里
- **FNAT (SNAT)**：用于 FullNAT 的 SNAT IP，做源地址转换
- **Rules**：将每个 Fore Endpoint 的流量做 FullNAT：源改 FNAT、目标改 Backend

## 配置模型

**`Config`** (`server.go:10-13`)：

```go
type Config struct {
    app.ApplicationConfig          // 基础应用配置（ZK、Prometheus、日志等）
    Database *mygorm.Config        // 数据库 DSN + 代码生成路径
}
```

**`mygorm.Config`** (`mygorm/database.go:20-23`)：

```go
type Config struct {
    DSN        string   // MySQL 连接字符串
    GenOutPath string   // 代码生成输出路径
}
```

## CLI 命令

| 命令 | 函数 | 说明 |
|------|------|------|
| `start` | `runServer()` | 启动 gRPC 服务 |
| `gen` | `gen()` | 运行 GORM gen 代码生成 |
| `dumpcfg` | `dumpConfig()` | 输出默认配置 JSON |
| `version` | `showVersion()` | 输出版本信息 |

## 依赖关系

### 内部模块依赖图

```
cmd/privatelinkl4fe/main.go
    │ 依赖
    ├── privatelink-l4fe (server.go)      ← 根包
    │     └── api/grpc_api.go
    │           └── mygorm/db (Query, DAO)
    │                 └── mygorm/model
    └── mygorm (database.go)
          └── mygorm/db (Use)
```

### 外部依赖

| 依赖 | 用途 |
|------|------|
| `git.ucloudadmin.com/cnat2/app` | 应用框架（初始化、gRPC server、日志等） |
| `git.ucloudadmin.com/l4fwd/proto` | L4 转发 protobuf 定义 |
| `gorm.io/gorm` + `gorm.io/gen` | ORM + 代码生成 |
| `gorm.io/driver/mysql` | MySQL 驱动 |
| `go.uber.org/zap` | 日志 |
| `google.golang.org/grpc` | gRPC 框架 |
| `github.com/prometheus/client_golang` | Prometheus 指标 |

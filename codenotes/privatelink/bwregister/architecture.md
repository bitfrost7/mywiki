# bwregister — 架构设计

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18

---

## 整体架构

**分层架构（Layered）**，部署为单一 Go 二进制进程。

```
┌─────────────────────────────────────────────────────┐
│                    CLI Entry                         │
│              cmd/main.go:18 (main)                   │
├─────────────────────────────────────────────────────┤
│                  Server Layer                        │
│         server.go:58 (Server struct)                 │
│   ┌──────────────────┬──────────────────────┐       │
│   │  Master Election  │    Cron Scheduler    │       │
│   │  ZK MasterLoop    │    InitCronTask()    │       │
│   │  server.go:175    │    server.go:104     │       │
│   └────────┬─────────┴──────────┬───────────┘       │
│            │                    │                     │
│   ┌────────▼────────────────────▼──────────┐        │
│   │              Task Layer                  │       │
│   │   task/task.go (Task struct, AddTask)   │       │
│   │   task/limiter.go (SyncAllConnectionInfo)│       │
│   │   task/user_config.go (SyncUserConfig)  │       │
│   └────────┬────────────────────┬───────────┘       │
│            │                    │                     │
│   ┌────────▼──────┐  ┌─────────▼─────────┐         │
│   │   gRPC Server  │  │   gRPC Client     │         │
│   │  api/grpc.go   │  │  BWTrafficCli     │         │
│   │  :24 / :40     │  │  task/limiter.go  │         │
│   └────────────────┘  │  :170 / :190 / :210│         │
│                       └─────────┬─────────┘         │
├─────────────────────────────────┼───────────────────┤
│            DB Layer              │                   │
│   db/db.go (Database struct)     │                   │
│   db/query/gen.go (Query/Use)    │                   │
│   db/model/*.gen.go (ORM模型)    │                   │
└──────────────────────────────────┴──────────────────┘
                                   │
                    ┌──────────────▼─────────────┐
                    │       MySQL Database        │
                    │  t_vpc_endpoint             │
                    │  t_service                  │
                    │  t_user_config              │
                    └────────────────────────────┘
```

---

## 核心流程

### 启动流程

```
cmd/main.go:18 main()
  └─ cmd/main.go:43 runServer()
       ├─ cmd/main.go:53 loadConfig() → 读取 JSON 配置
       └─ server.go:66 NewServer(cfg)
            ├─ s.Init(cfg)              → 初始化 Application 框架
            ├─ s.InitGRPCServer()       → 初始化 gRPC Server
            ├─ cfg.SetDefaultValue()    → 设置 DB 连接默认值
            ├─ ZK.NewMaster2()          → 注册 Master 选举
            ├─ db.NewDatabase()         → 初始化数据库连接
            ├─ s.InitCronTask(ctx)     → 注册 4 个定时任务
            ├─ api.RegisterGrpcServer() → 注册 gRPC 服务
            └─ xpro.CollectSysMetrics() → 启动系统指标采集
```

### 定时任务（Cron）

全部注册在 `server.go:104 InitCronTask()`：

| 任务 | 周期 | Master 限制 | 说明 |
|------|------|-------------|------|
| SyncAllConnectionInfo | `RegisterSpec`（默认 10s） | ✅ 仅 Master | 查询 DB → 同步流量信息到 UTraffic |
| SyncUserConfig | `SyncUserConfigSpec`（默认 60s） | ❌ 所有节点 | 从 DB 同步用户配置到内存缓存 |
| monMaster | `MonMasterSpec`（默认 5s） | ❌ 所有节点 | 上报当前节点 Master/Follow 状态 |
| RegisterTrafficManagerInfo | `SyncZKPathSpec`（默认 10s） | ✅ 仅 Master | 注册节点到 ZK 路由 |

### 数据流：带宽限速同步

```
[Server.InitCronTask]
   ↓ (每10s, 仅Master)
[Task.AddTask → SyncAllConnectionInfo]
   ↓
[Task.GetAllConnectionInfo]
   ├─ db.Database.DescribeAllConnections(t_vpc_endpoint JOIN t_service)
   │   └─ t_vpc_endpoint.DeleteTime=0, ConnectStatus=1
   │   └─ t_service.DeleteTime=0
   ├─ 检查 CloseStatus → 停服连接限速 1KB
   ├─ 检查 CheckDisableLimitBandwidth → 白名单不限速
   └─ 生成 TrafficInfo (IPv4 & IPv6) + ShareBWInfo
   ↓
[Task.SyncAllConnectionInfo]
   ├─ BWTrafficCli.SyncAllTrafficInfo  → gRPC → UTraffic
   └─ BWTrafficCli.SyncAllShareBWInfo  → gRPC → UTraffic
```

---

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| CLI入口 | `cmd/main.go` | 命令行解析、配置加载、启动/工具命令分发 |
| 服务主控 | `server.go` | Server 结构的生命周期管理、Master 选举、Cron 调度 |
| gRPC API | `api/grpc.go` | 对外提供限速信息查询接口 |
| 任务框架 | `task/task.go` | 任务注册与启动，Master 前置判断 |
| 限速逻辑 | `task/limiter.go` | 连接信息查询 → 带宽计算 → gRPC 同步 |
| 用户配置 | `task/user_config.go` | 从 DB 同步用户白名单配置到内存 |
| DB连接管理 | `db/db.go` | MySQL 连接初始化、GORM Query 封装、业务查询 |
| DB查询上下文 | `db/query/gen.go` | gorm gen 生成的 ORM 查询层，提供事务/读写分离 |
| 数据表模型 | `db/model/*.gen.go` | gorm gen 自动生成的表结构模型 |
| Prometheus监控 | `prometheus/prometheus.go` | 系统指标、DB指标、gRPC指标的定义与采集 |
| 代码生成工具 | `cmd/tools/mysqlgen/main.go` | 基于 gorm gen 的数据表模型和查询代码生成 |

---

## Master 选举机制

使用 ZooKeeper 实现 Master 选举：

1. `NewServer()`（`server.go:76`）中调用 `s.ZK.NewMaster2()` 注册 Master 竞选
2. 当选为 Master 时，`MasterLoop()`（`server.go:175`）通过原子变量 `s.master uint32` 记录状态
3. `isMaster()`（`server.go:195`）通过 `atomic.CompareAndSwapUint32` 检查当前是否为 Master
4. 定时任务中 `isMaster != nil` 表示该任务只允许 Master 执行
5. 降级为 Follower 时同样记录日志

---

## 依赖关系

```
cmd/main.go
  └── server.go (bwregister package)
        ├── api/grpc.go     → gRPC 服务注册
        ├── db/db.go        → 数据库连接
        │     ├── db/query/gen.go    → gorm gen Query
        │     └── db/model/*.gen.go  → 表模型
        ├── task/task.go    → 任务调度
        │     ├── task/limiter.go    → 带宽同步 + gRPC Client
        │     └── task/user_config.go → 用户配置
        ├── prometheus/prometheus.go → 指标
        └── app.Application  → cnat2 应用框架
              ├── ZK (zkutils)       → ZooKeeper
              └── Grpc (grpc)         → gRPC Server
```

---

## 关键设计决策

1. **全量同步而非增量**：每次任务周期全量读取数据库 JOIN 查询，适合连接数在可控范围内（万级）的场景
2. **Master-Slave 避免重复同步**：只有 Master 执行带宽同步，Slave 作为热备
3. **用户配置内存缓存**：用户白名单配置每分钟从数据库同步到内存 map，避免每次连接查询都读库
4. **Prometheus 全覆盖**：所有 gRPC 请求、DB 操作、Client 调用、任务执行均有指标监控
5. **GORM Gen 代码生成**：数据表和查询代码由 gorm gen 自动生成，减少手写 ORM 代码

---

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (源自代码) | 全部 |
| 需人工审查 | 0 |

*所有架构描述均基于源代码事实和 graphify 知识图谱分析。*

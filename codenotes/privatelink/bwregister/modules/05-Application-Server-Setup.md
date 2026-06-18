# 模块: Application Server Setup

> 社区 #5 — 15 节点 · 凝聚力 0.12

---

## 概述

应用服务器设置模块是 bwregister 的核心编排层。`Server` 结构体整合了 Application 框架（`cnat2/app`）、数据库、任务调度和 ZooKeeper Master 选举，是 bwregister 所有能力的汇聚点。

---

## 文件索引

**`server.go`** — 主服务定义与初始化（L1-205）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Config` | `:21` | 服务配置结构体 |
| `Config.VerifyParams()` | `:34` | 验证配置必填参数 |
| `Config.SetDefaultValue()` | `:49` | 设置数据库连接默认值 |
| `Server` | `:58` | 服务主结构体 |
| `NewServer()` | `:66` | 构造函数，完整的初始化流程 |
| `InitCronTask()` | `:104` | 注册 4 个定时任务 |
| `Start()` | `:168` | 启动服务（任务 + gRPC） |
| `MasterLoop()` | `:175` | Master 选举回调 |
| `isMaster()` | `:195` | 原子检查 Master 状态 |
| `monMaster()` | `:199` | 上报 Master 指标 |

---

## Config 结构体

**`server.go:22-32`**：

```go
type Config struct {
    app.ApplicationConfig
    DBConfig           db.Config    // 数据库连接配置
    RegisterZKPath     string       // ZK 注册路径
    RegisterSpec       string       // 注册任务 cron 表达式
    SyncUserConfigSpec string       // 用户配置同步 cron 表达式
    MonMasterSpec      string       // Master 状态监控 cron 表达式
    SyncZKPathSpec     string       // ZK 路径同步 cron 表达式
    ClusterID          string       // 集群标识
    MasterServicePath  string       // Master 服务路径
    MasterLockPath     string       // Master 锁路径
}
```

---

## Server 初始化流程

**`NewServer()` 在 `server.go:66-102`**：

```
1. s.Init(cfg)                             — 初始化 Application 框架（日志、ZK、gRPC）
2. s.InitGRPCServer()                      — 创建 gRPC Server
3. cfg.SetDefaultValue()                   — 设置 ConnMaxLifetime / MaxIdleConns 默认值
4. s.ZK.NewMaster2(...)                    — ZK Master 选举注册（server.go:76）
5. db.NewDatabase()                        — 初始化 MySQL 连接（server.go:84）
6. s.InitCronTask(ctx)                     — 注册定时任务（server.go:89）
7. api.RegisterGrpcServer(s.Grpc, s.t)     — 注册 gRPC 服务（server.go:94）
8. xpro.CollectSysMetrics()                — 启动系统指标采集（server.go:97）
```

---

## 定时任务注册

全部在 `InitCronTask()`（`server.go:104-166`）：

**任务 1**: 带宽限速注册（每 10s，仅 Master）
- `server.go:114` — `AddTask(RegisterSpec, isMaster, SyncAllConnectionInfo)`
- 核心任务：读取 DB 连接 → 计算限速 → 同步到 UTraffic

**任务 2**: 用户配置同步（每 60s，所有节点）
- `server.go:131-136` — 启动时立即执行一次，然后按周期执行
- 将 `t_user_config` 表数据同步到内存 `UserConfig` 缓存

**任务 3**: Master 状态上报（每 5s，所有节点）
- `server.go:144` — `AddTask(MonMasterSpec, nil, monMaster)`
- 通过 Prometheus Gauge 上报当前节点是否为 Master

**任务 4**: ZK 路由注册（每 10s，仅 Master）
- `server.go:153` — `AddTask(SyncZKPathSpec, isMaster, RegisterTrafficManagerInfo)`
- 将本节点注册为流量管理器到 ZK 路由

---

## Server 结构体

**`server.go:58-64`**：

```go
type Server struct {
    app.Application        // 嵌入 cnat2 应用框架（Log, ZK, Grpc 等）
    cfg    *Config         // 服务配置
    db     *db.Database    // 数据库访问层
    master uint32          // Master 标志（原子操作）
    t      *task.Task      // 任务调度器
}
```

嵌入 `app.Application` 获得了：日志（`s.Logger`）、ZooKeeper 客户端（`s.ZK`）、gRPC 服务器（`s.Grpc`）、上下文管理、服务发现等能力。

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `NewServer()` | Database Connection Manager (C8) | 调用 `db.NewDatabase()` |
| `NewServer()` | gRPC Server Monitoring (C6) | 调用 `api.RegisterGrpcServer()` |
| `NewServer()` | Bandwidth Traffic Manager (C7) | 通过 `s.t` 引用 |
| `InitCronTask()` | Bandwidth Traffic Manager (C7) | 注册带宽同步任务 |
| `Config` | Main Configuration Loader (C9) | 配置由 `cmd/main.go` 加载 |
| `NewServer()` | Monitoring (prometheus) | 调用 `xpro.CollectSysMetrics()` |

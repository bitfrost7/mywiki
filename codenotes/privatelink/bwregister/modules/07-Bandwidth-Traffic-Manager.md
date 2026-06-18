# 模块: Bandwidth Traffic Manager

> 社区 #7 — 12 节点 · 凝聚力 0.16

---

## 概述

带宽流量管理器是 bwregister 的核心业务模块，负责从数据库查询所有活跃连接信息，计算带宽限速值，并通过 gRPC Client 同步到带宽计算平台（UTraffic）。该模块包含连接信息查询、限速值计算、共享带宽聚合和 gRPC 调用四个子功能。

---

## 文件索引

### 任务调度框架

**`task/task.go`** — 任务基类（L1-53）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Task` | `:13` | 任务结构体，持有 cron 调度器、数据库引用和 gRPC Client |
| `InitTask()` | `:19` | 构造函数，初始化 Task 和 BWTrafficCli |
| `AddTask()` | `:30` | 注册定时任务，支持 Master 前置判断 |
| `StartTask()` | `:49` | 启动 cron 调度器 |

### 限速核心逻辑

**`task/limiter.go`** — 带宽计算与同步（L1-219）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| 常量定义 | `:17-25` | Namespace、限速单位（KB/MB）、带宽上限 |
| `SyncAllConnectionInfo()` | `:27` | 入口：获取连接信息并并行同步 TrafficInfo 和 ShareBWInfo |
| `GetAllConnectionInfo()` | `:50` | 核心：查询 DB + 计算限速 + 生成 TrafficInfo/ShareBWInfo |
| `RegisterTrafficManagerInfo()` | `:160` | 注册本节点为流量管理器到 UTraffic |
| `BWTrafficCli` | `:165` | gRPC Client 封装结构体 |
| `SyncAllShareBWInfo()` | `:170` | 同步共享带宽信息到 UTraffic |
| `SyncAllTrafficInfo()` | `:190` | 同步流量限速信息到 UTraffic |
| `RegisterTrafficManagerInfo()` (cli) | `:210` | 注册流量管理器到 UTraffic |

---

## 核心数据流

### SyncAllConnectionInfo（`task/limiter.go:27`）

```
GetAllConnectionInfo()
  ├── db.DescribeAllConnections()     → 查询活跃连接
  └── 遍历 connections:
       ├── 计算限速值:
       │    ├── 正常: ConnectBw * MB
       │    ├── 停服: 1 * KB
       │    └── 白名单: BandwidthMax * MB
       ├── 生成 TrafficInfo (IPv4)
       ├── 生成 TrafficInfo (IPv6)
       └── 聚合 ShareBWInfo (按 ServiceID)
               ↓
SyncAllConnectionInfo():
  ├── eg.Go(cli.SyncAllTrafficInfo)    → 全量同步 TrafficInfo
  └── eg.Go(cli.SyncAllShareBWInfo)    → 全量同步 ShareBWInfo
```

---

## 关键常量

**`task/limiter.go:17-25`**：

```go
const (
    Namespace     = "pl"           // 普线命名空间
    NamespaceIPv6 = "pl-ipv6"      // IPv6 命名空间
    KB = 1000                      // 千字节
    MB = 1000 * KB                 // 兆字节
    BandwidthMax = 10000 * MB      // 带宽上限
)
```

---

## 带宽计算规则

在 `GetAllConnectionInfo()` 中，限速值计算分三种情况（`task/limiter.go:60-69`）：

| 条件 | 限速值 | 场景 |
|------|--------|------|
| `CloseStatus == 1`（停服） | `1 * KB` | 服务已关闭，最低速率 |
| `CheckDisableLimitBandwidth() == true`（白名单） | `BandwidthMax * MB` | 不限速用户（白名单） |
| 默认 | `ConnectBw * MB` | 正常限速 |

---

## ShareBWInfo 聚合

在 `sharebwInfoMap`（`task/limiter.go:58`）中以 `conn.ServiceID` 为键聚合共享带宽信息。每个 Service 对应 IPv4/IPv6 各一个 ShareBWInfo 记录。

**`task/limiter.go:98-155`** 中：
- 首次遇到 ServiceID：创建新的 `ShareBWInfo` 对（IPv4 + IPv6），`SpeedLimitOff=true`
- 再次遇到：将 Endpoint 的 IP 追加到 `AssociateIP` 列表

---

## BWTrafficCli 核心方法

### SyncAllTrafficInfo

**`task/limiter.go:190-208`**：调用 `utrafficCli.SyncAllTrafficInfo()`，全量替换带宽限速信息。

### SyncAllShareBWInfo

**`task/limiter.go:170-187`**：调用 `utrafficCli.SyncAllShareBWInfo()`，全量替换共享带宽信息。

### RegisterTrafficManagerInfo

**`task/limiter.go:210-219`**：调用 `utrafficCli.RegisterTrafficManagerInfo()`，携带 `ProductType_PL` 注册为流量管理器。

### 监控埋点

每个 Client 方法都有完整的 Prometheus 监控（`task/limiter.go:173, 180-181, 193, 200-201`）：

```go
xpro.ClientRequestSentTotal.WithLabelValues("SyncAllShareBWInfo", "grpc", "UTrafficAPIClient").Inc()
xpro.ClientResponseReceivedTotal.WithLabelValues(...).Inc()
xpro.ClientResponseDuration.WithLabelValues(...).Observe(...)
```

---

## Task 结构体

**`task/task.go:13-17`**：

```go
type Task struct {
    c   *cron.Cron       // cron 调度器
    d   *db.Database     // 数据库访问
    cli *BWTrafficCli    // 带宽平台 gRPC Client
}
```

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `GetAllConnectionInfo()` | Database Connection Manager (C8) | 调用 `db.DescribeAllConnections()` |
| `GetAllConnectionInfo()` | User Configuration Model (C0) | 调用 `CheckDisableLimitBandwidth()` |
| `SyncAllConnectionInfo()` | Application Server Setup (C5) | 由 `InitCronTask()` 调度 |
| `BWTrafficCli` | gRPC 调用 (UTraffic 外部) | 调用带宽计算平台 |
| `Task` | gRPC Server Monitoring (C6) | 对外 API 通过 Task 查询 |

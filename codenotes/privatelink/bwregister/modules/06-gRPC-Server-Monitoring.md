# 模块: gRPC Server Monitoring

> 社区 #6 — 19 节点 · 凝聚力 0.10

---

## 概述

gRPC 服务监控模块对外暴露带宽限速信息的查询接口，并包含完整的 Prometheus 监控埋点。该模块实现了 `UTrafficDataAPI` gRPC 服务，供带宽计算平台调用获取流量限速信息和共享带宽信息。

---

## 文件索引

**`api/grpc.go`** — gRPC 服务实现（L1-53）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `GRPCServer` | `:12` | gRPC 服务结构体 |
| `RegisterGrpcServer()` | `:17` | 注册 gRPC 服务到 gRPC Server |
| `GetAllTrafficInfo()` | `:24` | 获取全量资源限速信息 |
| `GetAllShareBWInfo()` | `:40` | 获取全量共享带宽信息 |

---

## GRPCServer 结构体

**`api/grpc.go:12-15`**：

```go
type GRPCServer struct {
    utrafficProto.UnimplementedUTrafficDataAPIServer
    t *task.Task
}
```

- 嵌入 `UnimplementedUTrafficDataAPIServer` 实现默认 gRPC 接口
- 持有 `*task.Task` 引用以调用带宽查询逻辑

---

## gRPC 方法

### GetAllTrafficInfo

**`api/grpc.go:24-37`**：

```go
func (s *GRPCServer) GetAllTrafficInfo(ctx context.Context, _ *utrafficProto.GetAllTrafficInfoRequest) (*utrafficProto.GetAllTrafficInfoResponse, error) {
    m := xpro.NewGRPCServerMonitor("GetAllTrafficInfo")
    trafficInfos, _, err := s.t.GetAllConnectionInfo(ctx)
    m.Done(err)
    // ... 返回 trafficInfos
}
```

返回：所有活跃端点的 `TrafficInfo`，包含 IPv4/IPv6 双栈限速信息。

### GetAllShareBWInfo

**`api/grpc.go:40-53`**：

```go
func (s *GRPCServer) GetAllShareBWInfo(ctx context.Context, _ *utrafficProto.GetAllShareBWInfoRequest) (*utrafficProto.GetAllShareBWInfoResponse, error) {
    m := xpro.NewGRPCServerMonitor("GetAllShareBWInfo")
    _, sharebwInfos, err := s.t.GetAllConnectionInfo(ctx)
    m.Done(err)
    // ... 返回 sharebwInfos
}
```

返回：全量共享带宽信息，按 `ServiceID` 聚合。

---

## Prometheus 监控

**`prometheus/prometheus.go:157-178`** — `GRPCServerMonitor`：

| 函数/类型 | 行号 | 说明 |
|-----------|------|------|
| `GRPCServerMonitor` | `:157` | gRPC 监控器结构体 |
| `NewGRPCServerMonitor()` | `:162` | 创建监控器，记录请求接收 |
| `.Done()` | `:170` | 完成回调，记录响应和延时 |

### 指标

| 指标 | 行号 | 类型 | 说明 |
|------|------|------|------|
| `ServerRequestReceived` | `:37` | Counter | 请求接收计数，标签: `api`, `type` |
| `ServerResponseSent` | `:45` | Counter | 响应发送计数，标签: `api`, `type`, `retcode` |
| `ServerResponseSentDelay` | `:53` | Histogram | 响应延时分布（Buckets: 50~3000ms） |
| `ServerResponseSentDelayTotal` | `:64` | Gauge | 响应延时累计 |

### 调用链路

`NewGRPCServerMonitor("GetAllTrafficInfo")` → `ServerRequestReceived +1`
→ 执行 `s.t.GetAllConnectionInfo(ctx)`
→ `m.Done(err)` → `ServerResponseSent +1` + `ServerResponseSentDelay.Observe()` + `ServerResponseSentDelayTotal +1`

---

## 服务注册

**`server.go:94`** 在 `NewServer()` 中：

```go
api.RegisterGrpcServer(s.Grpc, s.t)
```

将 `GRPCServer` 注册到由 Application 框架创建的 gRPC Server 上。

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `RegisterGrpcServer()` | Application Server Setup (C5) | 由 `server.go:94` 调用 |
| `GetAllTrafficInfo()` | Bandwidth Traffic Manager (C7) | 调用 `s.t.GetAllConnectionInfo()` |
| `GetAllShareBWInfo()` | Bandwidth Traffic Manager (C7) | 同上 |
| `NewGRPCServerMonitor()` | prometheus | 指标记录 |

# bwregister — API 文档

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 协议: gRPC | **验证状态**: ✓

---

## 协议概述

bwregister 使用 **gRPC** 协议对外提供两个查询方法，均实现 `UTrafficDataAPI` 服务接口（定义在 `git.ucloudadmin.com/utraffic/protov2` 中）。客户端通过 gRPC Channel 连接，服务端使用 `google.golang.org/grpc` 标准库。

---

## gRPC 服务: UTrafficDataAPI

### 服务注册

服务注册入口在 `api/grpc.go:17`：

```go
func RegisterGrpcServer(s *grpc.Server, t *task.Task) {
    utrafficProto.RegisterUTrafficDataAPIServer(s, &GRPCServer{t: t})
}
```

`GRPCServer` 结构体定义在 `api/grpc.go:12`，持有 `*task.Task` 引用以查询数据库。

---

### GetAllTrafficInfo

获取全量要计算的**资源限速信息**。

| 属性 | 值 |
|------|-----|
| 方法 | `GetAllTrafficInfo` |
| 位置 | `api/grpc.go:24` |
| 请求 | `GetAllTrafficInfoRequest`（空请求） |
| 响应 | `GetAllTrafficInfoResponse` — 包含 `[]*common.TrafficInfo` |

**业务描述**：查询所有活跃连接的限速信息，返回每个端点的 IPv4 和 IPv6 两个 TrafficInfo 记录，包含命名空间、UUID、入/出口带宽、资源状态和共享带宽 ID。被带宽计算平台调用以获取需要计算限速的资源。

**数据来源**：`task.Task.GetAllConnectionInfo()` → `db.Database.DescribeAllConnections()` → `t_vpc_endpoint` JOIN `t_service`。

**实现逻辑**（`task/limiter.go:50-158`）：
1. 从数据库查询所有活跃连接
2. 对每个连接判断停服状态（`CloseStatus==1` 则限速 1KB）
3. 检查用户配置是否禁用限速（`CheckDisableLimitBandwidth` → `task/user_config.go:57`）
4. 分别为 IPv4 和 IPv6 生成 TrafficInfo
5. 聚合生成 ShareBWInfo（以 ServiceID 为聚合键）

---

### GetAllShareBWInfo

获取全量要计算的**共享带宽信息**。

| 属性 | 值 |
|------|-----|
| 方法 | `GetAllShareBWInfo` |
| 位置 | `api/grpc.go:40` |
| 请求 | `GetAllShareBWInfoRequest`（空请求） |
| 响应 | `GetAllShareBWInfoResponse` — 包含 `[]*common.ShareBWInfo` |

**业务描述**：查询所有活跃连接对应的共享带宽信息。与 `GetAllTrafficInfo` 共享底层数据源（`GetAllConnectionInfo`），但只返回 `ShareBWInfo` 分片。共享带宽类型标记为 `SHARE_BW_TYPE_INSIGNIFICANCE`（不限制速度的共享带宽）。

---

### 监控埋点

每个 gRPC 方法都通过 `prometheus.NewGRPCServerMonitor`（`prometheus/prometheus.go:157`）进行监控：

| 指标 | 类型 | 标签 |
|------|------|------|
| `privatelink_bwregister_server_request_received` | Counter | `api`, `type=grpc` |
| `privatelink_bwregister_server_response_sent` | Counter | `api`, `type=grpc`, `retcode` |
| `privatelink_bwregister_server_response_sent_delay` | Histogram | `api`, `type=grpc`（Buckets: 50~3000ms） |
| `privatelink_bwregister_server_response_sent_delay_total` | Gauge | `api`, `type=grpc` |

---

## 内部 RPC 调用（Client 侧）

bwregister 作为 gRPC Client 调用带宽计算平台（UTraffic）的接口：

### SyncAllTrafficInfo

| 属性 | 值 |
|------|-----|
| 调用位置 | `task/limiter.go:190` |
| 客户端 | `BWTrafficCli.utrafficCli` |
| 说明 | 全量更新带宽限速信息到带宽计算平台 |

### SyncAllShareBWInfo

| 属性 | 值 |
|------|-----|
| 调用位置 | `task/limiter.go:170` |
| 客户端 | `BWTrafficCli.utrafficCli` |
| 说明 | 全量更新共享带宽信息到带宽计算平台 |

### RegisterTrafficManagerInfo

| 属性 | 值 |
|------|-----|
| 调用位置 | `task/limiter.go:210` |
| 客户端 | `BWTrafficCli.utrafficCli` |
| 说明 | 注册本节点为流量管理器，携带 `ProductType_PL` 和 `ClusterID` |

### 内部 Client 监控

每个 Client 调用都通过 Prometheus 指标监控：

| 指标 | 类型 | 标签 |
|------|------|------|
| `privatelink_bwregister_client_request_sent_total` | Counter | `api`, `type=grpc`, `Service=UTrafficAPIClient` |
| `privatelink_bwregister_client_response_received_total` | Counter | `api`, `type=grpc`, `Service`, `code` |
| `privatelink_bwregister_client_response_received_delay` | Histogram | `api`, `type=grpc`, `Service` |

---

## 配置结构

配置 JSON 示例（`conf/bwregister.json`）：

```json
{
  "ServiceAddr": "10.72.137.110:16639",
  "DBConfig": { "DSN": "mysql dsn" },
  "RegisterSpec": "*/10 * * * * *",
  "SyncUserConfigSpec": "0 * * * * *",
  "MonMasterSpec": "*/5 * * * * *",
  "SyncZKPathSpec": "*/10 * * * * *",
  "ClusterID": "privatelink-bwregister",
  "MasterLockPath": "/NS/.../privatelink-bwregister-lock",
  "MasterServicePath": "/NS/.../privatelink-bwregister/ip:port"
}
```

完整配置结构定义在 `server.go:21`。

---

## CLI 命令

| 命令 | 位置 | 说明 |
|------|------|------|
| `bwregister -c <path> start` | `cmd/main.go:35` | 启动服务 |
| `bwregister dumpcfg` | `cmd/main.go:33` | 输出默认配置 JSON |
| `bwregister version` | `cmd/main.go:37` | 输出版本信息 |

---

## 架构文件索引

| 文件 | 说明 |
|------|------|
| `cmd/main.go` | CLI 入口与配置加载 |
| `server.go` | 服务主结构、初始化、Cron 任务注册 |
| `api/grpc.go` | gRPC 服务实现 |
| `task/task.go` | 任务调度框架 |
| `task/limiter.go` | 带宽限速逻辑核心 |
| `task/user_config.go` | 用户配置同步与查询 |
| `db/db.go` | 数据库连接与查询 |
| `db/query/gen.go` | gorm gen 查询上下文 |
| `prometheus/prometheus.go` | Prometheus 指标定义与采集 |
| `conf/bwregister.json` | 配置示例 |

# 模块: Monitoring & Observability

> 对应 Community #6（部分） + Prometheus 封装

---

## 概述

监控与可观测性模块封装了 bwregister 的全部 Prometheus 指标定义与采集逻辑，涵盖 gRPC 服务监控、数据库监控、客户端调用监控、系统资源监控和任务状态监控。所有指标统一以 `privatelink_bwregister_` 前缀命名。

---

## 文件索引

**`prometheus/prometheus.go`** — Prometheus 指标与采集（L1-184）

### 指标变量

| 变量名 | 行号 | 类型 | 标签 | 说明 |
|--------|------|------|------|------|
| `CommonGauge` | `:18` | GaugeVec | `type` | 通用指标（如 is_master） |
| `ServerResourceGauge` | `:29` | GaugeVec | `type` | 系统资源（CPU、内存、DB连接数） |
| `ServerRequestReceived` | `:37` | CounterVec | `api`, `type` | 服务端请求接收计数 |
| `ServerResponseSent` | `:45` | CounterVec | `api`, `type`, `retcode` | 服务端响应计数 |
| `ServerResponseSentDelay` | `:53` | HistogramVec | `api`, `type` | 响应延时分布（Buckets: 50~3000ms） |
| `ServerResponseSentDelayTotal` | `:64` | GaugeVec | `api`, `type` | 响应延时累计 |
| `ClientRequestSentTotal` | `:73` | CounterVec | `api`, `type`, `Service` | 客户端请求计数 |
| `ClientResponseReceivedTotal` | `:81` | CounterVec | `api`, `type`, `Service`, `code` | 客户端响应计数 |
| `ClientResponseDuration` | `:90` | HistogramVec | `api`, `type`, `Service` | 客户端响应延时分布 |
| `TaskStatusCounter` | `:98` | CounterVec | `task_name`, `status` | 任务状态计数 |
| `SyncFailCounter` | `:108` | CounterVec | `type` | 同步失败计数 |

### 函数

| 函数 | 行号 | 说明 |
|------|------|------|
| `CollectSysMetrics()` | `:118` | 协程采集 CPU/内存使用率（每 10s） |
| `ExportDBStats()` | `:140` | 数据库连接池统计回调 |
| `ExportDBBeforeMetric()` | `:144` | 数据库请求前回调 |
| `ExportDBAfterMetric()` | `:148` | 数据库请求后回调 |
| `NewGRPCServerMonitor()` | `:162` | 创建 gRPC 服务监控器 |
| `.Done()` | `:170` | gRPC 请求完成回调 |
| `init()` | `:180` | 注册所有指标到 Prometheus |

---

## 系统资源采集

**`CollectSysMetrics()` 在 `prometheus/prometheus.go:118-136`**：

启动一个后台 goroutine，每 10 秒采集：
- **CPU 使用率**：`ServerResourceGauge{type="cpu_usage"}`
- **内存使用率**：`ServerResourceGauge{type="mem_usage"}`

采集使用 `github.com/shirou/gopsutil/v3/process` 库。

---

## 数据库监控

三个回调函数通过 gorm plugin 自动注册：

| 回调 | 行号 | 触发的指标 |
|------|------|-----------|
| `ExportDBStats` | `:140` | `ServerResourceGauge{type="db_connections"}` — 活跃连接数 |
| `ExportDBBeforeMetric` | `:144` | `ClientRequestSentTotal` — 每个DB请求前递增 |
| `ExportDBAfterMetric` | `:148` | `ClientResponseReceivedTotal` + `ClientResponseDuration` — 每个DB请求后记录 |

---

## gRPC 服务监控

**`GRPCServerMonitor` 在 `prometheus/prometheus.go:157-178`**：

```go
// 请求开始
m := NewGRPCServerMonitor("GetAllTrafficInfo")
// → ServerRequestReceived +1

// 请求结束
m.Done(err)
// → ServerResponseSent +1 (retcode=success/fail)
// → ServerResponseSentDelay.Observe(duration)
// → ServerResponseSentDelayTotal +1
```

---

## 指标全景

```
┌──────────────────────────────────────────────────┐
│                  bwregister                       │
│                                                   │
│  系统资源指标:                                      │
│  ├─ privatelink_bwregister_common_gauge           │
│  │   └─ type=is_master                            │
│  └─ privatelink_bwregister_server_resource_gauge  │
│      ├─ type=cpu_usage                            │
│      ├─ type=mem_usage                            │
│      └─ type=db_connections                       │
│                                                   │
│  gRPC 服务器指标:                                   │
│  ├─ server_request_received{api,type=grpc}         │
│  ├─ server_response_sent{api,type=grpc,retcode}    │
│  ├─ server_response_sent_delay{api,type=grpc}      │
│  └─ server_response_sent_delay_total{api,type=grpc}│
│                                                   │
│  客户端(UTraffic)指标:                              │
│  ├─ client_request_sent_total{api,type=grpc,Service}│
│  ├─ client_response_received_total{api,grpc,c,code} │
│  └─ client_response_duration{api,type=grpc,Service} │
│                                                   │
│  DB 指标:                                          │
│  ├─ client_request_sent_total{type=db,table}       │
│  ├─ client_response_received_total{type=db,code}   │
│  └─ client_response_duration{type=db}              │
│                                                   │
│  任务指标:                                          │
│  ├─ task_status_counter{task_name,status}          │
│  └─ sync_fail_counter{type}                        │
└──────────────────────────────────────────────────┘
```

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `CollectSysMetrics()` | Application Server Setup (C5) | 由 `server.go:97` 调用 |
| `ExportDBStats/Before/After` | Database Connection Manager (C8) | 在 `gormDB.Use(plugin)` 中注册 |
| `NewGRPCServerMonitor()` | gRPC Server (C6) | 在每个 gRPC 方法中创建 |
| `Client*` 指标 | Bandwidth Traffic Manager (C7) | 在每个 gRPC Client 调用中记录 |
| `TaskStatusCounter` | Bandwidth Traffic Manager (C7) | 在 `server.go:122` 中递增 |
| `CommonGauge` | Application Server Setup (C5) | 在 `monMaster()` 中设置 |
| `init()` | 全局 | 在包导入时自动注册指标 |

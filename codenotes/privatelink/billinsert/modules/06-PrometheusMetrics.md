# billinsert - module 06: Prometheus Metrics

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 12** (6 nodes, 凝聚力 0.29)
> **验证状态**: ✓ | **来源文件**: `prometheus/prometheus.go`

---

## 1. 模块职责

Prometheus Metrics 模块定义了 billinsert 的所有 Prometheus 指标，负责：

- **指标定义**：9 个 Prometheus 指标（Counter、Gauge、Histogram）
- **系统资源采集**：定时采集进程 CPU 和内存使用率
- **DB 监控回调**：与 `privatelink-utils/gorm/plugin` 插件集成，上报数据库操作指标
- **指标注册**：在 `init()` 函数中自动注册所有指标到 Prometheus 默认注册表

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `CollectSysMetrics()` | `prometheus/prometheus.go:96-114` | 函数 | 启动 goroutine 每 10 秒采集 CPU/Mem |
| `ExportDBStats()` | `prometheus/prometheus.go:118-120` | 函数 | 上报数据库连接数 |
| `ExportDBBeforeMetric()` | `prometheus/prometheus.go:122-124` | 函数 | DB 操作前上报请求计数 |
| `ExportDBAfterMetric()` | `prometheus/prometheus.go:126-133` | 函数 | DB 操作后上报响应计数+延迟 |
| `init()` | `prometheus/prometheus.go:135-138` | 函数 | 注册所有指标 |

## 3. 指标清单

### 3.1 CommonGauge（通用状态 Gauge）

| 指标名 | Label | 设置位置 | 说明 |
|--------|-------|----------|------|
| `privatelink_billinsert_common_gauge` | `type` | `server.go:173` | `is_master` 值为 1 或 0 |

### 3.2 ServerResourceGauge（资源占用 Gauge）

| 指标名 | Label | 设置位置 | 说明 |
|--------|-------|----------|------|
| `privatelink_billinsert_server_resource_gauge` | `type` | `prometheus.go:105` | CPU 使用率（每 10 秒） |
| | | `prometheus.go:109` | 内存使用率（每 10 秒） |
| | | `prometheus.go:119` | 数据库连接数（由 Monitor 插件触发） |

### 3.3 外部请求指标

| 指标名 | Labels | 说明 |
|--------|--------|------|
| `privatelink_billinsert_client_request_sent_total` | `api`（"api"/"db"）, `type`（请求类型）, `service`（后端服务/表名） | 请求计数 |
| `privatelink_billinsert_client_response_received_total` | `api`, `type`, `service`, `code`（RetCode/"success"/"fail"） | 响应计数 |
| `privatelink_billinsert_client_response_received_delay` | `api`, `type`, `service` | 延迟分布（Buckets: 50/100/200/500/1000/1500/2000/2500/3000ms） |

### 3.4 任务指标

| 指标名 | Labels | 说明 |
|--------|--------|------|
| `privatelink_billinsert_task_status_counter` | `task_name`, `status` | 任务状态计数（如 `insert_traffic_info/completed`） |

### 3.5 监控拉取指标

| 指标名 | Labels | 说明 |
|--------|--------|------|
| `privatelink_billinsert_fetch_metrics_fail` | `type`（"qps_limit"/"fetch_fail"/"fetch_empty"/"invalid_resource_ids"）, `metric`（指标名称） | 拉取失败计数 |
| `privatelink_billinsert_fetch_metrics_delay` | `metric` | 拉取延迟分布 |

### 3.6 流量插入指标

| 指标名 | Labels | 说明 |
|--------|--------|------|
| `privatelink_billinsert_traffic_insert_fail` | （无） | 流量写入失败计数 |

## 4. 关键实现逻辑

### 4.1 系统资源采集（`prometheus/prometheus.go:96-114`）

```go
func CollectSysMetrics() error {
    p, _ := process.NewProcess(int32(os.Getpid()))
    go func() {
        ticker := time.NewTicker(10 * time.Second)
        for range ticker.C {
            cpuUsage, _ := p.CPUPercent()
            memUsage, _ := p.MemoryPercent()
            ServerResourceGauge.WithLabelValues("cpu_usage").Set(cpuUsage)
            ServerResourceGauge.WithLabelValues("mem_usage").Set(float64(memUsage))
        }
    }()
    return nil
}
```

使用 `github.com/shirou/gopsutil/v3/process` 获取进程级资源数据。

### 4.2 DB 监控集成（`prometheus/prometheus.go:118-133`）

三个回调函数作为 `gorm/plugin` 的钩子，在每次 GORM 数据库操作前后调用：

- `ExportDBStats(stats *sql.DBStats)`：在 Monitor 插件定时触发时上报 `OpenConnections`
- `ExportDBBeforeMetric(data *plugin.CustomMetric)`：每次操作前上报请求 `ClientRequestSentTotal`
- `ExportDBAfterMetric(data *plugin.CustomMetric)`：每次操作后上报响应计数和延迟

### 4.3 注册（`prometheus/prometheus.go:135-138`）

所有指标在 `init()` 中通过 `prometheus.MustRegister()` 注册。

此外，`cmd/main.go:88-90` 的 `init()` 额外注册了版本信息指标：
```go
prometheus.MustRegister(version.NewCollector("privatelink_billinsert"))
```

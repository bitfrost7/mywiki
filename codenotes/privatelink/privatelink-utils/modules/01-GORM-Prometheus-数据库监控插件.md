# 模块 01：GORM Prometheus 数据库监控插件

## 概述

该模块对应图分析 **Community 0「Database Monitoring」**（7 个节点）和 **Community 1「Metrics Configuration」**（6 个节点），提供 GORM 数据库操作的 Prometheus 监控插件。通过 GORM 回调机制，在每次数据库操作前后自动记录耗时和结果，同时支持周期性地采集数据库连接池状态。

## 源文件

- **`gorm/plugin/prometheus.go`** — 完整实现（149 行）

## 核心结构体

### Config — 监控配置 (`prometheus.go:30-39`)

```go
type Config struct {
    DBStatCollectInterval int
    DBStatCollector       DBStatCollector
    DBBeforeMetricCollector CustomMetricCollector
    DBAfterMetricCollector  CustomMetricCollector
}
```

配置定义了四种回调/参数：
- **`DBStatCollectInterval`** — 连接池状态采集周期（秒），默认值 10 秒
- **`DBStatCollector`** — 用户实现的连接池统计上报函数
- **`DBBeforeMetricCollector`** — 操作前调用，用于采集指标
- **`DBAfterMetricCollector`** — 操作后调用，用于采集结果和耗时

### PrometheusMonitor — 监控实例 (`prometheus.go:41-43`)

```go
type PrometheusMonitor struct {
    cfg *Config
}
```

核心监控对象，持有配置引用。实现 GORM 的 `Plugin` 接口（`Name()` + `Initialize()`）。

**图分析关系**：
- `PrometheusMonitor`（Community 0）通过字段 `cfg` 引用 `Config`（Community 1）——跨社区引用，说明配置定义与运行时分离
- `PrometheusMonitor` 上的方法（`Name`, `CollectDBStatus`, `dbBeforeOperation`, `dbAfterOperation`, `RegisterCallback`, `Initialize`）全部分布在 Community 0，形成以监控执行为核心的社区

### CustomMetric — 指标数据点 (`prometheus.go:11-20`)

```go
type CustomMetric struct {
    Action   string
    Table    string
    Result   bool
    Duration time.Duration
}
```

表示一次 SQL 操作的完整指标记录。`Duration` 字段引用了标准库的 `time.Duration`（图分析中跨实体引用）。

### DBStatCollector — 连接池状态收集函数 (`prometheus.go:24`)

```go
type DBStatCollector func(stat *sql.DBStats)
```

接收 `database/sql.DBStats` 的函数类型。用户在此函数中实现自己的指标上报逻辑（如 Prometheus Gauge 更新）。

### CustomMetricCollector — SQL 指标收集函数 (`prometheus.go:28`)

```go
type CustomMetricCollector func(data *CustomMetric)
```

接收 `*CustomMetric` 的函数类型。`Config` 引用此类型作为 before/after 收集器字段。

## 核心方法

### Initialize — 插件入口 (`prometheus.go:140-149`)

```go
func (p *PrometheusMonitor) Initialize(db *gorm.DB) error
```

GORM Plugin 接口方法。逻辑：
1. 若 `DBStatCollector` 非 nil，设置默认采集间隔（10 秒）并启动 `CollectDBStatus` 协程
2. 调用 `RegisterCallback` 注册全部回调
3. 返回错误（若有）

### RegisterCallback — 注册 GORM 回调 (`prometheus.go:95-138`)

为 **6 种 GORM 操作**各注册 before/after 回调，共 12 个回调点：

| 操作 | Before 回调注册点 | After 回调注册点 |
|------|------------------|-----------------|
| Create | `Create().Before("gorm:create")` | `Create().After("gorm:create")` |
| Update | `Update().Before("gorm:update")` | `Update().After("gorm:update")` |
| Query | `Query().Before("gorm:query")` | `Query().After("gorm:query")` |
| Delete | `Delete().Before("gorm:delete")` | `Delete().After("gorm:delete")` |
| Row | `Row().Before("gorm:row")` | `Row().After("gorm:row")` |
| Raw | `Raw().Before("gorm:raw")` | `Raw().After("gorm:raw")` |

每个 before 回调调用 `dbBeforeOperation(action)`，每个 after 回调调用 `dbAfterOperation(action)`。

### CollectDBStatus — 连接池状态采集 (`prometheus.go:55-67`)

```go
func (p *PrometheusMonitor) CollectDBStatus(db *gorm.DB)
```

启动一个独立 goroutine，使用 `time.NewTicker` 按 `DBStatCollectInterval` 的间隔周期执行：
1. 调用 `db.DB()` 获取 `*sql.DB`
2. 调用 `sqlDB.Stats()` 获取 `sql.DBStats`
3. 将统计信息传递给 `cfg.DBStatCollector`

**图分析关系**：内部调用了 `DBStatCollector`（Community 1 的节点），同时引用了 `time.Duration`（计时器间隔）。

### dbBeforeOperation — 操作前处理 (`prometheus.go:69-77`)

```go
func (p *PrometheusMonitor) dbBeforeOperation(action string) func(db *gorm.DB)
```

返回 GORM 回调函数：
1. 通过 `db.Set("start_time", time.Now())` 记录操作开始时间到 GORM session
2. 调用 `cfg.DBBeforeMetricCollector` 传入 `CustomMetric{Action, Table}`

### dbAfterOperation — 操作后处理 (`prometheus.go:79-93`)

```go
func (p *PrometheusMonitor) dbAfterOperation(action string) func(db *gorm.DB)
```

返回 GORM 回调函数：
1. 从 session 中取出 `start_time`
2. 计算 `time.Since(startTime)` 得到实际耗时
3. 通过 `db.Statement.Error == nil` 判断操作结果
4. 调用 `cfg.DBAfterMetricCollector` 传入完整 `CustomMetric{Action, Table, Result, Duration}`

## 图分析社区归属

### Community 0 — Database Monitoring（运行时行为）

| 节点 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `PrometheusMonitor` | struct | `prometheus.go:41` | 监控结构体 |
| `.Name()` | method | `prometheus.go:51` | 返回"prometheus_monitor" |
| `.CollectDBStatus()` | method | `prometheus.go:55` | 连接池状态采集 |
| `.dbBeforeOperation()` | method | `prometheus.go:69` | 操作前处理 |
| `.dbAfterOperation()` | method | `prometheus.go:79` | 操作后处理 |
| `.RegisterCallback()` | method | `prometheus.go:95` | 回调注册 |
| `.Initialize()` | method | `prometheus.go:140` | 插件初始化入口 |

### Community 1 — Metrics Configuration（类型定义）

| 节点 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `prometheus.go` | file | `prometheus.go:1` | 文件节点 |
| `CustomMetric` | struct | `prometheus.go:11` | 指标数据点 |
| `Duration` | field type | `prometheus.go:19` | `time.Duration` 引用 |
| `DBStatCollector` | type | `prometheus.go:24` | 连接池统计函数类型 |
| `CustomMetricCollector` | type | `prometheus.go:28` | SQL 指标函数类型 |
| `Config` | struct | `prometheus.go:30` | 监控配置 |
| `NewMonitor()` | function | `prometheus.go:45` | 构造器 |

## 使用示例

```go
import "git.ucloudadmin.com/unetworks/privatelink/privatelink-utils/gorm/plugin"

// 1. 创建监控配置
monitorCfg := &plugin.Config{
    DBStatCollectInterval: 15,
    DBStatCollector: func(stat *sql.DBStats) {
        // 上报连接池统计到 Prometheus
        prometheusGauge.WithLabelValues("open_connections").Set(float64(stat.OpenConnections))
    },
    DBBeforeMetricCollector: func(data *plugin.CustomMetric) {
        // 在指标采集前计数
        prometheusCounter.WithLabelValues(data.Action, data.Table).Inc()
    },
    DBAfterMetricCollector: func(data *plugin.CustomMetric) {
        // 上报操作耗时
        prometheusHistogram.WithLabelValues(data.Action, data.Table, fmt.Sprint(data.Result)).Observe(data.Duration.Seconds())
    },
}

// 2. 创建监控实例并注册到 GORM
monitor := plugin.NewMonitor(monitorCfg)
db.Use(monitor) // 自动调用 monitor.Initialize(db)
```

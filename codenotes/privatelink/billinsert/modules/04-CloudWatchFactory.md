# billinsert - module 04: CloudWatch Factory

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 7** (Monitor Data API, 18 nodes) + **Community 9** (CloudWatch Metrics, 5 nodes) + **Community 10** (CloudWatch Factory, 8 nodes)
> **验证状态**: ✓ | **来源文件**: `factory/factory.go`, `factory/cloudwatch/impl.go`, `factory/cloudwatch/basic.go`, `factory/cloudwatch/expand.go`

---

## 1. 模块职责

CloudWatch Factory 是 billinsert 的 **监控数据拉取层**，负责通过内部 CloudWatch Admin API 获取 VPC Endpoint 的带宽监控数据。核心能力：

- **HTTP 客户端封装**：基于 `privatelink-utils/httpclient` 实现，自动注入 `ApiKey` 鉴权头
- **QPS 限流**：使用 `golang.org/x/time/rate` 令牌桶限流器，默认 10 QPS
- **指标查询**：支持 4 个带宽指标（IPv4 In/Out + IPv6 In/Out）
- **批量拉取**：20 个资源一组分批请求，4 个指标并发拉取
- **重试机制**：内置 3 次重试，处理限流和临时故障
- **流量计算**：梯形积分法计算流量总量

## 2. 主要函数/类型清单

### 2.1 Factory 入口

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Factory` | `factory/factory.go:8-10` | 结构体 | 工厂门面，含 `CloudwatchImpl` |
| `InitFactory()` | `factory/factory.go:12-16` | 函数 | 创建 Factory 实例 |

### 2.2 CloudWatch 实现层

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `CloudwatchImpl` | `factory/cloudwatch/impl.go:26-32` | 结构体 | CloudWatch 客户端实现 |
| `NewCloudwatchImpl()` | `factory/cloudwatch/impl.go:34-42` | 函数 | 创建客户端实例，初始化限流器 |
| `APIRequestWithMetrics()` | `factory/cloudwatch/basic.go:62-78` | 方法 | 通用 API 请求（带 Prometheus 埋点） |
| `QueryMonitorData()` | `factory/cloudwatch/basic.go:81-110` | 方法 | 查询监控数据（含空结果和无效资源处理） |

### 2.3 数据拉取与计算层

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `FetchEndpointTrafficInfos()` | `factory/cloudwatch/expand.go:13-15` | 方法 | 带重试的流量数据拉取 |
| `FetchEndpointTrafficInfosWithRetry()` | `factory/cloudwatch/expand.go:17-64` | 方法 | 重试逻辑实现（最多 3 次） |
| `BatchFetchEndpointTrafficInfos()` | `factory/cloudwatch/expand.go:66-81` | 方法 | 分批拉取（每批 20 个 endpoint） |
| `FetchEndpointInOutBandTrafficData()` | `factory/cloudwatch/expand.go:83-105` | 方法 | 并发拉取 4 个带宽指标 |
| `CalcTrafficSum()` | `factory/cloudwatch/expand.go:107-125` | 函数 | 梯形积分法计算流量总量 |

### 2.4 请求/响应结构体

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `QueryMonitorDataRequest` | `factory/cloudwatch/basic.go:15-24` | 结构体 | 监控数据查询请求 |
| `Selector` | `factory/cloudwatch/basic.go:26-30` | 结构体 | 指标选择器（Metric + LongResourceId + Tags） |
| `QueryMonitorDataResponse` | `factory/cloudwatch/basic.go:32-36` | 结构体 | 监控数据查询响应 |
| `MonitorDataResult` | `factory/cloudwatch/basic.go:38-41` | 结构体 | 监控数据结果集 |
| `MonitorDataItem` | `factory/cloudwatch/basic.go:43-47` | 结构体 | 指标数据项 |
| `Result` | `factory/cloudwatch/basic.go:49-54` | 结构体 | 单个资源查询结果 |
| `MetricValue` | `factory/cloudwatch/basic.go:56-59` | 结构体 | 监控数据点（Timestamp + Value） |

## 3. 关键实现逻辑

### 3.1 请求架构（`factory/cloudwatch/basic.go:62-78`）

```
APIRequestWithMetrics(req, resp)
  │
  ├─ 打点: ClientRequestSentTotal +1
  │
  ├─ 发起 HTTP POST (注入 ApiKey 头)
  │
  └─ defer:
      ├─ ClientResponseReceivedTotal +1 (含 RetCode)
      └─ ClientResponseDuration 记录延迟
```

### 3.2 监控数据查询（`factory/cloudwatch/basic.go:81-110`）

```go
QueryMonitorData(req)
  ├─ 设置 Backend = "CloudWatchAdmin", Action = "QueryMonitorData"
  ├─ APIRequestWithMetrics()
  ├─ 检查 resp.RetCode != 0 → 返回错误
  ├─ 检查 resp.Data == nil || len(resp.Data.List) == 0
  │   ├─ 存在 InvalidResourceIds → 上报告警指标
  │   └─ 全部为空 → 记录日志
  └─ 返回 resp
```

### 3.3 流量数据拉取流程（`factory/cloudwatch/expand.go`）

```
FetchEndpointInOutBandTrafficData(endpointIDs, region, startTime, endTime)
  │
  ├─ 定义 4 个指标:
  │   ├─ ep_in_bw          (IPv4 入带宽)
  │   ├─ ep_out_bw         (IPv4 出带宽)
  │   ├─ ep_in_bw_ipv6     (IPv6 入带宽)
  │   └─ ep_out_bw_ipv6    (IPv6 出带宽)
  │
  └─ 并发 goroutine 拉取：
      ├─ goroutine 1: BatchFetchEndpointTrafficInfos(ep_in_bw)
      ├─ goroutine 2: BatchFetchEndpointTrafficInfos(ep_out_bw)
      ├─ goroutine 3: BatchFetchEndpointTrafficInfos(ep_in_bw_ipv6)
      └─ goroutine 4: BatchFetchEndpointTrafficInfos(ep_out_bw_ipv6)
```

### 3.4 分批拉取（`factory/cloudwatch/expand.go:66-81`）

```go
batchSize := 20
for start := 0; start < len(endpointIDs); start += batchSize {
    end := min(start + batchSize, len(endpointIDs))
    batch := endpointIDs[start:end]
    batchTrafficData := FetchEndpointTrafficInfos(ctx, batch, metric, region, startTime, endTime)
    // merge into result map
}
```

### 3.5 重试机制（`factory/cloudwatch/expand.go:17-64`）

- 最多重试 3 次
- 每次请求前等待令牌桶限流（`i.limiter.Wait(timeoutCtx)`），超时 1 秒
- 限流等待超时 → 重试
- 查询失败 → 重试
- 查询返回空 → 放弃（不重试）
- 成功后 break

### 3.6 流量计算：梯形积分法（`factory/cloudwatch/expand.go:107-125`）

```go
func CalcTrafficSum(trafficValues []*MetricValue) uint64 {
    // 1. 按时间戳排序
    sort.Slice(trafficValues, func(i, j int) bool {
        return trafficValues[i].Timestamp < trafficValues[j].Timestamp
    })
    // 2. 梯形积分: sum += (preRate + curRate) * (curTs - preTs) / 2
    for i := 1; i < len(trafficValues); i++ {
        preRate := trafficValues[i-1].Value
        preTs := trafficValues[i-1].Timestamp
        curRate := trafficValues[i].Value
        curTs := trafficValues[i].Timestamp
        trafficSum += (preRate + curRate) * uint64(curTs - preTs) / 2
    }
    return trafficSum
}
```

该算法将带宽离散采样点近似为连续变化，用梯形面积求和得到总流量（字节数）。

### 3.7 指标常量（`factory/cloudwatch/impl.go:9-23`）

| 常量 | 值 | 说明 |
|------|-----|------|
| `ServiceBackend` | `"CloudWatchAdmin"` | 网关后端服务名 |
| `FetchMetricTimeout` | 10 | 拉取超时（秒） |
| `EndpointInBandMetric` | `"ep_in_bw"` | IPv4 入带宽指标 |
| `EndpointOutBandMetric` | `"ep_out_bw"` | IPv4 出带宽指标 |
| `EndpointInBandIpv6Metric` | `"ep_in_bw_ipv6"` | IPv6 入带宽指标 |
| `EndpointOutBandIpv6Metric` | `"ep_out_bw_ipv6"` | IPv6 出带宽指标 |
| `EndpointProductKey` | `"ep"` | Endpoint 产品类型 |
| `CalcMethodRaw` | `"raw"` | 聚合方式（原始数据） |
| `EndpointMetricPeriod` | 60 | 数据点周期（秒） |

## 4. 重要设计决策

### 4.1 并发 vs 串行
4 个带宽指标使用 **goroutine + WaitGroup** 并发拉取，大幅缩短总耗时。

### 4.2 QPS 限流
每个 API 请求前通过 `rate.NewLimiter(rate.Limit(qpsLimit), int(qpsLimit))` 限流。限流等待超时 1 秒后会重试。

### 4.3 资源独立性
`APIRequestWithMetrics()` 方法与 `QueryMonitorData()` 方法分离，使得 API 调用和业务解耦——前者只负责 HTTP 请求+埋点，后者负责请求组装和响应解析。

## 5. 建议补充信息

1. CloudWatch Admin API 的完整文档（接口规范、字段约束）
2. `ep_in_bw` / `ep_out_bw` 指标的采样频率和精度
3. 梯形积分法在流量采样率不均匀时的误差分析
4. 重试策略在 CloudWatch 服务不可用时的退避行为

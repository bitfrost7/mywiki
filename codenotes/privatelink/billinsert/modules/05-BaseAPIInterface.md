# billinsert - module 05: Base API Interface

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 11** (4 nodes, 凝聚力 0.25)
> **验证状态**: ✓ | **来源文件**: `factory/common/common.go`

---

## 1. 模块职责

Base API Interface 定义了 billinsert 中所有外部 API 请求/响应的 **基类接口**，提供：

- **请求基类**：包含 `Backend`（网关注册 ID）、`Action`（API 名称）、`RequestUUID`
- **响应基类**：包含 `RetCode`（返回码）、`Message`（错误信息）
- **接口抽象**：`IBaseRequest` 获取 Action/Backend，`IBaseResponse` 获取 RetCode
- **Prometheus 埋点支持**：`APIRequestWithMetrics()` 通过接口获取 Action/Backend 和 RetCode 上报指标

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `BaseRequest` | `factory/common/common.go:4-8` | 结构体 | 请求基类（Backend, Action, RequestUUID） |
| `BaseResponse` | `factory/common/common.go:10-14` | 结构体 | 响应基类（Action, RetCode, Message） |
| `BaseRequest.GetAction()` | `factory/common/common.go:17-19` | 方法 | 获取 Action 名称 |
| `BaseRequest.GetBackend()` | `factory/common/common.go:21-23` | 方法 | 获取 Backend 名称 |
| `BaseResponse.GetRetCode()` | `factory/common/common.go:25-27` | 方法 | 获取返回码 |
| `IBaseRequest` | `factory/common/common.go:29-32` | 接口 | 请求接口（GetAction, GetBackend） |
| `IBaseResponse` | `factory/common/common.go:34-36` | 接口 | 响应接口（GetRetCode） |

## 3. 关键实现逻辑

### 3.1 接口设计

```go
type IBaseRequest interface {
    GetAction() string
    GetBackend() string
}

type IBaseResponse interface {
    GetRetCode() int
}
```

通过接口抽象，`APIRequestWithMetrics()` 可以统一处理所有 API 请求/响应的埋点逻辑，而无需关心具体结构体：

```go
func (i *CloudwatchImpl) APIRequestWithMetrics(ctx context.Context, req common.IBaseRequest, resp common.IBaseResponse, timeout ...uint32) (err error) {
    backend, action := req.GetBackend(), req.GetAction()
    xpro.ClientRequestSentTotal.WithLabelValues("api", backend, action).Inc()
    // ...
    defer func() {
        xpro.ClientResponseReceivedTotal.WithLabelValues("api", backend, action, strconv.Itoa(resp.GetRetCode())).Inc()
        // ...
    }()
}
```

### 3.2 与其他模块的关联

- `QueryMonitorDataRequest` 内嵌了 `common.BaseRequest`（`factory/cloudwatch/basic.go:16`）
- `QueryMonitorDataResponse` 内嵌了 `common.BaseResponse`（`factory/cloudwatch/basic.go:33`）
- `APIRequestWithMetrics()` 接受 `IBaseRequest` / `IBaseResponse` 接口参数

### 3.3 嵌入关系

```
BaseRequest                BaseResponse
  ├─ Backend                 ├─ Action
  ├─ Action                  ├─ RetCode
  └─ RequestUUID             └─ Message
        │                          │
        ▼                          ▼
QueryMonitorDataRequest     QueryMonitorDataResponse
  ├─ (嵌入 BaseRequest)       ├─ (嵌入 BaseResponse)
  ├─ Region                   ├─ TraceId
  ├─ StartTime                └─ Data *MonitorDataResult
  ├─ EndTime
  ├─ ProductKey
  ├─ CalcMethod
  ├─ Period
  └─ Selectors
```

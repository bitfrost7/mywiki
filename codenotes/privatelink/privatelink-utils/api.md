# API 文档

> 本库作为 utility library，不暴露网络 API（无 gRPC/REST 端点）。以下文档覆盖所有可导出的函数、类型和方法。

---

## 包 1: `gorm/plugin` — Prometheus 数据库监控

**源文件**: `gorm/plugin/prometheus.go`

### 类型定义

#### `Config`

监控配置结构体。

| 字段 | 类型 | 说明 |
|------|------|------|
| `DBStatCollectInterval` | `int` | 数据库连接池状态采集间隔（秒），默认 10 秒 |
| `DBStatCollector` | `DBStatCollector` | 连接池状态采集回调函数 |
| `DBBeforeMetricCollector` | `CustomMetricCollector` | 操作前指标采集回调 |
| `DBAfterMetricCollector` | `CustomMetricCollector` | 操作后指标采集回调 |

**位置**: `gorm/plugin/prometheus.go:30-39`

---

#### `CustomMetric`

SQL 执行指标的单个数据点。

| 字段 | 类型 | 说明 |
|------|------|------|
| `Action` | `string` | 数据库操作类型（如 "create", "query", "update", "delete", "row", "raw"） |
| `Table` | `string` | 操作涉及的表名 |
| `Result` | `bool` | 操作是否成功（`db.Statement.Error == nil`） |
| `Duration` | `time.Duration` | 操作耗时 |

**位置**: `gorm/plugin/prometheus.go:11-20`

---

#### `DBStatCollector`

```go
type DBStatCollector func(stat *sql.DBStats)
```

函数类型，用于采集 `database/sql.DBStats` 连接池统计信息。用户在此函数中实现自定义的指标上报逻辑。

**位置**: `gorm/plugin/prometheus.go:24`

---

#### `CustomMetricCollector`

```go
type CustomMetricCollector func(data *CustomMetric)
```

函数类型，用于采集 SQL 执行指标（表名、操作类型等）。用户在此函数中实现自定义的指标上报逻辑。

**位置**: `gorm/plugin/prometheus.go:28`

---

#### `PrometheusMonitor`

```go
type PrometheusMonitor struct {
    cfg *Config  // 未导出：配置引用
}
```

监控实例，包含配置和运行时状态。

**位置**: `gorm/plugin/prometheus.go:41-43`

---

### 函数

#### `NewMonitor(config *Config) *PrometheusMonitor`

创建并返回一个新的 `PrometheusMonitor` 实例。

- **参数**: `config` — 监控配置（非 nil）
- **返回值**: 初始化后的监控实例
- **位置**: `gorm/plugin/prometheus.go:45-49`

---

### 方法

#### `(*PrometheusMonitor) Name() string`

返回插件名称 `"prometheus_monitor"`。实现 GORM `Plugin` 接口。

**位置**: `gorm/plugin/prometheus.go:51-53`

---

#### `(*PrometheusMonitor) Initialize(db *gorm.DB) error`

GORM `Plugin` 接口入口。调用流程：

1. 若 `DBStatCollector` 非 nil，启动连接池状态采集协程（默认间隔 10 秒）
2. 调用 `RegisterCallback` 注册操作回调

**位置**: `gorm/plugin/prometheus.go:140-149`

---

#### `(*PrometheusMonitor) RegisterCallback(db *gorm.DB) error`

为 6 种操作（Create / Update / Query / Delete / Row / Raw）各注册 before/after 回调，共 12 个回调点。

- 每个 before 回调调用 `dbBeforeOperation(action)`
- 每个 after 回调调用 `dbAfterOperation(action)`

**位置**: `gorm/plugin/prometheus.go:95-138`

---

#### `(*PrometheusMonitor) CollectDBStatus(db *gorm.DB)`

启动一个后台协程，使用 `time.Ticker` 按配置间隔周期性采集 `sql.DBStats`。

**位置**: `gorm/plugin/prometheus.go:55-67`

---

#### `(*PrometheusMonitor) dbBeforeOperation(action string) func(db *gorm.DB)`

返回一个 GORM 回调函数，在操作前记录 `start_time` 到 GORM session。

**位置**: `gorm/plugin/prometheus.go:69-77`

---

#### `(*PrometheusMonitor) dbAfterOperation(action string) func(db *gorm.DB)`

返回一个 GORM 回调函数，在操作后计算耗时并调用 `DBAfterMetricCollector`。

**位置**: `gorm/plugin/prometheus.go:79-93`

---

## 包 2: `httpclient` — HTTP 客户端封装

**源文件**: `httpclient/httpclient.go`

### 类型定义

#### `Config`

HTTP 客户端配置。

| 字段 | 类型 | 说明 |
|------|------|------|
| `Proxy` | `string` | 代理地址（非空时所有请求转发到该代理） |
| `Timeout` | `uint32` | 超时时间（秒），0 表示不设超时 |

**位置**: `httpclient/httpclient.go:23-26`

---

#### `HTTPClient`

```go
type HTTPClient struct {
    Config *Config
    cli    *http.Client  // 未导出：标准库 HTTP 客户端
}
```

封装后的 HTTP 客户端。

**位置**: `httpclient/httpclient.go:28-31`

---

#### `HTTPResp`

统一 HTTP 响应结构。

| 字段 | 类型 | 说明 |
|------|------|------|
| `StatusCode` | `int` | HTTP 状态码 |
| `Body` | `[]byte` | 响应体原始字节 |

**位置**: `httpclient/httpclient.go:33-36`

---

### 函数

#### `NewHTTPClient(cfg *Config) *HTTPClient`

创建并返回一个新的 HTTP 客户端实例。

**位置**: `httpclient/httpclient.go:39-44`

---

### 方法（无上下文）

#### `(*HTTPClient) Native() *http.Client`

返回内部的标准库 `*http.Client`，允许直接操作底层客户端。

**位置**: `httpclient/httpclient.go:46-48`

---

#### `(*HTTPClient) Do(headers map[string]string, method, url string, body io.Reader, timeout ...uint32) (*HTTPResp, error)`

核心执行器。流程：

1. 使用 `context.Background()` 创建上下文
2. 若指定了 `timeout` 或配置了 `Config.Timeout`，设置超时上下文
3. 若配置了 `Proxy`，将 URL 替换为代理地址
4. 创建 `http.Request` 并设置请求头
5. 调用 `cli.Do()` 发送请求
6. 读取完整响应体
7. 返回 `HTTPResp` 结构

**位置**: `httpclient/httpclient.go:94-133`

---

#### `(*HTTPClient) Get(headers map[string]string, url string, timeout ...uint32) (*HTTPResp, error)`

发送 GET 请求。委托给 `h.Do(headers, http.MethodGet, url, nil, timeout...)`。

**位置**: `httpclient/httpclient.go:50-52`

---

#### `(*HTTPClient) GetJSON(url string, resp any, timeout ...uint32) error`

发送 GET 请求并直接反序列化 JSON 响应。

- 自动设置 `Content-Type: application/json`
- 校验状态码为 200
- 将响应体 JSON 反序列化到 `resp` 参数

**位置**: `httpclient/httpclient.go:55-68`

---

#### `(*HTTPClient) PostBytes(headers map[string]string, url string, body []byte, timeout ...uint32) (*HTTPResp, error)`

发送 POST 请求，请求体为原始字节。委托给 `h.Do(headers, http.MethodPost, url, bytes.NewReader(body), timeout...)`。

**位置**: `httpclient/httpclient.go:70-72`

---

#### `(*HTTPClient) PostJSON(url string, req, resp any, timeout ...uint32) error`

发送 POST 请求，请求体和响应体均为 JSON。

1. `json.Marshal(req)` 序列化请求体
2. `PostBytes` 发送
3. 校验状态码为 200
4. `json.Unmarshal` 反序列化响应体到 `resp`

**位置**: `httpclient/httpclient.go:75-92`

---

### 方法（上下文感知）

#### `(*HTTPClient) PostCtx(ctx context.Context, url string, req, resp any, timeout ...uint32) error`

带上下文的 POST 请求。委托给 `PostCtxWithHeader(ctx, url, nil, req, resp, timeout...)`。

- **ctx** 需被 `ucontext.ToLoggerContext` 封装过，以便提取日志上下文
- 内部通过 `ncontext.ExtractSessionIDFromCtx(ctx)` 提取 session ID 用于日志

**位置**: `httpclient/httpclient.go:137-139`

---

#### `(*HTTPClient) PostCtxWithHeader(ctx context.Context, url string, header map[string]string, req, resp any, timeout ...uint32) error`

带自定义 Header 的上下文感知 POST 请求。

1. 提取 session ID 构造结构化日志
2. JSON 序列化请求体
3. 合并自定义 Header
4. 调用 `PostBytes` 发送
5. 校验状态码
6. JSON 反序列化响应体

**位置**: `httpclient/httpclient.go:162-196`

---

#### `(*HTTPClient) PostCtxWithZkPath(ctx context.Context, zkCli *zkutils.ZKClient, zkPath, path string, hdr map[string]string, req, resp any, timeout ...uint32) error`

通过 ZooKeeper 服务发现地址后发送 POST 请求。

1. 使用 `zkresolver.NewNameResolver` + `zkresolver.NewZKPlugin` 解析 ZK 路径
2. `zk.ResolveRandom(wraper)` 随机获取一个后端地址
3. 构造 `http://{addr}/{path}` URL
4. 委托 `PostCtxWithHeader` 发送请求

**位置**: `httpclient/httpclient.go:143-158`

---

## 包 3: `ncontext` — 会话上下文工具

**源文件**: `ncontext/ncontext.go`

### 类型定义

#### `contextKey`

```go
type contextKey int
```

未导出类型，用于 context.WithValue 的 key，防止 key 冲突。

**位置**: `ncontext/ncontext.go:9`

---

### 变量

| 变量 | 类型 | 值 | 说明 |
|------|------|----|------|
| `SessionID` | `string` | `"session_id"` | 日志字段名，供 zap 日志使用 |
| `KeyForSessionID` | `contextKey` | `100` | context 中存储 session ID 的 key |

**位置**: `ncontext/ncontext.go:12-15`

---

### 函数

#### `SessionIDToContext(ctx context.Context, sessionID string) context.Context`

将指定的 session ID 存入 context 并返回新的 context。

- **参数**: `ctx` — 父上下文；`sessionID` — 要存入的会话 ID
- **返回值**: 包含 session ID 的新上下文

**位置**: `ncontext/ncontext.go:17-19`

---

#### `NewSessionIDToContext(ctx context.Context) context.Context`

生成一个新的 session ID 并存入 context。

- 内部调用 `ucontext.NewRequestID()` 生成唯一 ID
- 等效于 `SessionIDToContext(ctx, ucontext.NewRequestID())`

**位置**: `ncontext/ncontext.go:21-23`

---

#### `ExtractSessionIDFromCtx(ctx context.Context) string`

从 context 中提取 session ID。

- 若上下文中无 session ID，返回空字符串 `""`
- 返回值类型为 `string`

**位置**: `ncontext/ncontext.go:25-31`

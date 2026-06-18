# 模块 02：HTTP 客户端核心

## 概述

该模块对应图分析 **Community 3「HTTP Client」**（4 个节点）、**Community 4「HTTP Response」**（5 个节点）、**Community 6「HTTP Client Config」**（3 个节点）。提供基于标准库 `net/http` 的轻量级 HTTP 客户端封装，支持代理转发、超时控制、JSON 序列化便捷方法。

## 源文件

- **`httpclient/httpclient.go`** — 完整实现（196 行）

## 核心结构体

### Config — 客户端配置 (`httpclient.go:23-26`)

```go
type Config struct {
    Proxy   string
    Timeout uint32
}
```

- **`Proxy`** — 代理地址。非空时，所有请求的 URL 会被替换为代理地址
- **`Timeout`** — 请求超时时间（秒）。0 表示不设超时

**图分析归属**：Community 6「HTTP Client Config」。该社区还包含 `NewHTTPClient()` 函数和 `httpclient.go` 文件节点，代表配置的创建与定义紧密关联。

### HTTPClient — 客户端结构 (`httpclient.go:28-31`)

```go
type HTTPClient struct {
    Config *Config
    cli    *http.Client  // 未导出
}
```

封装了配置与底层 `*http.Client`。`Config` 字段公开暴露，允许外部在创建后修改配置。

**图分析归属**：Community 3「HTTP Client」。该社区还包括：
- `Client` — 标准库 `*http.Client`（内部字段类型引用）
- `Native()` 方法 — 暴露底层客户端
- `PostBytes()`/`PostJSON()` 方法 — POST 请求便捷封装

### HTTPResp — 统一响应结构 (`httpclient.go:33-36`)

```go
type HTTPResp struct {
    StatusCode int
    Body       []byte
}
```

统一 HTTP 响应结构。所有返回 `(*HTTPResp, error)` 的方法都使用此结构。

**图分析归属**：Community 4「HTTP Response」。该社区还包括 `Get()`、`GetJSON()`、`Do()` 方法以及 `io.Reader` 类型引用——这些方法要么返回 `*HTTPResp`，要么接收 `io.Reader` 类型参数。

## 核心方法

### 构造与基础

#### NewHTTPClient — 构造器 (`httpclient.go:39-44`)

```go
func NewHTTPClient(cfg *Config) *HTTPClient
```

创建 `HTTPClient` 实例。初始化内部的 `*http.Client` 为空的 `&http.Client{}`，用户可通过 `Config.Proxy` 和 `Config.Timeout` 控制请求行为。

#### Native — 暴露底层客户端 (`httpclient.go:46-48`)

```go
func (h *HTTPClient) Native() *http.Client
```

返回内部的标准库 `*http.Client`。当封装方法的灵活度不足时，调用方可以直接操作底层客户端。

### 核心执行器

#### Do — 核心请求执行 (`httpclient.go:94-133`)

```go
func (h *HTTPClient) Do(headers map[string]string, method, url string, body io.Reader, timeout ...uint32) (*HTTPResp, error)
```

所有请求方法的最终委托目标。执行流程：

1. **上下文创建**：使用 `context.Background()` 创建基础上下文
2. **超时设置**：若传入了 `timeout` 变参或 `Config.Timeout > 0`，创建带有超时的子上下文（`context.WithTimeout`）
3. **代理替换**：若 `Config.Proxy` 非空，将 `url` 替换为代理地址
4. **请求构造**：`http.NewRequestWithContext(ctx, strings.ToUpper(method), url, body)` —— 注意方法会被自动转为大写
5. **设置请求头**：遍历 `headers` map 设置到 `request.Header`
6. **发送请求**：`h.cli.Do(request)`
7. **读取响应**：`io.ReadAll(response.Body)`，返回 `&HTTPResp{StatusCode, Body}`

**错误处理**：`request` 创建失败或 `cli.Do` 调用失败均返回 error。调用方负责检查 `HTTPResp.StatusCode`。

**图分析关系**：`Do()` 方法（Community 4）引用 `io.Reader` 参数类型（Community 4 的 `Reader` 节点），被 `Get`、`GetJSON`、`PostBytes` 等方法调用。

### GET 方法

#### Get — 原始 GET (`httpclient.go:50-52`)

```go
func (h *HTTPClient) Get(headers map[string]string, url string, timeout ...uint32) (*HTTPResp, error)
```

发送 HTTP GET 请求。委托给 `h.Do(headers, http.MethodGet, url, nil, timeout...)`。

#### GetJSON — JSON GET (`httpclient.go:55-68`)

```go
func (h *HTTPClient) GetJSON(url string, resp any, timeout ...uint32) error
```

发送 GET 请求并自动解析 JSON 响应。

1. 设置 `Content-Type: application/json`
2. 调用 `h.Do()` 发送 GET 请求
3. 检查状态码是否为 200，非 200 返回包含状态码文本的错误
4. `json.Unmarshal(httpResp.Body, resp)` 反序列化

### POST 方法

#### PostBytes — 原始 POST (`httpclient.go:70-72`)

```go
func (h *HTTPClient) PostBytes(headers map[string]string, url string, body []byte, timeout ...uint32) (*HTTPResp, error)
```

发送 POST 请求，请求体为原始字节。委托给 `h.Do(headers, http.MethodPost, url, bytes.NewReader(body), timeout...)`。

#### PostJSON — JSON POST (`httpclient.go:75-92`)

```go
func (h *HTTPClient) PostJSON(url string, req, resp any, timeout ...uint32) error
```

发送 POST 请求，请求体和响应体均为 JSON。

1. `json.Marshal(req)` 序列化请求体
2. 调用 `h.PostBytes()` 发送
3. 检查状态码是否为 200
4. `json.Unmarshal(httpResp.Body, resp)` 反序列化响应体

## 图分析社区归属

### Community 3 — HTTP Client（客户端核心）

| 节点 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `HTTPClient` | struct | `httpclient.go:28` | 客户端结构体 |
| `Client` | field type | `httpclient.go:30` | `*http.Client` 内部字段 |
| `.Native()` | method | `httpclient.go:46` | 暴露底层客户端 |
| `.PostBytes()` | method | `httpclient.go:70` | 原始字节 POST |
| `.PostJSON()` | method | `httpclient.go:75` | JSON POST |

### Community 4 — HTTP Response（响应处理）

| 节点 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `HTTPResp` | struct | `httpclient.go:33` | 统一响应结构 |
| `.Get()` | method | `httpclient.go:50` | GET 请求 |
| `.GetJSON()` | method | `httpclient.go:55` | JSON GET |
| `.Do()` | method | `httpclient.go:94` | 核心执行器 |
| `Reader` | param type | `httpclient.go:94` | `io.Reader` 参数引用 |

### Community 6 — HTTP Client Config（配置）

| 节点 | 类型 | 位置 | 说明 |
|------|------|------|------|
| `httpclient.go` | file | `httpclient.go:1` | 文件节点 |
| `Config` | struct | `httpclient.go:23` | 配置结构体 |
| `NewHTTPClient()` | function | `httpclient.go:39` | 构造器 |

## 使用示例

```go
import "git.ucloudadmin.com/unetworks/privatelink/privatelink-utils/httpclient"

// 1. 创建 HTTP 客户端
cfg := &httpclient.Config{
    Timeout: 30, // 30 秒超时
}
cli := httpclient.NewHTTPClient(cfg)

// 2. GET 请求 + JSON 反序列化
var result map[string]interface{}
err := cli.GetJSON("http://example.com/api/v1/status", &result)

// 3. POST 请求 + JSON 交互
type Request struct {
    Name string `json:"name"`
}
type Response struct {
    ID string `json:"id"`
}
req := &Request{Name: "test"}
var resp Response
err = cli.PostJSON("http://example.com/api/v1/create", req, &resp)
```

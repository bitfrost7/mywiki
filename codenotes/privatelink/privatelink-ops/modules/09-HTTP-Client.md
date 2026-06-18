# 模块: HTTP 客户端

> 社区 #9 — 15 节点 · HTTP Client

---

## 概述

本模块实现通用 HTTP 客户端，封装了 GET/POST 请求和 JSON 序列化/反序列化。它被 `ResourceImpl`（模块 08）用于与 UResource 内部 API 通信。支持配置代理、超时控制和请求链路日志注入。

---

## 文件索引

**`httpclient/httpclient.go:1-166`**

### 配置与结构体

| 类型/常量 | 行号 | 说明 |
|-----------|------|------|
| `DefaultTimeout` | `:19` | 默认超时：10 秒 |
| `Config` | `:22` | 客户端配置：`Proxy`（代理地址）、`Timeout`（超时秒数） |
| `HTTPClient` | `:27` | HTTP 客户端结构体：封装 `*http.Client` |
| `HTTPResp` | `:32` | HTTP 响应结构体：`StatusCode` + `Body`（[]byte） |

### 构造函数

**`httpclient/httpclient.go:38-43`** — `NewHTTPClient()`

```go
func NewHTTPClient(cfg *Config) *HTTPClient {
    return &HTTPClient{
        Config: cfg,
        cli:    &http.Client{},
    }
}
```

### 基础 HTTP 方法

| 方法 | 行号 | 说明 |
|------|------|------|
| `Native()` | `:45` | 返回原生 `*http.Client` |
| `Get()` | `:49` | GET 请求 |
| `PostBytes()` | `:69` | POST 原始字节 |
| `Do()` | `:93` | **核心方法**：执行 HTTP 请求 |

### JSON 辅助方法

| 方法 | 行号 | 说明 |
|------|------|------|
| `GetJSON()` | `:54` | GET 请求，自动反序列化 JSON 响应 |
| `PostJSON()` | `:74` | POST JSON 请求，自动序列化请求体 + 反序列化响应 |
| `PostCtx()` | `:136` | **带 Context 的 POST**：注入日志 + SessionID → PostBytes |

### 核心 Do 方法

**`httpclient/httpclient.go:93-132`** — `Do()`

```go
func (h *HTTPClient) Do(headers map[string]string, method, url string, body io.Reader, timeout ...uint32) (*HTTPResp, error) {
    ctx := context.Background()
    to := h.Config.Timeout
    if len(timeout) > 0 {
        to = timeout[0]                        // :96-98 调用方可覆盖超时
    }
    if to != 0 {
        var cancelf func()
        ctx, cancelf = context.WithTimeout(ctx, time.Duration(to)*time.Second)  // :101
        defer cancelf()
    }
    if h.Config.Proxy != "" {
        url = h.Config.Proxy                   // :106 — 代理地址替换原始 URL
    }

    request, err := http.NewRequestWithContext(ctx, strings.ToUpper(method), url, body)  // :109
    for key, val := range headers {
        request.Header.Set(key, val)           // :114-116 — 设置请求头
    }

    response, err := h.cli.Do(request)          // :118 — 执行请求
    defer response.Body.Close()
    all, err := io.ReadAll(response.Body)       // :123 — 读取响应体
    return &HTTPResp{StatusCode: response.StatusCode, Body: all}, nil
}
```

### 带 Context 的 POST

**`httpclient/httpclient.go:136-166`** — `PostCtx()`

专为资源系统调用设计的方法，主要特性：

1. **日志注入**：从 Context 提取 Logger，追加 `session_id` 字段
2. **请求/响应日志**：记录完整的请求 URL、Header、Body 和响应 Body
3. **状态码校验**：非 200 时返回错误
4. **自动序列化**：自动 JSON 序列化请求体 + 反序列化响应体

```go
func (h *HTTPClient) PostCtx(ctx context.Context, url string, req, resp any, timeout ...uint32) error {
    l := ucontext.Logger(ctx).With(zap.String(ncontext.SessionID, ...))
    b, _ := json.Marshal(req)
    l.Infow("http request", "header", hdr, "url", url, "body", string(b))

    httpResp, err := h.PostBytes(hdr, url, b, timeout...)
    if httpResp.StatusCode != http.StatusOK {
        return fmt.Errorf("post json with status code: %d, ...", httpResp.StatusCode, ...)
    }
    l.Infow("http response", "resp", string(httpResp.Body))

    json.Unmarshal(httpResp.Body, resp)
    return nil
}
```

---

## 调用场景

本模块在 **`server.go:62`** 中创建：

```go
httpCli := httpclient.NewHTTPClient(&cfg.HTTPConfig)
```

然后注入到 `uresource.NewUResourceImpl(cfg.InternalAPIURL, httpCli)` 中，用于所有 UResource API 调用。

**全部调用链路**：

```
ResourceImpl.APIRequest(ctx, req, resp)    — factory/uresource/basic.go:40
  └─ httpclient.PostCtx(ctx, url, req, resp)  — httpclient.go:136
       ├─ 日志记录（请求）
       ├─ json.Marshal(req) → PostBytes() → Do()
       │    └─ Do() → http.Client.Do()  — 实际 HTTP 调用
       ├─ 日志记录（响应）
       └─ json.Unmarshal(body, resp)
```

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `HTTPClient` | Application Server (M01) | 在 NewServer 中创建 |
| `PostCtx()` | Resource Label Operations (M08) | UResource API 通过此方法调用 |
| `ncontext.SessionID` | Context Utilities (M10) | 日志中注入 SessionID |

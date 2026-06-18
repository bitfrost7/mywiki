# 架构文档

## 整体架构

`privatelink-utils` 是一个**轻量级的 Go 工具库**，以库的形式（library）被外部服务引用，不独立部署。其架构分为三个独立的工具模块：

```
┌─────────────────────────────────────────────────────┐
│                 External Application                │
│       (直接 import 各子包，按需使用)                   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Module 1: GORM Prometheus 监控插件           │   │
│  │  gorm/plugin/prometheus.go                   │   │
│  │  ┌──────────┐  ┌──────────────────────┐      │   │
│  │  │ Config   │  │ PrometheusMonitor    │      │   │
│  │  │ (配置)   │──│ .Initialize()        │      │   │
│  │  │          │  │ .RegisterCallback()  │      │   │
│  │  │          │  │ .CollectDBStatus()   │      │   │
│  │  │          │  │ .dbBeforeOperation() │      │   │
│  │  │          │  │ .dbAfterOperation()  │      │   │
│  │  └──────────┘  └──────────────────────┘      │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Module 2: HTTP 客户端                        │   │
│  │  httpclient/httpclient.go                    │   │
│  │  ┌──────────┐  ┌──────────────────────┐      │   │
│  │  │ Config   │  │ HTTPClient           │      │   │
│  │  │ (代理/   │──│ .Get() / .GetJSON()  │      │   │
│  │  │  超时)   │  │ .PostBytes()/.Post() │      │   │
│  │  └──────────┘  │ .Do() ← 核心执行器   │      │   │
│  │                │ .Native()            │      │   │
│  │                └──────────────────────┘      │   │
│  │  ┌──────────────┐                            │   │
│  │  │ HTTPResp     │ ← 统一响应结构              │   │
│  │  │ StatusCode   │                            │   │
│  │  │ Body []byte  │                            │   │
│  │  └──────────────┘                            │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │  Module 3: 会话上下文工具                     │   │
│  │  ncontext/ncontext.go                        │   │
│  │  ┌──────────────────────────────┐            │   │
│  │  │ contextKey (int)            │            │   │
│  │  │ SessionID = "session_id"    │            │   │
│  │  │ SessionIDToContext()        │            │   │
│  │  │ NewSessionIDToContext()     │            │   │
│  │  │ ExtractSessionIDFromCtx()   │            │   │
│  │  └──────────────────────────────┘            │   │
│  │                                               │   │
│  │  httpclient 中的上下文感知方法:                │   │
│  │  .PostCtx() → .PostCtxWithHeader()           │   │
│  │            → .PostCtxWithZkPath()             │   │
│  └──────────────────────────────────────────────┘   │
│                                                     │
├─────────────────────────────────────────────────────┤
│                External Dependencies                │
│  ┌───────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │   GORM    │ │  net/http│ │  ZooKeeper/zkres │   │
│  │ (gorm.io) │ │(标准库)  │ │(企业内部 nameres)│   │
│  └───────────┘ └──────────┘ └──────────────────┘   │
│  ┌───────────┐ ┌──────────┐                        │
│  │  ucontext │ │   zap   │                        │
│  │(企业内部)  │ │(日志)    │                        │
│  └───────────┘ └──────────┘                        │
└─────────────────────────────────────────────────────┘
```

## 模块间的依赖关系

三个模块彼此**独立**（无内部直接依赖），但通过共享的上下文约定间接关联：

```
ncontext (会话上下文工具)
    │
    │ 被 httpclient 模块引用
    ▼
httpclient (HTTP 客户端 — PostCtx 系列方法使用 ncontext.ExtractSessionIDFromCtx)
    │
    │ 无直接依赖
    ▼
gorm/plugin (Prometheus 监控插件 — 完全独立)
```

## 数据流

### 1. GORM 监控插件数据流

```
GORM DB 操作（Create/Update/Query/Delete/Row/Raw）
    │
    ├─► before 回调: dbBeforeOperation(action)
    │     └─► 记录开始时间到 db.Set("start_time", time.Now())
    │     └─► 调用 DBBeforeMetricCollector(&CustomMetric{Action, Table})
    │
    └─► after 回调: dbAfterOperation(action)
          └─► 从 db.Get("start_time") 取出开始时间
          └─► 计算 time.Since(startTime)
          └─► 调用 DBAfterMetricCollector(&CustomMetric{Action, Table, Result, Duration})
```

### 2. HTTP 客户端数据流

```
调用方
    │
    ├─► .PostCtx(ctx, url, req, resp)
    │     └─► .PostCtxWithHeader(ctx, url, nil, req, resp)
    │           ├─► 提取 session_id: ncontext.ExtractSessionIDFromCtx(ctx)
    │           ├─► JSON 序列化请求体
    │           ├─► 日志记录请求
    │           ├─► .PostBytes(hdr, url, body)  ← 实际发送
    │           │     └─► .Do(hdr, POST, url, body)
    │           │           ├─► 设置超时上下文
    │           │           ├─► 若配置了 Proxy，替换 URL
    │           │           ├─► http.NewRequestWithContext()
    │           │           ├─► h.cli.Do(request)
    │           │           └─► io.ReadAll(response.Body) → HTTPResp
    │           ├─► 校验状态码
    │           ├─► 日志记录响应
    │           └─► JSON 反序列化响应体
    │
    └─► .PostCtxWithZkPath(ctx, zkCli, zkPath, path, hdr, req, resp)
          ├─► 通过 zkresolver 解析 ZK 路径 → 获取真实 IP 地址
          ├─► 构造 http://{addr}/{path} URL
          └─► 委托 .PostCtxWithHeader() 发送请求
```

### 3. Session ID 上下文数据流

```
外部请求进入
    │
    ├─► 创建上下文:
    │     NewSessionIDToContext(ctx)    ← 自动生成新 session ID
    │     或
    │     SessionIDToContext(ctx, id)   ← 从外部传入已有 session ID
    │
    └─► 后续调用:
          ExtractSessionIDFromCtx(ctx)  → "session_id_xxxx"
          │
          └─► 传递给 zap 日志:
                l.With(zap.String(ncontext.SessionID, sessionID))
```

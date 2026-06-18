# privatelink-utils — PrivateLink 公共工具库

> 代码注释文档。基于图分析（graph.json）社区聚类和源文件分析生成。

## 项目概述

`privatelink-utils` 是一个 **Go 公共工具库（Utility Library）**，属于 UCloud PrivateLink 产品体系。它以库的形式提供三个核心能力：

1. **GORM Prometheus 监控插件** — 通过 GORM 回调机制采集数据库操作耗时、连接池状态等指标
2. **HTTP 客户端封装** — 基于 `net/http` 的轻量级封装，支持超时、代理、JSON 序列化、ZooKeeper 服务发现
3. **会话上下文工具** — Session ID 在 `context.Context` 中的存取与传递，支持请求链路追踪

## 技术栈

| 组件 | 用途 |
|------|------|
| **Go 1.18+** | 开发语言 |
| **GORM** | 数据库 ORM（监控插件的回调钩子） |
| **Prometheus** | 指标采集（通过回调函数向用户暴露） |
| **ZooKeeper** | 服务发现（通过 ZK 解析后端地址） |
| **zap** | 结构化日志 |
| **ucontext** | 企业内部上下文/日志封装 |

## 项目结构

```
privatelink-utils/
├── gorm/plugin/prometheus.go       # GORM 数据库监控插件（149 行）
├── httpclient/httpclient.go        # HTTP 客户端封装（196 行）
├── ncontext/ncontext.go            # 会话上下文工具（31 行）
├── README.md                       # 本文件
├── go.mod
└── go.sum
```

## 图分析社区总览

图分析将代码划分为 **8 个社区**，覆盖 3 个源文件：

| 社区编号 | 社区名称 | 节点数 | 对应源文件 | 模块 |
|---------|---------|--------|-----------|------|
| 0 | Database Monitoring | 7 | `gorm/plugin/prometheus.go` | Module 01 |
| 1 | Metrics Configuration | 6 | `gorm/plugin/prometheus.go` | Module 01 |
| 2 | Session Context | 4 | `httpclient/httpclient.go` + `ncontext/ncontext.go` | Module 03 |
| 3 | HTTP Client | 4 | `httpclient/httpclient.go` | Module 02 |
| 4 | HTTP Response | 5 | `httpclient/httpclient.go` | Module 02 |
| 5 | Session Context Keys | 4 | `ncontext/ncontext.go` | Module 03 |
| 6 | HTTP Client Config | 3 | `httpclient/httpclient.go` | Module 02 |
| 7 | Private Link Library | 1 | `README.md` | — |

## 调用链

```
应用代码
  │
  ├─► gorm/plugin/prometheus.go:NewMonitor(config)    ← 创建监控
  │     └─► .Initialize(db)                           ← 注册 GORM 回调
  │           ├─► .CollectDBStatus(db)                 ← 启动连接池状态采集协程
  │           └─► .RegisterCallback(db)                ← 注册 before/after 回调
  │                 ├─► .dbBeforeOperation(action)     ← 操作前记录开始时间
  │                 └─► .dbAfterOperation(action)      ← 操作后计算耗时
  │
  ├─► httpclient/httpclient.go:NewHTTPClient(cfg)     ← 创建 HTTP 客户端
  │     ├─► .Get() / .GetJSON()                       ← GET 请求（委托 .Do()）
  │     ├─► .PostBytes() / .PostJSON()                 ← POST 请求（委托 .Do()）
  │     ├─► .Do()                                      ← 核心执行方法
  │     ├─► .PostCtx(ctx, ...)                         ← 带上下文的 POST
  │     ├─► .PostCtxWithHeader(ctx, ...)               ← 带自定义 Header 的 POST
  │     └─► .PostCtxWithZkPath(ctx, zkCli, ...)       ← 通过 ZK 发现地址的 POST
  │
  └─► ncontext/ncontext.go                             ← Session ID 上下文工具
        ├─► SessionIDToContext(ctx, sessionID)
        ├─► NewSessionIDToContext(ctx)
        └─► ExtractSessionIDFromCtx(ctx)
```

## 各模块文档

| 文档 | 对应社区 | 说明 |
|------|---------|------|
| [modules/01-GORM-Prometheus-数据库监控插件.md](modules/01-GORM-Prometheus-数据库监控插件.md) | Communities 0, 1 | Prometheus 监控插件：类型定义与运行时方法 |
| [modules/02-HTTP-客户端核心.md](modules/02-HTTP-客户端核心.md) | Communities 2, 3, 4, 6 | HTTP 客户端：配置、核心结构、请求方法 |
| [modules/03-会话上下文与链路追踪.md](modules/03-会话上下文与链路追踪.md) | Communities 2, 5 | ncontext 工具 + HTTP 上下文感知方法 |

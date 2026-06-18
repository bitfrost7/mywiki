# 模块: 应用服务器与启动入口

> 社区 #8 — 26 节点 · 凝聚系数低 · Application Configuration

---

## 概述

本模块涵盖 privatelink-ops 服务的启动入口、配置加载和服务器的生命周期管理。`cmd/main.go` 是二进制入口点，`server.go` 定义核心 `Server` 结构体并组装所有依赖（数据库、HTTP 客户端、工厂、API 路由）。工厂模式（`factory/`）用于初始化外部系统集成组件。

---

## 文件索引

### CLI 入口

**`cmd/main.go:18-88`** — 主入口

| 函数/变量 | 行号 | 说明 |
|-----------|------|------|
| `main()` | `:18` | 入口函数，解析 flag `-c` 指定配置路径；按子命令分发（start / dumpcfg / version） |
| `runServer()` | `:43` | 加载配置 → `NewServer(cfg)` → `s.Start()` |
| `loadConfig()` | `:53` | 读取 JSON 配置文件 → `ioutil.ReadFile` + `json.Unmarshal` |
| `dumpConfig()` | `:65` | 打印默认配置模板（用于生成初始配置文件） |
| `showVerson()` | `:73` | 打印 Prometheus 版本信息（注意函数名 typo "Verson"） |
| `usage()` | `:77` | 打印命令行使用说明 |
| `init()` | `:86` | 注册 Prometheus 版本指标收集器 |

**启动流程**（**`cmd/main.go:18-51`**）：

```
$ privatelink-ops -c conf/config.json start
  → main() :18
    → runServer() :43
      → loadConfig() :53 (读取 conf/config.json)
      → ops.NewServer(cfg) → server.go:51
      → s.Start() → server.go:73 (StartAndServe)
```

### 服务主控

**`server.go:1-77`** — Server 结构体与生命周期

| 结构体/函数 | 行号 | 说明 |
|-------------|------|------|
| `Config` | `:16` | 应用配置：继承 `app.ApplicationConfig`，包含 `InternalAPIURL`、`HTTPConfig`、`DBConfig` |
| `Config.VerifyParams()` | `:23` | 校验配置参数（InternalAPIURL 和 DSN 不能为空） |
| `Config.SetDefaultValue()` | `:31` | 设置 HTTP 超时默认值（10s）和 DB 连接池默认值（MaxIdleConns=100, ConnMaxLifetime=1h） |
| `Server` | `:43` | 核心服务结构体，聚合 `Application`、`Database`、`API` |
| `NewServer()` | `:51` | 构造函数：初始化所有依赖并串联 |
| `Server.Start()` | `:73` | 启动服务（委托给 `StartAndServe`） |

**依赖装配**（**`server.go:51-71`**）：

```go
func NewServer(cfg *Config) *Server {
    s := &Server{cfg: cfg}
    s.Init(cfg)
    s.cfg.SetDefaultValue()

    database, err := db.NewDatabase(s.Logger.L(), &cfg.DBConfig)  // :56
    httpCli := httpclient.NewHTTPClient(&cfg.HTTPConfig)           // :62
    fac := factory.InitFactory()                                   // :63
    fac.UResource = uresource.NewUResourceImpl(cfg.InternalAPIURL, httpCli) // :64

    s.api, err = api.NewAPI(&s.Application, s.db, fac)            // :66
    return s
}
```

### 工厂模式

**`factory/factory.go:1-15`** — 工厂结构体

| 结构体/函数 | 行号 | 说明 |
|-------------|------|------|
| `Factory` | `:8` | 工厂结构体，包含 `UResource` 资源系统客户端 |
| `InitFactory()` | `:13` | 构造函数，返回空工厂实例；`UResource` 字段由调用方在 `NewServer` 中注入 |

**`factory/uresource/impl.go:1-31`** — UResource 客户端实现

| 结构体/函数 | 行号 | 说明 |
|-------------|------|------|
| `UresourceAll / UresourceInvisible / UresourceVisible` | `:8-10` | 可见性状态常量（0=全部, 1=不可见, 2=可见） |
| `ServiceBackend` | `:14` | 后端服务名称 `"UResource"` |
| `ResourceImpl` | `:18` | 资源系统客户端：包含 URL、backend 名称、HTTP 客户端 |
| `NewUResourceImpl()` | `:25` | 构造函数 |

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `db.NewDatabase()` | Database Operations (M05) | 创建数据库连接实例 |
| `api.NewAPI()` | API Core Framework (M02) | 注册 API 路由和处理器 |
| `uresource.NewUResourceImpl()` | Resource Label Operations (M08) | 初始化资源系统客户端 |
| `httpclient.NewHTTPClient()` | HTTP Client (M09) | 创建 HTTP 客户端 |

---

## 设计要点

- **配置驱动**：所有外部依赖（数据库 DSN、内部 API 地址、HTTP 超时）均通过配置文件注入，支持默认值兜底
- **依赖注入**：通过 `NewServer` 构造函数显式组装依赖，不依赖全局变量或 init 函数
- **Prometheus 集成**：启动时注册版本指标，便于监控系统识别服务版本
- **工具子命令**：`dumpcfg` 子命令可快速生成配置模板，降低部署配置门槛

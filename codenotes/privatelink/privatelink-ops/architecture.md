# privatelink-ops — 架构设计

> 自动生成文档 | 系统: [[privatelink]] | 基于 graphify 知识图谱分析

---

## 整体架构

**单体分层架构（Monolithic Layered）**，部署为单一 Go 二进制进程，对外暴露 HTTP API。

```
┌──────────────────────────────────────────────────────────────────┐
│                      CLI Entry (cmd/main.go)                     │
│              main() :18 — flag 解析 → start / dumpcfg / version  │
├──────────────────────────────────────────────────────────────────┤
│                       Server Layer (server.go)                    │
│   NewServer(cfg) :51                                              │
│   ├─ Init(cfg) — cnat2 app 框架初始化                             │
│   ├─ db.NewDatabase() — MySQL 连接初始化                          │
│   ├─ httpclient.NewHTTPClient() — HTTP 客户端                     │
│   ├─ factory.InitFactory() — 工厂初始化                           │
│   ├─ uresource.NewUResourceImpl() — 资源系统客户端                │
│   └─ api.NewAPI() — API 路由与处理层                              │
├──────────────────────────────────────────────────────────────────┤
│                      API Layer (api/)                             │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  Gin Router — POST / → api.handle() :85                  │   │
│   │  Action 分发器 :115-128                                   │   │
│   │                                                           │   │
│   │  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐ │   │
│   │  │SetResource   │  │SetResource   │  │User Config     │ │   │
│   │  │Invisible     │  │Visible       │  │CRUD            │ │   │
│   │  │:87           │  │:85           │  │:29 / :24 / :25 │ │   │
│   │  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘ │   │
│   └─────────┼─────────────────┼───────────────────┼──────────┘   │
│             │                 │                   │               │
├─────────────┼─────────────────┼───────────────────┼──────────────┤
│             ▼                 ▼                   ▼               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Database Layer (db/)                   │   │
│  │  db/db.go — Database struct (NewDatabase :43)            │   │
│  │  ├─ GetVPCEndpoints() :79                                │   │
│  │  ├─ GetServices() :110                                   │   │
│  │  ├─ UpdateEndpointInvisibleType() :152                   │   │
│  │  ├─ UpdateEndpointServiceInvisibleType() :143            │   │
│  │  ├─ AddUserConfig() :161                                 │   │
│  │  ├─ DeleteUserConfig() :176                              │   │
│  │  └─ UpdateUserConfig() :189                              │   │
│  │                                                          │   │
│  │  db/query/gen.go — GORM Gen Query 层                     │   │
│  │  db/model/*.gen.go — 数据表 ORM 模型                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                             │                                    │
│                    ┌────────▼────────┐                            │
│                    │  MySQL Database  │                           │
│                    │  t_vpc_endpoint  │                           │
│                    │  t_service       │                           │
│                    │  t_user_config   │                           │
│                    │  t_service_whitelist                         │
│                    │  t_service_snatips                          │
│                    └─────────────────┘                           │
├──────────────────────────────────────────────────────────────────┤
│                     External Integration                          │
│  ┌────────────────────┐  ┌────────────────────────────────────┐  │
│  │  HTTP Client       │  │  UResource (资源标签系统)           │  │
│  │  httpclient.go     │  │  factory/uresource/                │  │
│  │  → POST JSON       │  │  SetInvisibleLabel / DelLabel      │  │
│  └────────────────────┘  └────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 核心流程

### 启动流程

```
cmd/main.go:18 main()
  ├─ cmd/main.go:43 runServer()
  │    ├─ cmd/main.go:53 loadConfig() → 读取 JSON 配置文件
  │    └─ server.go:51 NewServer(cfg)
  │         ├─ s.Init(cfg)                            → cnat2 app 初始化
  │         ├─ cfg.SetDefaultValue()                  → 设置默认参数
  │         ├─ db.NewDatabase(zapLogger, &cfg.DBConfig) → 初始化 MySQL 连接
  │         ├─ httpclient.NewHTTPClient(&cfg.HTTPConfig) → 创建 HTTP 客户端
  │         ├─ factory.InitFactory()                  → 初始化工厂
  │         └─ api.NewAPI(app, db, fac)               → 初始化 API 层
  │              ├─ api.InitValidate()                 → 初始化校验器
  │              └─ api.InitRouter()                   → 注册 Gin 路由
  └─ server.go:73 s.Start()
       └─ s.StartAndServe() → 启动 HTTP 服务
```

### 请求处理流程：资源可见性操作

以 `SetResourceInvisible` 为例：

```
Client → POST / → Gin Router → api.handle() :85
  │
  1. 读取 Body → 解析 ReqBase → 获取 Action="SetResourceInvisible"
  2. 设置请求上下文 (RequestUUID)
  3. 分发到 a.SetResourceInvisible(c) :117
  │
  ▼
SetResourceInvisible() :22
  │
  1. parseInput(c, req) → JSON 反序列化 + validator 校验
  │   ResourceType: required + oneof=Endpoint/EndpointService
  │   ResourceId: required
  │
  2. 分支：ResourceType == "Endpoint"
  │   ├─ a.db.GetVPCEndpoints(ctx, resourceId, 0, 0) → 查询 t_vpc_endpoint
  │   │   (确认资源存在、唯一、未删除)
  │   ├─ a.fac.UResource.SetInvisibleLabel(ctx, resourceId)
  │   │   └─ UResource(expand.go:8) → IAddResourceLabel
  │   │       → HTTPClient.PostCtx() → POST → UResource 系统
  │   └─ a.db.UpdateEndpointInvisibleType(ctx, resourceId, 1)
  │       → 更新 t_vpc_endpoint.visible_type = 1
  │
  3. 分支：ResourceType == "EndpointService"
  │   ├─ a.db.GetServices(ctx, resourceId, 0, 0) → 查询 t_service
  │   ├─ a.fac.UResource.SetInvisibleLabel(ctx, resourceId)
  │   └─ a.db.UpdateEndpointServiceInvisibleType(ctx, resourceId, 1)
  │       → 更新 t_service.visible_type = 1
  │
  4. 返回 req.GenResponse(nil) → {RetCode:0, Message:"Success"}
```

### 请求处理流程：用户配置 CRUD

以 `AddUserConfig` 为例：

```
Client → POST / → api.handle() :85 → a.AddUserConfig(c) :121
  │
  ▼
AddUserConfig() :29
  │
  1. parseInput(c, req) → 校验 ConfigKey, ConfigValue, OperatorName 必填
  2. a.addUserConfigInDB(ctx, req) :44
  │   └─ 构造 TUserConfig 模型 → a.db.AddUserConfig(ctx, userConfig)
  │       → INSERT INTO t_user_config (company_id, account_id, resource_id,
  │         config_key, config_val, operator_name, insert_time)
  │
  3. 返回 req.GenResponse(nil)
```

---

## 核心模块

| 模块 | 文件 | 职责 |
|------|------|------|
| CLI 入口 | `cmd/main.go` | 命令行解析（start/dumpcfg/version）、配置加载 |
| 服务主控 | `server.go` | Server 结构生命周期管理、依赖初始化 |
| API 核心 | `api/api.go` | Gin 路由注册、请求解析、Action 分发、校验器初始化 |
| API 处理器 | `api/SetResource*.go` | 资源可见性设置/取消处理逻辑 |
| API 处理器 | `api/[Add/Delete/Update]UserConfig.go` | 用户配置 CRUD 处理逻辑 |
| 响应基础 | `api/base.go` | ReqBase/RespBase、GenResponse/GenRetCode |
| 错误码 | `api/error.go` | 全局错误变量与错误码映射 |
| 资源类型 | `api/convert.go` | 资源类型常量定义 |
| DB 操作 | `db/db.go` | 数据库连接初始化、业务查询方法 |
| DB 查询层 | `db/query/gen.go` | GORM Gen Query 结构体、事务/读写分离 |
| DB 查询对象 | `db/query/t_*.gen.go` | 各数据表的 GORM Gen 查询对象（自动生成） |
| DB 模型 | `db/model/*.gen.go` | 各数据表的结构体模型（自动生成） |
| HTTP 客户端 | `httpclient/httpclient.go` | 通用 HTTP 客户端（GET/POST/JSON） |
| 工厂 | `factory/factory.go` | 工厂结构体，聚合 UResource 客户端 |
| 资源标签操作 | `factory/uresource/expand.go` | SetInvisibleLabel / DeleteResourceLabel |
| 资源系统请求 | `factory/uresource/basic.go` | IAddResourceLabel / IDeleteResourceLabel 请求构造 |
| 资源系统客户端 | `factory/uresource/impl.go` | ResourceImpl 结构体、NewUResourceImpl |
| 通用请求类型 | `factory/common/common.go` | BaseRequest / BaseResponse |
| 上下文工具 | `ncontext/ncontext.go` | SessionID 上下文传递工具 |
| 代码生成工具 | `cmd/tools/mysqlgen/main.go` | 基于 gorm gen 的数据表模型和查询代码生成 |

---

## 数据模型关联

```
t_service              ──── t_vpc_endpoint
  service_id (PK)      │      endpoint_id (PK)
  company_id            │      service_id (FK → t_service.service_id)
  account_id            │      company_id
  visible_type          │      account_id
  resource_type         │      visible_type
  resource_id           │      connect_status
                       │
t_user_config          t_service_whitelist
  company_id (复合PK)   │      service_id (FK)
  account_id (复合PK)   │      company_id
  resource_id (复合PK)  │
  config_key (复合PK)   t_service_snatips
  config_val            │      service_id (FK)
                       │      ip
```

---

## 依赖关系

```
cmd/main.go
  └── server.go (privatelink_ops package)
        ├── api/          → API 处理器
        │     ├── api/base.go       → 请求/响应基类
        │     ├── api/error.go      → 错误码
        │     ├── api/convert.go    → 资源类型常量
        │     ├── api/AddUserConfig.go
        │     ├── api/DeleteUserConfig.go
        │     ├── api/UpdateUserConfig.go
        │     ├── api/SetResourceVisible.go
        │     └── api/SetResourceInvisible.go
        ├── db/db.go      → 数据库操作
        │     ├── db/query/gen.go   → GORM Gen Query
        │     │     ├── db/query/t_service.gen.go
        │     │     ├── db/query/t_user_config.gen.go
        │     │     ├── db/query/t_vpc_endpoint.gen.go
        │     │     ├── db/query/t_service_whitelist.gen.go
        │     │     └── db/query/t_service_snatips.gen.go
        │     └── db/model/*.gen.go → 数据表模型
        ├── factory/      → 工厂层
        │     ├── factory.go
        │     ├── common/common.go
        │     └── uresource/ → 资源系统集成
        │           ├── impl.go
        │           ├── basic.go
        │           └── expand.go
        ├── httpclient/httpclient.go → HTTP 客户端
        ├── ncontext/ncontext.go     → 上下文工具
        └── app.Application → cnat2 应用框架
```

---

## 关键设计决策

1. **单端点 API 设计**：所有操作通过 `POST /` + `Action` 字段分发，简化路由管理，适合内部运维工具场景
2. **双层状态同步**：资源可见性操作同时修改数据库和外部标签系统，保证两种视图的一致性
3. **用户配置软删除**：`DeleteUserConfig` 执行物理删除（`DELETE`），而非逻辑删除（软删除）
4. **GORM Gen 代码生成**：所有数据表模型和查询代码由 `gorm.io/gen` 自动生成，确保类型安全
5. **UResource 异步集成**：通过 HTTP Client 调用内部 UResource 系统管理资源标签，解耦标签系统
6. **请求链路追踪**：通过 `RequestUUID` 和 `session_id` 贯穿整个请求生命周期，便于日志审计
7. **Validator 国际化**：使用 `go-playground/validator` 的英文翻译器，提供标准化错误消息

---

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度（源自代码） | 全部 |
| 需人工审查 | 0 |

*所有架构描述均基于源代码事实和 graphify 知识图谱分析。*

# privatelink-ops — PrivateLink 运维 API 服务

> Graphify 自动分析 | 580 节点 · 31 个 Go 源文件 · 33 社区

---

## 概览

privatelink-ops 是一个基于 Go 和 Gin 框架构建的 HTTP API 服务，作为 PrivateLink 产品的运维操作入口。它提供统一的 JSON RPC 风格接口，支持资源可见性控制（设置/取消不可见标签）和用户配置的增删改查（CRUD）操作。服务通过 MySQL (GORM Gen) 进行数据持久化，并通过内部 HTTP Client 调用资源系统（UResource）管理资源标签。

| 指标 | 数值 |
|------|------|
| Go 源文件数 | 31 |
| 社区数（Go 代码） | 21 |
| API 动作数 | 5 |
| 数据库表 | 5 |
| 核心抽象（God Nodes） | 8 |

---

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心抽象：

| 节点 | 连接数 | 类型 | 文件 |
|------|--------|------|------|
| `ITServiceDo` | 30 | code | `db/query/gen.go` |
| `ITUserConfigDo` | 30 | code | `db/query/gen.go` |
| `ITVpcEndpointDo` | 30 | code | `db/query/gen.go` |
| `ITServiceSnatipDo` | 30 | code | `db/query/gen.go` |
| `ITServiceWhitelistDo` | 30 | code | `db/query/gen.go` |
| `tService` | 24 | code | `db/query/t_service.gen.go` |
| `tUserConfig` | 24 | code | `db/query/t_user_config.gen.go` |
| `tVpcEndpoint` | 24 | code | `db/query/t_vpc_endpoint.gen.go` |

---

## 社区导航

| # | 社区 | 节点数 | 模块文档 |
|---|------|--------|----------|
| 8 | Application Configuration | 26 | [01-Application-Server](modules/01-Application-Server.md) |
| 5,10,30,31 | API Core Framework | 39 | [02-API-Core-Framework](modules/02-API-Core-Framework.md) |
| 11,14 | User Config API Handlers | 10 | [03-User-Config-Handlers](modules/03-User-Config-Handlers.md) |
| 12,13 | Resource Visibility Handlers | 10 | [04-Resource-Visibility-Handlers](modules/04-Resource-Visibility-Handlers.md) |
| 0-4,7 | Database Query Layer | 372 | [05-Database-Query-Layer](modules/05-Database-Query-Layer.md) |
| 6 | Database Operations | 35 | [06-Database-Operations](modules/06-Database-Operations.md) |
| 16-18,24,25 | Database Table Models | 18 | [07-Database-Models](modules/07-Database-Models.md) |
| 19,20,32 | Resource Label Operations | 8 | [08-Resource-Label-Operations](modules/08-Resource-Label-Operations.md) |
| 9 | HTTP Client | 15 | [09-HTTP-Client](modules/09-HTTP-Client.md) |
| 6 (部分) | Context Utilities | 5 | [10-Context-Utilities](modules/10-Context-Utilities.md) |
| 15 | Code Generation Tool | 5 | [11-Code-Generation-Tool](modules/11-Code-Generation-Tool.md) |

### CI / 基础设施社区（简略）

| # | 社区 | 说明 |
|---|------|------|
| 21 | Build Images | GitLab CI Docker 镜像构建 |
| 22 | Manual Build Images | 手工触发构建 |
| 23 | Code Quality Checks | 代码检查与测试 |
| 26-27 | Documentation | README 与设计文档 |
| 28 | Merge Request Template | MR 模板 |
| 29 | Build Test | 构建测试 |

---

## API 接口

服务使用单个 POST 端点 `POST /`，通过 JSON 请求体中的 `Action` 字段进行动作分发。

| Action | 说明 | 文档 |
|--------|------|------|
| `SetResourceInvisible` | 设置资源不可见标签 | [API 文档](api.md) |
| `SetResourceVisible` | 取消资源不可见标签 | [API 文档](api.md) |
| `AddUserConfig` | 添加用户配置 | [API 文档](api.md) |
| `DeleteUserConfig` | 删除用户配置 | [API 文档](api.md) |
| `UpdateUserConfig` | 更新用户配置 | [API 文档](api.md) |

---

## 数据流

```
Client Request
    │ POST /
    ▼
Gin Router (api/api.go:81)
    │
    ▼
api.handle() (api/api.go:85)
    │ JSON 解析 → 提取 Action
    │ Action dispatcher (api/api.go:115-128)
    ▼
┌─────────────────┬──────────────────┬──────────────────┐
│ SetResource      │ SetResource      │ User Config      │
│ Invisible        │ Visible          │ CRUD             │
│ api/:87          │ api/:85          │ Add/Delete/Update│
└────────┬─────────┴──────┬───────────┴────────┬─────────┘
         │                │                    │
    ┌────▼────┐      ┌────▼────┐         ┌────▼────┐
    │UResource│      │UResource│         │  DB     │
    │SetLabel │      │DelLabel │         │ CRUD    │
    │:46     │      │:45     │         │:161-208│
    └────┬────┘      └────┬────┘         └─────────┘
         │                │                    │
    ┌────▼────────────────▼────────────────────▼──┐
    │              MySQL Database                   │
    │  t_vpc_endpoint · t_service · t_user_config   │
    └───────────────────────────────────────────────┘
         │
    ┌────▼───────────────────┐
    │  UResource (Internal)   │
    │  HTTP POST → 标签管理   │
    └────────────────────────┘
```

---

## 关键配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `InternalAPIURL` | — | UResource 内部 API 地址 |
| `HTTPConfig.Timeout` | 10s | HTTP 客户端超时 |
| `DBConfig.DSN` | — | MySQL 连接 DSN |
| `DBConfig.ConnMaxLifetime` | 1h | 数据库连接最大生命周期 |
| `DBConfig.MaxIdleConns` | 100 | 最大空闲连接数 |

---

## 架构特点

- **单端点分发**：所有 API 动作均通过 `POST /` 统一入口，按 `Action` 字段分发，类似 JSON RPC 风格
- **双层持久化**：资源可见性操作同时更新数据库（`visible_type` 字段）和外部资源标签系统（UResource），保证状态一致
- **GORM Gen 自动生成**：数据库模型和查询层代码由 gorm gen 自动生成，减少手写 ORM 代码
- **Gin + Validator 校验**：使用 `go-playground/validator` 进行参数校验，支持国际化错误消息
- **请求追踪**：通过 `RequestUUID` 和 `session_id` 实现请求链路追踪，日志上下文贯穿 DB 和 HTTP 调用

---

## Graphify 分析报告

> 来源：graphify 知识图谱分析

- 图谱覆盖率：代码社区覆盖全部 Go 源文件
- 5 个主要 API 处理函数构成核心业务逻辑
- `Use()` 函数是社区间桥接节点，连接查询上下文到各个数据表查询层
- `NewDatabase()` 是次级桥接节点，连接数据库初始化与 API 层

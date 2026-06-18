# 模块: 数据库查询层 — GORM Gen 中间件

> 社区 #7 — 29 节点 · Database Query Layer

---

## 概述

本模块是 GORM Gen 自动生成的查询层核心，定义 `Query` 结构体及其关联方法。它聚合了五个数据表（`t_service`、`t_user_config`、`t_vpc_endpoint`、`t_service_snatips`、`t_service_whitelist`）的查询对象，并提供事务、读写分离和上下文查询的能力。`Use()` 函数作为桥接节点连接 GORM DB 实例到各查询层。

**所有代码由 `gorm.io/gen` 自动生成，不可手动编辑。**

---

## 文件索引

### 查询聚合层

**`db/query/gen.go:1-117`** — 查询结构体与核心方法

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Use()` | `:18` | **桥接函数**：将 `*gorm.DB` 实例转换为 `*Query` 结构体，初始化 5 个数据表的查询对象 |
| `Query` | `:29` | 查询聚合结构体：包含 5 个表查询对象（`TService`, `TServiceSnatip`, `TServiceWhitelist`, `TUserConfig`, `TVpcEndpoint`） |
| `Query.Available()` | `:39` | 检查 DB 是否可用 |
| `Query.clone()` | `:41` | 克隆查询实例（用于事务） |
| `Query.ReadDB()` | `:52` | 切换到只读副本（`dbresolver.Read`） |
| `Query.WriteDB()` | `:56` | 切换到主库写入（`dbresolver.Write`） |
| `Query.ReplaceDB()` | `:60` | 替换底层 `*gorm.DB` 实例 |
| `queryCtx` | `:71` | 上下文查询结构体：5 个表查询的 Do 接口（`ITServiceDo` 等） |
| `Query.WithContext()` | `:79` | 将 Context 注入到所有查询对象中 |
| `Query.Transaction()` | `:89` | 事务封装函数 |
| `Query.Begin()` | `:93` | 手动开启事务 |
| `QueryTx` | `:98` | 事务对象：`Commit()`、`Rollback()`、`SavePoint()`、`RollbackTo()` |

### 查询对象文件

每个数据表的 GORM Gen 查询对象，包含字段定义和 CRUD 方法：

| 文件 | 对应表 | 节点数 |
|------|--------|--------|
| **`db/query/t_service.gen.go`** | `t_service` | 69 |
| **`db/query/t_user_config.gen.go`** | `t_user_config` | 69 |
| **`db/query/t_vpc_endpoint.gen.go`** | `t_vpc_endpoint` | 69 |
| **`db/query/t_service_snatips.gen.go`** | `t_service_snatips` | 68 |
| **`db/query/t_service_whitelist.gen.go`** | `t_service_whitelist` | 68 |

每个查询对象文件定义的内容结构（以 `t_service.gen.go` 为例）：

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `tService` | — | 包内私有查询结构体 |
| `ITServiceDo` | — | 公开查询接口 |
| `newTService()` | `:22` | 构造函数：绑定模型 + 注册字段 |
| 字段定义 | `:30-50` | 每个列对应的 `field.*` 类型字段（Uint32/String/Time） |
| `tServiceDo` | — | 内嵌的 GORM `gen.DO` 实现 |

---

## 查询对象字段列表

### t_service.gen.go 字段（行 ~30-50）

| 字段变量 | Go 类型 | 对应列 |
|----------|---------|--------|
| `ID` | field.Uint32 | id |
| `ServiceID` | field.String | service_id |
| `CompanyID` | field.Uint32 | company_id |
| `AccountID` | field.Uint32 | account_id |
| `Description` | field.String | description |
| `AutoAccept` | field.Uint32 | auto_accept |
| `Payer` | field.Uint32 | payer |
| `ConnectBw` | field.Uint32 | connect_bw |
| `VnetID` | field.String | vnet_id |
| `IPVersion` | field.Uint32 | ip_version |
| `SubnetworkID` | field.String | subnetwork_id |
| `TunnelID` | field.Uint32 | tunnel_id |
| `IP` | field.String | ip |
| `ResourceType` | field.Uint32 | resource_type |
| `ResourceID` | field.String | resource_id |
| `VisibleType` | field.Uint32 | visible_type |
| `CloseStatus` | field.Uint32 | close_status |
| `ChannelID` | field.Uint32 | channel_id |
| `InsertTime` | field.Uint32 | insert_time |
| `UpdateTime` | field.Time | update_time |
| `DeleteTime` | field.Uint32 | delete_time |

### t_vpc_endpoint.gen.go 字段

| 字段变量 | Go 类型 | 对应列 |
|----------|---------|--------|
| `EndpointID` | field.String | endpoint_id |
| `ServiceID` | field.String | service_id |
| `Ipv4` | field.String | ipv4 |
| `Ipv6` | field.String | ipv6 |
| `Mac` | field.String | mac |
| `ConnectBw` | field.Uint32 | connect_bw |
| `ConnectStatus` | field.Uint32 | connect_status |
| `CloseStatus` | field.Uint32 | close_status |
| `VisibleType` | field.Uint32 | visible_type |
| `ChannelID` | field.Uint32 | channel_id |
| `InsertTime` | field.Uint32 | insert_time |
| `UpdateTime` | field.Time | update_time |
| `DeleteTime` | field.Uint32 | delete_time |

### t_user_config.gen.go 字段

| 字段变量 | Go 类型 | 对应列 |
|----------|---------|--------|
| `CompanyID` | field.Uint32 | company_id |
| `AccountID` | field.Uint32 | account_id |
| `ResourceID` | field.String | resource_id |
| `ConfigKey` | field.String | config_key |
| `ConfigVal` | field.String | config_val |
| `OperatorName` | field.String | operator_name |
| `InsertTime` | field.Uint32 | insert_time |
| `UpdateTime` | field.Time | update_time |

### t_service_whitelist.gen.go 字段

| 字段变量 | Go 类型 | 对应列 |
|----------|---------|--------|
| `ServiceID` | field.String | service_id |
| `CompanyID` | field.Uint32 | company_id |
| `Remark` | field.String | remark |
| `InsertTime` | field.Uint32 | insert_time |
| `DeleteTime` | field.Uint32 | delete_time |

### t_service_snatips.gen.go 字段

| 字段变量 | Go 类型 | 对应列 |
|----------|---------|--------|
| `ServiceID` | field.String | service_id |
| `IP` | field.String | ip |
| `IPType` | field.Uint32 | ip_type |
| `Mac` | field.String | mac |
| `InsertTime` | field.Uint32 | insert_time |
| `DeleteTime` | field.Uint32 | delete_time |

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `Use()` | Application Server (M01) | 在 `db.NewDatabase()` 中调用，初始化查询层 |
| `WithContext()` | Database Operations (M06) | `db/db.go` 中各业务方法通过 `WithContext` 注入 Context |
| `Transaction()` | Database Operations (M06) | 提供事务能力 |
| 所有 `IT*Do` 接口 | Database Operations (M06) | `queryCtx` 结构体作为业务查询的入口 |

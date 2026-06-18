# billinsert - module 08: Data Model

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 0** (Service Data Model, 20 nodes) + **Community 1** (VPC Endpoint Model, 20 nodes) + **Community 2** (Service SNAT IP Model, 19 nodes) + **Community 3** (Service Whitelist Model, 19 nodes) + **Community 4** (Traffic Info Model, 19 nodes) + Schema 社区 (14,15,19,20,21)
> **验证状态**: ✓ | **来源文件**: `db/model/*.gen.go`, `db/query/*.gen.go`

---

## 1. 模块职责

Data Model 模块是 gorm.io/gen **自动生成的 ORM 层**，包含所有数据库表的：

- **数据模型（Model）**：Go 结构体，映射 MySQL 表字段（`db/model/*.gen.go`）
- **查询对象（Query）**：类型安全的 CRUD 操作接口（`db/query/*.gen.go`）

## 2. 数据表 Schema

### 2.1 t_service — 服务表

**结构体**: `TService` (`db/model/t_service.gen.go:14-33`)
**查询对象**: `tService` / `ITServiceDo` (`db/query/t_service.gen.go`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint32 (PK, autoIncrement) | 自增主键 |
| `service_id` | string (not null) | 服务 ID |
| `company_id` | uint32 (not null) | 企业 ID |
| `account_id` | uint32 (not null) | 账户 ID |
| `description` | string (not null) | 服务描述 |
| `auto_accept` | uint32 (not null) | 是否自动接受连接请求 |
| `payer` | uint32 (not null) | 付费方（0=服务方付费, 1=端点付费） |
| `connect_bw` | uint32 (not null) | 连接带宽 |
| `vnet_id` | string (not null) | VNet ID |
| `subnetwork_id` | string (not null) | 子网 ID |
| `tunnel_id` | uint32 (not null) | 隧道 ID |
| `ip` | string (not null) | 服务 IP |
| `resource_type` | uint32 (not null) | 资源类型 |
| `resource_id` | string (not null) | 资源 ID |
| `visible_type` | uint32 (not null, default:2) | 可见类型 |
| `insert_time` | uint32 (not null) | 创建时间（Unix 时间戳） |
| `update_time` | time.Time (not null, default:CURRENT_TIMESTAMP) | 更新时间 |
| `delete_time` | uint32 (not null) | 删除时间（0=未删除） |

### 2.2 t_vpc_endpoint — VPC 端点表

**结构体**: `TVpcEndpoint` (`db/model/t_vpc_endpoint.gen.go:14-33`)
**查询对象**: `tVpcEndpoint` / `ITVpcEndpointDo` (`db/query/t_vpc_endpoint.gen.go`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint32 (PK, autoIncrement) | 自增主键 |
| `endpoint_id` | string (not null) | 端点 ID |
| `service_id` | string (not null) | 关联服务 ID |
| `company_id` | uint32 (not null) | 企业 ID |
| `account_id` | uint32 (not null) | 账户 ID |
| `vnet_id` | string (not null) | VNet ID |
| `subnetwork_id` | string (not null) | 子网 ID |
| `tunnel_id` | uint32 (not null) | 隧道 ID |
| `ipv4` | string (not null) | IPv4 地址 |
| `ipv6` | string (not null) | IPv6 地址 |
| `mac` | string (not null) | MAC 地址 |
| `connect_bw` | uint32 (not null) | 连接带宽 |
| `connect_status` | uint32 (not null) | 连接状态 |
| `close_status` | uint32 (not null) | 关闭状态 |
| `visible_type` | uint32 (not null, default:2) | 可见类型 |
| `insert_time` | uint32 (not null) | 创建时间（Unix 时间戳） |
| `update_time` | time.Time (not null, default:CURRENT_TIMESTAMP) | 更新时间 |
| `delete_time` | uint32 (not null) | 删除时间（0=未删除） |

### 2.3 t_traffic_info — 流量计费表

**结构体**: `TTrafficInfo` (`db/model/t_traffic_info.gen.go:10-21`)
**查询对象**: `tTrafficInfo` / `ITTrafficInfoDo` (`db/query/t_traffic_info.gen.go`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint64 (PK, autoIncrement) | 自增主键 |
| `endpoint_id` | string (not null) | 端点 ID |
| `service_id` | string (not null) | 服务 ID |
| `payer` | uint32 (not null) | 付费方（0=服务方, 1=端点） |
| `account_id` | uint32 (not null) | 计费归属账户 ID |
| `company_id` | uint32 (not null) | 计费归属企业 ID |
| `max_traffic` | uint64 (not null) | 最大流量（In 和 Out 中的较大值） |
| `in_traffic` | uint64 (not null) | 入流量（字节） |
| `out_traffic` | uint64 (not null) | 出流量（字节） |
| `insert_time` | uint32 (not null) | 记录时间（Unix 时间戳） |

### 2.4 t_service_snatips — 服务 SNAT IP 表（未在业务中使用）

**结构体**: `TServiceSnatip` (`db/model/t_service_snatips.gen.go:10-17`)
**查询对象**: `tServiceSnatip` / `ITServiceSnatipDo` (`db/query/t_service_snatips.gen.go`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint32 (PK, autoIncrement) | 自增主键 |
| `service_id` | string (not null) | 服务 ID |
| `ip` | string (not null) | SNAT IP |
| `mac` | string (not null) | MAC 地址 |
| `insert_time` | uint32 (not null) | 创建时间 |
| `delete_time` | uint32 (not null) | 删除时间（0=未删除） |

### 2.5 t_service_whitelist — 服务白名单表（未在业务中使用）

**结构体**: `TServiceWhitelist` (`db/model/t_service_whitelist.gen.go:10-17`)
**查询对象**: `tServiceWhitelist` / `ITServiceWhitelistDo` (`db/query/t_service_whitelist.gen.go`)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | uint32 (PK, autoIncrement) | 自增主键 |
| `service_id` | string (not null) | 服务 ID |
| `company_id` | uint32 (not null) | 白名单企业 ID |
| `remark` | string (not null) | 备注 |
| `insert_time` | uint32 (not null) | 创建时间 |
| `delete_time` | uint32 (not null) | 删除时间（0=未删除） |

## 3. 查询对象接口

每张表的查询对象都实现了对应的 Do 接口，提供完整的 CRUD 方法：

| 接口 | 表 | 文件 | 使用 |
|------|-----|------|------|
| `ITServiceDo` | `t_service` | `db/query/t_service.gen.go:159` | ✅ `db/db.go:107` |
| `ITVpcEndpointDo` | `t_vpc_endpoint` | `db/query/t_vpc_endpoint.gen.go:159` | ✅ `db/db.go:106` |
| `ITTrafficInfoDo` | `t_traffic_info` | `db/query/t_traffic_info.gen.go:127` | ✅ `db/db.go:129` |
| `ITServiceSnatipDo` | `t_service_snatips` | `db/query/t_service_snatips.gen.go:111` | ❌ 未在业务代码中使用 |
| `ITServiceWhitelistDo` | `t_service_whitelist` | `db/query/t_service_whitelist.gen.go:111` | ❌ 未在业务代码中使用 |

## 4. 关键实现逻辑

### 4.1 JOIN 查询用法（`db/db.go:105-126`）

`GetAllConnectionsLastInterval()` 使用了 gorm.io/gen 的类型安全 JOIN 语法：

```go
e.WithContext(ctx).Select(
    e.EndpointID,
    e.ServiceID,
    e.AccountID,
    e.CompanyID,
    e.Ipv4,
    e.Ipv6,
    s.Payer.As("s_payer"),
    s.AccountID.As("s_account_id"),
    s.CompanyID.As("s_company_id"),
).LeftJoin(
    s, s.ServiceID.EqCol(e.ServiceID),
).Where(
    e.InsertTime.Lt(endTime),
    field.Or(e.DeleteTime.Eq(0), e.DeleteTime.Gt(startTime)),
).Scan(&result)
```

### 4.2 软删除判断

表中的 `delete_time` 字段使用 **0 表示未删除**，非零值为删除时间戳。这是自定义的软删除实现，非 GORM 内置的 `gorm.DeletedAt`。

### 4.3 表名约定

所有表名以 `t_` 前缀开头。`TableName()` 方法返回对应的常量字符串。

## 5. 代码生成关系

```
cmd/tools/mysqlgen/main.go:genOut()
  │
  ├─ db/model/t_service.gen.go         → TService 结构体
  ├─ db/model/t_vpc_endpoint.gen.go    → TVpcEndpoint 结构体
  ├─ db/model/t_traffic_info.gen.go    → TTrafficInfo 结构体
  ├─ db/model/t_service_snatips.gen.go → TServiceSnatip 结构体
  ├─ db/model/t_service_whitelist.gen.go → TServiceWhitelist 结构体
  │
  └─ db/query/gen.go                   → Query 门面 (Use)
      ├─ db/query/t_service.gen.go     → tService / ITServiceDo
      ├─ db/query/t_vpc_endpoint.gen.go → tVpcEndpoint / ITVpcEndpointDo
      ├─ db/query/t_traffic_info.gen.go → tTrafficInfo / ITTrafficInfoDo
      ├─ db/query/t_service_snatips.gen.go → tServiceSnatip / ITServiceSnatipDo
      └─ db/query/t_service_whitelist.gen.go → tServiceWhitelist / ITServiceWhitelistDo
```

## 6. 重要发现

### 6.1 未使用的表代码
`t_service_snatips` 和 `t_service_whitelist` 的 model 和 query 代码已生成，但：
- 未在 `db/query/gen.go` 的 `Use()` 函数中注册
- 未被任何业务代码引用

这可能是因为代码生成配置包含多张表但 billinsert 业务只使用了其中 3 张。

### 6.2 主键类型差异
- `TService.id`、`TVpcEndpoint.id`、`TServiceSnatip.id`、`TServiceWhitelist.id`：`uint32`
- `TTrafficInfo.id`：`uint64`（流量记录预计会有更多数据量）

### 6.3 时间字段
- `insert_time`：统一使用 `uint32`（Unix 时间戳）
- `update_time`：使用 `time.Time`（MySQL CURRENT_TIMESTAMP）

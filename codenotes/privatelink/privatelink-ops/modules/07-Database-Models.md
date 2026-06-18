# 模块: 数据库表模型

> 社区 #16, #17, #18, #24, #25 — 18 节点 · GORM Gen 自动生成

---

## 概述

本模块包含五个数据表的 GORM 模型定义，所有代码由 `gorm.io/gen` 代码生成工具自动生成（见模块 11）。每个模型定义对应一个 MySQL 表，包含表名常量、结构体定义和 `TableName()` 方法。

**所有代码由 `gorm.io/gen` 自动生成，不可手动编辑。**

---

## 文件索引

### t_service — 端点服务表

**`db/model/t_service.gen.go:1-41`**

| 常量/结构体 | 行号 | 说明 |
|-------------|------|------|
| `TableNameTService` | `:11` | 表名常量：`"t_service"` |
| `TService` | `:14` | 服务数据模型 |
| `TableName()` | `:39` | GORM 表名接口实现 |

**TService 字段**：

| 字段 | 类型 | 数据库列 | 说明 |
|------|------|----------|------|
| `ID` | uint32 | id (PK, autoIncrement) | 自增主键 |
| `ServiceID` | string | service_id | 服务唯一 ID |
| `CompanyID` | uint32 | company_id | 公司 ID |
| `AccountID` | uint32 | account_id | 账户 ID |
| `Description` | string | description | 服务描述 |
| `AutoAccept` | uint32 | auto_accept | 是否自动接受连接 |
| `Payer` | uint32 | payer | 付费方 |
| `ConnectBw` | uint32 | connect_bw | 连接带宽 |
| `VnetID` | string | vnet_id | VNet ID |
| `IPVersion` | uint32 | ip_version | IP 版本 |
| `SubnetworkID` | string | subnetwork_id | 子网 ID |
| `TunnelID` | uint32 | tunnel_id | 隧道 ID |
| `IP` | string | ip | IP 地址 |
| `ResourceType` | uint32 | resource_type | 资源类型 |
| `ResourceID` | string | resource_id | 资源 ID（关联 UResource） |
| `VisibleType` | uint32 | visible_type, default:2 | 可见性（2=可见, 1=不可见） |
| `CloseStatus` | uint32 | close_status | 关闭状态 |
| `ChannelID` | uint32 | channel_id | 通道 ID |
| `InsertTime` | uint32 | insert_time | 创建时间（Unix 时间戳） |
| `UpdateTime` | time.Time | update_time, default:CURRENT_TIMESTAMP | 更新时间 |
| `DeleteTime` | uint32 | delete_time | 删除时间（0=未删除） |

### t_vpc_endpoint — VPC 端点表

**`db/model/t_vpc_endpoint.gen.go:1-39`**

| 常量/结构体 | 行号 | 说明 |
|-------------|------|------|
| `TableNameTVpcEndpoint` | `:11` | 表名常量：`"t_vpc_endpoint"` |
| `TVpcEndpoint` | `:14` | VPC 端点数据模型 |

**TVpcEndpoint 字段**（不同于 TService 的字段）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `EndpointID` | string | 端点唯一 ID |
| `ServiceID` | string | 关联的服务 ID |
| `Ipv4` | string | IPv4 地址 |
| `Ipv6` | string | IPv6 地址 |
| `Mac` | string | MAC 地址 |
| `ConnectBw` | uint32 | 连接带宽 |
| `ConnectStatus` | uint32 | 连接状态 |
| `VisibleType` | uint32 | 可见性（默认 2=可见） |
| `CloseStatus` | uint32 | 关闭状态 |
| `ChannelID` | uint32 | 通道 ID |
| `InsertTime` | uint32 | 创建时间 |
| `UpdateTime` | time.Time | 更新时间 |
| `DeleteTime` | uint32 | 删除时间 |

### t_user_config — 用户配置表

**`db/model/t_user_config.gen.go:1-29`**

| 常量/结构体 | 行号 | 说明 |
|-------------|------|------|
| `TableNameTUserConfig` | `:11` | 表名常量：`"t_user_config"` |
| `TUserConfig` | `:14` | 用户配置数据模型 |

**TUserConfig 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | uint32 | 自增主键 |
| `CompanyID` | uint32 | 公司 ID |
| `AccountID` | uint32 | 账户 ID |
| `ResourceID` | string | 资源 ID |
| `ConfigKey` | string | 配置键（如 `disable_limit_bandwidth`） |
| `ConfigVal` | string | 配置值 |
| `OperatorName` | string | 操作人 |
| `InsertTime` | uint32 | 创建时间 |
| `UpdateTime` | time.Time | 更新时间 |

### t_service_whitelist — 服务白名单表

**`db/model/t_service_whitelist.gen.go:1-22`**

| 常量/结构体 | 行号 | 说明 |
|-------------|------|------|
| `TableNameTServiceWhitelist` | `:7` | 表名常量：`"t_service_whitelist"` |
| `TServiceWhitelist` | `:10` | 服务白名单数据模型 |

**TServiceWhitelist 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | uint32 | 自增主键 |
| `ServiceID` | string | 服务 ID |
| `CompanyID` | uint32 | 公司 ID |
| `Remark` | string | 备注 |
| `InsertTime` | uint32 | 创建时间 |
| `DeleteTime` | uint32 | 删除时间 |

### t_service_snatips — 服务 SNAT IP 表

**`db/model/t_service_snatips.gen.go:1-23`**

| 常量/结构体 | 行号 | 说明 |
|-------------|------|------|
| `TableNameTServiceSnatip` | `:7` | 表名常量：`"t_service_snatips"` |
| `TServiceSnatip` | `:10` | 服务 SNAT IP 数据模型 |

**TServiceSnatip 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | uint32 | 自增主键 |
| `ServiceID` | string | 服务 ID |
| `IP` | string | IP 地址 |
| `IPType` | uint32 | IP 类型（默认 1） |
| `Mac` | string | MAC 地址 |
| `InsertTime` | uint32 | 创建时间 |
| `DeleteTime` | uint32 | 删除时间 |

---

## 表关系概览

```
t_service ──1:N──→ t_vpc_endpoint (service_id)
  │
  ├── t_service_whitelist (service_id) — 服务级别的白名单
  ├── t_service_snatips  (service_id) — 服务的 SNAT IP
  │
t_user_config — 独立的配置表，通过 company_id + account_id + resource_id 关联
```

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `TService` | Database Operations (M06) | `GetServices()` 使用此模型 |
| `TVpcEndpoint` | Database Operations (M06) | `GetVPCEndpoints()` 使用此模型 |
| `TUserConfig` | Database Operations (M06) | 用户配置 CRUD 方法使用此模型 |
| 所有模型 | Database Query Layer (M05) | 查询对象通过 `UseModel()` 绑定模型 |
| `TService`, `TVpcEndpoint` | Resource Visibility (M04) | 可见性操作使用这些模型 |

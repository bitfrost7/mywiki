# billing — module_07_DB_Models

> 自动生成文档 | 社区 14, 15, 20, 21, 22 | 系统: billing | 时间: 2026-06-18

---

# DB Models — 数据模型（自动生成）

## 1. 模块职责

本模块包含 **GORM Gen 自动生成**的数据模型结构体（Model），每张表对应一个独立的 Go 文件。这些结构体直接映射到 MySQL 表结构，用于 GORM 的 CRUD 操作。

## 2. 文件清单

| 文件 | 社区 | 对应表 | 主结构体 | 表名 |
|------|------|--------|---------|------|
| `db/model/t_billing_info.gen.go` | C20 | `t_billing_info` | `TBillingInfo` | `t_billing_info` |
| `db/model/t_connect_info.gen.go` | C21 | `t_connect_info` | `TConnectInfo` | `t_connect_info` |
| `db/model/t_service.gen.go` | C14 | `t_service` | `TService` | `t_service` |
| `db/model/t_traffic_info.gen.go` | C22 | `t_traffic_info` | `TTrafficInfo` | `t_traffic_info` |
| `db/model/t_vpc_endpoint.gen.go` | C15 | `t_vpc_endpoint` | `TVpcEndpoint` | `t_vpc_endpoint` |

## 3. 主要结构体定义

### 3.1 TBillingInfo（`db/model/t_billing_info.gen.go:10-27`）

| 字段 | 类型 | GORM 标签 | 业务含义 |
|------|------|-----------|----------|
| ID | int64 | primaryKey | 主键 ID |
| ItemID | string | column:item_id | 资源 ID (EndpointID / ServiceID) |
| Type | uint32 | column:type | 计费类型 (1=流量 / 2=实例 / 10=Service记录 / 11=Service记录 / 12=零流量) |
| OrderNo | string | column:order_no | UBill 订单号 |
| AccountID | uint32 | column:account_id | 账户 ID |
| CompanyID | uint32 | column:company_id | 公司 ID |
| TrafficSum | uint64 | column:traffic_sum | 流量合计（MB） |
| Multiple | uint32 | column:multiple | 实例倍数（小时数） |
| State | string | column:state | 订单状态 ("init" / "success") |
| Comment | string | column:comment | 备注（失败时记录错误信息） |
| StartTime | uint32 | column:start_time | 计费开始时间 |
| EndTime | uint32 | column:end_time | 计费结束时间 |
| BillingTime | uint32 | column:billing_time | 实际扣费时间 |
| RegionID | uint32 | column:region_id | 可用区 ID |
| CreateTime | uint32 | column:create_time | 创建时间 |
| UpdateTime | uint32 | column:update_time | 更新时间 |

### 3.2 TConnectInfo（`db/model/t_connect_info.gen.go:10-17`）

连接信息表，记录 Endpoint 与 Service 的连接关系及时间区间。

### 3.3 TService（`db/model/t_service.gen.go:14-33`）

服务表，包含 `Payer` 字段区分 Endpoint 付费还是 Service 付费。

### 3.4 TTrafficInfo（`db/model/t_traffic_info.gen.go:10-22`）

流量信息表，记录每条流量的出入方向、所属 Endpoint/Service、账户信息等。

### 3.5 TVpcEndpoint（`db/model/t_vpc_endpoint.gen.go:14-31`）

VPC Endpoint 表，记录端点的账户信息、关联 Service、创建/删除时间。

## 4. 自动生成方式

参见 `README.md` 和 `cmd/tools/mysqlgen/main.go`：

1. 配置 `cmd/tools/mysqlgen/conf/gen.json`，指定 DSN、输出路径、表名
2. 运行 `go run cmd/tools/mysqlgen/main.go`
3. GORM Gen 自动读取 MySQL 表结构生成对应 Model 和 Query 代码

## 5. 涉及的源文件

所有文件均为自动生成，不可编辑：
- `db/model/t_billing_info.gen.go`
- `db/model/t_connect_info.gen.go`
- `db/model/t_service.gen.go`
- `db/model/t_traffic_info.gen.go`
- `db/model/t_vpc_endpoint.gen.go`

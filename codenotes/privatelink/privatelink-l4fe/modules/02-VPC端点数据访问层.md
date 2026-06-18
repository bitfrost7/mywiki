# 模块 02：VPC 端点数据访问层 — VPC Endpoint Data Access

## 概述

该模块对应图分析 **Community 1「VPC Endpoint Data Access」**（71 个节点，内聚度 0.06），提供 `t_vpc_endpoint` 表的 ORM 数据访问层代码。由 GORM gen 自动生成。

## 源文件

- **`mygorm/db/t_vpc_endpoint.gen.go`** — DAO 实现（自动生成，436 行）
- **`mygorm/model/t_vpc_endpoint.gen.go`** — 数据模型（自动生成，35 行）

## 核心结构体

### TVpcEndpoint 模型 (`model/t_vpc_endpoint.gen.go:14-30`)

映射 `t_vpc_endpoint` 表，字段包括：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | `uint32` | 自增主键 |
| `EndpointID` | `string` | 端点 ID（业务主键） |
| `ServiceID` | `string` | 关联的服务 ID |
| `AccountID` | `uint32` | 所属账户 |
| `VnetID` | `string` | 虚拟网络 ID |
| `SubnetworkID` | `string` | 子网 ID |
| `TunnelID` | `uint32` | 隧道 ID |
| `Ipv4` | `string` | IPv4 地址 |
| `Ipv6` | `string` | IPv6 地址 |
| `Mac` | `string` | MAC 地址 |
| `ConnectBw` | `uint32` | 连接带宽 |
| `ConnectStatus` | `uint32` | 连接状态（1=已连接） |
| `InsertTime` | `uint32` | 插入时间 |
| `UpdateTime` | `time.Time` | 更新时间 |
| `DeleteTime` | `uint32` | 删除时间（0=未删除） |

### tVpcEndpoint DAO 结构 (`db/t_vpc_endpoint.gen.go:51-72`)

与 `tService` DAO 结构类似，包含所有字段的 field.Expr 和完整的 CRUD 接口 `ITVpcEndpointDo`。

## 在系统中的使用

该 DAO 在 `api/grpc_api.go:207-214` 中被调用：

```go
vpcEndpoints, err = tx.TVpcEndpoint.WithContext(ctx).Select().Where(
    g.query.TVpcEndpoint.ServiceID.In(serviceIDs...),
    g.query.TVpcEndpoint.ConnectStatus.Eq(1), // 已连接
    g.query.TVpcEndpoint.DeleteTime.Eq(0),
).Find()
```

查询条件：
- `ServiceID IN (...)` — 按 Service ID 过滤
- `ConnectStatus = 1` — 只返回已连接的端点
- `DeleteTime = 0` — 未删除

返回的 VPC Endpoint 数据用于构建：
- `foreIPs` — 前端 VIP 列表（`grpc_api.go:42-57`）
- `foreGroups` — 每个 Endpoint 对应一个 GwGroup（`grpc_api.go:68-109`）

## IP 地址处理

每个 Endpoint 可能同时有 IPv4 和 IPv6 地址：
- 每个非空地址会同时出现在 `foreIPs` 列表和对应的 `GwGroup.Endpoints` 中
- IPv4 endpoint ID 后缀 `-ipv4`，IPv6 后缀 `-ipv6`

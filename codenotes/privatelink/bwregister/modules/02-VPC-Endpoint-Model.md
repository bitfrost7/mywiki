# 模块: VPC Endpoint Model

> 社区 #1 — 20 节点 · 凝聚力 0.06

---

## 概述

VPC Endpoint 模型封装了 `t_vpc_endpoint` 数据表的 ORM 模型与查询层。该表存储 Privatelink VPC 端点的详细信息，包括网络信息、连接状态、带宽配置等，是带宽限速计算的核心数据源之一。

---

## 文件索引

### 数据表模型

**`db/model/t_vpc_endpoint.gen.go`** — gorm gen 自动生成（L11-39）

| 结构体 | 行号 | 说明 |
|--------|------|------|
| `TableNameTVpcEndpoint` | `:11` | 常量，表名 `t_vpc_endpoint` |
| `TVpcEndpoint` | `:14` | VPC 端点数据模型 |

**TVpcEndpoint 字段（关键）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `EndpointID` | string | 端点 ID |
| `ServiceID` | string | 关联的服务 ID |
| `CompanyID` | uint32 | 公司 ID |
| `AccountID` | uint32 | 账户 ID |
| `TunnelID` | uint32 | 隧道 ID |
| `Ipv4` | string | IPv4 地址 |
| `Ipv6` | string | IPv6 地址 |
| `ConnectBw` | uint32 | 连接带宽 |
| `ConnectStatus` | uint32 | 连接状态（1=已连接） |
| `CloseStatus` | uint32 | 关闭状态（1=停服） |
| `DeleteTime` | uint32 | 删除时间（0=未删除） |
| `InsertTime` | uint32 | 创建时间 |
| `UpdateTime` | time.Time | 更新时间 |

### 查询层

**`db/query/t_vpc_endpoint.gen.go`** — gorm gen 自动生成的查询对象

| 类型 | 说明 |
|------|------|
| `tVpcEndpoint` | 查询结构体 |
| `ITVpcEndpointDo` | 查询接口 |
| `newTVpcEndpoint()` | 构造函数 |

### 业务使用

**`db/db.go`** 中 `Database.DescribeAllConnections()` 组织对 `t_vpc_endpoint` 的核心查询（L121-150）。

---

## 核心查询

**`Database.DescribeAllConnections()`** 在 `db/db.go:121` 执行：

```go
conds = append(conds, e.DeleteTime.Eq(0))      // 未删除
conds = append(conds, e.ConnectStatus.Eq(1))    // 已连接
conds = append(conds, s.DeleteTime.Eq(0))       // 服务未删除
```

该查询 JOIN `t_vpc_endpoint` 和 `t_service`，筛选出所有有效连接。

---

## 端点在限速流程中的作用

在 `task/limiter.go:50` 中，每个 VPC Endpoint 的带宽计算逻辑：

1. **正常状态**：限速值 = `ConnectBw * MB`
2. **停服状态**（`CloseStatus == 1`）：限速值 = `1 * KB`（`task/limiter.go:62-64`）
3. **白名单用户**（`CheckDisableLimitBandwidth` 返回 true）：限速值 = `BandwidthMax * MB`（`task/limiter.go:66-69`）
4. 同时为 IPv4 和 IPv6 各生成一条 TrafficInfo 记录

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `ITVpcEndpointDo` | Database Transaction Context (C3) | 通过 `queryCtx.TVpcEndpoint` 桥接 |
| `Use()` | Database Connection Manager (C8) | 通过 `query.Use(gormDB)` 桥接 |
| `DescribeAllConnections()` | Bandwidth Traffic Manager (C7) | 带宽同步从 DB 读取端点数据 |
| `newTVpcEndpoint()` | Database Transaction Context (C3) | 构造函数涉及事务上下文 |

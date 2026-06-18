# 模块: Service Model Operations

> 社区 #4 + #2（合并） — 12 + 8 节点 · 凝聚力 0.09 / 0.11

---

## 概述

Service 模型封装了 `t_service` 数据表的 ORM 模型与查询操作层。该表存储 Privatelink 服务端口的定义信息，包括服务 ID、所属公司/账户、带宽配置和网络信息。Service 模型在带宽计算中作为连接的关联方，提供服务端的所属关系和付费信息。

社区 #2（Service Query Operations, 8 节点）和社区 #4（Service Model Operations, 12 节点）因同属 `t_service` 表而被归类为相邻社区。

---

## 文件索引

### 数据表模型

**`db/model/t_service.gen.go`** — gorm gen 自动生成（L11-41）

| 结构体 | 行号 | 说明 |
|--------|------|------|
| `TableNameTService` | `:11` | 常量，表名 `t_service` |
| `TService` | `:14` | 服务数据模型 |

**TService 字段（关键）**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ServiceID` | string | 服务 ID |
| `CompanyID` | uint32 | 服务所属公司 ID |
| `AccountID` | uint32 | 服务所属账户 ID |
| `Payer` | uint32 | 付费方（用于 JOIN 查询时区分付费关系） |
| `Description` | string | 服务描述 |
| `AutoAccept` | uint32 | 是否自动接受连接请求 |
| `ConnectBw` | uint32 | 默认连接带宽 |
| `TunnelID` | uint32 | 隧道 ID |
| `IP` | string | 服务 IP |
| `CloseStatus` | uint32 | 关闭状态 |
| `ResourceType` | uint32 | 资源类型 |
| `ResourceID` | string | 资源 ID |
| `DeleteTime` | uint32 | 删除时间 |
| `InsertTime` | uint32 | 创建时间 |
| `UpdateTime` | time.Time | 更新时间 |

### 查询层

**`db/query/t_service.gen.go`** — gorm gen 自动生成的查询对象

| 类型 | 说明 |
|------|------|
| `tService` | 查询结构体 |
| `ITServiceDo` | 查询接口 |
| `newTService()` | 构造函数 |
| `tServiceDo` | 查询 DO（Data Object） |

---

## 核心查询

**`Database.DescribeAllConnections()`** 在 `db/db.go:121-150` 中 JOIN `t_service`：

```go
.Join(s, s.ServiceID.EqCol(e.ServiceID))
.Where(conds...)
```

通过 `s.ServiceID.As("s_service_id")` 等别名将 Service 字段混入 `ConnectionInfo` 结果。这是 bwregister 中对 `t_service` 的唯一查询场景。

---

## ServiceInfo 结构体

定义在 `db/db.go:108-114`：

```go
type ServiceInfo struct {
    SServiceID  string `gorm:"column:s_service_id"`
    SCompanyID  uint32 `gorm:"column:s_company_id"`
    SAccountID  uint32 `gorm:"column:s_account_id"`
    SPayer      uint32 `gorm:"column:s_payer"`
    SDeleteTime uint32 `gorm:"column:s_delete_time"`
}
```

作为 `ConnectionInfo` 的嵌入部分（`db/db.go:116-119`），在带宽计算中用于：

1. **付费方判断**：`SCompanyID` / `SAccountID` 确定服务方
2. **ShareBW 聚合键**：`SServiceID` 作为共享带宽的聚合键
3. **白名单检查**：`CheckDisableLimitBandwidth(SCompanyID, SAccountID)` 在 `task/limiter.go:66`

---

## ShareBWInfo 中的服务角色

在 `task/limiter.go:98-155`，服务 ID（`conn.SServiceID`）作为共享带宽的聚合键：

```go
if sharebwInfo, ok := sharebwInfoMap[conn.ServiceID]; !ok {
    // 首次遇到该 Service，创建新的 ShareBWInfo
}
```

所有属于同一 Service 的 Endpoint 共享一个 ShareBWInfo 分组。

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `ITServiceDo` | Database Transaction Context (C3) | 通过 `queryCtx.TService` 桥接 |
| `Use()` | Database Connection Manager (C8) | 通过 `query.Use(gormDB)` 桥接 |
| `DescribeAllConnections()` | Bandwidth Traffic Manager (C7) | JOIN t_service 读取服务方信息 |

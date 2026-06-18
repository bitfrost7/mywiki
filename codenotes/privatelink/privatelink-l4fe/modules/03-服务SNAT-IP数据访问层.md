# 模块 03：服务 SNAT IP 数据访问层 — Service SNAT IP Data Access

## 概述

该模块对应图分析 **Community 2「Service SNAT IP Data Access」**（70 个节点，内聚度 0.06），提供 `t_service_snatips` 表的 ORM 数据访问层代码。由 GORM gen 自动生成。

## 源文件

- **`mygorm/db/t_service_snatips.gen.go`** — DAO 实现（自动生成，400 行）
- **`mygorm/model/t_service_snatips.gen.go`** — 数据模型（自动生成，22 行）

## 核心结构体

### TServiceSnatip 模型 (`model/t_service_snatips.gen.go:10-17`)

映射 `t_service_snatips` 表，字段包括：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | `uint32` | 自增主键 |
| `ServiceID` | `string` | 关联的服务 ID |
| `IP` | `string` | SNAT IP 地址 |
| `Mac` | `string` | MAC 地址 |
| `InsertTime` | `uint32` | 插入时间 |
| `DeleteTime` | `uint32` | 删除时间（0=未删除） |

## 在系统中的使用

该 DAO 在 `api/grpc_api.go:224-228` 中被调用：

```go
serviceSnatips, err = tx.TServiceSnatip.WithContext(ctx).Select().Where(
    g.query.TServiceSnatip.ServiceID.In(serviceIDs...),
    g.query.TServiceSnatip.DeleteTime.Eq(0),
).Find()
```

查询条件：
- `ServiceID IN (...)` — 按 Service ID 过滤
- `DeleteTime = 0` — 未删除

返回的 SNAT IP 数据用于构建：
- `fnatips` — FNAT IP 地址列表（`grpc_api.go:60-66`）
- `fnatGroups` — FNAT 转发组（`grpc_api.go:111-133`）

## FullNAT 特性

与 Fore 和 Backend 不同，FNAT 转发组的端口范围从 **1025** 开始（注释说明：只有 fullnat group 是从 1025 开始），详见 `grpc_api.go:118`。

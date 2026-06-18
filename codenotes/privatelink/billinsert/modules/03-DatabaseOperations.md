# billinsert - module 03: Database Operations

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 6** (14 nodes, 凝聚力 0.10)
> **验证状态**: ✓ | **来源文件**: `db/query/gen.go`

---

## 1. 模块职责

Database Operations 是 gorm.io/gen 自动生成的 **查询门面层**，负责：

- **统一查询入口**：通过 `Use()` 函数返回包含所有表查询对象的 `Query` 结构体
- **读写分离**：提供 `ReadDB()` / `WriteDB()` 方法，支持通过 `dbresolver` 插件路由到不同数据库实例
- **事务管理**：提供 `Transaction()`、`Begin()`、`Commit()`、`Rollback()` 等完整事务操作
- **上下文传递**：通过 `WithContext()` 将 context.Context 传递到所有查询操作中

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Use()` | `db/query/gen.go:18-25` | 函数 | 全局入口，传入 `*gorm.DB` 返回 `*Query` |
| `Query` | `db/query/gen.go:27-33` | 结构体 | 查询门面，聚合所有表查询对象 |
| `Query.Available()` | `db/query/gen.go:35` | 方法 | 检查 db 是否可用 |
| `Query.ReadDB()` | `db/query/gen.go:46-48` | 方法 | 切换到只读数据库 |
| `Query.WriteDB()` | `db/query/gen.go:50-52` | 方法 | 切换到只写数据库 |
| `Query.ReplaceDB()` | `db/query/gen.go:54-61` | 方法 | 替换底层 `*gorm.DB` 实例 |
| `queryCtx` | `db/query/gen.go:63-67` | 结构体 | 携带上下文（context）的查询代理 |
| `Query.WithContext()` | `db/query/gen.go:69-75` | 方法 | 注入 context，返回带上下文的查询代理 |
| `Query.Transaction()` | `db/query/gen.go:77-79` | 方法 | 事务执行函数 |
| `Query.Begin()` | `db/query/gen.go:81-84` | 方法 | 开启事务 |
| `QueryTx` | `db/query/gen.go:86-89` | 结构体 | 事务对象（含 Commit / Rollback / SavePoint 方法） |

## 3. 关键实现逻辑

### 3.1 Query 结构（`db/query/gen.go:27-33`）

```go
type Query struct {
    db *gorm.DB
    TService     tService
    TTrafficInfo tTrafficInfo
    TVpcEndpoint tVpcEndpoint
}
```

billinsert 仅使用 3 张表，因此 `Query` 仅包含这 3 个查询对象。**注意**：`db/query/` 目录下还生成了 `t_service_snatips.gen.go` 和 `t_service_whitelist.gen.go`，但它们未在 `Use()` 中注册，表明 billinsert 的**查询入口与实际使用的表不匹配**——这可能是代码生成时配置了多余的表，或者这两个表的查询代码被保留但未使用。

### 3.2 Use() 初始化（`db/query/gen.go:18-25`）

```go
func Use(db *gorm.DB, opts ...gen.DOOption) *Query {
    return &Query{
        db:           db,
        TService:     newTService(db, opts...),
        TTrafficInfo: newTTrafficInfo(db, opts...),
        TVpcEndpoint: newTVpcEndpoint(db, opts...),
    }
}
```

### 3.3 读写分离（`db/query/gen.go:46-52`）

```go
func (q *Query) ReadDB() *Query {
    return q.ReplaceDB(q.db.Clauses(dbresolver.Read))
}
func (q *Query) WriteDB() *Query {
    return q.ReplaceDB(q.db.Clauses(dbresolver.Write))
}
```

利用 `gorm.io/plugin/dbresolver` 的 `Read` / `Write` 子句实现读写分离路由。

### 3.4 上下文传递（`db/query/gen.go:69-75`）

`WithContext()` 将 context 传递到所有子查询对象中，确保日志、监控、超时等可以正确获取上下文信息。

### 3.5 查询对象接口

每个表的查询对象（如 `tService`）实现了 `ITServiceDo` 接口，提供类型安全的 CRUD 操作：

| 接口 | 文件 | 对应表 |
|------|------|--------|
| `ITServiceDo` | `db/query/t_service.gen.go` | `t_service` |
| `ITTrafficInfoDo` | `db/query/t_traffic_info.gen.go` | `t_traffic_info` |
| `ITVpcEndpointDo` | `db/query/t_vpc_endpoint.gen.go` | `t_vpc_endpoint` |
| `ITServiceSnatipDo` | `db/query/t_service_snatips.gen.go` | `t_service_snatips`（未在 Use() 注册） |
| `ITServiceWhitelistDo` | `db/query/t_service_whitelist.gen.go` | `t_service_whitelist`（未在 Use() 注册） |

## 4. 重要设计决策

### 4.1 gorm.io/gen 自动生成
整个 `db/query/` 目录由 `cmd/tools/mysqlgen` 工具自动生成。配置在 `cmd/tools/mysqlgen/conf/gen.json`：

```json
{
    "DSN": "...",
    "OutPath": "../../../db/query",
    "ModelPath": "../../../db/model",
    "Tables": ["t_service", "t_vpc_endpoint", "t_traffic_info"]
}
```

### 4.2 社区间桥梁
`Use()` 是系统中 **betweenness 最高的节点**（0.330），它连接了：
- Database Operations ↔ Database Layer（通过 `*gorm.DB`）
- Database Operations ↔ Service Data Model
- Database Operations ↔ Traffic Info Model
- Database Operations ↔ VPC Endpoint Model

## 5. 建议补充信息

1. `t_service_snatips` 和 `t_service_whitelist` 的代码已生成但未被 `Use()` 注册，是否为废弃代码？
2. dbresolver 的具体配置（读写分离的目标实例）
3. 生成的查询代码版本是否与当前 schema 一致（需要重新执行 `mysqlgen`）

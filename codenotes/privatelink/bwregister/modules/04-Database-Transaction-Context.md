# 模块: Database Transaction Context

> 社区 #3 — 14 节点 · 凝聚力 0.10

---

## 概述

数据库事务上下文是 gorm gen 自动生成的查询框架层，提供统一的数据库访问入口（`Use()`）、查询上下文（`WithContext()`）和事务管理（`Transaction()`/`Begin()`/`Commit()`/`Rollback()`）。该模块是连接各业务模型（Service/UserConfig/VPCEndpoint）查询的枢纽，也是整个 bwregister 数据库访问的基础设施层。

---

## 文件索引

**`db/query/gen.go`** — gorm gen 自动生成的查询入口（L1-105）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `Use()` | `:18` | 全局查询入口，基于 `*gorm.DB` 初始化 Query |
| `Query` | `:27` | 查询结构体，聚合三个表的查询对象 |
| `.Available()` | `:35` | 检查数据库连接是否可用 |
| `.clone()` | `:37` | 克隆查询对象（用于事务） |
| `.ReadDB()` | `:46` | 切换到只读数据库 |
| `.WriteDB()` | `:50` | 切换到写入数据库 |
| `.ReplaceDB()` | `:54` | 替换底层的 `*gorm.DB` |
| `queryCtx` | `:63` | 上下文查询结构体，持有三个表的接口引用 |
| `.WithContext()` | `:69` | 绑定 context 到查询 |
| `.Transaction()` | `:77` | 执行事务（回调模式） |
| `.Begin()` | `:81` | 手动开始事务 |
| `QueryTx` | `:86` | 事务查询类型，嵌入 `*Query` |
| `.Commit()` | `:91` | 提交事务 |
| `.Rollback()` | `:95` | 回滚事务 |
| `.SavePoint()` | `:99` | 设置保存点 |
| `.RollbackTo()` | `:103` | 回滚到保存点 |

---

## 核心数据结构

### Query 结构体

`db/query/gen.go:27-33`：

```go
type Query struct {
    db *gorm.DB
    TService     tService
    TUserConfig  tUserConfig
    TVpcEndpoint tVpcEndpoint
}
```

聚合了全部三张业务表的查询对象，应用层通过 `query.TService`, `query.TUserConfig`, `query.TVpcEndpoint` 访问。

### queryCtx 结构体

`db/query/gen.go:63-67`：

```go
type queryCtx struct {
    TService     ITServiceDo
    TUserConfig  ITUserConfigDo
    TVpcEndpoint ITVpcEndpointDo
}
```

持有三张表的`DO`接口引用，通过 `WithContext(ctx)` 传入 context。

---

## 核心流程

### 初始化入口

在 `db/db.go:45` `NewDatabase()` 中：

```go
gormDB, err := gorm.Open(...)
return &Database{db: query.Use(gormDB)}, nil
```

`query.Use(gormDB)` 创建包含三个表查询器的顶层 `Query` 实例。

### 业务查询调用方式

在 `db/db.go:121` `DescribeAllConnections()`：

```go
e := d.db.TVpcEndpoint  // 端点查询器
s := d.db.TService      // 服务查询器
e.WithContext(ctx).Select(...).Join(...).Where(...).Scan(&results)
```

在 `db/db.go:152` `GetUserConfig()`：

```go
t := d.db.TUserConfig
t.WithContext(ctx).Select(...).Find()
```

---

## 社区桥接

`Use()` 是图中跨社区中心度最高的节点（0.650），连接了：

| 目的社区 | 连接方式 |
|----------|----------|
| User Configuration Model (C0) | 初始化 `TUserConfig` |
| VPC Endpoint Model (C1) | 初始化 `TVpcEndpoint` |
| Service Model Operations (C2/C4) | 初始化 `TService` |
| Database Connection Manager (C8) | 由 `NewDatabase()` 调用 |
| Database Transaction Context (C3) | 自身 |

---

## 事务的使用

bwregister 的 `DescribeAllConnections()` 和 `GetUserConfig()` 均为只读查询，当前未使用事务功能。`Transaction()`/`Begin()` 等方法是为未来写入操作预留的框架能力。

写入/更新操作为纯全量替换的同步模式，不在本服务内直接修改数据。

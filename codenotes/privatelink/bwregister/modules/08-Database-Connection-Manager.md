# 模块: Database Connection Manager

> 社区 #8 — 12 节点 · 凝聚力 0.20

---

## 概述

数据库连接管理器负责初始化 MySQL 数据库连接、配置连接池参数、集成日志和监控中间件，并封装业务查询方法。该模块是 bwregister 的数据访问层核心，管理数据库生命周期并提供 `DescribeAllConnections()` 和 `GetUserConfig()` 两个业务查询入口。

---

## 文件索引

**`db/db.go`** — 数据库连接管理与业务查询（L1-167）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| 默认常量 | `:24-26` | `DefaultConnMaxLifetime=1h`, `DefaultMaxIdleConns=100` |
| `Config` | `:28` | 数据库连接配置（DSN, ConnMaxLifetime, MaxIdleConns） |
| `extract()` | `:34` | 上下文日志提取器（RequestUUID, SessionID） |
| `Database` | `:41` | 数据库封装结构体 |
| `NewDatabase()` | `:45` | 构造函数：初始化 GORM 连接和监控 |
| `EndpointInfo` | `:92` | VPC 端点信息结构体（DB 查询结果映射） |
| `ServiceInfo` | `:108` | 服务信息结构体（DB 查询结果映射） |
| `ConnectionInfo` | `:116` | 连接信息结构体（组合 EndpointInfo + ServiceInfo） |
| `DescribeAllConnections()` | `:121` | 查询所有活跃连接（JOIN 查询） |
| `GetUserConfig()` | `:152` | 查询所有用户配置 |

---

## Database 结构体

**`db/db.go:41-43`**：

```go
type Database struct {
    db *query.Query     // gorm gen 查询入口
}
```

通过 `query.Query` 封装了三张表的查询能力：`TService`、`TUserConfig`、`TVpcEndpoint`。

---

## 连接初始化

**`NewDatabase()` 在 `db/db.go:45-90`**：

```
1. 创建 zapgorm2 logger          (L46-47)
2. 配置日志上下文提取器 extract   (L47)
3. 设置日志级别                  (L50-59)
4. gorm.Open(mysql.Open(DSN))   (L61-66)
5. gormDB.Use(插件)             (L69-77)
   └─ plugin.NewMonitor() 监控中间件
6. sqlDB.SetConnMaxLifetime()   (L84)
7. sqlDB.SetMaxIdleConns()      (L85)
8. return &Database{db: query.Use(gormDB)}  (L87-89)
```

### 日志上下文提取

**`extract()` 在 `db/db.go:34-39`**：

```go
func extract(ctx context.Context) []zapcore.Field {
    fields = append(fields, zap.Any(ucontext.RequestUUID, ...))
    fields = append(fields, zap.Any(ncontext.SessionID, ...))
    return fields
}
```

自动从 context 中提取 `RequestUUID` 和 `SessionID` 附加到数据库日志。

### 监控中间件

**`db/db.go:69-77`**：使用 `privatelink-utils/gorm/plugin.NewMonitor()`：

```go
gormDB.Use(plugin.NewMonitor(&plugin.Config{
    DBStatCollectInterval:   10,                         // DB 统计采集间隔
    DBStatCollector:         xpro.ExportDBStats,          // 连接数统计
    DBBeforeMetricCollector: xpro.ExportDBBeforeMetric,   // 请求前指标
    DBAfterMetricCollector:  xpro.ExportDBAfterMetric,    // 请求后指标
}))
```

指标包括：
- `privatelink_bwregister_server_resource_gauge{type="db_connections"}` — 数据库连接数
- `privatelink_bwregister_client_request_sent_total{type="db"}` — DB 请求计数
- `privatelink_bwregister_client_response_received_total{type="db"}` — DB 响应计数
- `privatelink_bwregister_client_response_received_delay{type="db"}` — DB 响应延时

---

## 数据模型结构体

### ConnectionInfo

**`db/db.go:116-119`**：组合了 Endpoint 和 Service 两方信息：

```go
type ConnectionInfo struct {
    EndpointInfo          // 端点侧信息
    ServiceInfo           // 服务侧信息
}
```

### EndpointInfo

**`db/db.go:92-106`**：映射 `t_vpc_endpoint` 表字段（EndpointID, ServiceID, CompanyID, AccountID, TunnelID, Ipv4, Ipv6, ConnectBw, ConnectStatus, CloseStatus, InsertTime, UpdateTime, DeleteTime）

### ServiceInfo

**`db/db.go:108-114`**：映射 `t_service` 表字段（SServiceID, SCompanyID, SAccountID, SPayer, SDeleteTime）

---

## 核心业务查询

### DescribeAllConnections

**`db/db.go:121-150`**：

```go
func (d *Database) DescribeAllConnections(ctx context.Context) ([]*ConnectionInfo, error) {
    e := d.db.TVpcEndpoint
    s := d.db.TService
    conds := []gen.Condition{
        e.DeleteTime.Eq(0),       // 端点未删除
        e.ConnectStatus.Eq(1),    // 端点已连接
        s.DeleteTime.Eq(0),       // 服务未删除
    }
    err := e.WithContext(ctx).
        Select(e.EndpointID, ..., s.ServiceID.As("s_service_id"), ...).
        Join(s, s.ServiceID.EqCol(e.ServiceID)).
        Where(conds...).Scan(&results)
}
```

这是 bwregister 最核心的查询，通过 JOIN `t_vpc_endpoint` 和 `t_service`，筛选所有活跃的 VPC 端点连接。

### GetUserConfig

**`db/db.go:152-167`**：查询 `t_user_config` 表所有配置记录，用于构建内存中的用户配置缓存。

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `NewDatabase()` | Application Server Setup (C5) | 由 `server.go:84` 调用 |
| `NewDatabase()` | Database Transaction Context (C3) | 通过 `query.Use(gormDB)` 创建 |
| `DescribeAllConnections()` | Bandwidth Traffic Manager (C7) | 带宽同步任务调用 |
| `GetUserConfig()` | User Configuration Model (C0/C12) | 用户配置同步调用 |
| `Config` | 系统配置 | DB 连接配置由应用配置传入 |

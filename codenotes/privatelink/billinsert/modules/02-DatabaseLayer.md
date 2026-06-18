# billinsert - module 02: Database Layer

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 8** (9 nodes, 凝聚力 0.24)
> **验证状态**: ✓ | **来源文件**: `db/db.go`

---

## 1. 模块职责

Database Layer 是 billinsert 的数据库连接管理层，负责：

- **GORM 初始化**：使用 `zapgorm2` 日志适配器将 GORM 日志接入 zap 日志系统
- **监控中间件**：注册自定义 GORM 插件，上报 DB 操作指标到 Prometheus
- **连接池配置**：设置连接最大存活时间和最大空闲连接数
- **数据查询**：提供业务所需的两个核心查询方法（获取活跃连接、批量插入流量）

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Config` | `db/db.go:28-32` | 结构体 | 数据库配置（DSN、连接生命周期、空闲连接数） |
| `extract()` | `db/db.go:34-39` | 函数 | 从 context 中提取 RequestUUID 和 SessionID 用于日志 |
| `Database` | `db/db.go:41-43` | 结构体 | 数据库门面，封装 `*query.Query` |
| `NewDatabase()` | `db/db.go:45-90` | 函数 | GORM 初始化入口 |
| `ConnectionInfo` | `db/db.go:92-102` | 结构体 | JOIN 查询结果结构体（端点+服务连接信息） |
| `GetAllConnectionsLastInterval()` | `db/db.go:105-126` | 方法 | 获取指定时间段内所有活跃连接 |
| `CreateTrafficInfo()` | `db/db.go:128-134` | 方法 | 批量插入流量计费记录 |

## 3. 关键实现逻辑

### 3.1 GORM 初始化流程（`db/db.go:45-90`）

```
NewDatabase(zapLogger, cfg)
  │
  ├─1. 创建 zapgorm2 日志适配器，绑定 extract() 提取上下文信息
  │
  ├─2. 根据日志级别设置 GORM 日志模式:
  │     Debug/Info → Info 模式
  │     Warn       → Warn 模式
  │     其他       → Error 模式
  │
  ├─3. gorm.Open(mysql.Open(cfg.DSN), &gorm.Config{Logger: loggerI})
  │
  ├─4. 注册监控插件 (plugin.NewMonitor):
  │     ├─ DBStatCollectInterval: 10 (秒)
  │     ├─ DBStatCollector:         xpro.ExportDBStats
  │     ├─ DBBeforeMetricCollector: xpro.ExportDBBeforeMetric
  │     └─ DBAfterMetricCollector:  xpro.ExportDBAfterMetric
  │
  ├─5. sqlDB.SetConnMaxLifetime(cfg.ConnMaxLifetime * time.Hour)
  │     └─ 默认 1 小时（通过 server.go 设置）
  │
  └─6. sqlDB.SetMaxIdleConns(cfg.MaxIdleConns)
        └─ 默认 100（通过 server.go 设置）
```

### 3.2 活跃连接查询（`db/db.go:105-126`）

```sql
SELECT
  e.endpoint_id, e.service_id, e.account_id, e.company_id,
  e.ipv4, e.ipv6,
  s.payer AS s_payer, s.account_id AS s_account_id, s.company_id AS s_company_id
FROM t_vpc_endpoint e
LEFT JOIN t_service s ON s.service_id = e.service_id
WHERE e.insert_time < endTime
  AND (e.delete_time = 0 OR e.delete_time > startTime)
```

查询逻辑说明：
- `LEFT JOIN t_service`：获取服务侧 payer、account_id、company_id
- `insert_time < endTime`：确保端点在计费周期开始前已创建
- `delete_time = 0 OR delete_time > startTime`：端点在计费周期内未被删除
- 使用 `field.Or()` 组合条件（`db/db.go:121`）

### 3.3 批量插入（`db/db.go:128-134`）

```go
func (d *Database) CreateTrafficInfo(ctx context.Context, infos []*model.TTrafficInfo) error {
    t := d.db.TTrafficInfo
    if err := t.WithContext(ctx).CreateInBatches(infos, 20); err != nil {
        return err
    }
    return nil
}
```

- 每批 20 条记录，避免单条大事务

### 3.4 日志上下文提取（`db/db.go:34-39`）

`extract()` 函数在每个 GORM 日志输出时从 context 中提取：
- `RequestUUID`（来自 `ucontext`)
- `SessionID`（来自 `ncontext`）

### 3.5 默认连接池参数（`db/db.go:23-26`）

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `DefaultConnMaxLifetime` | 1 | 单位：小时 |
| `DefaultMaxIdleConns` | 100 | 最大空闲连接数 |

## 4. 重要设计决策

### 4.1 监控插件
使用 `privatelink-utils/gorm/plugin.Monitor` 插件，通过回调函数上报：
- **DBStats**：每 10 秒上报数据库连接数（`OpenConnections`）
- **BeforeMetric**：每次 DB 操作前上报请求计数
- **AfterMetric**：每次 DB 操作后上报响应计数 + 延迟

### 4.2 日志级别映射
GORM 日志模式根据 zap Logger 级别动态调整，避免在生产环境打印过多 SQL。

## 5. 建议补充信息

1. `plugin.NewMonitor` 的具体实现细节
2. DSN 中 `parseTime=true` 和 `loc=Local` 的时间处理影响
3. 连接池参数的调优依据（当前 `MaxIdleConns=100` 是否偏大）

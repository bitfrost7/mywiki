# billing — module_02_Database_Operations

> 自动生成文档 | 社区 8 | 系统: billing | 时间: 2026-06-18

---

# Database Operations — 数据库操作模块

## 1. 模块职责

本模块是 billing 服务的**数据访问层核心**，负责：
- **数据库连接管理**：初始化 GORM + MySQL 连接，配置连接池与日志
- **流量数据查询**：按计费周期聚合获取流量信息
- **连接/付费方信息查询**：获取有效连接与端点付费方信息
- **订单管理**：创建计费订单、更新订单状态、重试失败订单
- **监控集成**：接入 DB 监控插件，上报 SQL 执行指标

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 说明 |
|------------|----------|------|
| `Config` | `db/db.go:30-34` | 数据库配置：DSN、连接生命周期、最大空闲连接数 |
| `extract` | `db/db.go:36-41` | 从 Context 提取 RequestUUID/SessionID 用于日志 |
| `Database` | `db/db.go:43-45` | 数据库对象，持有 `query.Query` 实例 |
| `NewDatabase` | `db/db.go:47-92` | GORM 初始化 + 日志级别适配 + 监控插件 + 连接池配置 |
| `TrafficInfo` | `db/db.go:94-102` | 流量信息聚合结构体（Endpoint/Service/Payer/Traffic） |
| `GetAllTrafficInfosLastInterval` | `db/db.go:105-124` | 获取上小时流量数据，按 EndpointID 分组求和 |
| `CreateBillingInfo` | `db/db.go:126-145` | 批量创建计费订单（每批 20 条） |
| `GetAllInitBillingInfo` | `db/db.go:147-166` | 查询指定时间前的未支付订单（提供给重试逻辑） |
| `GetAllConnectInfo` | `db/db.go:168-191` | 查询计费周期内的有效连接 |
| `EndpointPayerInfo` | `db/db.go:193-200` | Endpoint 付费方信息结构体（含 Service 付费方） |
| `GetAllEndpointPayerInfo` | `db/db.go:202-223` | 查询 Endpoint + Service 关联的付费方信息（LEFT JOIN） |
| `BillingOrder` | `db/db.go:225-248` | 更新订单状态（支付成功写入 OrderNo/BillingTime，失败写入错误原因） |
| `ReBillingWithOrderPaid` | `db/db.go:250-304` | 事务内重试失败订单：FOR UPDATE 锁定 → 查询已支付 → 重新扣费 |
| `SimplifyErrMsg` | `db/db.go:306-315` | 截断错误消息到 200 字符 |

## 3. 关键实现逻辑

### 3.1 数据库初始化（`NewDatabase` @ `db/db.go:47-92`）

```
1. 创建 zapgorm2 日志适配器，集成 extract() 注入请求上下文
2. 根据日志级别适配 GORM 日志级别（Debug/Info → Info, Warn → Warn, 其他 → Error）
3. gorm.Open(mysql.Open(DSN), ...) — 建立 MySQL 连接
4. gormDB.Use(plugin.NewMonitor(...)) — 接入 privatelink-utils 的 DB 监控插件
   - DBStatCollectInterval: 10s
   - 上报连接数、SQL 执行前后指标到 Prometheus
5. sqlDB.SetConnMaxLifetime / SetMaxIdleConns — 配置连接池
6. query.Use(gormDB) — 初始化 GORM Gen 生成的查询结构
```

### 3.2 流量数据查询（`GetAllTrafficInfosLastInterval` @ `db/db.go:105-124`）

- 查询 `t_traffic_info` 表，筛选 `insert_time ∈ (startTime, endTime]`
- 按 `endpoint_id` 分组，对 `out_traffic` 和 `in_traffic` 求和
- 使用 GORM Gen 的 `Select().Group().Scan()` 将结果映射到 `TrafficInfo` 结构体
- **关键 SQL**: `SELECT endpoint_id, SUM(out_traffic) AS out_traffic_sum, SUM(in_traffic) AS in_traffic_sum FROM t_traffic_info WHERE insert_time > ? AND insert_time <= ? GROUP BY endpoint_id`

### 3.3 连接信息查询（`GetAllConnectInfo` @ `db/db.go:168-191`）

查询计费周期内**仍在连接中**或**存在有效连接时段**的记录：

- **活跃连接**：`start_time < endTime AND end_time = 0`（连接尚未断开）
- **有效连接**：`start_time < endTime AND end_time > startTime`（连接时段与计费周期有交集）
- 使用 `field.Or(activeExpr, efficExpr)` 组合条件
- 按 `endpoint_id` 分组去重

### 3.4 付费方信息查询（`GetAllEndpointPayerInfo` @ `db/db.go:202-223`）

- `t_vpc_endpoint` LEFT JOIN `t_service` ON `service_id`
- 同时获取 Endpoint 的 account/company 和 Service 的 account/company
- 条件：`insert_time < endTime` + `(delete_time = 0 OR delete_time > startTime)`
- 排除已删除的 Endpoint

### 3.5 重试事务（`ReBillingWithOrderPaid` @ `db/db.go:250-304`）

```
Transaction:
  1. SELECT ... FOR UPDATE — 悲观锁锁定待重试订单
  2. 遍历每个失败订单:
     a. 调用 rePaid 回调（查询 UBill 已支付 → 若未支付则重新扣费）
     b. 成功: 更新 OrderNo/State/Comment/BillingTime
     c. 失败: 仅更新 Comment/UpdateTime（记录错误）
```

- 使用 `clause.Locking{Strength: "UPDATE"}` 实现行级锁
- 查询范围：`startTime ∈ [rebillStartTime, rebillEndTime)` + `state != success` + `type = orderType`

### 3.6 订单状态更新（`BillingOrder` @ `db/db.go:225-248`）

- 成功：更新 `state = "success"`、`order_no`、`billing_time`
- 失败：更新 `comment`（错误原因，截断至 200 字符）
- 匹配条件：`item_id + start_time + type` 唯一确定一条订单记录

## 4. 涉及的源文件

- `db/db.go`（全部，315 行）

# billing — 架构设计

> 自动生成文档 | 系统: billing | 时间: 2026-06-18
> **置信度**: 高 | **验证状态**: ✓

---

# 架构设计

## 整体架构

**cron 驱动的单体应用（Cron-Driven Monolith）**

billing 是一个**定时任务驱动的单体服务**，无 HTTP API 服务端口，不对外暴露 RPC/HTTP 接口。核心架构特征：

- **定时调度**：依赖 `github.com/robfig/cron/v3` 库按 cron 表达式周期性执行计费任务
- **主从选主**：基于 ZooKeeper 的 Master 选举机制，同一集群中仅 master 节点执行计费
- **分层结构**：`server.go`(编排层) → `task/`(业务层) → `db/`(数据层) + `factory/`(外部调用层)
- **后付费模型**：先使用后付费，每小时统计用量并向 UBill 系统发起后付费扣费

## 路由机制

**无外部路由**。billing 不接收外部请求，所有"路由"体现在：

1. **cron 表达式路由**：`server.go:116-163` 中注册的 5 个定时任务，每个任务绑定一个 cron spec 字符串
2. **UBill Action 路由**：`factory/ubill/basic.go` 中每个方法设置不同的 `Action` 字段值，由 UBill 网关根据 Action 分发

## 核心模块

| 模块 | 社区 | 文件位置 | 职责 |
|------|------|----------|------|
| Application Server | C5 | `server.go`, `cmd/main.go` | 服务生命周期管理、配置加载、cron 注册、ZK 选主 |
| Database Operations | C8 | `db/db.go` | MySQL 数据库初始化、CRUD 操作、GORM 查询封装 |
| Billing Logic | C9 | `task/billing.go`, `task/rebilling.go` | 流量/实例计费计算、订单创建、支付与重试 |
| Factory Layer | C10,C7,C11,C12 | `factory/*.go` | UBill 外部计费 API 的 HTTP 客户端封装 |
| Data Access Layer | C6 | `db/query/gen.go` | GORM 生成的查询入口，读写分离 + 事务管理 |
| Metrics | C5 | `prometheus/prometheus.go` | Prometheus 指标收集（系统 + 业务） |
| Main CLI | C13 | `cmd/tools/mysqlgen/main.go` | 数据库模型代码生成工具 |

## 数据流

### 流量计费流程

```
1. cron 触发 TrafficBilling 任务
   └── server.go:116-124
       ↓
2. Task.TrafficBilling()
   └── task/billing.go:39-121
       │
       ├── 2a. db.GetAllTrafficInfosLastInterval()  → 获取上小时流量数据
       │    └── db/db.go:105-124
       │
       ├── 2b. 按 Payer 分流：
       │    ├── Payer=0(Service付费): 聚合到Service订单 + 记录Endpoint流量
       │    └── Payer=1(Endpoint付费): 直接生成Endpoint订单
       │
       ├── 2c. db.CreateBillingInfo()  → 批量写入订单表
       │    └── db/db.go:126-145
       │
       └── 2d. 对每个可计费订单：
            ├── fac.UBillImpl.TrafficPostPaid()  → 调用UBill扣费
            │    └── factory/ubill/expand.go:8-39
            └── db.BillingOrder()  → 更新订单状态
                 └── db/db.go:225-248
```

### 实例计费流程

```
1. cron 触发 InstanceBilling 任务
   └── server.go:136-144
       ↓
2. Task.InstanceBilling()
   └── task/billing.go:157-249
       │
       ├── 2a. db.GetAllConnectInfo()  → 获取有效连接
       │    └── db/db.go:168-191
       │
       ├── 2b. db.GetAllEndpointPayerInfo()  → 获取付费方信息
       │    └── db/db.go:202-223
       │
       ├── 2c. 计算实例倍数（不足1小时按1小时算）
       │    └── InstanceMultiple() @ task/billing.go:252-258
       │
       ├── 2d. 按 Payer 分流（同流量计费）
       │
       ├── 2e. db.CreateBillingInfo()  → 写入订单
       │
       └── 2f. 对每个可计费订单：
            ├── fac.UBillImpl.InstancePostPaid()  → 调用UBill扣费
            └── db.BillingOrder()  → 更新订单状态
```

### 重试计费流程

```
1. cron 触发 ReBilling 任务
   └── server.go:127-134 / server.go:146-154
       ↓
2. db.ReBillingWithOrderPaid()
   └── db/db.go:250-304
       │
       ├── 事务内 FOR UPDATE 锁定失败订单
       │
       ├── 对每个失败订单：
       │   ├── 查询UBill是否已支付 → 若已支付，直接更新状态
       │   └── 若未支付 → 重新扣费
       │
       └── 更新订单状态（成功/失败）
```

### 主从选主流

```
1. NewServer()  → ZK.NewMaster2() 注册选主
   └── server.go:83-88
       ↓
2. isMaster()  → atomic CAS 判断
   └── server.go:197-199
       ↓
3. MasterLoop()  → 监听ZK上下文，切换主从状态
   └── server.go:177-195
       ↓
4. 每个 cron 任务执行前检查 isMaster()
   └── task/task.go:27-34
```

## 定时任务配置

定义在 `server.go:29-36`，通过配置文件注入：

| 任务 | 配置字段 | 典型值 | 说明 |
|------|----------|--------|------|
| 流量计费 | TrafficBillingSpec | `"0 0 * * * *"` | 每小时整点执行 |
| 流量重试 | TrafficReBillingSpec | 按需 | 周期重试失败订单 |
| 实例计费 | InstanceBillingSpec | `"0 0 * * * *"` | 每小时整点执行 |
| 实例重试 | InstanceReBillingSpec | 按需 | 周期重试失败订单 |
| 主从监控 | MonMasterSpec | `"*/5 * * * * *"` | 每5秒上报主从状态 |

## 关键设计决策

1. **聚合计费**：Service 付费模式下，同一 Service 下所有 Endpoint 的流量/实例费聚合为一个订单，减少扣费次数
2. **零流量不计费**：流量为 0 的订单标记为 `NoTrafficRecord`，仅记录不扣费
3. **幂等重试**：重试时先查询 UBill 是否已支付，已支付的直接更新状态而非重复扣费
4. **FOR UPDATE 锁**：重试时使用 `SELECT ... FOR UPDATE` 悲观锁，防止并发重试
5. **Prometheus 埋点**：关键路径均有指标上报（落单数、失败数、任务完成数、API 调用延迟等）

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (≥0.9) | 所有主要结构和逻辑均从源码直接确认 |
| 需人工审查 | 0 个事实 |

*置信度基于源码可验证性计算*

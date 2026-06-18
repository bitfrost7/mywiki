# billing — 代码知识图谱

> Graphify 自动分析 | PrivateLink 计费服务
> 模块: Go 单体应用 · cron 驱动 · 后付费计费

---

## 概览

billing 是 PrivateLink 的**定时计费服务**，以 cron 调度方式周期性执行流量费和实例费的计算、扣费与重试。非 HTTP API 服务，无外部请求入口；通过 ZooKeeper 选主确保同一时刻仅 master 节点执行计费任务。

| 指标 | 数值 |
|------|------|
| Go 源文件数 | 24 |
| 社区数 | 27（有效代码社区 9 个） |
| 架构模式 | cron 驱动 + 分层单体 |
| 计费类型 | 流量后付费 / 实例后付费 |
| 外部依赖 | UBill 计费系统 · Prometheus · MySQL (GORM) |

---

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心抽象：

| 节点 | 连接数 | 文件 |
|------|--------|------|
| `Logger` | 9 | `db/db.go` |
| `Database` | 8 | `db/db.go` |
| `Task` | 6 | `task/task.go` |
| `Factory` | 4 | `factory/factory.go` |
| `Server` | 6 | `server.go` |
| `Context` | 7 | `db/db.go` |

---

## 社区导航

按功能组织的代码社区（模块）：

| # | 社区 | 社区名称 | 主要文件 | 说明 |
|---|------|----------|----------|------|
| 1 | 5 | Application Server | `server.go`, `cmd/main.go`, `task/task.go`, `prometheus/prometheus.go` | 服务启动、配置加载、cron 注册、主从选主 |
| 2 | 8 | Database Operations | `db/db.go` | 数据库初始化、数据查询与写入操作 |
| 3 | 9 | Billing Logic | `task/billing.go`, `task/rebilling.go` | 流量/实例计费与重试的核心业务逻辑 |
| 4 | 10,7,11,12 | Factory Layer | `factory/factory.go`, `factory/ubill/*.go`, `factory/common/common.go` | UBill 计费 API 封装、请求/响应结构体 |
| 5 | 6 | Data Access Layer | `db/query/gen.go` | GORM 生成的查询入口，读写分离与事务 |
| 6 | 0-4 | Query Models | `db/query/t_*.gen.go` | GORM 生成的每表查询结构（自动生成） |
| 7 | 14,15,20-22 | DB Models | `db/model/t_*.gen.go` | GORM 生成的每表数据模型（自动生成） |
| 8 | 13 | Main Configuration | `cmd/tools/mysqlgen/main.go` | 代码生成工具入口 |

---

## 关键流程图

```
[ZooKeeper 选主]
      |
[Server.Start()]
      |
[cron 调度] ──┬── TrafficBilling  (每小时)
              ├── TrafficReBilling (周期重试)
              ├── InstanceBilling  (每小时)
              ├── InstanceReBilling (周期重试)
              └── MonMaster        (每5秒)
      |
[Task] ──→ [db.Database] ──→ [MySQL]
      └──→ [factory.Factory] ──→ [UBill API]
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `api.md` | UBill 外部 API 接口说明 |
| `architecture.md` | 架构设计与数据流 |
| `modules/` | 各模块详细文档 |

# billing — module_01_Application_Server

> 自动生成文档 | 社区 5 | 系统: billing | 时间: 2026-06-18

---

# Application Server — 应用服务模块

## 1. 模块职责

本模块是 billing 服务的**入口与编排层**，负责：
- **服务启动**：加载配置、初始化依赖（DB/Factory/Cron）、注册 ZK 选主
- **Cron 任务注册**：将计费任务绑定到 cron 表达式
- **主从管理**：通过 ZooKeeper 实现 Master 选举，确保单一节点执行计费
- **指标采集**：系统资源（CPU/内存/DB连接数）与业务指标的上报

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Config` | `server.go:21-37` | 结构体 | 服务配置，含 DB、HTTP、cron、ZK 等全部配置项 |
| `VerifyParams` | `server.go:39-52` | 方法 | 配置参数校验，确保必填项非空 |
| `SetDefaultValue` | `server.go:54-64` | 方法 | 设置默认值（HTTP 超时、DB 连接池） |
| `Server` | `server.go:66-73` | 结构体 | 核心服务对象，持有 app.Application、DB、Factory、Task |
| `NewServer` | `server.go:75-110` | 函数 | 初始化服务：ZK 选主 → DB 初始化 → Factory → Cron 注册 → 指标收集 |
| `InitCronTask` | `server.go:112-166` | 方法 | 注册 5 个定时任务到 cron 调度器 |
| `Start` | `server.go:168-175` | 方法 | 启动 cron + app 生命周期 |
| `MasterLoop` | `server.go:177-195` | 方法 | ZK Master 回调，atomic CAS 切换主从状态 |
| `isMaster` | `server.go:197-199` | 方法 | 原子操作判断当前节点是否为 Master |
| `monMaster` | `server.go:201-207` | 方法 | 每 5 秒上报主从状态到 Prometheus |
| `LastHourRange` | `server.go:210-215` | 函数 | 计算上小时的 [startTime, endTime) 时间戳 |

**cmd/main.go:**

| 函数 | 代码位置 | 说明 |
|------|----------|------|
| `main` | `cmd/main.go:20-43` | CLI 入口，支持 3 个子命令：start / dumpcfg / version |
| `runServer` | `cmd/main.go:45-53` | 加载配置并启动服务 |
| `loadConfig` | `cmd/main.go:55-65` | 读取 JSON 配置文件 |
| `dumpConfig` | `cmd/main.go:67-73` | 输出默认配置模板 |
| `init` | `cmd/main.go:88-90` | 注册 Prometheus 版本 Collector |

**task/task.go:**

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `Task` | `task/task.go:12-16` | 任务结构体，持有 cron、DB、Factory |
| `InitTask` | `task/task.go:18-24` | 初始化 Task 实例 |
| `AddTask` | `task/task.go:26-43` | 添加带 Master 检查的定时任务 |
| `StartTask` | `task/task.go:45-49` | 启动 cron 调度器 |

## 3. 关键实现逻辑

### 3.1 服务启动流程（`NewServer` @ `server.go:75-110`）

```
1. s.Init(cfg)             — app 框架初始化
2. cfg.SetDefaultValue()   — 配置默认值填充
3. ZK.NewMaster2()         — ZooKeeper Master 选举注册
4. db.NewDatabase()        — GORM + MySQL 连接初始化 + 监控插件
5. factory.InitFactory()   — UBill HTTP Client 初始化
6. InitCronTask()          — 注册 5 个定时任务
7. CollectSysMetrics()     — 启动系统指标协程（CPU/内存每 10s 采集）
```

### 3.2 Master 选举机制

billing 使用 ZooKeeper 实现 Master 选举（`server.go:83-88`）：

- `ZK.NewMaster2()` 在 ZK 路径上注册临时节点，抢注成功的节点成为 Master
- Master 状态通过 `atomic` 包中的 `uint32` 标志位维护（`server.go:72`）
- `MasterLoop`（`server.go:177-195`）：当 ZK 上下文取消时（失联或失去 Master），将状态切回 follower
- 每个 cron 任务执行前调用 `isMaster()`（`task/task.go:28-34`）：非 Master 节点跳过任务执行
- `monMaster`（`server.go:201-207`）：每 5 秒将当前主从状态上报到 `privatelink_billing_common_gauge{type="is_master"}`

### 3.3 Cron 任务注册（`InitCronTask` @ `server.go:112-166`）

注册 5 个定时任务：

| 序号 | 任务 | 回调函数 | 调度表达式 |
|------|------|----------|-----------|
| 1 | 流量计费 | `TrafficBilling` | 从 `cfg.TrafficBillingSpec` 读取 |
| 2 | 流量重试 | `TrafficReBilling` | 从 `cfg.TrafficReBillingSpec` 读取 |
| 3 | 实例计费 | `InstanceBilling` | 从 `cfg.InstanceBillingSpec` 读取 |
| 4 | 实例重试 | `InstanceReBilling` | 从 `cfg.InstanceReBillingSpec` 读取 |
| 5 | 主从监控 | `monMaster` | 从 `cfg.MonMasterSpec` 读取，典型 5s 间隔 |

### 3.4 配置结构（`Config` @ `server.go:21-37`）

| 字段                      | 类型                  | 说明                          |
| ----------------------- | ------------------- | --------------------------- |
| `ApplicationConfig`     | embedded            | app 框架配置（ServiceAddr, ZK 等） |
| `DBConfig`              | `db.Config`         | MySQL DSN + 连接池配置           |
| `HTTPConfig`            | `httpclient.Config` | UBill HTTP 客户端配置            |
| `RegionID`              | uint32              | 可用区 ID                      |
| `MasterLockPath`        | string              | ZK Master 锁路径               |
| `MasterServicePath`     | string              | ZK 服务注册路径                   |
| `InternalAPIURL`        | string              | UBill 系统 API 地址             |
| `TrafficBillingSpec`    | string              | 流量计费 cron 表达式               |
| `TrafficReBillingSpec`  | string              | 流量重试 cron 表达式               |
| `InstanceBillingSpec`   | string              | 实例计费 cron 表达式               |
| `InstanceReBillingSpec` | string              | 实例重试 cron 表达式               |
| `MonMasterSpec`         | string              | 主从监控 cron 表达式               |
| `ReBillingCycleTime`    | uint32              | 重试周期（天）                     |
| `ReBillingTimeOut`      | uint32              | 重试超时（秒）                     |
| `ActivityId`            | uint32              | 活动 ID                       |

## 4. 涉及的源文件

- `cmd/main.go`（全部，90 行）
- `server.go`（全部，215 行）
- `task/task.go`（全部，49 行）
- `prometheus/prometheus.go`（全部，134 行）

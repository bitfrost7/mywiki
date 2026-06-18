# billinsert - module 01: Application Server

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> 社区: **Community 5** (28 nodes, 凝聚力 0.07)
> **验证状态**: ✓ | **来源文件**: `server.go`, `cmd/main.go`, `task/task.go`, `task/insert.go`

---

## 1. 模块职责

Application Server 是 billinsert 的核心编排模块，负责：

- **CLI 入口**：解析命令行参数（`start` / `dumpcfg` / `version`）
- **配置管理**：加载、校验、设置默认值的配置生命周期管理
- **服务初始化**：ZooKeeper 选主、数据库连接、CloudWatch 工厂初始化
- **Cron 任务调度**：注册并启动定时插入流量任务和主从状态监控任务
- **主从管理**：Master/Slave 状态切换感知、Prometheus 上报

## 2. 主要函数/类型清单

| 类型/函数名 | 代码位置 | 类型 | 说明 |
|------------|----------|------|------|
| `Config` | `server.go:21-34` | 结构体 | 应用级配置，含 DB、CloudWatch、Region 等 |
| `Config.VerifyParams()` | `server.go:36-49` | 方法 | 校验必填配置项 |
| `Config.SetDefaultValue()` | `server.go:51-64` | 方法 | 设置默认值（超时、连接池、QPS 限制） |
| `Server` | `server.go:66-73` | 结构体 | 服务主对象，聚合 Application、DB、Factory、Task |
| `NewServer()` | `server.go:75-110` | 函数 | 服务初始化入口（选主、DB、Factory、Cron、指标） |
| `Server.InitCronTask()` | `server.go:112-135` | 方法 | 注册两个 Cron 任务 |
| `Server.Start()` | `server.go:137-142` | 方法 | 启动 Cron + 应用 Serve 循环 |
| `Server.MasterLoop()` | `server.go:144-162` | 方法 | ZK Master 回调，感知主从切换 |
| `Server.isMaster()` | `server.go:164-166` | 方法 | CAS 检查当前是否为主 |
| `Server.monMaster()` | `server.go:168-174` | 方法 | 上报主从状态到 Prometheus |
| `EveryHourRange()` | `server.go:177-182` | 函数 | 计算当前小时的起止时间戳 |
| `main()` | `cmd/main.go:20-43` | 函数 | CLI 入口，解析命令并分发 |
| `runServer()` | `cmd/main.go:45-53` | 函数 | 加载配置并调用 NewServer().Start() |
| `loadConfig()` | `cmd/main.go:55-65` | 函数 | 从 JSON 文件读取配置 |
| `dumpConfig()` | `cmd/main.go:67-73` | 函数 | 打印默认配置模板 |
| `showVersion()` | `cmd/main.go:75-77` | 函数 | 打印版本 |
| `usage()` | `cmd/main.go:79-86` | 函数 | 打印使用帮助 |
| `init()` | `cmd/main.go:88-90` | 函数 | 注册 Prometheus 版本信息采集 |
| `Task` | `task/task.go:13-17` | 结构体 | Cron 任务封装 |
| `InitTask()` | `task/task.go:19-26` | 函数 | 创建 Task 实例 |
| `Task.AddTask()` | `task/task.go:28-45` | 方法 | 添加带 Master 检查的 Cron 任务 |
| `Task.StartTask()` | `task/task.go:47-51` | 方法 | 启动 Cron 调度器 |
| `InsertTrafficInfo()` | `task/insert.go:16-63` | 方法 | 核心业务：拉取流量并写入数据库 |
| `TrafficInOutMax()` | `task/insert.go:66-69` | 函数 | 合并 IPv4 + IPv6 流量 |
| `Max()` | `task/insert.go:71-76` | 函数 | 取两个 uint64 的最大值 |

## 3. 关键实现逻辑

### 3.1 服务启动流程（`server.go:75-110`）

```
NewServer(cfg)
  ├─ s.Init(cfg)                // 基类初始化（日志、ZK 客户端等）
  ├─ cfg.SetDefaultValue()      // 设置配置默认值
  ├─ s.ZK.NewMaster2(...)       // ZK 选主注册
  ├─ db.NewDatabase(...)        // GORM 数据库连接初始化
  ├─ factory.InitFactory(...)   // CloudWatch HTTP 客户端初始化
  ├─ s.InitCronTask(ctx)        // 注册 Cron 定时任务
  └─ xpro.CollectSysMetrics()   // 启动系统资源指标采集 goroutine
```

### 3.2 Cron 任务调度（`server.go:112-135`）

| 任务 | Cron 表达式 | 频率 | 说明 |
|------|-------------|------|------|
| `InsertTrafficInfo` | 配置项 `InsertTrafficSpec`（默认 `"0 2 * * * *"`） | 每小时第 2 分钟 | 拉取上一小时的流量数据并写入 `t_traffic_info` |
| `monMaster` | 配置项 `MonMasterSpec`（默认 `"*/5 * * * * *"`） | 每 5 秒 | 上报当前主从状态到 Prometheus |

**Master 守卫机制**（`task/task.go:29-37`）：
- InsertTrafficInfo 任务注册时传入了 `isMaster` 回调函数
- 每次任务触发时，先检查是否为 Master，非 Master 跳过执行
- monMaster 任务没有 `isMaster` 检查（所有节点都上报）

### 3.3 流量插入核心流程（`task/insert.go:16-63`）

```
InsertTrafficInfo(region, startTime, endTime)
  │
  ├─1. d.GetAllConnectionsLastInterval(ctx, startTime, endTime)
  │     └─ 查询 t_vpc_endpoint LEFT JOIN t_service
  │        获取所有在计费周期内活跃的 Endpoint 连接信息
  │
  ├─2. fac.CloudwatchImpl.FetchEndpointInOutBandTrafficData(endpointIDs, region, startTime, endTime)
  │     └─ 并发拉取 4 个指标的监控数据
  │
  ├─3. 遍历每个连接：
  │     ├─ TrafficInOutMax() 合并 IPv4 + IPv6 入/出流量
  │     ├─ Max(In, Out) 取最大流量
  │     └─ 确定计费归属（端点付费 PayerEndpointInt=1 / 服务方付费 PayerEndpointServiceInt=0）
  │
  └─4. db.CreateTrafficInfo(ctx, trafficInfos) 批量写入
```

### 3.4 计费归属逻辑（`task/insert.go:41-48`）

```go
// PayerEndpointInt = 1: 端点付费 → 使用端点侧 account_id / company_id
// PayerEndpointServiceInt = 0: 服务方付费 → 使用服务侧 s_account_id / s_company_id
if c.Payer == PayerEndpointInt {
    trafficInfo.AccountID = c.AccountID
    trafficInfo.CompanyID = c.CompanyID
}
if c.Payer == PayerEndpointServiceInt {
    trafficInfo.AccountID = c.SAccountID
    trafficInfo.CompanyID = c.SCompanyID
}
```

### 3.5 主从切换生命周期（`server.go:144-166`）

```
MasterLoop(ctx)  // ZK 回调，当本节点成为 Master 时调用
  ├─ CAS: master 0→1 (标记为主)
  ├─ 等待 context 取消（主从切换或服务停止）
  └─ CAS: master 1→0 (标记为从)
```

## 4. 关键配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| `InsertTrafficSpec` | `"0 2 * * * *"` | 每小时第 2 分钟执行（Cron 含秒字段） |
| `MonMasterSpec` | `"*/5 * * * * *"` | 每 5 秒检查主从状态 |
| `CloudWatchQPSLimit` | 10 | CloudWatch API 限流 |

## 5. 不确定内容标注

### 【确认】
- `dumpConfig()` 打印的默认配置模板仅包含 `ApplicationConfig` 字段，不包含 billinsert 自定义字段。

## 6. 建议补充信息

1. ZK Master Path 的命名规则与 ZK 集群部署拓扑
2. 多 Region 部署时的配置差异
3. 流量插入失败时的告警和重试策略

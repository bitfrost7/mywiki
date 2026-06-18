# billinsert - 架构设计

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> **验证状态**: ✓ | **来源**: graphify 代码图谱全量分析

---

# 架构设计

## 整体架构

**后台定时任务（Background Scheduler）**。这是一个典型的 **定时任务 + 数据搬运** 服务，非 Web 服务，不对外暴露 HTTP API。它通过 ZooKeeper 实现 Master/Slave 选主，确保同一时刻只有一个实例执行流量插入任务。

### 架构层次

```
┌─────────────────────────────────────────────────────┐
│                   cmd/main.go                       │
│               CLI 入口 (start/dumpcfg/version)       │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  server.go                          │
│  ┌─────────────┐  ┌───────────┐  ┌───────────────┐  │
│  │ ZK 选主     │  │ DB 初始化  │  │ Factory 初始化 │  │
│  └─────────────┘  └───────────┘  └───────────────┘  │
│  ┌────────────────────────────────────────────────┐  │
│  │            Cron 任务调度                        │  │
│  │  ┌──────────────────┐  ┌────────────────────┐  │  │
│  │  │ InsertTrafficInfo│  │  monMaster          │  │  │
│  │  │ (每小时执行)      │  │ (每5秒检查主从状态)  │  │  │
│  │  └────────┬─────────┘  └────────────────────┘  │  │
│  └───────────┼────────────────────────────────────┘  │
└──────────────┼───────────────────────────────────────┘
               │
    ┌──────────┴──────────┬──────────────────┐
    ▼                     ▼                  ▼
┌────────────┐  ┌─────────────────┐  ┌──────────────┐
│ db/db.go   │  │ factory/        │  │ prometheus/  │
│ Database   │  │ cloudwatch/     │  │ metrics      │
│ Layer      │  │ CloudWatch API  │  │              │
└─────┬──────┘  └─────────────────┘  └──────────────┘
      │
┌─────▼─────────────────────────────────────────┐
│ db/query/ + db/model/ (gorm.io/gen 生成)      │
│ TService / TVpcEndpoint / TTrafficInfo        │
└───────────────────────────────────────────────┘
```

## 数据流

```
[定时触发: cron "0 2 * * * *" (每小时第2分钟)]
    │
    ▼
task.InsertTrafficInfo()
    │
    ├─1. db.GetAllConnectionsLastInterval()
    │     └─ JOIN t_vpc_endpoint + t_service
    │        筛选条件: insert_time < endTime AND (delete_time=0 OR delete_time > startTime)
    │
    ├─2. fac.CloudwatchImpl.FetchEndpointInOutBandTrafficData()
    │     └─ 并发拉取 4 个指标的数据:
    │         ├─ ep_in_bw (IPv4 入带宽)
    │         ├─ ep_out_bw (IPv4 出带宽)
    │         ├─ ep_in_bw_ipv6 (IPv6 入带宽)
    │         └─ ep_out_bw_ipv6 (IPv6 出带宽)
    │         └─ 按 20 个资源一组分批查询，每次请求间隔受 QPS 限流
    │
    ├─3. TrafficInOutMax() 合并 IPv4 + IPv6 流量
    │
    ├─4. 组装 TTrafficInfo 记录（含计费归属: 端点付费/服务方付费）
    │
    └─5. db.CreateTrafficInfo() 批量写入 t_traffic_info 表
```

## 核心模块

| 模块 | 文件位置 | 职责 |
|------|----------|------|
| CLI 入口 | `cmd/main.go` | 解析命令行参数，分发到 `start` / `dumpcfg` / `version` |
| 应用服务 | `server.go` | ZK 选主、DB/Factory 初始化、Cron 任务注册与启动 |
| 定时任务 | `task/task.go`, `task/insert.go` | Cron 任务管理 + 流量数据插入主逻辑 |
| 数据库层 | `db/db.go` | GORM 初始化、连接查询（JOIN 查询）、批量写入 |
| ORM 查询模型 | `db/query/*.gen.go` | gorm.io/gen 自动生成的表查询对象（tService, tTrafficInfo, tVpcEndpoint） |
| ORM 数据模型 | `db/model/*.gen.go` | gorm.io/gen 自动生成的 Go 结构体（TService, TVpcEndpoint, TTrafficInfo 等） |
| CloudWatch 工厂 | `factory/factory.go` | 工厂初始化，组合 CloudwatchImpl |
| CloudWatch 实现 | `factory/cloudwatch/impl.go` | HTTP 客户端初始化、QPS 限流器 |
| CloudWatch API | `factory/cloudwatch/basic.go` | 请求/响应结构体定义、指标查询方法 |
| CloudWatch 计算 | `factory/cloudwatch/expand.go` | 批量拉取、重试、梯形积分法流量计算 |
| API 基类 | `factory/common/common.go` | IBaseRequest / IBaseResponse 接口 |
| Prometheus | `prometheus/prometheus.go` | 指标定义、系统资源采集、DB 监控回调 |
| 代码生成工具 | `cmd/tools/mysqlgen/main.go` | `gorm.io/gen` 封装，自动生成 model 和 query 代码 |

## 关键设计决策

### 1. Master/Slave 选主
- 通过 ZooKeeper `NewMaster2()` 实现选主（`server.go:83-88`）
- 每次 InsertTraffic 任务执行前检查 `isMaster()` 状态
- 每 5 秒通过 `monMaster()` 上报主从状态到 Prometheus

### 2. Cron 表达式配置
```json
"InsertTrafficSpec": "0 2 * * * *"    // 每小时第 2 分钟插入流量
"MonMasterSpec":     "*/5 * * * * *"   // 每 5 秒检查主从状态
```

### 3. 流量计算算法
使用 **梯形积分法**（`factory/cloudwatch/expand.go:107-125`）计算流量总量：
```
sum += (preRate + curRate) * (curTs - preTs) / 2
```

### 4. QPS 限流
CloudWatch API 调用受 `rate.Limiter` 控制，默认 10 QPS（`server.go:62-63`）。

### 5. 批量写入
`CreateTrafficInfo` 使用 `CreateInBatches(infos, 20)` 分批写入，避免大事务。

## 跨社区桥梁节点

| 节点 | Betweenness | 连接社区 |
|------|-------------|----------|
| `Use()` | 0.330 | Database Operations ↔ Database Layer / Service Data Model / Traffic Info Model / VPC Endpoint Model |
| `NewDatabase()` | 0.178 | Database Layer ↔ Application Server / Database Operations |
| `newTTrafficInfo()` | 0.151 | Traffic Info Model ↔ Database Operations |

## 输入/输出

| 方向 | 接口 | 说明 |
|------|------|------|
| 输入 | 配置文件 `conf/config.json` | 服务启动参数（DB DSN、ZK 地址、Region、API Key 等） |
| 输入 | CloudWatch Admin API | 拉取端点带宽监控数据 |
| 输出 | `t_traffic_info` 表 | 写入流量计费记录 |
| 输出 | Prometheus 指标 | 服务资源、任务状态、API 延迟、失败计数 |

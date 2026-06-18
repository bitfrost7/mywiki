# recycle — 架构设计

> 自动生成文档 | 系统: recycle | 时间: 2026-06-18
> **置信度**: 高 | **验证状态**: ✓

---

# 架构设计

## 整体架构

**cron 驱动 + HTTP API 的单体服务（Cron-Driven Monolith with HTTP API）**

recycle 是一个**定时任务驱动 + HTTP API 控制**的单体服务。同时提供：

- **HTTP API**：接收外部系统的停服/恢复/删除请求，仅处理 VPC Endpoint（`api/api.go:74-83`）
- **定时调度**：依赖 `github.com/robfig/cron/v3` 按 cron 表达式批量执行回收操作，同时处理 Endpoint 和 Service（`server.go:132-175`）
- **主从选主**：基于 ZooKeeper 的 Master 选举，同一集群中仅 master 节点执行回收（`server.go:83-88`）
- **分层结构**：`server.go`(编排层) → `api/`(接口层) + `task/`(业务层) → `db/`(数据层) + `factory/`(外部调用层)

### 三阶段回收模型

| 阶段 | 条件 | 操作 | 说明 |
|------|------|------|------|
| 停服 | 欠费后 CloseDelayTime（默认5分钟缓冲） | 更新 CloseStatus=1，断开连接记录 | 用户仍可恢复 |
| 恢复 | 停服后 24h 内（由 URecycleV2 侧控制） | 更新 CloseStatus=0，重建连接记录 | 仅在窗口期内可恢复 |
| 删除 | 停服超 24h（由 URecycleV2 侧控制） | 调用 PrivateLink API 删除资源，通知回收系统 | 不可恢复 |

**关键时序关系**：`CloseDelayTime` 是 recycle 侧控制的停服缓冲期（`server.go:59-61`），而 24h 恢复窗口由 URecycleV2 系统侧通过 `CloseTime` 和 `DeleteTime` 字段控制。

## 路由机制

### HTTP API 路由

所有请求走同一 POST `/` 路径，由 `Api.Handel()` 根据 `Action` 字段分发（`api/api.go:74-83`）。

| HTTP 方法 | 路径 | Action | 处理函数 | 调用的 Task 方法 | 文件:行号 |
|-----------|------|--------|----------|-----------------|-----------|
| POST | `/` | `CloseEndpoint` | `Api.CloseEndpoint()` | `Task.CloseEndpointWithDelay()` | `api/recycle.go:19-27` |
| POST | `/` | `RecycleEndpoint` | `Api.RecoverEndpoint()` | `Task.RecoverEndpoint()` | `api/recycle.go:30-38` |
| POST | `/` | `DeleteEndpoint` | `Api.DeleteEndpoint()` | `Task.DeleteEndpoint()` | `api/recycle.go:41-49` |

**注意**：API Action 名称 `RecycleEndpoint`（`api/api.go:77`）在路由层映射到方法 `RecoverEndpoint`（`api/recycle.go:30`），二者对应同一业务操作。

**Master 检查**：所有 API 请求仅在 master 节点处理，非 master 节点返回 `"Server is not master, cant reply"`（`server.go:123-127`）。

### Cron 路由

cron 任务注册于 `server.go:132-175`，每个任务同时处理 Endpoint 和 Service 两类资源：

| 任务 | cron spec 字段 | 回调（Endpoint） | 回调（Service） | 注册位置 |
|------|---------------|-----------------|----------------|----------|
| 停服 | `ToCloseSpec` | `CloseEndpointWithDelay` | `CloseEndpointServiceWithDelay` | `server.go:137-139` |
| 恢复 | `ToRecoverSpec` | `RecoverEndpoint` | `RecoverEndpointService` | `server.go:147-149` |
| 删除 | `ToDeleteSpec` | `DeleteEndpoint` | `DeleteEndpointService` | `server.go:157-159` |
| 主从监控 | `MonMasterSpec` | — | `monMaster` | `server.go:167-169` |

## 核心模块

| 模块 | 社区 | 文件位置 | 职责 |
|------|------|----------|------|
| 应用服务器 | C13, C3 | `cmd/main.go`, `server.go`, `task/task.go`, `prometheus/prometheus.go` | 服务生命周期、配置加载、cron 注册、ZK 选主、指标 |
| API 请求处理 | C6, C14, C28 | `api/api.go`, `api/recycle.go`, `api/code.go`, `factory/common/common.go` | HTTP POST 请求路由、Action 分发、错误码 |
| 资源回收业务 | C9, C32, C33 | `task/recycle_endpoint.go`, `task/recycle_service.go`, `db/db.go` | 三阶段回收核心逻辑：数据库状态更新 + 外部通知 |
| 外部服务工厂层 | C7, C4, C8, C10, C19, C11, C20 | `factory/*.go` | URecycleV2/PrivateLink/UResource 的 HTTP API 封装 |
| 数据库访问层 | C5, C12 | `db/query/gen.go`, `db/db.go` | MySQL GORM 连接管理、查询入口、事务封装 |
| 数据模型 | C0-2, C17-18, C24 | `db/model/*.go`, `db/query/t_*.go` | 三张表的 GORM 自动生成模型和查询结构 |

## 数据流

### Endpoint 停服流程

```
1. cron 触发 CloseEndpointWithDelay 或 API 直接调用
   └── server.go:137-139 / api/recycle.go:26
       ↓
2. Task.CloseEndpointWithDelay()
   └── task/recycle_endpoint.go:13-33
       │
       ├── 2a. fac.URecycle.GetToCloseEndpointList()
       │    └── factory/urecycle/expand.go:8-19 → basic.go:114-127 (Action: GetToCloseResourceList)
       │
       ├── 2b. fac.UResource.IGetResourceInfoById()  ← 过滤 RegionId
       │    └── factory/uresource/expand.go:9-21 → basic.go:65-79 (Action: IGetResourceById)
       │
       ├── 2c. 时间校验: now - CloseTime > delay
       │    └── task/recycle_endpoint.go:29
       │
       └── 2d. Task.CloseEndpoint()
            └── task/recycle_endpoint.go:37-52
                ├── db.CloseEndpointConnectInDB()  → 事务内双表更新
                │    └── db/db.go:93-118
                │        ├── UPDATE t_vpc_endpoint SET close_status=1
                │        └── UPDATE t_connect_info SET end_time=now
                │
                └── fac.URecycle.NotifyClosedEndpoint()  → 通知回收系统
                     └── factory/urecycle/expand.go:92-106
```

### Endpoint 恢复流程

```
1. cron 触发 RecoverEndpoint 或 API 直接调用
   └── server.go:147-149 / api/recycle.go:37
       ↓
2. Task.RecoverEndpoint()
   └── task/recycle_endpoint.go:55-87
       │
       ├── 2a. fac.URecycle.GetToRecoverEndpointList()
       │    └── factory/urecycle/expand.go:36-48
       ├── 2b. 过滤 RegionId
       ├── 2c. db.RecoverEndpointConnectInDB()  → 事务内三步骤
       │    └── db/db.go:120-168
       │        ├── SELECT endpoint WHERE close_status=1
       │        ├── UPDATE close_status=0
       │        └── if connect_status=1: INSERT INTO t_connect_info (start_time=now)
       └── 2d. fac.URecycle.NotifyRecoveredEndpoint()
            └── factory/urecycle/expand.go:124-138
```

### Endpoint 删除流程

```
1. cron 触发 DeleteEndpoint 或 API 直接调用
   └── server.go:157-159 / api/recycle.go:48
       ↓
2. Task.DeleteEndpoint()
   └── task/recycle_endpoint.go:90-122
       │
       ├── 2a. fac.URecycle.GetToDeleteEndpointList()
       │    └── factory/urecycle/expand.go:64-76
       ├── 2b. 过滤 RegionId
       ├── 2c. fac.PrivateLink.DeleteEndpoint()  → 调用网络系统删除
       │    └── factory/privatelink/expand.go:8-23
       │        └── factory/privatelink/basic.go:63-76 → APIRequestWithMetrics
       └── 2d. fac.URecycle.NotifyRecycledEndpoint()
            └── factory/urecycle/expand.go:156-170
```

### Service 回收流程

同 Endpoint 流程三阶段，区别在于：

- 停服时联级更新关联 Endpoint（`db/db.go:170-200`）：
  ```
  事务内：
    ├── UPDATE t_vpc_endpoint SET close_status=1 WHERE service_id=?
    ├── UPDATE t_service SET close_status=1 WHERE service_id=?
    └── UPDATE t_connect_info SET end_time=now WHERE service_id=? AND end_time=0
  ```
- 恢复时批量重建连接记录（`db/db.go:202-260`）
- 删除时调用 `PrivateLink.DeleteEndpointService()`（`task/recycle_service.go:109`），`Force=true`

### 主从选主流

```
1. NewServer()  → ZK.NewMaster2() 注册选主
   └── server.go:83-88
       ↓
2. isMaster()  → atomic CAS 判断 (atomic.CompareAndSwapUint32)
   └── server.go:205-207
       ↓
3. MasterLoop()  → 监听ZK上下文，切换主从状态
   └── server.go:185-203
       ↓
4. 每个 cron 任务执行前检查 isMaster()
   └── task/task.go:31-37
5. API 请求前检查 isMaster()
   └── server.go:123-127
```

## 定时任务配置

定义在 `server.go:22-35`，通过配置文件注入：

| 任务 | 配置字段 | 说明 |
|------|----------|------|
| 停服 | `ToCloseSpec` | 检查需停服资源（典型每小时一次） |
| 恢复 | `ToRecoverSpec` | 检查需恢复资源（典型每小时一次） |
| 删除 | `ToDeleteSpec` | 检查需删除资源（典型每小时一次） |
| 主从监控 | `MonMasterSpec` | 典型每 5 秒一次 |

## 数据库表结构

| 表名 | 模型 | 查询结构 | 说明 |
|------|------|----------|------|
| `t_vpc_endpoint` | `db/model/t_vpc_endpoint.gen.go:14-34` | `db/query/t_vpc_endpoint.gen.go` | VPC Endpoint 资源表，含 close_status、connect_status |
| `t_service` | `db/model/t_service.gen.go:14-36` | `db/query/t_service.gen.go` | Endpoint Service 资源表 |
| `t_connect_info` | `db/model/t_connect_info.gen.go:10-16` | `db/query/t_connect_info.gen.go` | 连接历史记录表 |

## 关键设计决策

1. **三阶段回收模型**：停服 → 可恢复窗口 → 删除，给用户 24 小时恢复缓冲期
2. **RegionId 过滤**：每个 Task 持有 `regionId`，操作前通过 UResource 查询资源 RegionId，仅操作本 Region 资源（`task/recycle_endpoint.go:26-28`）
3. **ZK 主从锁**：仅 master 节点执行 cron 任务和 API 处理，follower 拒接请求（`server.go:123-127`）
4. **幂等通知**：每次操作完成后均调用 URecycleV2 的回调接口通知状态变更
5. **Prometheus 埋点**：关键路径均有指标上报（`prometheus/prometheus.go`），含任务完成数、失败数、API 延迟等
6. **GORM 事务**：所有数据库写操作均在 `d.db.Transaction()` 内执行（`db/db.go:94, 120, 170, 202`）
7. **延迟停服机制**：`CloseDelayTime` 配置（默认 5 分钟缓冲），`time.Now().Unix() - resource.CloseTime > delay` 判定（`task/recycle_endpoint.go:29`）
8. **API 仅处理 Endpoint**：HTTP API 仅提供 Endpoint 的停服/恢复/删除操作，Service 回收仅由 cron 触发
9. **三层封装架构**：每个外部子系统（URecycle/PrivateLink/UResource）均遵循 impl.go → basic.go → expand.go 的三层结构

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (≥0.9) | 所有主要结构和逻辑均从源码直接确认 |
| 需人工审查 | 0 个事实 |

*置信度基于源码可验证性计算*

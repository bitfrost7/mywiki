# recycle — 代码知识图谱

> Graphify 自动分析 | PrivateLink 带宽回收服务
> Go 单体应用 · cron 驱动 · 三阶段资源回收

---

## 概览

recycle 是 PrivateLink 的**带宽回收服务**，负责 VPC Endpoint 和 Endpoint Service 的**欠费回收生命周期管理**。采用 cron 驱动的三阶段模型：**停服 → 恢复窗口 → 删除回收**，通过 ZooKeeper 选主确保同一时刻仅 master 节点执行回收任务。

| 指标 | 数值 |
|------|------|
| Go 源文件数 | 29（不含自动生成代码） |
| 图节点数 | 482 |
| 社区数 | 34（有效代码社区 16 个） |
| 架构模式 | cron 驱动 + 分层单体 + HTTP API |
| 资源类型 | VPC Endpoint (390) / Endpoint Service (389) |
| 回收模型 | 停服(延迟 5m+) → 可恢复(24h) → 删除 |
| 外部依赖 | URecycleV2 · UResource · PrivateLink · Prometheus · MySQL (GORM) |

---

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心抽象：

| 节点 | 源文件 | 说明 |
|------|--------|------|
| `Server` | `server.go` | 服务编排层：生命周期、选主、cron 注册、API 初始化 |
| `Task` | `task/task.go` | 定时任务封装：cron 绑定、Master 检查、任务启动 |
| `Api` | `api/api.go` | HTTP API 处理器：请求解析、Action 路由分发 |
| `Database` | `db/db.go` | 数据库封装：GORM 连接管理、事务操作、监控插件 |
| `Factory` | `factory/factory.go` | 外部服务聚合工厂：URecycleV2 / PrivateLink / UResource |
| `URecycleImpl` | `factory/urecycle/impl.go` | 回收系统客户端：获取待处理列表 + 通知状态变更 |
| `ResourceImpl` | `factory/uresource/impl.go` | 资源系统客户端：查询资源详细信息 |
| `PrivateLinkImpl` | `factory/privatelink/impl.go` | 网络系统客户端：执行 VPC Endpoint/Service 删除 |

---

## 社区导航

按功能组织的代码社区（模块）：

| # | 社区ID | 模块名称 | 主要文件 | 说明 |
|---|--------|----------|----------|------|
| 1 | C13, C3 | 应用服务器 | `cmd/main.go`, `server.go`, `task/task.go`, `prometheus/prometheus.go` | 服务启动、配置加载、cron 注册、ZK 选主、指标采集 |
| 2 | C6, C14, C28 | API 请求处理 | `api/api.go`, `api/recycle.go`, `api/code.go`, `factory/common/common.go` | 请求路由、Action 分发、错误码定义、请求/响应结构体 |
| 3 | C9, C32, C33 | 资源回收核心业务 | `task/recycle_endpoint.go`, `task/recycle_service.go`, `db/db.go` | 停服/恢复/删除三阶段业务逻辑，数据库状态更新 |
| 4 | C7, C4, C8, C10, C19, C11, C20 | 外部服务工厂层 | `factory/*` 全部文件 | 三个外部系统的 HTTP API 封装：URecycleV2 / PrivateLink / UResource |
| 5 | C5, C12 | 数据库访问层 | `db/query/gen.go`, `db/db.go` | GORM 查询入口、事务管理、读写分离、监控插件 |
| 6 | C16 | 代码生成工具 | `cmd/tools/mysqlgen/main.go` | GORM 数据库模型代码生成器入口 |

---

## 关键流程图

```
[HTTP API] ── POST / ──→ [Api.Handel()] ──→ CloseEndpoint / RecycleEndpoint / DeleteEndpoint
                                │
[ZooKeeper 选主] ──→ [Server.MasterLoop()]
      │
[Server.Start()]
      │
[cron 调度] ──┬── ToCloseSpec    (延时停服: 查待停服列表 → 过滤 RegionId → 校验时间 → 执行)
              ├── ToRecoverSpec  (恢复窗口: 查可恢复列表 → 更新状态 → 重建连接)
              ├── ToDeleteSpec   (删除回收: 查待删列表 → PrivateLink 删除 → 通知系统)
              └── MonMasterSpec  (每5秒上报主从状态到 Prometheus)
      │
[Task] ──→ [db.Database] ──→ [MySQL (t_vpc_endpoint / t_service / t_connect_info)]
      └──→ [Factory]
              ├── [URecycleV2]  — 获取待处理列表 + 通知状态变更 (GetToClose / NotifyClosed ...)
              ├── [UResource]   — 查询资源信息 (RegionId 过滤)
              └── [PrivateLink] — 执行 VPC Endpoint / Service 删除 (DeleteVPCEndpoint)
```

---

## 相关文档

| 文档 | 说明 |
|------|------|
| `api.md` | HTTP API 接口说明 |
| `architecture.md` | 架构设计与数据流 |
| `modules/` | 各模块详细文档 |

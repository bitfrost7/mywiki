# bwregister — 带宽注册与同步服务

> Graphify 自动分析 | 368 节点 · 661 边 · 21 社区

---

## 概览

bwregister 是一个运行在 Privatelink 体系中的 Go 服务，负责从数据库读取 VPC 端点和服务的连接信息，计算限速带宽值，并通过 gRPC 将流量限速信息（TrafficInfo）和共享带宽信息（ShareBWInfo）同步到带宽计算平台（UTraffic）。

| 指标 | 数值 |
|------|------|
| 节点数 | 368 |
| 边数 | 661 |
| 社区数 | 21 |
| 核心抽象（God Nodes） | 10 |
| gRPC API | 2 个方法 |

---

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心抽象：

| 节点 | 连接数 | 类型 | 文件 |
|------|--------|------|------|
| `tServiceDo` | 45 | code | `db/query/t_service.gen.go` |
| `tUserConfigDo` | 45 | code | `db/query/t_user_config.gen.go` |
| `tVpcEndpointDo` | 45 | code | `db/query/t_vpc_endpoint.gen.go` |
| `ITServiceDo` | 30 | code | `db/query/gen.go` |
| `ITUserConfigDo` | 30 | code | `db/query/gen.go` |
| `ITVpcEndpointDo` | 30 | code | `db/query/gen.go` |
| `tService` | 24 | code | `db/query/t_service.gen.go` |
| `tUserConfig` | 24 | code | `db/query/t_user_config.gen.go` |
| `tVpcEndpoint` | 24 | code | `db/query/t_vpc_endpoint.gen.go` |
| `Query` | 14 | code | `db/query/gen.go` |

---

## 社区导航

| # | 社区 | 节点数 | 凝聚力 |
|---|------|--------|--------|
| 1 | [User Configuration Model](modules/01-User-Configuration-Model.md) | 20 | 0.06 |
| 2 | [VPC Endpoint Model](modules/02-VPC-Endpoint-Model.md) | 20 | 0.06 |
| 3 | [Service Query Operations](modules/03-Service-Model-Operations.md) | 8 | 0.11 |
| 4 | [Database Transaction Context](modules/04-Database-Transaction-Context.md) | 14 | 0.10 |
| 5 | [Service Model Operations](modules/03-Service-Model-Operations.md) | 12 | 0.09 |
| 6 | [Application Server Setup](modules/05-Application-Server-Setup.md) | 15 | 0.12 |
| 7 | [gRPC Server Monitoring](modules/06-gRPC-Server-Monitoring.md) | 19 | 0.10 |
| 8 | [Bandwidth Traffic Manager](modules/07-Bandwidth-Traffic-Manager.md) | 12 | 0.16 |
| 9 | [Database Connection Manager](modules/08-Database-Connection-Manager.md) | 12 | 0.20 |
| 10 | [Main Configuration Loader](modules/09-Main-Configuration-Loader.md) | 7 | 0.36 |
| 11 | [Config Generation Tool](modules/10-Config-Generation-Tool.md) | 4 | 0.80 |

### 工具 / CI 社区（简略）

| # | 社区 | 说明 |
|---|------|------|
| 14 | Multi-Arch Build Images | Docker arm64/amd64 构建 |
| 15 | Manual Build Images | 手工触发构建 |
| 16 | Code Quality Checks | 代码检查与测试 |
| 17 | Service Documentation | 文档 |
| 18 | Database Model Generator | gorm gen 生成数据表模型 |
| 19 | Master Branch Template | 主分支模板 |
| 20 | Build Image Testing | 构建镜像测试 |

---

## gRPC API 接口

| 方法 | 位置 | 说明 |
|------|------|------|
| `GetAllTrafficInfo` | `api/grpc.go:24` | 获取全量资源限速信息（TrafficInfo） |
| `GetAllShareBWInfo` | `api/grpc.go:40` | 获取全量共享带宽信息（ShareBWInfo） |

---

## 数据流

```
bandwidth-calculation-platform (UTraffic)
        ↑ gRPC SyncAllTrafficInfo / SyncAllShareBWInfo
        |
bwregister (Task Loop)
        ↑ 定时任务 (cron)
        |
bwregister (Server.InitCronTask)
        ↑ NewDatabase()
        |
MySQL (privatelink db)
    ├── t_vpc_endpoint    — VPC 端点信息
    ├── t_service         — 服务信息
    └── t_user_config     — 用户配置（限速白名单等）
```

---

## 关键配置

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `RegisterSpec` | `*/10 * * * * *` | 每10秒注册连接限速值 |
| `SyncUserConfigSpec` | `0 * * * * *` | 每分钟同步用户配置 |
| `MonMasterSpec` | `*/5 * * * * *` | 每5秒上报主从状态 |
| `SyncZKPathSpec` | `*/10 * * * * *` | 每10秒同步节点信息 |
| `ClusterID` | `privatelink-bwregister` | 集群标识 |

---

## 架构特点

- **Master-Slave 模式**：通过 ZooKeeper 进行 Master 选举，只有 Master 节点执行"注册限速"和"同步ZK路径"等关键任务
- **Cron 驱动**：使用 `robfig/cron/v3` 实现定时任务，支持秒级精度
- **全量同步**：每次任务周期都是全量从数据库读取连接信息并同步到带宽计算平台
- **gRPC 双向**：对外提供 gRPC Server 供查询，对内作为 gRPC Client 调用 UTraffic 平台

---

## Graphify 分析报告

> 来源：graphify 知识图谱分析 (commit `32707c4f`)

- 图谱提取率：97% EXTRACTED · 3% INFERRED
- 未检测到导入循环
- 86 个孤立节点（连接 ≤1），需关注潜在的文档盲区
- `Use()` 是社区间桥接节点（跨社区中心度 0.650），连接数据库事务上下文到各模型层
- `NewDatabase()` 是次级桥接节点（跨社区中心度 0.363），连接数据库连接管理与应用启动流程

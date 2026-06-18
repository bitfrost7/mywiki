# billinsert — 代码知识图谱

> Graphify 自动分析 | 527 节点 · 975 边 · 25 社区

---

## 概览

| 指标 | 数值 |
|------|------|
| 节点数 | 527 |
| 边数 | 975 |
| 社区数 | 25 |
| Go 源码文件 | ~15 个 |
| 生成代码文件 | ~10 个（`db/model/*.gen.go`, `db/query/*.gen.go`） |
| 主要职责 | 每分钟定时拉取 CloudWatch 监控流量数据，写入计费数据库 |

## 项目定位

`billinsert` 是 **Privatelink 流量计费记录服务**。它作为后台常驻进程运行，通过 ZooKeeper 选主（Master/Slave），周期性地：

1. 查询当前活跃的 VPC Endpoint 连接
2. 调用内部 CloudWatch API 拉取端点入/出带宽（IPv4 + IPv6）的原始监控数据
3. 按梯形积分法计算流量总量
4. 批量写入 `t_traffic_info` 计费表

本服务 **不对外暴露 HTTP API**，仅提供定时任务执行。

## 核心抽象（God Nodes）

连接数最多的节点，代表系统的核心数据抽象：

| 节点 | 连接数 | 类型 | 文件 |
|------|--------|------|------|
| `tServiceDo` | 45 | code | `db/query/t_service.gen.go` |
| `tServiceSnatipDo` | 45 | code | `db/query/t_service_snatips.gen.go` |
| `tServiceWhitelistDo` | 45 | code | `db/query/t_service_whitelist.gen.go` |
| `tTrafficInfoDo` | 45 | code | `db/query/t_traffic_info.gen.go` |
| `tVpcEndpointDo` | 45 | code | `db/query/t_vpc_endpoint.gen.go` |
| `ITServiceDo` | 30 | code | `db/query/t_service.gen.go` |
| `ITTrafficInfoDo` | 30 | code | `db/query/t_traffic_info.gen.go` |
| `ITVpcEndpointDo` | 30 | code | `db/query/t_vpc_endpoint.gen.go` |

## 社区导航

按大小排序的代码社区（功能模块）：

| # | 社区 | 节点数 | 凝聚度 |
|---|------|--------|--------|
| 5 | **Application Server** (`server.go`, `cmd/main.go`, `task/*.go`) | 28 | 0.07 |
| 0 | **Service Data Model** (`db/query/t_service.gen.go`) | 20 | 0.06 |
| 1 | **VPC Endpoint Model** (`db/query/t_vpc_endpoint.gen.go`) | 20 | 0.06 |
| 2 | **Service SNAT IP Model** (`db/query/t_service_snatips.gen.go`) | 19 | 0.06 |
| 3 | **Service Whitelist Model** (`db/query/t_service_whitelist.gen.go`) | 19 | 0.06 |
| 4 | **Traffic Info Model** (`db/query/t_traffic_info.gen.go`) | 19 | 0.06 |
| 7 | **Monitor Data API** (`factory/cloudwatch/basic.go`) | 18 | 0.11 |
| 6 | **Database Operations** (`db/query/gen.go`) | 14 | 0.10 |
| 8 | **Database Layer** (`db/db.go`) | 9 | 0.24 |
| 10 | **CloudWatch Factory** (`factory/cloudwatch/impl.go`, `factory/factory.go`) | 8 | 0.27 |
| 12 | **Prometheus Metrics** (`prometheus/prometheus.go`) | 6 | 0.29 |
| 9 | **CloudWatch Metrics** (`factory/cloudwatch/expand.go`) | 5 | 0.33 |
| 11 | **Base API Interface** (`factory/common/common.go`) | 4 | 0.25 |
| 13 | **Main Configuration** (`cmd/tools/mysqlgen/main.go`) | 4 | 0.80 |

## 关键依赖

| 依赖 | 用途 |
|------|------|
| `gorm.io/gen` | ORM 代码生成器 (gorm.io/gen v0.3.26) |
| `github.com/robfig/cron/v3` | 定时任务调度 |
| `git.ucloudadmin.com/unetworks/privatelink/privatelink-utils` | HTTP 客户端、GORM 监控插件、上下文工具 |
| `git.ucloudadmin.com/cnat2/app` | 应用框架（ZK 选主、日志、服务生命周期） |
| `github.com/prometheus/client_golang` | Prometheus 指标暴露 |
| `git.ucloudadmin.com/unetworks/privatelink/billinsert/factory/cloudwatch` | CloudWatch 监控数据拉取 |

---

## 模块文档

| 文档 | 对应社区 | 内容 |
|------|----------|------|
| `modules/01-ApplicationServer.md` | Community 5 | 服务入口、配置、ZK 选主、Cron 调度 |
| `modules/02-DatabaseLayer.md` | Community 8 | 数据库连接初始化、GORM 配置、连接查询 |
| `modules/03-DatabaseOperations.md` | Community 6 | `query.Use()` 入口、读写分离、事务管理 |
| `modules/04-CloudWatchFactory.md` | Communities 7+9+10 | CloudWatch API 请求、流量数据拉取与计算 |
| `modules/05-BaseAPIInterface.md` | Community 11 | 请求/响应基类接口 |
| `modules/06-PrometheusMetrics.md` | Community 12 | Prometheus 指标定义与采集 |
| `modules/07-MainConfiguration.md` | Community 13 | GORM 代码生成工具 (`mysqlgen`) |
| `modules/08-DataModel.md` | Communities 0-4, 14-21 | ORM 查询模型与数据表 Schema |

---

## Graphify 分析报告

> 以下内容来自 graphify 的 GRAPH_REPORT.md

# Graph Report - billinsert (2026-06-18)

## Summary
- 527 nodes · 975 edges · 25 communities (18 shown, 7 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 18 edges (avg confidence: 0.6)

## Graph Freshness
- Built from commit: `32707c4f`

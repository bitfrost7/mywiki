# billinsert - API 文档

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-18
> **验证状态**: ✓

---

# API 文档

## 说明

`billinsert` 是一个后台定时任务服务，**不对外暴露 HTTP API 端点**。它的所有行为由 **配置文件** 和 **命令行参数** 控制。

## 命令行接口

| 命令 | 文件位置 | 说明 |
|------|----------|------|
| `billinsert -c <config> start` | `cmd/main.go:37` | 启动服务（ZK 选主 + Cron 定时任务） |
| `billinsert dumpcfg` | `cmd/main.go:35` | 打印默认配置结构（JSON 格式），用于生成配置模板 |
| `billinsert version` | `cmd/main.go:39` | 打印编译版本信息 |

## 配置项

配置文件路径通过 `-c` 参数指定（默认 `conf/config.json`）。

| 配置项 | 类型 | 位置 | 说明 |
|--------|------|------|------|
| `ServiceAddr` | string | `conf/config.json:2` | 服务监听地址，用于 ZK 注册 |
| `AdminAddr` | string | `conf/config.json:3` | 管理端口 |
| `Logger.Development` | bool | `conf/config.json:6` | 日志开发模式 |
| `Logger.Level` | string | `conf/config.json:7` | 日志级别（debug/info/warn/error） |
| `GRPCDial.Timeout` | int | `conf/config.json:9` | gRPC 连接超时（秒） |
| `GRPCDial.Insecure` | bool | `conf/config.json:10` | 是否允许不安全 gRPC 连接 |
| `DBConfig.DSN` | string | `conf/config.json:13` | MySQL 连接串 |
| `ZKServers` | []string | `conf/config.json:15-21` | ZK 服务器地址列表 |
| `RegionId` | uint32 | `server.go:25` | 地域 ID（配置中值为 666003/test03） |
| `Region` | string | `server.go:26` | 地域名称 |
| `InternalAPIURL` | string | `server.go:27` | 内部 API 地址 |
| `MasterServicePath` | string | `server.go:28` | ZK Master 服务路径 |
| `MasterLockPath` | string | `server.go:29` | ZK Master 锁路径 |
| `InsertTrafficSpec` | string | `server.go:30` | Cron 表达式，流量插入调度（默认 `"0 2 * * * *"`，每小时第2分钟） |
| `MonMasterSpec` | string | `server.go:31` | Cron 表达式，主从状态监控（默认 `"*/5 * * * * *"`，每5秒） |
| `CloudWatchApiKey` | string | `server.go:32` | CloudWatch API 鉴权 Key |
| `CloudWatchQPSLimit` | uint32 | `server.go:33` | CloudWatch API QPS 限制（默认 10） |

## 配置默认值（`server.go:51-64`）

```
HTTPConfig.Timeout      = 20 (秒，如果未设置)
DBConfig.ConnMaxLifetime = 1 (小时，如果未设置)
DBConfig.MaxIdleConns    = 100 (如果未设置)
CloudWatchQPSLimit       = 10 (如果未设置)
```

## 配置校验（`server.go:36-49`）

以下字段为必填，为空时将返回 `"empty config"` 错误：

- `DBConfig.DSN`
- `RegionId`
- `InternalAPIURL`
- `Region`
- `MasterServicePath`
- `MasterLockPath`
- `InsertTrafficSpec`
- `MonMasterSpec`
- `CloudWatchApiKey`

## Prometheus 指标

本服务通过 Prometheus `NewCollector` 注册版本信息（`cmd/main.go:89`），并在 `prometheus/prometheus.go` 中注册了以下指标：

| 指标 | 类型 | Label | 说明 |
|------|------|-------|------|
| `privatelink_billinsert_common_gauge` | Gauge | `type` | 通用 Gauge（如 `is_master`） |
| `privatelink_billinsert_server_resource_gauge` | Gauge | `type` | 服务资源（cpu/mem/db_connections） |
| `privatelink_billinsert_client_request_sent_total` | Counter | `api/type/service` | 外部请求计数 |
| `privatelink_billinsert_client_response_received_total` | Counter | `api/type/service/code` | 外部响应计数 |
| `privatelink_billinsert_client_response_received_delay` | Histogram | `api/type/service` | 响应延迟分布 |
| `privatelink_billinsert_task_status_counter` | Counter | `task_name/status` | 任务状态统计 |
| `privatelink_billinsert_fetch_metrics_fail` | Counter | `type/metric` | 指标拉取失败计数 |
| `privatelink_billinsert_fetch_metrics_delay` | Histogram | `metric` | 指标拉取延迟 |
| `privatelink_billinsert_traffic_insert_fail` | Counter | - | 流量插入失败计数 |

## 代码生成工具

`cmd/tools/mysqlgen/main.go` 是一个独立的代码生成工具，用于根据 MySQL 表结构自动生成 GORM Model 和 Query 代码：

```bash
cd cmd/tools/mysqlgen
# 编辑 conf/gen.json 配置 DSN / OutPath / ModelPath / Tables
go run main.go -c conf/gen.json
```

生成的文件：
| 目录 | 内容 |
|------|------|
| `db/model/*.gen.go` | 对应表结构的 Go 结构体（TService, TVpcEndpoint, TTrafficInfo, TServiceSnatip, TServiceWhitelist） |
| `db/query/*.gen.go` | 每张表的查询对象（tService, tVpcEndpoint, tTrafficInfo 等） |
| `db/query/gen.go` | 统一的 Query 入口对象（Use(), ReadDB(), WriteDB(), Transaction() 等） |

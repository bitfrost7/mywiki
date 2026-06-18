# 模块 10：数据表 Schema 定义 — Table Schema Definitions

## 概述

该模块对应四个图分析社区，都是数据库表的 ORM 模型定义：

| 社区编号 | 社区名称 | 节点数 | 源文件 |
|---------|---------|--------|--------|
| 9 | Service Table Schema | 4 | `mygorm/model/t_service.gen.go` |
| 10 | VPC Endpoint Table Schema | 4 | `mygorm/model/t_vpc_endpoint.gen.go` |
| 13 | Service SNAT Table Schema | 3 | `mygorm/model/t_service_snatips.gen.go` |
| 14 | Service Whitelist Table Schema | 3 | `mygorm/model/t_service_whitelist.gen.go` |

所有模型均由 GORM gen 工具自动生成，映射真实的 MySQL 表结构。

## 表关系图

```
t_service (1) ────── (N) t_vpc_endpoint
    │                     │
    │                     │ 外键: service_id
    │
    ├── (N) t_service_snatips
    │      外键: service_id
    │
    └── (N) t_service_whitelist
           外键: service_id
```

## t_service 表

**文件**: `mygorm/model/t_service.gen.go`
**表名**: `t_service`

核心字段：

| 字段 | 数据库类型 | 说明 |
|------|-----------|------|
| `service_id` | varchar | 服务唯一标识，业务主键 |
| `account_id` | int | 所属账户 |
| `tunnel_id` | int | 隧道 ID，用于网络隔离 |
| `ip` | varchar | 服务后端 IP |
| `resource_type` | int | 关联资源类型 |
| `resource_id` | varchar | 关联资源 ID |
| `auto_accept` | int | 是否自动接受连接请求 |
| `payer` | int | 付费方 |
| `connect_bw` | int | 连接带宽限制 |
| `vnet_id` | varchar | 虚拟网络 ID |
| `subnetwork_id` | varchar | 子网 ID |
| `description` | varchar | 描述 |
| `insert_time` | int | 创建时间戳 |
| `update_time` | datetime | 更新时间 |
| `delete_time` | int | 删除时间戳（0=未删除） |

## t_vpc_endpoint 表

**文件**: `mygorm/model/t_vpc_endpoint.gen.go`
**表名**: `t_vpc_endpoint`

核心字段：

| 字段 | 数据库类型 | 说明 |
|------|-----------|------|
| `endpoint_id` | varchar | 端点唯一标识 |
| `service_id` | varchar | 关联服务 ID（外键） |
| `account_id` | int | 所属账户 |
| `tunnel_id` | int | 隧道 ID |
| `ipv4` | varchar | IPv4 地址 |
| `ipv6` | varchar | IPv6 地址 |
| `mac` | varchar | MAC 地址 |
| `connect_status` | int | 连接状态（1=已连接） |
| `connect_bw` | int | 连接带宽 |
| `vnet_id` | varchar | 虚拟网络 ID |
| `subnetwork_id` | varchar | 子网 ID |
| `delete_time` | int | 删除时间戳（0=未删除） |

连接状态枚举：
- **0**: 未连接
- **1**: 已连接（API 查询只返回此状态）

## t_service_snatips 表

**文件**: `mygorm/model/t_service_snatips.gen.go`
**表名**: `t_service_snatips`

核心字段：

| 字段 | 数据库类型 | 说明 |
|------|-----------|------|
| `service_id` | varchar | 关联服务 ID（外键） |
| `ip` | varchar | SNAT IP 地址 |
| `mac` | varchar | MAC 地址 |
| `delete_time` | int | 删除时间戳（0=未删除） |

## t_service_whitelist 表

**文件**: `mygorm/model/t_service_whitelist.gen.go`
**表名**: `t_service_whitelist`

核心字段：

| 字段 | 数据库类型 | 说明 |
|------|-----------|------|
| `service_id` | varchar | 关联服务 ID（外键） |
| `account_id` | int | 白名单账户 ID |
| `delete_time` | int | 删除时间戳（0=未删除） |

当前代码中未查询此表。

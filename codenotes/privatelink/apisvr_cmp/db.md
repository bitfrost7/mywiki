# 数据模型

## 数据库表概览

apisvr 使用 6 个核心数据表来管理 PrivateLink 服务的资源、连接和配置信息。

## 表结构详情

### t_service - 终端节点服务表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_service.gen.go:15 |
| service_id | string | 服务唯一标识 | db/model/t_service.gen.go:16 |
| company_id | uint32 | 公司 ID | db/model/t_service.gen.go:17 |
| account_id | uint32 | 账户 ID | db/model/t_service.gen.go:18 |
| description | string | 服务描述 | db/model/t_service.gen.go:19 |
| auto_accept | uint32 | 是否自动接受连接 | db/model/t_service.gen.go:20 |
| payer | uint32 | 付费方（服务端/终端节点） | db/model/t_service.gen.go:21 |
| connect_bw | uint32 | 连接带宽 | db/model/t_service.gen.go:22 |
| vnet_id | string | VPC 网络 ID | db/model/t_service.gen.go:23 |
| ip_version | uint32 | IP 版本 | db/model/t_service.gen.go:24 |
| subnetwork_id | string | 子网 ID | db/model/t_service.gen.go:25 |
| tunnel_id | uint32 | 隧道 ID | db/model/t_service.gen.go:26 |
| ip | string | IP 地址 | db/model/t_service.gen.go:27 |
| resource_type | uint32 | 资源类型 | db/model/t_service.gen.go:28 |
| resource_id | string | 资源 ID | db/model/t_service.gen.go:29 |
| visible_type | uint32 | 可见类型（可见/不可见） | db/model/t_service.gen.go:30 |
| close_status | uint32 | 关闭状态 | db/model/t_service.gen.go:31 |
| channel_id | uint32 | 渠道 ID | db/model/t_service.gen.go:32 |
| insert_time | uint32 | 创建时间 | db/model/t_service.gen.go:33 |
| update_time | time.Time | 更新时间 | db/model/t_service.gen.go:34 |
| delete_time | uint32 | 删除时间（软删除） | db/model/t_service.gen.go:35 |

### t_vpc_endpoint - 终端节点表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_vpc_endpoint.gen.go:15 |
| endpoint_id | string | 终端节点唯一标识 | db/model/t_vpc_endpoint.gen.go:16 |
| service_id | string | 关联的服务 ID | db/model/t_vpc_endpoint.gen.go:17 |
| company_id | uint32 | 公司 ID | db/model/t_vpc_endpoint.gen.go:18 |
| account_id | uint32 | 账户 ID | db/model/t_vpc_endpoint.gen.go:19 |
| vnet_id | string | VPC 网络 ID | db/model/t_vpc_endpoint.gen.go:20 |
| subnetwork_id | string | 子网 ID | db/model/t_vpc_endpoint.gen.go:21 |
| tunnel_id | uint32 | 隧道 ID | db/model/t_vpc_endpoint.gen.go:22 |
| ipv4 | string | IPv4 地址 | db/model/t_vpc_endpoint.gen.go:23 |
| ipv6 | string | IPv6 地址 | db/model/t_vpc_endpoint.gen.go:24 |
| mac | string | MAC 地址 | db/model/t_vpc_endpoint.gen.go:25 |
| connect_bw | uint32 | 连接带宽 | db/model/t_vpc_endpoint.gen.go:26 |
| connect_status | uint32 | 连接状态 | db/model/t_vpc_endpoint.gen.go:27 |
| close_status | uint32 | 关闭状态 | db/model/t_vpc_endpoint.gen.go:28 |
| visible_type | uint32 | 可见类型 | db/model/t_vpc_endpoint.gen.go:29 |
| channel_id | uint32 | 渠道 ID | db/model/t_vpc_endpoint.gen.go:30 |
| insert_time | uint32 | 创建时间 | db/model/t_vpc_endpoint.gen.go:31 |
| update_time | time.Time | 更新时间 | db/model/t_vpc_endpoint.gen.go:32 |
| delete_time | uint32 | 删除时间（软删除） | db/model/t_vpc_endpoint.gen.go:33 |

### t_connect_info - 连接信息表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_connect_info.gen.go:11 |
| endpoint_id | string | 终端节点 ID | db/model/t_connect_info.gen.go:12 |
| service_id | string | 服务 ID | db/model/t_connect_info.gen.go:13 |
| start_time | uint32 | 连接开始时间 | db/model/t_connect_info.gen.go:14 |
| end_time | uint32 | 连接断开时间 | db/model/t_connect_info.gen.go:15 |

### t_service_whitelist - 服务白名单表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_service_whitelist.gen.go:11 |
| service_id | string | 服务 ID | db/model/t_service_whitelist.gen.go:12 |
| company_id | uint32 | 白名单公司 ID | db/model/t_service_whitelist.gen.go:13 |
| remark | string | 备注 | db/model/t_service_whitelist.gen.go:14 |
| insert_time | uint32 | 创建时间 | db/model/t_service_whitelist.gen.go:15 |
| delete_time | uint32 | 删除时间（软删除） | db/model/t_service_whitelist.gen.go:16 |

### t_service_snatips - 服务 SNAT IP 表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_service_snatips.gen.go:11 |
| service_id | string | 服务 ID | db/model/t_service_snatips.gen.go:12 |
| ip | string | SNAT IP 地址 | db/model/t_service_snatips.gen.go:13 |
| ip_type | uint32 | IP 类型（IPv4/IPv6） | db/model/t_service_snatips.gen.go:14 |
| mac | string | MAC 地址 | db/model/t_service_snatips.gen.go:15 |
| insert_time | uint32 | 创建时间 | db/model/t_service_snatips.gen.go:16 |
| delete_time | uint32 | 删除时间（软删除） | db/model/t_service_snatips.gen.go:17 |

### t_user_config - 用户配置表

| 字段 | 类型 | 说明 | 文件位置 |
|------|------|------|----------|
| id | uint32 | 主键，自增 | db/model/t_user_config.gen.go:15 |
| company_id | uint32 | 公司 ID | db/model/t_user_config.gen.go:16 |
| account_id | uint32 | 账户 ID | db/model/t_user_config.gen.go:17 |
| resource_id | string | 资源 ID | db/model/t_user_config.gen.go:18 |
| config_key | string | 配置键 | db/model/t_user_config.gen.go:19 |
| config_val | string | 配置值 | db/model/t_user_config.gen.go:20 |
| operator_name | string | 操作者名称 | db/model/t_user_config.gen.go:21 |
| insert_time | uint32 | 创建时间 | db/model/t_user_config.gen.go:22 |
| update_time | time.Time | 更新时间 | db/model/t_user_config.gen.go:23 |

## 关键数据库操作

### 服务相关操作

| 操作 | 方法 | 文件位置 | 功能 |
|------|------|----------|------|
| 创建服务 | CreateService | db/db.go:92 | 创建新的服务记录 |
| 查询服务 | GetServices | db/db.go:129 | 根据条件查询服务 |
| 软删除服务 | DeleteServiceSoft | db/db.go:117 | 软删除服务（设置删除时间） |
| 查询服务列表 | DescribeVPCEndpointServices | db/db.go:447 | 分页查询服务列表 |

### 终端节点相关操作

| 操作 | 方法 | 文件位置 | 功能 |
|------|------|----------|------|
| 创建终端节点 | CreateVPCEndpoint | db/db.go:250 | 创建新的终端节点记录 |
| 查询终端节点 | GetVPCEndpoints | db/db.go:342 | 根据条件查询终端节点 |
| 软删除终端节点 | DeleteVPCEndpointSoft | db/db.go:273 | 软删除终端节点 |
| 更新连接状态 | UpdateVPCEndpointConnectionStatus | db/db.go:306 | 更新终端节点连接状态和带宽 |
| 添加 IPv6 地址 | AddVPCEndpointIPv6Address | db/db.go:296 | 为终端节点添加 IPv6 地址 |

### 白名单相关操作

| 操作 | 方法 | 文件位置 | 功能 |
|------|------|----------|------|
| 创建白名单记录 | CreateServiceWhiteListRecord | db/db.go:387 | 创建服务白名单记录 |
| 查询白名单 | GetServiceWhiteListRecords | db/db.go:398 | 查询服务的白名单记录 |
| 删除白名单记录 | DeleteServiceWhiteListRecordSoft | db/db.go:409 | 软删除白名单记录 |

### SNAT IP 相关操作

| 操作 | 方法 | 文件位置 | 功能 |
|------|------|----------|------|
| 创建 SNAT IP | CreateSnatIps | db/db.go:197 | 批量创建 SNAT IP 记录 |
| 查询 SNAT IP | GetAllServiceSnatIps | db/db.go:235 | 查询服务的所有 SNAT IP |
| 删除 SNAT IP | DeleteServiceSnatIpsSoft | db/db.go:210 | 软删除服务的 SNAT IP |

## 数据库特性

### 软删除机制
所有主要表都使用软删除机制，通过 `delete_time` 字段标记删除状态，实际数据保留在数据库中。

### 自动生成
数据库模型和查询代码使用 GORM Gen 自动生成，不可手动编辑。生成配置位于 `cmd/tools/mysqlgen/conf/gen.json`。

### 监控集成
数据库操作集成了 Prometheus 监控，记录查询性能和统计信息（db/db.go:69）。
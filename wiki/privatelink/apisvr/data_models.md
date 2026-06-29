%% state: pending-review | confidence: 9 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# 数据模型 — PrivateLink

## 核心表结构

### 1. VPC终端节点表 (t_vpc_endpoint)
**主要字段**：
| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| endpoint_id | string | 终端节点ID，主标识 | NOT NULL |
| service_id | string | 关联的终端节点服务ID | NOT NULL |
| company_id | uint32 | 公司ID | NOT NULL |
| account_id | uint32 | 账户ID | NOT NULL |
| vnet_id | string | VPC ID | NOT NULL |
| subnetwork_id | string | 子网ID | NOT NULL |
| ipv4 | string | IPv4地址 | NOT NULL |
| ipv6 | string | IPv6地址 | NOT NULL |
| connect_status | uint32 | 连接状态 | NOT NULL |
| visible_type | uint32 | 可见类型 | NOT NULL, DEFAULT 2 |
| delete_time | uint32 | 删除时间（软删除标记） | NOT NULL |

**索引策略**：
- 主键：`id` (自增)
- 唯一索引：`endpoint_id`
- 查询索引：`service_id`, `company_id`, `account_id`
- 状态索引：`connect_status`, `delete_time`

[[源文件:t_vpc_endpoint.gen.go:L14-34]]

### 2. 终端节点服务表 (t_service)
**主要字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| service_id | string | 服务ID |
| company_id | uint32 | 公司ID |
| account_id | uint32 | 账户ID |
| payer | uint32 | 付费方（0-Endpoint，1-Service） |
| auto_accept | uint32 | 是否自动接受连接 |
| channel_id | uint32 | 渠道ID |
| close_status | uint32 | 关闭状态 |

### 3. 服务白名单表 (t_service_whitelist)
**主要字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| service_id | string | 服务ID |
| company_id | uint32 | 公司ID |
| account_id | uint32 | 账户ID |

### 4. 连接信息表 (t_connect_info)
**主要字段**：
| 字段 | 类型 | 说明 |
|------|------|------|
| endpoint_id | string | 终端节点ID |
| service_id | string | 服务ID |
| connect_status | uint32 | 连接状态 |
| accept_time | uint32 | 接受时间 |

## 数据关系
```
t_service (1) → (n) t_vpc_endpoint
    ↓ (白名单控制)
t_service_whitelist
    ↑
t_vpc_endpoint (1) → (n) t_connect_info
```

## 状态枚举

### 连接状态 (connect_status)
| 值 | 常量名 | 说明 |
|----|--------|------|
| 0 | ConnectStatusPendingInt | 等待接受 |
| 1 | ConnectStatusConnectedInt | 已连接 |
| 2 | ConnectStatusRejectedInt | 已拒绝 |
| 3 | ConnectStatusServiceDeletedInt | 服务已删除 |

### 可见类型 (visible_type)
| 值 | 常量名 | 说明 |
|----|--------|------|
| 0 | UresourceVisible | 可见资源 |
| 1 | UresourceInvisible | 不可见资源 |
| 2 | UresourceAll | 全部资源 |

### 付费方 (payer)
| 值 | 常量名 | 说明 |
|----|--------|------|
| 0 | PayerEndpointInt | 终端节点付费 |
| 1 | PayerServiceInt | 服务端付费 |

### 自动接受 (auto_accept)
| 值 | 常量名 | 说明 |
|----|--------|------|
| 0 | AutoAcceptDisableInt | 不自动接受 |
| 1 | AutoAcceptConnectInt | 自动接受连接 |

## 查询接口
### DB层查询方法（GORM Gen生成）

**终端节点查询**：
```go
// 基础查询
GetVPCEndpoints(ctx, endpointId, accountId, invisible)
GetVPCEndpointsWithDeleted(ctx, endpointId, accountId, invisible)

// 统计查询
GetVPCEndpointCountByServiceID(ctx, serviceId)
GetIdleVPCEndpoints(ctx, accountId)

// 条件查询
DescribeVPCEndpoints(ctx, accountId, invisible, endpointIds, vpcId, subnetId)
```

**服务查询**：
```go
GetServices(ctx, serviceId, channelId, invisible)
GetServiceWhiteListRecords(ctx, serviceId)
```

## 数据生命周期

### 创建流程
```
API请求 → 参数校验 → 配额检查 → 白名单验证
    ↓
资源创建 → IP分配 → 计费处理 → 数据库持久化
```

### 删除流程
```
API请求 → 软删除标记 → 异步清理
                       ├── 计费资源清理
                       ├── VPC IP释放
                       └── 资源系统删除
```

### 更新流程
```
API请求 → 数据查询 → 业务验证 → 更新操作
                                   ├── 数据库更新
                                   ├── 资源系统更新
                                   └── VPC网络更新
```

## 数据一致性保证

### 1. 软删除机制
- `delete_time`字段标记删除状态
- 查询时过滤已删除记录（除非明确查询）
- 异步清理确保最终一致性

### 2. 状态同步
- 数据库状态与资源系统状态同步
- 定期校验与修复任务
- 连接状态的实时更新

### 3. 事务边界
- 单数据库操作：数据库事务
- 跨系统操作：补偿事务（回滚机制）
- 异步操作：最终一致性

## 性能优化

### 索引设计
- 高频查询字段建立组合索引
- 状态字段建立部分索引
- 大表分区策略（按时间分区）

### 查询优化
- 分页查询避免全表扫描
- 批量ID查询使用IN语句
- 关联查询使用预加载

### 缓存策略
- 热点数据内存缓存
- 资源系统结果缓存
- 配置信息本地缓存

## 相关页面
- [[privatelink/apisvr/endpoint_management]]
- [[privatelink/apisvr/interfaces/CreateVPCEndpoint]]
- [[privatelink/apisvr/architecture]]
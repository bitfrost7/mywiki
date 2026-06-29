%% state: pending-review | confidence: 8 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# PrivateLink — 核心概念与业务模型

## 概述
本文档详细阐述PrivateLink服务的核心业务概念、数据模型、业务规则和系统约束，为开发人员和使用者提供统一的概念理解基础。

## 1. 核心业务实体

### 1.1 VPC终端节点服务 (VPC Endpoint Service)
**定义**: 提供网络服务的实体，允许其他VPC通过终端节点连接到该服务。[[源文件:base.go:L51-L68]]

|| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| ServiceId | string | 服务唯一标识 | [[源文件:base.go:L53]] |
| Description | string | 服务描述 | [[源文件:base.go:L54]] |
| Name | string | 服务名称 | [[源文件:base.go:L55]] |
| Tag | string | 业务标签 | [[源文件:base.go:L56]] |
| AutoAcceptEnabled | bool | 是否自动接受连接 | [[源文件:base.go:L57]] |
| Payer | string | 付费方类型 | [[源文件:base.go:L58]] |
| VPCId | string | 所属VPC ID | [[源文件:base.go:L59]] |
| SubnetId | string | 所属子网ID | [[源文件:base.go:L60]] |
| IPVersion | string | IP协议版本 | [[源文件:base.go:L61]] |
| ConnectBandwidth | uint32 | 连接带宽(Mbps) | [[源文件:base.go:L62]] |
| ResourceType | string | 后端资源类型 | [[源文件:base.go:L63]] |
| ResourceId | string | 后端资源ID | [[源文件:base.go:L64]] |
| ResourceIP | string | 后端资源IP | [[源文件:base.go:L65]] |
| SnatIPs | []string | SNAT IP列表 | [[源文件:base.go:L66]] |

### 1.2 VPC终端节点 (VPC Endpoint)
**定义**: 消费者VPC中连接到终端节点服务的端点实体。[[源文件:base.go:L33-L49]]

|| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| EndpointId | string | 终端节点唯一标识 | [[源文件:base.go:L34]] |
| Name | string | 终端节点名称 | [[源文件:base.go:L35]] |
| Tag | string | 业务标签 | [[源文件:base.go:L36]] |
| VPCId | string | 所属VPC ID | [[源文件:base.go:L37]] |
| SubnetId | string | 所属子网ID | [[源文件:base.go:L38]] |
| IPVersion | string | IP协议版本 | [[源文件:base.go:L39]] |
| IPv4Address | string | IPv4地址 | [[源文件:base.go:L40]] |
| IPv6Address | string | IPv6地址 | [[源文件:base.go:L41]] |
| ServiceId | string | 关联的服务ID | [[源文件:base.go:L42]] |
| ServiceDescription | string | 服务描述 | [[源文件:base.go:L43]] |
| ConnectBandwidth | uint32 | 连接带宽(Mbps) | [[源文件:base.go:L44]] |
| Payer | string | 付费方类型 | [[源文件:base.go:L45]] |
| ConnectionStatus | string | 连接状态 | [[源文件:base.go:L46]] |
| CreateTime | uint32 | 创建时间 | [[源文件:base.go:L47]] |
| UpdateTime | uint32 | 更新时间 | [[源文件:base.go:L48]] |

### 1.3 终端节点连接 (Endpoint Connection)
**定义**: 终端节点与终端节点服务之间的连接关系。[[源文件:base.go:L79-L87]]

|| 属性 | 类型 | 说明 | 来源 |
|------|------|------|------|
| ServiceId | string | 服务ID | [[源文件:base.go:L80]] |
| Owner | uint32 | 所有者标识 | [[源文件:base.go:L81]] |
| EndpointId | string | 终端节点ID | [[源文件:base.go:L82]] |
| ConnectBandwidth | uint32 | 连接带宽(Mbps) | [[源文件:base.go:L83]] |
| ConnectionStatus | string | 连接状态 | [[源文件:base.go:L84]] |
| CreateTime | uint32 | 创建时间 | [[源文件:base.go:L85]] |
| UpdateTime | uint32 | 更新时间 | [[源文件:base.go:L86]] |

## 2. 数据模型 (数据库层)

### 2.1 终端节点服务表 (t_service)
|| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| id | uint32 | 主键ID | [[源文件:model/t_service.gen.go:L15]] |
| service_id | string | 服务ID | [[源文件:model/t_service.gen.go:L16]] |
| company_id | uint32 | 公司ID | [[源文件:model/t_service.gen.go:L17]] |
| account_id | uint32 | 账户ID | [[源文件:model/t_service.gen.go:L18]] |
| description | string | 描述 | [[源文件:model/t_service.gen.go:L19]] |
| auto_accept | uint32 | 自动接受(0/1) | [[源文件:model/t_service.gen.go:L20]] |
| payer | uint32 | 付费方类型 | [[源文件:model/t_service.gen.go:L21]] |
| connect_bw | uint32 | 连接带宽 | [[源文件:model/t_service.gen.go:L22]] |
| vnet_id | string | VPC ID | [[源文件:model/t_service.gen.go:L23]] |
| ip_version | uint32 | IP协议版本 | [[源文件:model/t_service.gen.go:L24]] |
| subnetwork_id | string | 子网ID | [[源文件:model/t_service.gen.go:L25]] |
| tunnel_id | uint32 | 隧道ID | [[源文件:model/t_service.gen.go:L26]] |
| ip | string | IP地址 | [[源文件:model/t_service.gen.go:L27]] |
| resource_type | uint32 | 资源类型 | [[源文件:model/t_service.gen.go:L28]] |
| resource_id | string | 资源ID | [[源文件:model/t_service.gen.go:L29]] |
| visible_type | uint32 | 可见性类型 | [[源文件:model/t_service.gen.go:L30]] |
| close_status | uint32 | 关闭状态 | [[源文件:model/t_service.gen.go:L31]] |
| channel_id | uint32 | 渠道ID | [[源文件:model/t_service.gen.go:L32]] |

### 2.2 终端节点表 (t_vpc_endpoint)
|| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| id | uint32 | 主键ID | [[源文件:model/t_vpc_endpoint.gen.go:L15]] |
| endpoint_id | string | 终端节点ID | [[源文件:model/t_vpc_endpoint.gen.go:L16]] |
| service_id | string | 服务ID | [[源文件:model/t_vpc_endpoint.gen.go:L17]] |
| company_id | uint32 | 公司ID | [[源文件:model/t_vpc_endpoint.gen.go:L18]] |
| account_id | uint32 | 账户ID | [[源文件:model/t_vpc_endpoint.gen.go:L19]] |
| vnet_id | string | VPC ID | [[源文件:model/t_vpc_endpoint.gen.go:L20]] |
| subnetwork_id | string | 子网ID | [[源文件:model/t_vpc_endpoint.gen.go:L21]] |
| tunnel_id | uint32 | 隧道ID | [[源文件:model/t_vpc_endpoint.gen.go:L22]] |
| ipv4 | string | IPv4地址 | [[源文件:model/t_vpc_endpoint.gen.go:L23]] |
| ipv6 | string | IPv6地址 | [[源文件:model/t_vpc_endpoint.gen.go:L24]] |
| mac | string | MAC地址 | [[源文件:model/t_vpc_endpoint.gen.go:L25]] |
| connect_bw | uint32 | 连接带宽 | [[源文件:model/t_vpc_endpoint.gen.go:L26]] |
| connect_status | uint32 | 连接状态 | [[源文件:model/t_vpc_endpoint.gen.go:L27]] |
| close_status | uint32 | 关闭状态 | [[源文件:model/t_vpc_endpoint.gen.go:L28]] |
| visible_type | uint32 | 可见性类型 | [[源文件:model/t_vpc_endpoint.gen.go:L29]] |
| channel_id | uint32 | 渠道ID | [[源文件:model/t_vpc_endpoint.gen.go:L30]] |

### 2.3 连接信息表 (t_connect_info)
|| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| id | uint32 | 主键ID | [[源文件:model/t_connect_info.gen.go:L11]] |
| endpoint_id | string | 终端节点ID | [[源文件:model/t_connect_info.gen.go:L12]] |
| service_id | string | 服务ID | [[源文件:model/t_connect_info.gen.go:L13]] |
| start_time | uint32 | 连接开始时间 | [[源文件:model/t_connect_info.gen.go:L14]] |
| end_time | uint32 | 连接断开时间 | [[源文件:model/t_connect_info.gen.go:L15]] |

## 3. 关键业务概念

### 3.1 VPC端点服务 vs VPC端点区别
|| 维度 | VPC端点服务 | VPC端点 |
|------|------------|--------|
| **角色** | 服务提供者 | 服务消费者 |
| **位置** | 服务提供者的VPC中 | 消费者的VPC中 |
| **数量** | 一个服务可被多个端点连接 | 一个端点只能连接一个服务 |
| **付费模式** | 可配置为服务付费或端点付费 | 根据服务配置确定 |

### 3.2 连接生命周期与状态
1. **创建中**: 终端节点创建过程中
2. **待接受**: 创建完成，等待服务所有者接受连接
3. **已接受**: 连接被接受，可以传输数据
4. **已拒绝**: 连接被服务所有者拒绝
5. **已断开**: 连接主动断开
6. **已删除**: 终端节点被删除

### 3.3 可见 vs 不可见资源
|| 特性 | 可见资源 | 不可见资源 |
|------|--------|----------|
| **用户可见性** | 用户可见且可管理 | 用户不可见 |
| **付费限制** | 无特殊限制 | 必须是服务端付费 [[源文件:error.go:L38]] |
| **使用场景** | 普通用户创建的资源 | 系统内部使用的资源 |
| **渠道检查** | 严格检查渠道ID | 可跳过渠道检查 |

### 3.4 资源所有权与多租户
1. **组织层级**: top_organization_id → organization_id → account_id
2. **跨组织访问**: 需要白名单授权
3. **资源隔离**: 基于公司和账户的资源隔离
4. **计费归属**: 根据付费方确定计费主体

### 3.5 带宽与IP版本考虑
1. **带宽范围**: 100-10000 Mbps [[源文件:GetPrivateLinkBandwidth.go:L31-L32]]
2. **IP协议支持**: IPv4, DualStack（IPv4+IPv6）
3. **IP分配策略**: 支持指定IP或系统自动分配
4. **网络兼容性**: 需要验证VPC和子网的支持情况

## 4. 定价模型

### 4.1 计费模式
1. **流量计费 (Traffic)**: 按实际传输流量计费 [[源文件:GetPrivatelinkPrice.go:L28]]
2. **实例计费 (Instance)**: 按资源实例规格计费 [[源文件:GetPrivatelinkPrice.go:L28]]

### 4.2 价格组成
|| 价格类型 | 说明 | 来源 |
|----------|------|------|
| ListPrice | 原价（官方定价） | [[源文件:GetPrivatelinkPrice.go:L30]] |
| CustomPrice | 折后价（渠道优惠） | [[源文件:GetPrivatelinkPrice.go:L31]] |
| Price | 总价（实际应付） | [[源文件:GetPrivatelinkPrice.go:L29]] |

### 4.3 影响因素
1. **产品类型**: Endpoint vs EndpointService
2. **渠道差异**: 不同渠道可能有不同的价格策略
3. **活动优惠**: 临时活动提供的价格优惠

## 5. 错误处理框架

### 5.1 错误码范围
- **通用错误**: 100-999
- **参数错误**: 230 [[源文件:error.go:L12]]
- **PrivateLink特定错误**: 217801-217827 [[源文件:error.go:L53-L80]]

### 5.2 关键错误场景
1. **配额限制**: 各种配额检查失败 [[源文件:error.go:L33-L34]]
2. **权限错误**: 白名单验证失败 [[源文件:error.go:L27]]
3. **资源状态**: 资源不存在或已关闭 [[源文件:error.go:L32-L36]]
4. **网络配置**: VPC/子网/IP地址相关错误 [[源文件:error.go:L20-L25]]

## 6. 系统架构组件关系

### 6.1 核心组件
1. **API层**: 提供RESTful接口，参数验证和路由转发 [[源文件:api.go]]
2. **业务逻辑层**: 实现具体的业务规则和流程
3. **数据访问层**: 数据库操作和资源管理 [[源文件:db/db.go]]
4. **计费系统**: 价格计算和资源购买 [[源文件:GetPrivatelinkPrice.go:L52]]
5. **资源系统**: 网络资源创建和管理

### 6.2 外部依赖
1. **VPC系统**: 验证VPC/子网信息，分配IP地址
2. **计费中心**: 资源购买和价格查询
3. **身份认证**: 用户身份验证和权限检查

## 相关页面
- [[privatelink/apisvr/utility_interfaces]]
- [[privatelink/apisvr/interfaces]]
- [[privatelink/apisvr/architecture]]
- [[privatelink/apisvr/error_handling]]
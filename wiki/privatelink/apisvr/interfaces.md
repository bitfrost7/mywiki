%% state: pending-review | confidence: 8 | type: interfaces | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# PrivateLink API — 接口文档索引

## 接口分组

### 1. VPC终端节点管理
|| 接口 | 方法 | 说明 | 复杂度 |
|------|------|------|:------:|
| [[privatelink/apisvr/interfaces/CreateVPCEndpoint\|CreateVPCEndpoint]] | POST | 创建终端节点 | 高（366行） |
| [[privatelink/apisvr/interfaces/DeleteVPCEndpoint\|DeleteVPCEndpoint]] | POST | 删除终端节点（检查可见性） | 中 |
| [[privatelink/apisvr/interfaces/IDeleteVPCEndpoint\|IDeleteVPCEndpoint]] | POST | 强制删除终端节点（忽略可见性） | 中 |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpoints\|DescribeVPCEndpoints]] | POST | 查询终端节点列表 | 中（157行） |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointAttribute\|UpdateVPCEndpointAttribute]] | POST | 更新终端节点属性 | 中（97行） |

### 2. VPC终端节点服务管理
|| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/CreateVPCEndpointServiceConfiguration\|CreateVPCEndpointServiceConfiguration]] | POST | 创建VPC终端节点服务配置 | 高（427行） | [[Community 6]] |
| [[privatelink/apisvr/interfaces/DeleteVPCEndpointServiceConfiguration\|DeleteVPCEndpointServiceConfiguration]] | POST | 删除VPC终端节点服务配置（检查可见性） | 中（36行） | [[Community 38]] |
| [[privatelink/apisvr/interfaces/IDeleteVPCEndpointServiceConfiguration\|IDeleteVPCEndpointServiceConfiguration]] | POST | 强制删除VPC终端节点服务配置（忽略可见性） | 中 | [[Community 40]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointServiceConfiguration\|DescribeVPCEndpointServiceConfiguration]] | POST | 查询VPC终端节点服务配置详情 | 中（149行） | [[Community 6]] |
| [[privatelink/apisvr/interfaces/IDescribeVPCEndpointServiceConfiguration\|IDescribeVPCEndpointServiceConfiguration]] | POST | 查询所有可见性类型的服务配置 | 中 | - |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointServiceConfiguration\|UpdateVPCEndpointServiceConfiguration]] | POST | 更新VPC终端节点服务配置 | 高（358行） | [[Community 15]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointServices\|DescribeVPCEndpointServices]] | POST | 列出VPC终端节点服务信息（概要） | 中（57行） | [[Community 22]] |
| [[privatelink/apisvr/interfaces/IDescribeVPCEndpointServices\|IDescribeVPCEndpointServices]] | POST | 列出所有可见性类型的服务 | 中 | - |

### 3. 连接管理
|| 接口 | 方法 | 说明 | 复杂度 |
|------|------|------|:------:|
| [[privatelink/apisvr/interfaces/AcceptVPCEndpointConnection\|AcceptVPCEndpointConnection]] | POST | 接受终端节点连接 | 中（83行） |
| [[privatelink/apisvr/interfaces/RejectVPCEndpointConnection\|RejectVPCEndpointConnection]] | POST | 拒绝终端节点连接 | 中（73行） |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointConnections\|DescribeVPCEndpointConnections]] | POST | 查询终端节点连接列表 | 中（110行） |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointConnectionAttribute\|UpdateVPCEndpointConnectionAttribute]] | POST | 更新终端节点连接属性 | 中（70行） |

### 4. 用户/白名单管理
|| 接口 | 方法 | 说明 | 复杂度 | 来源 |
|------|------|------|:------:|------|
| [[privatelink/apisvr/interfaces/AddUsersToVPCEndpointService\|AddUsersToVPCEndpointService]] | POST | 添加用户到服务白名单 | 中（119行） | [[源文件:AddUsersToVPCEndpointService.go:L1]] |
| [[privatelink/apisvr/interfaces/RemoveUsersToVPCEndpointService\|RemoveUsersToVPCEndpointService]] | POST | 从服务白名单移除用户 | 中（53行） | [[源文件:RemoveUsersToVPCEndpointService.go:L1]] |
| [[privatelink/apisvr/interfaces/UpdateUsersToVPCEndpointService\|UpdateUsersToVPCEndpointService]] | POST | 更新白名单用户备注 | 中（65行） | [[源文件:UpdateUsersToVPCEndpointService.go:L1]] |
| [[privatelink/apisvr/interfaces/ListVPCEndpointServiceUsers\|ListVPCEndpointServiceUsers]] | POST | 查询服务白名单用户 | 中（78行） | [[源文件:ListVPCEndpointServiceUsers.go:L1]] |

### 5. 实用工具接口
|| 接口 | 方法 | 说明 | 复杂度 | 来源 |
|------|------|------|:------:|------|
| [[privatelink/apisvr/interfaces/GetPrivateLinkPrice\|GetPrivateLinkPrice]] | POST | 查询PrivateLink资源价格 | 中（68行） | [[源文件:GetPrivatelinkPrice.go:L1]] |
| [[privatelink/apisvr/interfaces/GetPrivateLinkBandwidth\|GetPrivateLinkBandwidth]] | POST | 获取可用的带宽范围 | 低（35行） | [[源文件:GetPrivateLinkBandwidth.go:L1]] |
| [[privatelink/apisvr/interfaces/RefreshData\|RefreshData]] | POST | 内部数据刷新接口（临时使用） | 中（41行） | [[源文件:RefreshData.go:L1]] |

完整实用工具接口文档参见 [[privatelink/apisvr/utility_interfaces]]

## 通用数据结构
### 请求基类 (ReqBase)
|| 字段 | 类型 | 必填 | 说明 | 来源 |
|------|------|:----:|------|------|
| Action | string | ✅ | 接口名称 | [[源文件:base.go:L11]] |
| request_uuid | string | ❌ | 请求UUID | [[源文件:base.go:L12]] |
| top_organization_id | uint32 | ✅ | 顶层组织ID | [[源文件:base.go:L17]] |
| organization_id | uint32 | ✅ | 组织ID | [[源文件:base.go:L18]] |
| az_group | uint32 | ✅ | 可用区组 | [[源文件:base.go:L19]] |

### 响应基类 (RespBase)
|| 字段 | 类型 | 说明 | 来源 |
|------|------|------|------|
| Action | string | 接口名称 | [[源文件:base.go:L23]] |
| RetCode | int | 返回码，0表示成功 | [[源文件:base.go:L24]] |
| Message | string | 返回消息 | [[源文件:base.go:L25]] |

## 错误码体系
|| 错误分类 | 错误码范围 | 代表错误 | 说明 |
|----------|------------|----------|------|
| 参数错误 | 230 | RequestParamsErr | 请求参数验证失败 |
| 资源不存在 | 217803 | ResourceNotFoundErr | 资源不存在 |
| 权限错误 | 217812 | PermissionIsDeniedErr | 权限验证失败 |
| 配额错误 | 217818-217825 | 多种配额错误 | 各种配额检查失败 |
| VPC错误 | 217820、217827 | VPC相关错误 | IP分配失败、VPC不支持IPv6等 |
| 内部错误 | 500 | InternalServerErr | 数据库、资源系统等内部错误 |

完整错误列表参见 [[privatelink/apisvr/error_handling]]

## 相关页面
- [[privatelink/apisvr/overview]] - 服务概况
- [[privatelink/apisvr/architecture]] - 系统架构
- [[privatelink/apisvr/endpoint_management]] - 终端节点管理综合分析
- [[privatelink/apisvr/data_models]] - 数据模型
- [[privatelink/apisvr/whitelist_management]] - 白名单管理功能概述
- [[privatelink/apisvr/utility_interfaces]] - 实用工具接口概览
- [[privatelink/apisvr/core_concepts]] - 核心概念与业务模型
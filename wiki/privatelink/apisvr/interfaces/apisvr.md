%% state: pending-review | confidence: 10 | type: interfaces | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 | updated: 2026-06-29 %%

# PrivateLink API — 接口文档索引

## 接口分组

### 1. VPC终端节点管理
| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/CreateVPCEndpoint\|CreateVPCEndpoint]] | POST | 创建终端节点 | 高（366行） | [[Community 20]] |
| [[privatelink/apisvr/interfaces/DeleteVPCEndpoint\|DeleteVPCEndpoint]] | POST | 删除终端节点（检查可见性） | 低（34行） | [[Community 20]] |
| [[privatelink/apisvr/interfaces/IDeleteVPCEndpoint\|IDeleteVPCEndpoint]] | POST | 强制删除终端节点（忽略可见性） | 中（91行） | [[Community 20]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpoints\|DescribeVPCEndpoints]] | POST | 查询终端节点列表 | 中（157行） | [[Community 30]] |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointAttribute\|UpdateVPCEndpointAttribute]] | POST | 更新终端节点属性 | 中（97行） | [[Community 5]] |

### 2. VPC终端节点服务管理
| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/CreateVPCEndpointServiceConfiguration\|CreateVPCEndpointServiceConfiguration]] | POST | 创建VPC终端节点服务配置 | 高（427行） | [[Community 6]] |
| [[privatelink/apisvr/interfaces/DeleteVPCEndpointServiceConfiguration\|DeleteVPCEndpointServiceConfiguration]] | POST | 删除VPC终端节点服务配置（检查可见性） | 低（36行） | [[Community 38]] |
| [[privatelink/apisvr/interfaces/IDeleteVPCEndpointServiceConfiguration\|IDeleteVPCEndpointServiceConfiguration]] | POST | 强制删除VPC终端节点服务配置（忽略可见性） | 中（131行） | [[Community 40]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointServiceConfiguration\|DescribeVPCEndpointServiceConfiguration]] | POST | 查询VPC终端节点服务配置详情 | 中（149行） | [[Community 6]] |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointServiceConfiguration\|UpdateVPCEndpointServiceConfiguration]] | POST | 更新VPC终端节点服务配置 | 高（358行） | [[Community 15]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointServices\|DescribeVPCEndpointServices]] | POST | 列出VPC终端节点服务信息（概要） | 中（122行） | [[Community 22]] |

### 3. 连接管理
| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/AcceptVPCEndpointConnection\|AcceptVPCEndpointConnection]] | POST | 接受终端节点连接 | 中（83行） | [[Community 1]] |
| [[privatelink/apisvr/interfaces/RejectVPCEndpointConnection\|RejectVPCEndpointConnection]] | POST | 拒绝终端节点连接 | 中（73行） | [[Community 2]] |
| [[privatelink/apisvr/interfaces/DescribeVPCEndpointConnections\|DescribeVPCEndpointConnections]] | POST | 查询终端节点连接 | 中（110行） | [[Community 6]] |
| [[privatelink/apisvr/interfaces/UpdateVPCEndpointConnectionAttribute\|UpdateVPCEndpointConnectionAttribute]] | POST | 更新终端节点连接属性 | 中（70行） | [[Community 20]] |

### 4. 用户管理
| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/AddUsersToVPCEndpointService\|AddUsersToVPCEndpointService]] | POST | 添加用户到终端节点服务 | 中（119行） | [[Community 31]] |
| [[privatelink/apisvr/interfaces/RemoveUsersToVPCEndpointService\|RemoveUsersToVPCEndpointService]] | POST | 从终端节点服务移除用户 | 中（53行） | [[Community 32]] |
| [[privatelink/apisvr/interfaces/UpdateUsersToVPCEndpointService\|UpdateUsersToVPCEndpointService]] | POST | 更新用户权限 | 中（65行） | [[Community 33]] |
| [[privatelink/apisvr/interfaces/ListVPCEndpointServiceUsers\|ListVPCEndpointServiceUsers]] | POST | 列出终端节点服务用户 | 中（78行） | [[Community 34]] |

### 5. 其他接口
| 接口 | 方法 | 说明 | 复杂度 | AST社区 |
|------|------|------|:------:|:------:|
| [[privatelink/apisvr/interfaces/GetPrivateLinkBandwidth\|GetPrivateLinkBandwidth]] | POST | 获取PrivateLink带宽信息 | 低（35行） | - |
| [[privatelink/apisvr/interfaces/GetPrivatelinkPrice\|GetPrivatelinkPrice]] | POST | 获取PrivateLink价格信息 | 中（68行） | [[Community 39]] |
| [[privatelink/apisvr/interfaces/RefreshData\|RefreshData]] | POST | 刷新数据 | 低（41行） | - |

## 统计信息
- **总接口数**: 22个
- **高复杂度接口**: 3个（CreateVPCEndpoint、CreateVPCEndpointServiceConfiguration、UpdateVPCEndpointServiceConfiguration）
- **中复杂度接口**: 15个
- **低复杂度接口**: 4个（DeleteVPCEndpoint、DeleteVPCEndpointServiceConfiguration、GetPrivateLinkBandwidth、RefreshData）

## 数据准确性验证
所有接口行数已通过 `wc -l` 命令验证：
- IDeleteVPCEndpointServiceConfiguration: 131行（原文档错误: 46行）
- DescribeVPCEndpointServices: 122行（原文档错误: 57行）
- DeleteVPCEndpoint: 34行（原文档错误: 28行）
- IDeleteVPCEndpoint: 91行（原文档错误: 88行）

复杂度重新分类依据阈值：
- 高: >300行
- 中: 50-300行
- 低: <50行

## 文档状态说明
- 所有接口均有对应的源代码实现（位于 `/raw/assets/repo/privatelink/apisvr/api/`）
- 详细的接口文档正在编写中，将通过独立的接口页面提供完整的技术规范

## 相关页面
- [[privatelink/apisvr/overview]] - 服务概况
- [[privatelink/apisvr/architecture]] - 架构设计
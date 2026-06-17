# apisvr - api

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-17 22:22
路由类型: action
> **置信度**: 见文档末尾统计 | **验证状态**: ✓

---


# API 文档

## 路由机制
所有请求通过 JSON 中的 `Action` 字段进行路由分发，而非通过 URL 路径。请求应发送到统一的端点（推测为 POST 到 `/`），并在请求体中指定 `Action` 字段的值。

**关键事实**：此项目使用 **Action 字段路由**，不是 REST 路由。请求通过 JSON 中的 “Action” 字段分发，而非 URL 路径。

## Action 列表

### CreateVPCEndpointServiceConfiguration
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionCreateVPCEndpointServiceConfiguration |
| Handler | CreateVPCEndpointServiceConfiguration |
| 位置 | api/CreateVPCEndpointServiceConfiguration.go:128-128 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于创建 VPC 端点服务配置。

### DeleteVPCEndpointServiceConfiguration
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDeleteVPCEndpointServiceConfiguration |
| Handler | DeleteVPCEndpointServiceConfiguration |
| 位置 | api/DeleteVPCEndpointServiceConfiguration.go:21-21 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于删除 VPC 端点服务配置。

### DescribeVPCEndpointServiceConfigurations
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDescribeVPCEndpointServiceConfigurations |
| Handler | DescribeVPCEndpointServiceConfiguration |
| 位置 | api/DescribeVPCEndpointServiceConfiguration.go:47-47 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于查询 VPC 端点服务配置列表或详情。

### UpdateVPCEndpointServiceConfiguration
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionUpdateVPCEndpointServiceConfiguration |
| Handler | UpdateVPCEndpointServiceConfiguration |
| 位置 | api/UpdateVPCEndpointServiceConfiguration.go:96-96 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于更新 VPC 端点服务配置。

### DescribeVPCEndpointServices
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDescribeVPCEndpointServices |
| Handler | DescribeVPCEndpointServices |
| 位置 | db/db.go:795-795 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于查询 VPC 端点服务列表或详情。

### CreateVPCEndpoint
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionCreateVPCEndpoint |
| Handler | CreateVPCEndpoint |
| 位置 | db/db.go:250-250 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于创建 VPC 端点。

### DeleteVPCEndpoint
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDeleteVPCEndpoint |
| Handler | DeleteVPCEndpoint |
| 位置 | api/DeleteVPCEndpoint.go:21-21 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于删除 VPC 端点。

### DescribeVPCEndpoints
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDescribeVPCEndpoints |
| Handler | DescribeVPCEndpoints |
| 位置 | db/db.go:451-451 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于查询 VPC 端点列表或详情。

### UpdateVPCEndpointAttribute
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionUpdateVPCEndpointAttribute |
| Handler | UpdateVPCEndpointAttribute |
| 位置 | api/UpdateVPCEndpointAttribute.go:34-34 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于更新 VPC 端点的属性。

### AcceptVPCEndpointConnection
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionAcceptVPCEndpointConnection |
| Handler | AcceptVPCEndpointConnection |
| 位置 | api/AcceptVPCEndpointConnection.go:30-30 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于接受 VPC 端点连接请求。

### RejectVPCEndpointConnection
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionRejectVPCEndpointConnection |
| Handler | RejectVPCEndpointConnection |
| 位置 | api/RejectVPCEndpointConnection.go:26-26 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于拒绝 VPC 端点连接请求。

### DescribeVPCEndpointConnections
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionDescribeVPCEndpointConnections |
| Handler | DescribeVPCEndpointConnections |
| 位置 | db/db.go:590-590 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于查询 VPC 端点连接列表或详情。

### UpdateVPCEndpointConnectionAttribute
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionUpdateVPCEndpointConnectionAttribute |
| Handler | UpdateVPCEndpointConnectionAttribute |
| 位置 | api/UpdateVPCEndpointConnectionAttribute.go:28-28 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于更新 VPC 端点连接的属性。

### AddUsersToVPCEndpointService
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionAddUsersToVPCEndpointService |
| Handler | AddUsersToVPCEndpointService |
| 位置 | api/AddUsersToVPCEndpointService.go:37-37 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于向 VPC 端点服务添加用户。

### RemoveUsersToVPCEndpointService
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionRemoveUsersToVPCEndpointService |
| Handler | RemoveUsersToVPCEndpointService |
| 位置 | api/RemoveUsersToVPCEndpointService.go:25-25 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于从 VPC 端点服务移除用户。

### UpdateUsersToVPCEndpointService
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionUpdateUsersToVPCEndpointService |
| Handler | UpdateUsersToVPCEndpointService |
| 位置 | api/UpdateUsersToVPCEndpointService.go:27-27 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于更新 VPC 端点服务的用户信息。

### ListVPCEndpointServiceUsers
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionListVPCEndpointServiceUsers |
| Handler | ListVPCEndpointServiceUsers |
| 位置 | api/ListVPCEndpointServiceUsers.go:27-27 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于列出 VPC 端点服务的用户。

### GetPrivateLinkPrice
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionGetPrivateLinkPrice |
| Handler | GetPrivateLinkPrice |
| 位置 | api/GetPrivatelinkPrice.go:41-41 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于获取 PrivateLink 服务的价格信息。

### GetPrivateLinkBandwidth
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionGetPrivateLinkBandwidth |
| Handler | GetPrivateLinkBandwidth |
| 位置 | api/GetPrivateLinkBandwidth.go:21-21 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于获取 PrivateLink 服务的带宽信息。

### RefreshData
| 属性 | 值 |
|------|-----|
| Action 字段 | ActionRefreshData |
| Handler | RefreshData |
| 位置 | api/RefreshData.go:11-11 |
| 请求结构 | 【需确认】 |
| 响应结构 | 【需确认】 |

**业务描述**：【推测】用于刷新数据。具体刷新何种数据【需确认】。

---

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (≥0.9) | 313 |
| 中置信度 (0.6-0.9) | 370 |
| 低置信度 (0.3-0.6) | 0 |
| 不确定 (<0.3) | 0 |

- **平均置信度**: 0.80
- **需人工审查**: 0 个事实

*置信度基于来源可信度、完整性、一致性和可验证性计算*

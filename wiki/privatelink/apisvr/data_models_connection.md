%% state: pending-review | confidence: 7 | type: module | sources: privatelink/apisvr | module: data-models | stage: L1 | agent: writer | created: 2026-06-29 %%

# 连接管理数据模型

## 概述

本文档描述 VPC Endpoint 连接管理模块中使用的核心数据结构，包括请求/响应结构、数据库模型和中间数据结构。

## 核心数据结构

### 1. 连接信息结构 (EndpointConnectionInfo)

用于 `DescribeVPCEndpointConnections` 响应的数据结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/base.go:L79-L87]]。

| 字段 | 类型 | 描述 | JSON 标签 |
|------|------|------|----------|
| `ServiceId` | `string` | 终端节点服务ID | `"ServiceId"` |
| `Owner` | `uint32` | 终端节点所有者（公司ID） | `"Owner"` |
| `EndpointId` | `string` | 终端节点ID | `"EndpointId"` |
| `ConnectBandwidth` | `uint32` | 连接带宽（Mbps） | `"ConnectBandwidth"` |
| `ConnectionStatus` | `string` | 连接状态（字符串表示） | `"ConnectionStatus"` |
| `CreateTime` | `uint32` | 创建时间（Unix 时间戳） | `"CreateTime"` |
| `UpdateTime` | `uint32` | 更新时间（Unix 时间戳） | `"UpdateTime"` |

### 2. 接受连接请求结构 (AcceptVPCEndpointConnectionReq)

用于 `AcceptVPCEndpointConnection` 请求的数据结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L12-L23]]。

| 字段 | 类型 | 必须 | 描述 | 验证规则 | JSON 标签 |
|------|------|-----|------|---------|----------|
| `ServiceId` | `string` | ✅ | 终端节点服务ID | `required` | `"ServiceId"` |
| `EndpointId` | `string` | ✅ | 终端节点ID | `required` | `"EndpointId"` |
| `ConnectBandwidth` | `uint32` | ❌ | 连接带宽值（100-10000 Mbps） | `omitempty,min=100,max=10000` | `"ConnectBandwidth"` |

**继承字段**：`ReqBase` 通用请求基类。

### 3. 拒绝连接请求结构 (RejectVPCEndpointConnectionReq)

用于 `RejectVPCEndpointConnection` 请求的数据结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/RejectVPCEndpointConnection.go:L12-L19]]。

| 字段 | 类型 | 必须 | 描述 | 验证规则 | JSON 标签 |
|------|------|-----|------|---------|----------|
| `ServiceId` | `string` | ✅ | 终端节点服务ID | `required` | `"ServiceId"` |
| `EndpointId` | `string` | ✅ | 终端节点ID | `required` | `"EndpointId"` |

**继承字段**：`ReqBase` 通用请求基类。

### 4. 查询连接请求结构 (DescribeVPCEndpointConnectionsReq)

用于 `DescribeVPCEndpointConnections` 请求的数据结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/DescribeVPCEndpointConnections.go:L13-L33]]。

| 字段 | 类型 | 必须 | 描述 | 验证规则 | JSON 标签 |
|------|------|-----|------|---------|----------|
| `ServiceId` | `string` | ✅ | 终端节点服务ID | `required` | `"ServiceId"` |
| `Owner` | `uint32` | ❌ | 终端节点所有者（公司ID） | `-` | `"Owner"` |
| `EndpointId` | `string` | ❌ | 终端节点ID（指定时忽略其他过滤条件） | `omitempty` | `"EndpointId"` |
| `ConnectionStatus` | `string` | ❌ | 连接状态 | `omitempty,oneof=Pending Connected Disconnected` | `"ConnectionStatus"` |
| `Offset` | `uint32` | ❌ | 数据偏移量 | `-` | `"Offset"` |
| `Limit` | `uint32` | ❌ | 数据分页值 | `-` | `"Limit"` |

**继承字段**：`ReqBase` 通用请求基类。

### 5. 更新连接属性请求结构 (UpdateVPCEndpointConnectionAttributeReq)

用于 `UpdateVPCEndpointConnectionAttribute` 请求的数据结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/UpdateVPCEndpointConnectionAttribute.go:L12-L22]]。

| 字段 | 类型 | 必须 | 描述 | 验证规则 | JSON 标签 |
|------|------|-----|------|---------|----------|
| `ServiceId` | `string` | ✅ | 终端节点服务ID | `required` | `"ServiceId"` |
| `EndpointId` | `string` | ✅ | 终端节点ID | `required` | `"EndpointId"` |
| `ConnectBandwidth` | `uint32` | ❌ | 连接带宽值（100-10000 Mbps） | `omitempty,min=100,max=10000` | `"ConnectBandwidth"` |

**继承字段**：`ReqBase` 通用请求基类。

## 数据库模型

### TVpcEndpoint 表结构

终端节点连接的核心数据库表结构。

| 字段 | 类型 | 描述 | 对应响应字段 |
|------|------|------|-------------|
| `ServiceID` | `string` | 终端节点服务ID | `ServiceId` |
| `CompanyID` | `uint32` | 公司ID | `Owner` |
| `EndpointID` | `string` | 终端节点ID | `EndpointId` |
| `ConnectBw` | `uint32` | 连接带宽 | `ConnectBandwidth` |
| `ConnectStatus` | `uint32` | 连接状态（数值） | 通过 `GetConnectStatusName` 转换为 `ConnectionStatus` |
| `InsertTime` | `time.Time` | 插入时间 | `CreateTime`（转换为Unix时间戳） |
| `UpdateTime` | `time.Time` | 更新时间 | `UpdateTime`（转换为Unix时间戳） |

## 状态枚举

### 连接状态常量

定义在 `convert.go` 中的状态常量 [[源文件:/raw/assets/repo/privatelink/apisvr/api/convert.go:L23-L34]]。

#### 字符串表示
| 常量 | 值 | 描述 |
|------|----|------|
| `ConnectStatusPendingStr` | `"Pending"` | 等待接受 |
| `ConnectStatusConnectedStr` | `"Connected"` | 已连接 |
| `ConnectStatusDisconnectedStr` | `"Disconnected"` | 已拒绝/断开 |
| `ConnectStatusServiceDeletedStr` | `"ServiceDeleted"` | 服务已删除 |

#### 数值表示
| 常量 | 值 | 描述 |
|------|----|------|
| `ConnectStatusPendingInt` | 0 | 等待接受 |
| `ConnectStatusConnectedInt` | 1 | 已连接 |
| `ConnectStatusDisconnectedInt` | 2 | 已拒绝/断开 |
| `ConnectStatusServiceDeletedInt` | 100 | 服务已删除 |
| `ConnectStatusEmptyInt` | 10000 | 零值，用于校验用户未传值的情况 |

## 转换函数

### 状态转换函数

#### GetConnectStatusCode
将字符串状态转换为状态码 [[源文件:/raw/assets/repo/privatelink/apisvr/api/convert.go:L105-L118]]。
```go
func GetConnectStatusCode(s string) uint32 {
    switch s {
    case ConnectStatusPendingStr:
        return ConnectStatusPendingInt
    case ConnectStatusConnectedStr:
        return ConnectStatusConnectedInt
    case ConnectStatusDisconnectedStr:
        return ConnectStatusDisconnectedInt
    case ConnectStatusServiceDeletedStr:
        return ConnectStatusServiceDeletedInt
    default:
        return ConnectStatusEmptyInt
    }
}
```

#### GetConnectStatusName
将状态码转换为字符串表示 [[源文件:/raw/assets/repo/privatelink/apisvr/api/convert.go:L120-L133]]。
```go
func GetConnectStatusName(i uint32) string {
    switch i {
    case ConnectStatusPendingInt:
        return ConnectStatusPendingStr
    case ConnectStatusConnectedInt:
        return ConnectStatusConnectedStr
    case ConnectStatusDisconnectedInt:
        return ConnectStatusDisconnectedStr
    case ConnectStatusServiceDeletedInt:
        return ConnectStatusServiceDeletedStr
    default:
        return ConnectStatusDisconnectedStr
    }
}
```

### 响应构建函数

#### buildVPCEndpointConnectionsResponse
将数据库模型转换为响应结构 [[源文件:/raw/assets/repo/privatelink/apisvr/api/DescribeVPCEndpointConnections.go:L96-L110]]。
```go
func (a *API) buildVPCEndpointConnectionsResponse(endpointsDB []*model.TVpcEndpoint) []*EndpointConnectionInfo {
    connections := make([]*EndpointConnectionInfo, 0, len(endpointsDB))
    for _, e := range endpointsDB {
        connections = append(connections, &EndpointConnectionInfo{
            ServiceId:        e.ServiceID,
            Owner:            e.CompanyID,
            EndpointId:       e.EndpointID,
            ConnectBandwidth: e.ConnectBw,
            ConnectionStatus: GetConnectStatusName(e.ConnectStatus),
            CreateTime:       e.InsertTime,
            UpdateTime:       uint32(e.UpdateTime.Unix()),
        })
    }
    return connections
}
```

## 数据类型映射

| 数据库类型 | Go 类型 | JSON 类型 | 描述 |
|-----------|--------|----------|------|
| `connect_status` | `uint32` | `string` | 连接状态（通过转换函数） |
| `connect_bw` | `uint32` | `number` | 连接带宽（Mbps） |
| `insert_time` | `time.Time` | `number` | 创建时间（Unix时间戳） |
| `update_time` | `time.Time` | `number` | 更新时间（Unix时间戳） |

## 验证规则

### 带宽验证
- **范围**：100-10000 Mbps
- **验证标签**：`min=100,max=10000`
- **单位**：Mbps（兆比特每秒）

### 状态验证
- **允许值**：`"Pending"`, `"Connected"`, `"Disconnected"`
- **验证标签**：`oneof=Pending Connected Disconnected`

### 必需字段
- `ServiceId`：必须提供
- `EndpointId`：必须提供（除查询接口外）
- **验证标签**：`required`

## 相关文档
- [连接管理概述](../connection_management.md)
- [AcceptVPCEndpointConnection 接口](../interfaces/AcceptVPCEndpointConnection.md)
- [RejectVPCEndpointConnection 接口](../interfaces/RejectVPCEndpointConnection.md)
- [DescribeVPCEndpointConnections 接口](../interfaces/DescribeVPCEndpointConnections.md)
- [UpdateVPCEndpointConnectionAttribute 接口](../interfaces/UpdateVPCEndpointConnectionAttribute.md)
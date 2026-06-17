# API 文档

## 终端节点服务接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | CreateVPCEndpointServiceConfiguration | api/CreateVPCEndpointServiceConfiguration.go | 创建终端节点服务配置，支持负载均衡和后端资源 |
| / | POST | DeleteVPCEndpointServiceConfiguration | api/DeleteVPCEndpointServiceConfiguration.go | 删除终端节点服务配置 |
| / | POST | DescribeVPCEndpointServiceConfiguration | api/DescribeVPCEndpointServiceConfiguration.go | 查询终端节点服务配置详情 |
| / | POST | UpdateVPCEndpointServiceConfiguration | api/UpdateVPCEndpointServiceConfiguration.go | 更新终端节点服务配置属性 |
| / | POST | DescribeVPCEndpointServices | api/DescribeVPCEndpointServices.go | 查询终端节点服务列表，支持白名单过滤 |

## 终端节点接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | CreateVPCEndpoint | api/CreateVPCEndpoint.go | 创建终端节点，分配 IP 地址并建立连接 |
| / | POST | DeleteVPCEndpoint | api/DeleteVPCEndpoint.go | 删除终端节点，释放资源 |
| / | POST | DescribeVPCEndpoints | api/DescribeVPCEndpoints.go | 查询终端节点列表，支持 VPC 和子网过滤 |
| / | POST | UpdateVPCEndpointAttribute | api/UpdateVPCEndpointAttribute.go | 更新终端节点属性（如连接带宽） |

## 终端节点连接接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | AcceptVPCEndpointConnection | api/AcceptVPCEndpointConnection.go | 接受终端节点连接请求 |
| / | POST | RejectVPCEndpointConnection | api/RejectVPCEndpointConnection.go | 拒绝终端节点连接请求 |
| / | POST | DescribeVPCEndpointConnections | api/DescribeVPCEndpointConnections.go | 查询终端节点连接状态 |
| / | POST | UpdateVPCEndpointConnectionAttribute | api/UpdateVPCEndpointConnectionAttribute.go | 更新终端节点连接属性 |

## 白名单管理接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | AddUsersToVPCEndpointService | api/AddUsersToVPCEndpointService.go | 添加用户到终端节点服务白名单 |
| / | POST | RemoveUsersToVPCEndpointService | api/RemoveUsersToVPCEndpointService.go | 从终端节点服务白名单移除用户 |
| / | POST | UpdateUsersToVPCEndpointService | api/UpdateUsersToVPCEndpointService.go | 更新终端节点服务白名单用户信息 |
| / | POST | ListVPCEndpointServiceUsers | api/ListVPCEndpointServiceUsers.go | 查询终端节点服务白名单用户列表 |

## 计费和询价接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | GetPrivateLinkPrice | api/GetPrivatelinkPrice.go | 查询 PrivateLink 服务价格 |
| / | POST | GetPrivateLinkBandwidth | api/GetPrivateLinkBandwidth.go | 获取支持的带宽范围 |

## 内部管理接口

| 接口路径 | 方法 | 处理函数 | 文件位置 | 业务含义 |
|---------|------|---------|----------|----------|
| / | POST | IDeleteVPCEndpoint | api/IDeleteVPCEndpoint.go | 内部接口：强制删除终端节点 |
| / | POST | IDeleteVPCEndpointServiceConfiguration | api/IDeleteVPCEndpointServiceConfiguration.go | 内部接口：强制删除终端节点服务配置 |
| / | POST | RefreshData | api/RefreshData.go | 临时接口：用于数据刷新 |

## 请求路由机制

所有接口统一通过 POST 方法访问根路径 `/`，通过请求体中的 `Action` 字段进行路由分发：

```go
// api/api.go:163
switch req.Action {
case ActionCreateVPCEndpointServiceConfiguration:
    resp = a.CreateVPCEndpointServiceConfiguration(c)
case ActionDeleteVPCEndpointServiceConfiguration:
    resp = a.DeleteVPCEndpointServiceConfiguration(c)
// ... 其他 Action 处理
}
```

## 请求/响应格式

### 请求格式
```json
{
  "Action": "CreateVPCEndpoint",
  "request_uuid": "optional-request-id",
  "top_organization_id": 12345,
  "organization_id": 12345,
  "az_group": 1,
  // ... 其他业务参数
}
```

### 响应格式
```json
{
  "Action": "CreateVPCEndpointResponse",
  "RetCode": 0,
  "Message": "Success",
  // ... 其他业务响应字段
}
```

## 错误码定义

错误码在 `api/error.go` 中定义，常见错误码包括：
- `0`: 成功
- 参数错误类：请求参数校验失败
- 资源错误类：资源不存在、配额超限
- 权限错误类：权限拒绝、白名单限制
- 系统错误类：内部服务错误
%% state: pending-review | confidence: 7 | type: module | sources: privatelink/apisvr | module: error-handling | stage: L1 | agent: writer | created: 2026-06-29 %%

# 连接管理错误处理

## 概述

本文档描述 VPC Endpoint 连接管理模块中可能出现的错误场景、错误码和相应的处理策略。

## 通用错误场景

### 1. 请求参数验证错误

#### RequestParamsErr (错误码: 230)
- **触发条件**：请求参数验证失败
- **常见场景**：
  - 缺少必需字段（`ServiceId`, `EndpointId`） [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L32-L36]]
  - 带宽值超出范围（100-10000 Mbps） [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L22]]
  - 连接状态字符串无效 [[源文件:/raw/assets/repo/privatelink/apisvr/api/DescribeVPCEndpointConnections.go:L26]]

### 2. 资源不存在错误

#### ResourceNotFoundErr (错误码: 217803)
- **触发条件**：指定的资源不存在
- **处理逻辑**：
  ```go
  endpoints, err := a.db.GetVPCEndpointConnection(ctx, req.EndpointId, req.ServiceId, uresource.UresourceAll)
  if err != nil {
      ucontext.Logger(ctx).Errorw("get endpoints fail", "err", err)
      return req.GenResponse(InternalServerErr)
  }
  if len(endpoints) == 0 {
      return req.GenResponse(ResourceNotFoundErr)
  }
  ```
  [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L38-L45]]

- **影响接口**：所有连接管理接口
- **解决方案**：检查资源ID是否正确，或确认资源是否已被删除

### 3. 内部服务器错误

#### InternalServerErr (错误码: 500)
- **触发条件**：数据库查询失败、系统异常或资源重复
- **常见场景**：
  - 数据库连接失败 [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L38-L42]]
  - 查询到多个相同的资源ID [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L43-L49]]
  - 状态更新失败 [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L73-L77]]

## 连接管理特有错误场景

### 1. 资源重复错误

虽然不是特定的错误码，但查询到重复资源时会记录错误并返回 `InternalServerErr`：

```go
if len(endpoints) > 1 {
    ucontext.Logger(ctx).Errorw("more than one endpoint with same id", "endpoints", endpoints)
    return req.GenResponse(InternalServerErr)
}
```

[[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L43-L49]]

**日志信息**：`"more than one endpoint with same id"` 或 `"more than one service with same id"`

### 2. 连接状态检查逻辑

#### 状态无变化处理
- **场景**：连接已经处于目标状态
- **处理逻辑**：
  ```go
  if endpoint.ConnectStatus == ConnectStatusConnectedInt && endpoint.ConnectBw == req.ConnectBandwidth {
      return req.GenResponse(nil)
  }
  ```
  [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L69-L71]]

  ```go
  if endpoint.ConnectStatus == ConnectStatusDisconnectedInt {
      return req.GenResponse(nil)
  }
  ```
  [[源文件:/raw/assets/repo/privatelink/apisvr/api/RejectVPCEndpointConnection.go:L61-L63]]

- **表现**：返回成功（RetCode: 0），无实际状态变更

### 3. 带宽更新检查

#### 带宽无变化处理
- **场景**：新旧带宽值相同或带宽为0
- **处理逻辑**：
  ```go
  if req.ConnectBandwidth == 0 || endpoints[0].ConnectBw == req.ConnectBandwidth {
      req.GenResponse(nil)
  }
  ```
  [[源文件:/raw/assets/repo/privatelink/apisvr/api/UpdateVPCEndpointConnectionAttribute.go:L61-L63]]

- **表现**：返回成功，无实际更新操作

### 4. 服务查询失败

在 `DescribeVPCEndpointConnections` 中，如果服务不存在，返回空列表而不是错误：

```go
if len(serviceDB) == 0 {
    return &DescribeVPCEndpointConnectionsResp{
        RespBase:    req.GenResponse(ResourceNotFoundErr),
        TotalCount:  0,
        Connections: []*EndpointConnectionInfo{},
    }
}
```

[[源文件:/raw/assets/repo/privatelink/apisvr/api/DescribeVPCEndpointConnections.go:L69-L75]]

## 错误处理最佳实践

### 1. 前置验证
- **参数验证**：使用结构体标签进行基础验证
- **资源验证**：查询前验证资源存在性和唯一性
- **状态验证**：检查当前状态是否需要变更

### 2. 错误日志记录
- **结构化日志**：使用 `Errorw` 记录结构化日志
- **上下文信息**：包含资源ID、错误详情等关键信息
- **调试信息**：在开发环境中记录更详细的信息

### 3. 错误响应
- **明确的错误码**：使用预定义的错误码
- **清晰的错误信息**：提供可读的错误描述
- **适当的HTTP状态码**：映射到合适的HTTP状态码

### 4. 资源清理
- **异步清理**：状态变更后异步清理相关资源 [[源文件:/raw/assets/repo/privatelink/apisvr/api/AcceptVPCEndpointConnection.go:L78-L81]]
- **错误恢复**：清理失败时记录日志但不阻塞主流程

## 接口错误映射表

| 接口 | 错误场景 | 错误码 | 处理方式 |
|------|---------|-------|---------|
| `AcceptVPCEndpointConnection` | 参数验证失败 | 230 | 返回错误 |
| | 资源不存在 | 217803 | 返回错误 |
| | 资源重复 | 500 | 记录日志并返回错误 |
| | 连接已是目标状态 | 0 | 返回成功 |
| `RejectVPCEndpointConnection` | 参数验证失败 | 230 | 返回错误 |
| | 资源不存在 | 217803 | 返回错误 |
| | 连接已是拒绝状态 | 0 | 返回成功 |
| `DescribeVPCEndpointConnections` | 参数验证失败 | 230 | 返回错误 |
| | 服务不存在 | 217803 | 返回空列表 |
| | 服务重复 | 500 | 记录日志并返回错误 |
| `UpdateVPCEndpointConnectionAttribute` | 参数验证失败 | 230 | 返回错误 |
| | 资源不存在 | 217803 | 返回错误 |
| | 带宽无变化 | 0 | 返回成功 |

## 调试建议

### 1. 常见问题排查
- **资源不存在**：确认资源ID正确，检查资源状态
- **权限问题**：确认用户有操作权限
- **配额限制**：检查相关配额是否已满

### 2. 日志分析
- **错误日志位置**：`ucontext.Logger(ctx).Errorw`
- **关键信息**：资源ID、错误类型、操作类型
- **时间戳**：操作发生时间

### 3. 监控指标
- **错误率**：各接口错误率监控
- **响应时间**：异常请求的响应时间
- **资源状态**：连接状态的分布情况

## 相关文档
- [通用错误处理](../error_handling.md)
- [连接管理概述](../connection_management.md)
- [数据模型](../data_models_connection.md)
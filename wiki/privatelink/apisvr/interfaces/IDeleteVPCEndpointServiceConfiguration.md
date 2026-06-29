%% state: reviewed | confidence: 9 | type: api | sources: privatelink/apisvr | action: IDeleteVPCEndpointServiceConfiguration | stage: L2 | agent: writer | created: 2026-06-29 %%

# IDeleteVPCEndpointServiceConfiguration

## 描述

删除VPC终端节点服务配置接口。该接口支持强制删除模式，当服务存在活跃连接时，非强制删除会失败。删除操作包含软删除数据库记录，并异步清理相关资源（SNAT IP地址、计费资源、L4网关、白名单等）。

## 调用方式

| 字段 | 值 |
|------|:--:|
| Action | `IDeleteVPCEndpointServiceConfiguration` |
| 协议 | HTTP |
| 方法 | POST |
| 来源 | `api/IDeleteVPCEndpointServiceConfiguration.go` |

## 请求结构

| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| ServiceId | string | ✅ | 终端节点服务的ID [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L18]] |
| Force | bool | ❌ | 是否强制删除（默认false）[[源文件:IDeleteVPCEndpointServiceConfiguration.go:L21]] |

## 响应结构

| 字段 | 类型 | 说明 |
|------|------|------|
| 继承RespBase | - | 基础响应结构 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L25]] |

## 业务逻辑

1. **参数解析与校验** [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L33-L37]]：解析请求参数，验证ServiceId必填字段，校验失败返回`RequestParamsErr`

2. **服务信息获取** [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L48-L53]]：查询指定ServiceId的服务信息（包含已删除记录），数据库查询失败返回`InternalServerErr`

3. **前置检查**：
   - 服务不存在返回`ResourceNotFoundErr` [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L54-L56]]
   - 服务已删除则直接返回成功 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L62-L64]]
   - 检查服务活跃连接数，非强制模式且有活跃连接时返回`ActiveConnectionsExistErr` [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L72-L74]]

4. **服务软删除** [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L81-L84]]：标记服务为删除状态

5. **异步资源清理** [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L86-L130]]：
   - 释放服务的SNAT IPv4地址 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L88-L92]]
   - 解除分配的IPv6地址 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L94-L98]]
   - 删除服务的SNAT IP记录 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L100-L104]]
   - 删除按量计费服务的计费资源 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L105-L109]]
   - 删除VPC终端节点服务资源 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L110-L113]]
   - 删除L4网关配置 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L115-L118]]
   - 删除服务的白名单记录 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L119-L122]]
   - 更新关联终端节点状态为服务已删除 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L123-L127]]
   - 关闭连接信息 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L128]]

## 错误处理

| 错误码 | 说明 | 触发条件 |
|--------|------|----------|
| RequestParamsErr | 请求参数错误 | 参数解析或校验失败 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L36]] |
| ResourceNotFoundErr | 资源不存在 | 服务ID对应的服务不存在 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L55]] |
| ActiveConnectionsExistErr | 活跃连接存在 | 非强制删除且服务有活跃连接 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L73]] |
| InternalServerErr | 内部服务器错误 | 数据库操作、资源清理等失败 [[源文件:IDeleteVPCEndpointServiceConfiguration.go:L52]] |

## AST 引用

- 社区: [[Community 40]]

## 相关接口

- [[privatelink/apisvr/interfaces/ICreateVPCEndpointServiceConfiguration|ICreateVPCEndpointServiceConfiguration]] — 创建VPC终端节点服务配置
- [[privatelink/apisvr/interfaces/IDescribeVPCEndpointServiceConfiguration|IDescribeVPCEndpointServiceConfiguration]] — 查询VPC终端节点服务配置详情
- [[privatelink/apisvr/interfaces/IListVPCEndpointServiceConfigurations|IListVPCEndpointServiceConfigurations]] — 列举VPC终端节点服务配置
- [[privatelink/apisvr/interfaces/DeleteVPCEndpointServiceConfiguration|DeleteVPCEndpointServiceConfiguration]] — 公开版本删除接口
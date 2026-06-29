%% state: pending-review | confidence: 9 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# VPC终端节点管理 — 接口综合分析

## 概述
VPC终端节点管理是PrivateLink服务的核心功能模块，负责终端节点的生命周期管理，包括创建、查询、更新、删除操作。终端节点是VPC网络连接到终端节点服务的入口点。

## 数据库模型
```go
type TVpcEndpoint struct {
    EndpointID    string    // 终端节点ID，主标识
    ServiceID     string    // 关联的服务ID
    CompanyID     uint32    // 公司ID
    AccountID     uint32    // 账户ID
    VnetID        string    // VPC ID
    SubnetworkID  string    // 子网ID
    TunnelID      uint32    // 隧道ID
    Ipv4          string    // IPv4地址
    Ipv6          string    // IPv6地址
    Mac           string    // MAC地址
    ConnectBw     uint32    // 连接带宽
    ConnectStatus uint32    // 连接状态
    CloseStatus   uint32    // 关闭状态
    VisibleType   uint32    // 可见类型（0-可见，1-不可见，2-全部）
    ChannelID     uint32    // 渠道ID
    InsertTime    uint32    // 创建时间
    DeleteTime    uint32    // 删除时间（软删除标记）
}
```
[[源文件:t_vpc_endpoint.gen.go:L14-34]]

## 核心接口

### 1. CreateVPCEndpoint
**功能**：创建终端节点，包括资源创建、IP分配、计费处理等复杂流程。

**关键流程**：
1. 配额检查（空闲终端节点配额）
2. 服务验证（存在性、关闭状态、付费模式）
3. 白名单验证（跨公司访问控制）
4. 资源创建（资源系统、VPC网络、计费系统）
5. 数据库持久化

**复杂度**：高（366行代码，包含13个业务步骤） [[源文件:CreateVPCEndpoint.go]]

### 2. DeleteVPCEndpoint / IDeleteVPCEndpoint
**功能**：删除终端节点，支持软删除和硬删除两种模式。

**区别**：
- `DeleteVPCEndpoint`：普通删除，检查可见性
- `IDeleteVPCEndpoint`：强制删除，忽略可见性检查

**删除流程**：
1. 软删除标记（数据库DeleteTime字段）
2. 异步资源清理（计费、VPC、资源系统）
3. 连接状态更新

### 3. DescribeVPCEndpoints
**功能**：查询终端节点列表，支持多种过滤条件和分页。

**数据源**：
1. 数据库查询（基础信息）
2. 资源系统查询（扩展信息：Name、Tag等）
3. 结果合并与排序

### 4. UpdateVPCEndpointAttribute
**功能**：更新终端节点属性，支持IP协议切换。

**IP协议变更逻辑**：
- IPv4 → DualStack：申请IPv6地址
- DualStack → IPv4：释放IPv6地址

## 错误处理体系
| 错误分类 | 错误码范围 | 代表错误 |
|----------|------------|----------|
| 参数错误 | 230 | RequestParamsErr |
| 资源不存在 | 217803 | ResourceNotFoundErr |
| 权限错误 | 217812 | PermissionIsDeniedErr |
| 配额错误 | 217818-217825 | 多种配额错误 |
| VPC错误 | 217820、217827 | VPC相关错误 |
| 内部错误 | 500 | InternalServerErr |

完整错误列表参见 [[privatelink/apisvr/error_handling]]

## 关键业务规则

### 1. 可见性规则
- **可见资源**：普通用户可见，需要配额检查
- **不可见资源**：内部资源，无需配额检查
- **不可见资源付费限制**：必须是服务端付费

### 2. 渠道规则
- 渠道ID匹配检查（可跳过：`SkipChannelCheck`）
- 跨渠道连接特殊权限：`CheckEndpointCanConnectOtherChannel`

### 3. 白名单规则
- 同公司：自动允许
- 不同公司：检查白名单
- 无白名单：允许所有

### 4. 连接配额规则
- 服务级配额：`CheckEndpointCanConnectService`
- 公司级配额：基于公司ID和账户ID

### 5. IP地址管理
- IPv4：必选，随机分配或指定
- IPv6：可选，仅DualStack时有效
- 地址校验：VPC和子网范围内的合法地址

## 系统集成

### 资源系统 (UResource)
- 创建/删除终端节点资源
- 更新扩展信息（Name、Tag）
- 资源激活

### 计费系统 (UBill)
- 后付费资源购买（Endpoint付费模式）
- 资源删除时的计费清理

### VPC网络 (VPC Factory)
- IP地址分配（IPv4、IPv6）
- IP地址释放
- VPC/子网验证

### 数据库层 (DB)
- CRUD操作
- 软删除标记
- 连接状态管理

## 事务与回滚机制
CreateVPCEndpoint实现了复杂的回滚机制，每个步骤失败都会触发相应的回滚操作：

```go
rollbackEndpoint(ctx, req, endpointID, 
    hasResource,      // 是否有资源系统记录
    hasBuyResource,   // 是否有计费资源
    hasIPv4,          // 是否有IPv4地址
    hasIPv6,          // 是否有IPv6地址
    hasEndpointInDB)  // 是否有数据库记录
```

回滚顺序与创建顺序相反，确保资源清理的完整性。

## 性能考虑
1. **异步操作**：资源清理、连接更新等操作异步执行
2. **批量查询**：DescribeVPCEndpoints支持批量ID查询
3. **分页支持**：Offset/Limit分页，避免大数据量问题
4. **缓存策略**：资源系统查询结果合并，减少重复查询

## 相关页面
- [[privatelink/apisvr/interfaces/CreateVPCEndpoint]]
- [[privatelink/apisvr/interfaces/DeleteVPCEndpoint]]
- [[privatelink/apisvr/interfaces/IDeleteVPCEndpoint]]
- [[privatelink/apisvr/interfaces/DescribeVPCEndpoints]]
- [[privatelink/apisvr/interfaces/UpdateVPCEndpointAttribute]]
- [[privatelink/apisvr/data_models]]
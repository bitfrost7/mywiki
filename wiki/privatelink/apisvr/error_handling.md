%% state: pending-review | confidence: 9 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# 错误处理 — PrivateLink API Server

## 错误码体系

### 通用错误码
| 错误码 | 错误常量 | 描述 | 使用场景 |
|--------|----------|------|----------|
| 0 | nil | Success | 操作成功 |
| 160 | MissingActionErr | 缺少Action参数 | 请求参数校验 |
| 161 | ActionNotFoundErr | Action不存在 | 路由匹配失败 |
| 230 | RequestParamsErr | 请求参数错误 | 参数验证失败 |
| 500 | InternalServerErr | 内部服务器错误 | 未分类的系统错误 |

[[源文件:error.go:L9-13]]

### PrivateLink专用错误码 (217801-218000)
| 错误码 | 错误常量 | 描述 | 触发条件 |
|--------|----------|------|----------|
| 217801 | NotSupportNLBErr | NLB暂不支持 | 创建NLB类型服务 |
| 217802 | NotSupportIPv6Err | IPv6不支持 | IPv6相关操作 |
| 217803 | ResourceNotFoundErr | 资源不存在 | 查询不存在的资源 |
| 217804 | VPCDismatchErr | VPC不匹配 | 跨VPC操作 |
| 217805 | WithoutIntranetIPErr | 无内网IP | 资源缺少内网IP |
| 217806 | MoreThanOneIPErr | 多个内网IP | 资源有多个IP需指定 |
| 217807 | IPNotBelongErr | IP不属于资源 | IP地址验证失败 |
| 217808 | VPCNotFoundErr | VPC不存在 | VPC查询失败 |
| 217809 | SubnetNotFoundErr | 子网不存在 | 子网查询失败 |
| 217810 | IPVersionErr | IP版本错误 | IP协议版本不匹配 |
| 217811 | IPNotBelongSubnetErr | IP不属于子网 | IP子网验证失败 |
| 217812 | PermissionIsDeniedErr | 权限被拒绝 | 白名单验证失败 |
| 217813 | RecordAlreadyExistsErr | 记录已存在 | 创建重复记录 |
| 217814 | TooManySnatIpsCreatErr | 创建过多SNAT IP | SNAT IP配额超限 |
| 217815 | HasRepeatSnatIpErr | SNAT IP重复 | SNAT IP重复创建 |
| 217816 | ActiveConnectionsExistErr | 存在活跃连接 | 删除有连接的服务 |
| 217817 | ServiceNotExistErr | 服务不存在 | 服务查询失败 |
| 217818 | IdleEPQuotaExceededErr | 空闲终端节点配额超限 | 创建可见终端节点 |
| 217819 | ResourceTypeDisMatchErr | 资源类型不匹配 | 资源类型验证失败 |
| 217820 | VPCNotSupportIPv6Err | VPC不支持IPv6 | IPv6操作失败 |
| 217821 | ServiceHasBeenClosedErr | 服务已关闭 | 操作已关闭的服务 |
| 217822 | GetPrivateLinkPriceErr | 获取价格错误 | 价格查询失败 |
| 217823 | InvisibleEndpointPayerErr | 不可见终端节点必须服务付费 | 不可见资源付费验证 |
| 217824 | ConnectEPQuotaExceededErr | 服务连接终端节点配额超限 | 服务连接数超限 |
| 217825 | ResourceQuotaExceededErr | 资源配额超限 | 资源系统配额检查 |
| 217826 | ChannelDisMatchErr | 渠道不匹配 | 渠道验证失败 |
| 217827 | VPCAllocateIPErr | VPC分配IP失败 | IP地址分配失败 |

[[源文件:error.go:L15-43]]

## 错误映射机制

### 错误码映射表 (ErrCodeDefine)
```go
ErrCodeDefine = map[error]int{
    nil:               0,
    MissingActionErr:  160,
    ActionNotFoundErr: 161,
    RequestParamsErr:  230,
    InternalServerErr: 500,
    // PrivateLink错误...
}
```
[[源文件:error.go:L44-80]]

### 错误描述映射表 (ErrCodeDescribe)
```go
ErrCodeDescribe = map[error]string{
    nil:              "Success",
    MissingActionErr: "Key parameter Action is missing...",
    // 其他错误描述...
}
```
[[源文件:error.go:L82-118]]

## 错误处理流程

### 1. 错误生成
```go
// 在业务逻辑中直接返回错误常量
return req.GenResponse(ResourceNotFoundErr)

// 或返回带描述的错误
return req.GenResponse(RequestParamsErr, "缺少必要参数VPCId")
```

### 2. 错误转换
```go
func (r *ReqBase) GenResponse(err error, desc ...string) *RespBase {
    code := ErrCodeDefine[err]
    message := ErrCodeDescribe[err]
    if len(desc) > 0 {
        message = fmt.Sprintf(message, desc[0])
    }
    return &RespBase{Code: code, Message: message}
}
```

### 3. 客户端接收
```json
{
    "Code": 217803,
    "Message": "The resource does not exist or has been deleted"
}
```

## 错误分类

### 1. 客户端错误 (4xx范围)
- **参数错误**：RequestParamsErr (230)
- **权限错误**：PermissionIsDeniedErr (217812)
- **配额错误**：IdleEPQuotaExceededErr (217818) 等

### 2. 服务端错误 (5xx范围)
- **内部错误**：InternalServerErr (500)
- **外部系统错误**：VPCAllocateIPErr (217827) 等
- **数据库错误**：转换为InternalServerErr

### 3. 业务逻辑错误 (21xxxx范围)
- **资源状态错误**：ServiceHasBeenClosedErr (217821)
- **配置错误**：VPCNotSupportIPv6Err (217820)
- **限制错误**：各种配额错误 (217818-217825)

## 错误日志记录

### 日志格式
```go
ucontext.Logger(ctx).Errorw(
    "操作失败描述",
    "err", err,          // 错误对象
    "endpointID", id,    // 相关资源ID
    "req", req,          // 请求参数（脱敏后）
)
```

### 日志级别
- **Error**：业务错误、外部系统错误
- **Warn**：可恢复的异常、配置问题
- **Info**：重要操作记录
- **Debug**：详细调试信息

## 错误恢复策略

### 1. 可重试错误
1. **网络错误**：外部系统调用失败
2. **临时错误**：资源系统繁忙
3. **超时错误**：VPC操作超时

**重试策略**：指数退避，最多3次重试

### 2. 不可恢复错误
1. **参数错误**：客户端必须修复
2. **权限错误**：需要申请权限
3. **配额错误**：需要提升配额

### 3. 异步补偿
1. **创建失败**：rollbackEndpoint清理已创建资源
2. **删除失败**：记录失败日志，定期重试
3. **更新失败**：回滚到之前状态

## 错误监控

### 关键指标
1. **错误率**：总请求中的错误比例
2. **错误类型分布**：各类错误的数量统计
3. **外部系统错误**：VPC、资源系统、计费系统错误
4. **响应时间异常**：与错误相关的延迟增加

### 告警规则
1. **错误率突增**：5分钟内错误率 > 5%
2. **关键错误持续**：ResourceNotFoundErr持续出现
3. **外部系统故障**：VPCAllocateIPErr连续失败
4. **服务不可用**：InternalServerErr大量出现

## 最佳实践

### 1. 错误信息设计
- **用户友好**：描述问题原因和解决方案
- **可追溯**：包含相关资源ID
- **安全**：不泄露内部信息

### 2. 错误处理
- **尽早失败**：参数校验阶段就返回错误
- **明确分类**：区分客户端和服务端错误
- **完整日志**：记录错误上下文便于排查

### 3. 客户端处理
- **重试策略**：根据错误码决定是否重试
- **降级方案**：关键错误提供降级方案
- **用户提示**：友好的错误提示信息

## 相关页面
- [[privatelink/apisvr/endpoint_management]]
- [[privatelink/apisvr/interfaces/CreateVPCEndpoint]]
- [[privatelink/apisvr/architecture]]
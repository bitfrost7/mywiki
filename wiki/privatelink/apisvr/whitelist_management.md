%% state: pending-review | confidence: 8 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# 服务用户白名单管理

## 概述
VPC终端节点服务的用户白名单管理功能，用于控制哪些公司可以访问特定的私有链接服务。通过白名单机制实现细粒度的访问权限控制。

## 核心功能

### 1. 白名单添加 (AddUsersToVPCEndpointService)
**功能**：向服务添加白名单用户/公司
**限制**：最多支持100个公司ID批量添加
**验证**：
- 服务存在性校验
- 公司ID真实性校验
- 重复添加检查
- 重复公司ID检查

### 2. 白名单移除 (RemoveUsersToVPCEndpointService)
**功能**：从服务移除白名单用户/公司
**限制**：最多支持100个公司ID批量删除
**验证**：
- 服务存在性校验
- 服务所有权验证

### 3. 白名单查询 (ListVPCEndpointServiceUsers)
**功能**：查询服务的白名单用户列表
**特性**：
- 自动去重处理（解决并发重复记录问题）
- 完整用户信息返回（公司ID、备注、创建时间）

## 数据结构

### 白名单记录模型
```json
{
  "ServiceID": "epsrv-xxx",
  "CompanyID": 100001,
  "Remark": "合作伙伴A",
  "InsertTime": 1625097600
}
```

### API数据结构
| 结构体 | 用途 | 字段说明 |
|--------|------|----------|
| AddEndpointServiceUser | 添加请求的用户结构 | CompanyId, Remark |
| EndpointServiceUser | 查询响应的用户结构 | CompanyId, Remark, CreateTime |

## 业务规则

### 权限控制
1. **服务所有者权限**：只有服务创建者可以管理白名单
2. **白名单验证**：创建终端节点时检查请求公司是否在服务白名单中
3. **默认可见性**：未设置白名单的服务对所有用户可见

### 数据一致性
1. **批量操作**：支持100个公司ID的批量操作
2. **重复处理**：
   - 添加时检查重复公司ID和已存在记录
   - 查询时自动去重处理并发产生的重复记录
3. **事务保证**：数据库操作确保数据一致性

### 验证流程
1. **服务验证**：确认服务存在且属于请求者
2. **公司验证**：验证公司ID的真实性（通过账户系统）
3. **权限验证**：检查是否已存在相同记录

## 错误处理模式

### 常见错误场景
| 错误码 | 场景 | 处理方式 |
|--------|------|----------|
| 217813 | 重复添加已存在的白名单记录 | 拒绝操作，返回具体错误信息 |
| 217817 | 服务不存在或已被删除 | 拒绝操作，提示资源不存在 |
| 230 | 请求参数错误（重复公司ID、非法公司ID等） | 拒绝操作，返回具体参数错误信息 |

### 容错机制
1. **批量操作原子性**：批量添加/删除要么全部成功，要么全部失败
2. **并发重复记录处理**：查询接口自动去重，避免因并发问题导致数据异常
3. **外部系统调用容错**：公司信息验证失败时明确提示"非法公司ID"

## 使用场景

### 场景1：合作伙伴接入
**需求**：允许特定合作伙伴访问私有服务
**流程**：
1. 合作伙伴提供公司ID
2. 通过AddUsersToVPCEndpointService添加到服务白名单
3. 合作伙伴可以创建终端节点连接服务

### 场景2：权限回收
**需求**：撤销某个合作伙伴的访问权限
**流程**：
1. 通过ListVPCEndpointServiceUsers查看现有白名单
2. 通过RemoveUsersToVPCEndpointService移除指定公司
3. 已建立的连接不受影响，但无法新建连接

### 场景3：权限审计
**需求**：查看服务的所有授权用户
**流程**：
1. 通过ListVPCEndpointServiceUsers获取完整白名单列表
2. 验证授权关系是否符合预期
3. 清理不必要的授权

## 接口关联

### 与服务管理接口的关联
- [[privatelink/apisvr/interfaces/CreateVPCEndpointServiceConfiguration]] - 创建服务时可设置初始白名单
- [[privatelink/apisvr/interfaces/DescribeVPCEndpointServiceConfiguration]] - 服务详情中包含白名单配置状态
- [[privatelink/apisvr/interfaces/UpdateVPCEndpointServiceConfiguration]] - 与服务配置更新协同工作

### 与终端节点接口的关联
- [[privatelink/apisvr/interfaces/CreateVPCEndpoint]] - 创建连接时检查白名单权限
- [[privatelink/apisvr/interfaces/AcceptVPCEndpointConnection]] - 连接接受时验证白名单权限

## 最佳实践

### 1. 白名单管理策略
- **最小权限原则**：只添加必要的合作伙伴
- **定期审计**：定期检查白名单，清理过期授权
- **备注清晰**：为每个授权添加明确的备注信息

### 2. 批量操作优化
- **批量添加**：合作初期批量添加所有合作伙伴
- **增量管理**：后期通过Add/Remove进行增量调整
- **批量删除**：合作结束时批量移除所有相关公司

### 3. 监控与告警
- **操作日志**：记录所有白名单变更操作
- **异常检测**：监控频繁的白名单变更操作
- **权限审计**：定期生成白名单权限报告
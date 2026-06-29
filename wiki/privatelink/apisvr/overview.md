%% state: draft | confidence: 7 | type: overview | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# Service Management — VPC终端节点服务管理

## 定位
Service Management模块负责VPC终端节点服务的全生命周期管理，包括服务的创建、配置、查询、更新和删除。该模块支持多种后端资源类型（ALB、NLB、IP），提供灵活的访问控制和网络配置选项。

## 技术栈
| 层 | 技术 | 说明 |
|-------|------|------|
| API | Gin + gRPC | RESTful API接口框架 |
| 数据库 | MySQL | 服务配置和状态持久化 |
| 资源平台 | UResource | 资源管理和计费 |
| 网络 | VPC Factory | 网络资源配置和管理 |
| 计费 | UBill | 后付费资源计费 |
| 监控 | Prometheus | 接口监控和指标收集 |

## 核心功能

### 1. 服务生命周期管理
- **创建服务**：支持ALB、NLB、IP三种资源类型，IPv4/DualStack网络协议
- **删除服务**：安全检查（活跃连接检查）、异步资源清理、软删除
- **强制删除**：支持强制删除有活跃连接的服务（运维场景）

### 2. 服务配置管理
- **查询服务**：支持精确查询和条件过滤，集成数据库和资源平台数据
- **更新服务**：支持部分更新，兼容性检查，IP协议版本转换
- **服务发现**：白名单访问控制，权限继承，默认公开策略

### 3. 网络资源配置
- **SNAT IP管理**：支持IPv4和IPv6 SNAT地址分配，最多4个IP对
- **IP版本管理**：支持IPv4和DualStack，支持版本转换和自动IPv6分配
- **带宽控制**：连接带宽控制，范围100-10000 Mbps

### 4. 访问控制
- **付费模式**：Endpoint（使用者付费）和EndpointService（服务商付费）
- **白名单管理**：服务级别的用户访问控制
- **自动连接接受**：支持自动接受终端节点连接

## 服务结构
```
apisvr/api/
├── CreateVPCEndpointServiceConfiguration.go    # 创建服务
├── DeleteVPCEndpointServiceConfiguration.go    # 普通删除
├── IDeleteVPCEndpointServiceConfiguration.go   # 强制删除
├── DescribeVPCEndpointServiceConfiguration.go  # 查询配置详情
├── IDescribeVPCEndpointServiceConfiguration.go # 内部查询
├── DescribeVPCEndpointServices.go              # 服务列表
├── UpdateVPCEndpointServiceConfiguration.go    # 更新配置
├── AddUsersToVPCEndpointService.go             # 添加用户
├── RemoveUsersToVPCEndpointService.go          # 移除用户
├── ListVPCEndpointServiceUsers.go              # 列出用户
└── UpdateUsersToVPCEndpointService.go          # 更新用户

apisvr/factory/
├── uresource/      # 资源平台交互
├── vpc/            # VPC网络交互
├── ubill/          # 计费系统交互
└── l4/             # L4网关管理

apisvr/db/
├── model/          # 数据模型
└── query/          # 数据库查询
```

## 关键特性

### 1. 数据一致性
- **原子操作**：创建、更新操作的完整回滚机制
- **异步清理**：删除操作的异步资源释放，确保接口响应速度
- **双数据源同步**：数据库与资源平台数据一致性保证

### 2. 高可用设计
- **无状态API**：所有状态存储在数据库和资源平台
- **错误恢复**：完善的错误处理和重试机制
- **监控告警**：关键操作监控和异常告警

### 3. 安全控制
- **权限验证**：组织级别的访问控制
- **输入验证**：严格的参数验证和清理
- **审计日志**：所有操作记录和审计跟踪

### 4. 性能优化
- **分页查询**：大数据量查询的分页支持
- **缓存策略**：频繁访问数据的缓存优化
- **异步处理**：耗时操作的异步执行

## 业务场景

### 场景1：创建云上服务暴露
```
用户创建ALB/NLB服务 → 配置网络和访问控制 → 服务可用 → 其他用户连接
```

### 场景2：跨VPC服务共享
```
服务提供商创建服务 → 添加白名单用户 → 用户查询可用服务 → 建立连接
```

### 场景3：服务运维管理
```
监控服务状态 → 调整带宽配置 → 添加SNAT IP → 故障时删除重建
```

### 场景4：网络升级迁移
```
IPv4服务 → 升级到DualStack → 自动分配IPv6地址 → 兼容现有连接
```

## 接口统计
| 接口类型 | 数量 | 说明 |
|----------|:----:|------|
| 创建类 | 1 | 服务创建 |
| 删除类 | 2 | 普通删除 + 强制删除 |
| 查询类 | 3 | 配置查询 + 列表查询 + 内部查询 |
| 更新类 | 5 | 配置更新 + 用户管理（4个） |
| **总计** | **11** | 完整服务管理功能 |

## 设计原则

### 1. 用户友好
- 默认值设置减少用户配置复杂度
- 清晰的错误信息和解决方案
- 渐进式配置更新，避免全量重配

### 2. 运维友好
- 完整的审计和日志记录
- 详细的监控指标
- 故障自愈和自动恢复

### 3. 扩展性
- 插件化架构，支持新资源类型
- 配置驱动的功能开关
- API版本管理，兼容旧版本

### 4. 安全性
- 最小权限原则
- 输入验证和输出过滤
- 敏感信息保护和脱敏

## 相关页面
- [[privatelink/apisvr/interfaces]] - 详细接口文档
- [[privatelink/apisvr/architecture]] - 架构设计文档
- [[privatelink/apisvr/modules/db-layer]] - 数据库层详解
- [[privatelink/apisvr/modules/factory-layer]] - 工厂层详解
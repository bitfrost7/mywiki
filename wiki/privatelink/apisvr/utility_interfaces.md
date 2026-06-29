%% state: pending-review | confidence: 8 | type: overview | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-29 %%

# PrivateLink — 实用工具接口

## 定位
提供PrivateLink服务的辅助功能接口，包括价格查询、带宽信息获取和内部数据刷新等实用工具。这些接口主要服务于运营管理、成本控制和系统维护等场景。[[源文件:api/api.go:L60-L64]]

## 接口概览

### 1. 价格查询
| 接口 | 方法 | 说明 | 复杂度 | 来源 |
|------|------|------|:------:|------|
| [[privatelink/apisvr/interfaces/GetPrivateLinkPrice\\|GetPrivateLinkPrice]] | POST | 查询PrivateLink资源价格 | 中（68行） | [[源文件:GetPrivatelinkPrice.go:L41]] |

**主要功能**：
- 支持两种资源类型：终端节点(Endpoint)和终端节点服务(EndpointService) [[源文件:GetPrivatelinkPrice.go:L17]]
- 支持两种计费模式：流量计费(Traffic)和实例计费(Instance) [[源文件:GetPrivatelinkPrice.go:L19]]
- 返回原价、总价和折后价信息 [[源文件:GetPrivatelinkPrice.go:L28-L32]]

### 2. 带宽信息
| 接口 | 方法 | 说明 | 复杂度 | 来源 |
|------|------|------|:------:|------|
| [[privatelink/apisvr/interfaces/GetPrivateLinkBandwidth\\|GetPrivateLinkBandwidth]] | POST | 获取可用的带宽范围 | 低（35行） | [[源文件:GetPrivateLinkBandwidth.go:L21]] |

**主要功能**：
- 返回固定的带宽范围：100-10000 Mbps [[源文件:GetPrivateLinkBandwidth.go:L30-L33]]
- 为资源创建时的带宽参数提供参考
- 无需参数，直接返回预设值

### 3. 内部工具
| 接口 | 方法 | 说明 | 复杂度 | 来源 |
|------|------|------|:------:|------|
| [[privatelink/apisvr/interfaces/RefreshData\\|RefreshData]] | POST | 内部数据刷新接口（临时使用） | 中（41行） | [[源文件:RefreshData.go:L11]] |

**主要功能**：
- 将数据库中的付费信息同步到计费系统 [[源文件:RefreshData.go:L14-L34]]
- 支持终端节点和终端节点服务两种资源类型 [[源文件:RefreshData.go:L21-L22]]
- 返回处理统计信息：总处理量、失败数量 [[源文件:RefreshData.go:L36-L40]]

## 核心业务概念

### 1. 定价模型
PrivateLink支持两种计费模式，通过GetPrivateLinkPrice接口查询具体价格：[[源文件:GetPrivatelinkPrice.go:L19]]

| 计费模式 | 说明 | 适用场景 |
|----------|------|----------|
| **流量计费 (Traffic)** | 按实际传输流量计费 | 流量波动大的场景 |
| **实例计费 (Instance)** | 按资源实例规格计费 | 稳定流量需求的场景 |

### 2. 带宽约束
通过GetPrivateLinkBandwidth接口获取带宽范围约束：[[源文件:GetPrivateLinkBandwidth.go:L30-L33]]

- **最小带宽**：100 Mbps [[源文件:GetPrivateLinkBandwidth.go:L32]]
- **最大带宽**：10000 Mbps [[源文件:GetPrivateLinkBandwidth.go:L31]]
- **单位**：Mbps（兆比特每秒）

### 3. 资源类型
PrivateLink支持两种资源类型，价格查询接口区分这两种类型：[[源文件:GetPrivatelinkPrice.go:L17]]

| 资源类型 | 说明 | 计费方式 |
|----------|------|----------|
| **Endpoint** | 终端节点 | 支持Traffic/Instance两种模式 |
| **EndpointService** | 终端节点服务 | 支持Traffic/Instance两种模式 |

### 4. 数据同步机制
RefreshData接口实现的数据同步流程：[[源文件:RefreshData.go:L14-L34]]

1. **数据拉取**：从数据库获取所有付费信息
2. **类型判断**：区分终端节点和终端节点服务
3. **计费同步**：调用计费系统的PostPaidBuyResourceWithCheck接口
4. **结果统计**：记录成功和失败数量

### 5. 验证规则
价格查询接口的参数验证规则：[[源文件:GetPrivatelinkPrice.go:L14-L19]]

| 参数 | 验证规则 | 说明 |
|------|----------|------|
| channel | required | 渠道ID必须存在 |
| ProductType | required, oneof=["Endpoint","EndpointService"] | 必须是合法的资源类型 |
| Paymode | omitempty, max=2, oneof=["Traffic","Instance"] | 计费模式数组，最多2个元素 |

## 技术实现特点

### 1. 价格查询实现
- 与内部计费系统集成 [[源文件:GetPrivatelinkPrice.go:L52]]
- 支持批量查询多种计费模式 [[源文件:GetPrivatelinkPrice.go:L50-L62]]
- 返回详细的价格集合 [[源文件:GetPrivatelinkPrice.go:L22-L25]]

### 2. 数据刷新实现
- 依赖ubill工厂层与计费系统交互 [[源文件:RefreshData.go:L6-L7]]
- 批处理设计，处理所有存量数据 [[源文件:RefreshData.go:L15]]
- 容错机制，部分失败不影响整体流程 [[源文件:RefreshData.go:L25-L26]] [[源文件:RefreshData.go:L31-L32]]

### 3. 接口注册
三个实用工具接口在API路由中的注册位置：[[源文件:api/api.go:L200-L205]]

- GetPrivateLinkPrice：ActionGetPrivateLinkPrice [[源文件:api/api.go:L200-L201]]
- GetPrivateLinkBandwidth：ActionGetPrivateLinkBandwidth [[源文件:api/api.go:L202-L203]]
- RefreshData：ActionRefreshData [[源文件:api/api.go:L204-L205]]

## 典型使用场景

### 1. 资源创建前的成本评估
1. 调用GetPrivateLinkBandwidth获取带宽范围
2. 根据需求选择带宽值
3. 调用GetPrivateLinkPrice查询对应配置的价格
4. 基于价格信息做出资源创建决策

### 2. 系统运维和数据同步
1. 管理员权限访问RefreshData接口
2. 触发数据库到计费系统的数据同步
3. 监控同步结果，根据失败数量排查问题
4. 定期执行同步，确保计费信息一致性

### 3. 产品配置和展示
1. 在用户界面展示支持的带宽范围
2. 根据用户选择的配置实时计算价格
3. 展示不同计费模式的成本对比
4. 提供详细的价格构成说明

## 相关页面
- [[privatelink/apisvr/core_concepts]] - 核心概念与业务模型
- [[privatelink/apisvr/interfaces]] - 完整的接口文档索引
- [[privatelink/apisvr/overview]] - 服务概况
- [[privatelink/apisvr/architecture]] - 系统架构
- [[privatelink/apisvr/error_handling]] - 错误处理机制
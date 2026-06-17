# factory 模块

## 模块职责

通过工厂模式集成外部服务，统一管理 VPC、LB、L4、计费、账户和资源管理等外部依赖。

## 主要类型/函数清单

| 名称 | 类型 | 功能简述 | 行号 |
|------|------|----------|------|
| Factory | struct | 外部服务工厂结构，聚合所有外部服务 | factory/factory.go:13 |
| InitFactory | function | 初始化空的工厂实例 | factory/factory.go:23 |
| VPCImpl | struct | VPC 服务实现 | factory/vpc/impl.go:22 |
| NewVPCImpl | function | 创建 VPC 服务实例 | factory/vpc/impl.go:29 |
| LBImpl | struct | 负载均衡服务实现 | factory/lb/impl.go:25 |
| NewLBImpl | function | 创建负载均衡服务实例 | factory/lb/impl.go:32 |
| L4Impl | struct | L4 网关服务实现 | factory/l4/ |
| UBillImpl | struct | 计费服务实现 | factory/ubill/ |
| UResourceImpl | struct | 资源管理服务实现 | factory/uresource/ |
| UAccountImpl | struct | 账户服务实现 | factory/uaccount/ |

## 关键实现逻辑

### 工厂模式
使用工厂模式聚合所有外部服务，通过 `Factory` 结构统一管理依赖。在服务器初始化时，根据配置创建各个服务实例并注入到工厂中（server.go:79）。

### HTTP 客户端封装
所有外部服务都使用统一的 HTTP 客户端（`httpclient.HTTPClient`）进行通信，支持超时配置和重试机制。

### 服务发现
L4 服务使用 ZooKeeper 进行服务发现，通过名称解析器动态获取服务地址（server.go:76）。

### 错误处理
每个外部服务都有特定的错误类型，如 VPC 服务的 `ErrVPCNotSupportIPv6`（factory/vpc/impl.go:18），用于区分不同服务的错误情况。

## 外部依赖

- **privatelink-utils/httpclient**: 统一的 HTTP 客户端
- **VPC 服务**: 提供 IP 分配、子网管理、VPC 信息查询等功能
- **LB 服务**: 提供负载均衡器查询和管理功能
- **L4 服务**: 提供网关 DPID 查询等功能
- **计费服务**: 提供资源计费和购买功能
- **资源管理服务**: 提供资源查询和管理功能
- **账户服务**: 提供账户信息查询功能
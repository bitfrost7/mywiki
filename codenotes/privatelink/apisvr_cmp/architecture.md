# 架构设计

## 整体架构模式

apisvr 采用**分层架构**模式，结合**工厂模式**进行外部服务集成：

- **API 层**: 处理 HTTP 请求，参数校验，业务逻辑编排
- **数据层**: 封装数据库操作，使用 GORM 进行数据持久化
- **集成层**: 通过工厂模式集成外部服务（VPC、LB、L4、计费等）
- **监控层**: Prometheus 指标收集和系统监控

## 核心模块划分

| 模块名 | 文件位置 | 职责 |
|--------|----------|------|
| API 层 | `api/` | HTTP 请求处理、参数校验、业务逻辑编排 |
| 数据层 | `db/` | 数据库连接管理、CRUD 操作、事务处理 |
| 工厂层 | `factory/` | 外部服务集成（VPC、LB、L4、计费、账户、资源） |
| 应用层 | `server.go` | 服务器初始化、依赖注入、生命周期管理 |
| 入口层 | `cmd/main.go` | 应用启动、配置加载、命令行处理 |
| 监控层 | `prometheus/` | 系统指标收集、数据库监控、请求统计 |

## 关键接口/抽象定义

### 核心结构体

| 接口/类型 | 文件位置 | 职责 |
|-----------|----------|------|
| `Server` | `server.go:55` | 主服务器结构，管理应用生命周期 |
| `API` | `api/api.go:78` | API 处理器，管理路由和请求分发 |
| `Database` | `db/db.go:34` | 数据库封装，提供数据访问接口 |
| `Factory` | `factory/factory.go:13` | 外部服务工厂，统一管理依赖 |

### API 接口定义

| 接口名称 | 文件位置 | 功能 |
|----------|----------|------|
| `CreateVPCEndpointServiceConfiguration` | `api/api.go:39` | 创建终端节点服务配置 |
| `DeleteVPCEndpointServiceConfiguration` | `api/api.go:40` | 删除终端节点服务配置 |
| `DescribeVPCEndpointServiceConfigurations` | `api/api.go:41` | 查询终端节点服务配置 |
| `UpdateVPCEndpointServiceConfiguration` | `api/api.go:42` | 更新终端节点服务配置 |
| `CreateVPCEndpoint` | `api/api.go:45` | 创建终端节点 |
| `DeleteVPCEndpoint` | `api/api.go:46` | 删除终端节点 |
| `DescribeVPCEndpoints` | `api/api.go:47` | 查询终端节点 |
| `UpdateVPCEndpointAttribute` | `api/api.go:48` | 更新终端节点属性 |
| `AcceptVPCEndpointConnection` | `api/api.go:50` | 接受终端节点连接 |
| `RejectVPCEndpointConnection` | `api/api.go:51` | 拒绝终端节点连接 |

### 数据库接口

| 方法 | 文件位置 | 功能 |
|------|----------|------|
| `CreateService` | `db/db.go:92` | 创建服务记录 |
| `GetServices` | `db/db.go:129` | 查询服务记录 |
| `DeleteServiceSoft` | `db/db.go:117` | 软删除服务 |
| `CreateVPCEndpoint` | `db/db.go:250` | 创建终端节点记录 |
| `GetVPCEndpoints` | `db/db.go:342` | 查询终端节点记录 |
| `DeleteVPCEndpointSoft` | `db/db.go:273` | 软删除终端节点 |

### 工厂接口

| 服务 | 文件位置 | 功能 |
|------|----------|------|
| `VPCImpl` | `factory/vpc/impl.go:22` | VPC 服务集成（IP 分配、子网管理） |
| `LBImpl` | `factory/lb/impl.go:25` | 负载均衡服务集成 |
| `L4Impl` | `factory/l4/` | L4 网关服务集成 |
| `UBillImpl` | `factory/ubill/` | 计费服务集成 |
| `UResourceImpl` | `factory/uresource/` | 资源管理服务集成 |
| `UAccountImpl` | `factory/uaccount/` | 账户服务集成 |

## 数据流概览

### 请求处理流程

1. **HTTP 请求接收**: Gin 框架接收 POST 请求到 `/` 路径
2. **请求解析**: 解析 JSON 请求体，提取 `Action` 字段
3. **路由分发**: 根据 `Action` 值分发到对应的处理函数 (`api/api.go:163`)
4. **参数校验**: 使用 validator 进行参数校验 (`api/api.go:108`)
5. **业务处理**: 调用数据库和外部服务完成业务逻辑
6. **响应返回**: 统一封装响应格式，返回 JSON 结果

### 典型业务流程（创建终端节点）

1. **配额检查**: 检查空闲终端节点配额 (`api/CreateVPCEndpoint.go:87`)
2. **服务验证**: 获取并验证服务信息 (`api/CreateVPCEndpoint.go:98`)
3. **权限校验**: 检查白名单和跨渠道权限 (`api/CreateVPCEndpoint.go:149`)
4. **网络验证**: 检查 VPC 和子网信息 (`api/CreateVPCEndpoint.go:171`)
5. **资源创建**: 调用 VPC 服务分配 IP 地址 (`api/CreateVPCEndpoint.go:214`)
6. **数据持久化**: 创建数据库记录 (`api/CreateVPCEndpoint.go:241`)
7. **计费处理**: 如需终端节点付费，购买计费资源 (`api/CreateVPCEndpoint.go:206`)

### 监控数据流

1. **请求统计**: 记录请求接收次数 (`api/api.go:160`)
2. **响应统计**: 记录响应发送次数和延迟 (`api/api.go:213`)
3. **数据库监控**: 记录数据库操作指标 (`db/db.go:69`)
4. **系统指标**: 收集系统级监控数据 (`prometheus/`)
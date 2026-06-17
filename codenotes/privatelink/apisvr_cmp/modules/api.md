# api 模块

## 模块职责

处理 HTTP 请求，进行参数校验、业务逻辑编排和响应封装，是系统的核心 API 层。

## 主要类型/函数清单

| 名称 | 类型 | 功能简述 | 行号 |
|------|------|----------|------|
| API | struct | API 处理器主结构，管理路由和依赖 | api/api.go:78 |
| InitRouter | method | 初始化 Gin 路由器 | api/api.go:127 |
| handle | method | 统一请求处理入口，根据 Action 分发 | api/api.go:134 |
| CreateVPCEndpoint | method | 创建终端节点 | api/CreateVPCEndpoint.go:74 |
| DeleteVPCEndpoint | method | 删除终端节点 | api/DeleteVPCEndpoint.go |
| DescribeVPCEndpoints | method | 查询终端节点列表 | api/DescribeVPCEndpoints.go:46 |
| CreateVPCEndpointServiceConfiguration | method | 创建终端节点服务配置 | api/CreateVPCEndpointServiceConfiguration.go |
| checkVPCSubnet | method | 检查 VPC 和子网信息 | api/common.go:13 |
| checkIPs | method | 检查 IP 地址是否属于子网 | api/common.go:41 |
| parseInput | method | 解析和校验输入参数 | api/api.go:263 |

## 关键实现逻辑

### 请求路由机制
所有 HTTP 请求统一通过 POST 方法访问根路径 `/`，通过请求体中的 `Action` 字段进行路由分发。`handle` 方法解析请求后，使用 switch 语句将请求分发到对应的处理函数（api/api.go:163）。

### 参数校验
使用 `validator.v9` 进行参数校验，通过 `InitValidate` 方法初始化校验器（api/api.go:108）。支持自定义校验规则和错误消息国际化。

### 业务逻辑编排
每个 API 处理函数都遵循相似的模式：
1. 解析请求参数
2. 权限和配额检查
3. 调用数据库操作
4. 调用外部服务（VPC、LB 等）
5. 数据持久化
6. 返回响应

### 错误处理
统一错误处理机制，通过 `ErrCodeDefine` 和 `ErrCodeDescribe` 映射错误码和错误消息（api/error.go:44）。所有错误都转换为统一的响应格式。

## 外部依赖

- **db.Database**: 数据库操作接口，用于数据持久化
- **factory.Factory**: 外部服务工厂，集成 VPC、LB、L4 等服务
- **app.Application**: 应用基础框架，提供日志、配置等功能
- **github.com/gin-gonic/gin**: HTTP Web 框架
- **gopkg.in/go-playground/validator.v9**: 参数校验库
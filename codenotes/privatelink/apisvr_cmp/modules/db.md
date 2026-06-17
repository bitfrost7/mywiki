# db 模块

## 模块职责

封装数据库操作，提供数据访问接口，使用 GORM 进行数据持久化和查询。

## 主要类型/函数清单

| 名称 | 类型 | 功能简述 | 行号 |
|------|------|----------|------|
| Database | struct | 数据库封装结构，管理 GORM 连接 | db/db.go:34 |
| NewDatabase | function | 创建数据库连接，初始化监控插件 | db/db.go:45 |
| CreateService | method | 创建服务记录 | db/db.go:92 |
| GetServices | method | 查询服务记录 | db/db.go:129 |
| DeleteServiceSoft | method | 软删除服务 | db/db.go:117 |
| CreateVPCEndpoint | method | 创建终端节点记录 | db/db.go:250 |
| GetVPCEndpoints | method | 查询终端节点记录 | db/db.go:342 |
| DeleteVPCEndpointSoft | method | 软删除终端节点 | db/db.go:273 |
| UpdateVPCEndpointConnectionStatus | method | 更新终端节点连接状态 | db/db.go:306 |
| CreateServiceWhiteListRecord | method | 创建白名单记录 | db/db.go:387 |
| GetServiceWhiteListRecords | method | 查询白名单记录 | db/db.go:398 |
| CreateSnatIps | method | 批量创建 SNAT IP 记录 | db/db.go:197 |
| GetAllServiceSnatIps | method | 查询服务的所有 SNAT IP | db/db.go:235 |

## 关键实现逻辑

### 数据库连接管理
使用 GORM 连接 MySQL 数据库，配置连接池参数（最大连接生命周期、最大空闲连接数）。集成 Prometheus 监控插件，记录数据库操作指标（db/db.go:69）。

### 软删除机制
所有主要表都使用软删除机制，通过 `delete_time` 字段标记删除状态，实际数据保留在数据库中。查询时默认过滤已删除记录（`delete_time = 0`）。

### 会话管理
每个数据库操作都会创建新的会话 ID，通过 `ncontext.NewSessionIDToContext` 注入到上下文中，用于追踪和调试（db/db.go:93）。

### 查询构建
使用 GORM Gen 生成的类型安全查询构建器，支持链式调用和条件组合。查询时只选择必要的字段，避免全表扫描。

### 事务处理
虽然当前代码中没有显式的事务处理，但通过 GORM 的上下文机制支持事务操作。

## 外部依赖

- **gorm.io/gorm**: ORM 框架，提供数据库操作接口
- **gorm.io/gen**: 代码生成工具，生成类型安全的查询构建器
- **gorm.io/driver/mysql**: MySQL 数据库驱动
- **go.uber.org/zap**: 日志库，用于数据库操作日志
- **model 包**: 自动生成的数据模型定义
- **query 包**: 自动生成的查询构建器
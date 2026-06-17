# server 模块

## 模块职责

管理服务器的初始化、依赖注入和生命周期，是应用的启动入口。

## 主要类型/函数清单

| 名称 | 类型 | 功能简述 | 行号 |
|------|------|----------|------|
| Config | struct | 服务器配置结构 | server.go:24 |
| Server | struct | 服务器主结构，管理应用生命周期 | server.go:55 |
| NewServer | function | 创建服务器实例，初始化所有依赖 | server.go:63 |
| Start | method | 启动服务器 | server.go:97 |
| VerifyParams | method | 验证配置参数 | server.go:33 |
| SetDefaultValue | method | 设置配置默认值 | server.go:43 |

## 关键实现逻辑

### 依赖注入
在 `NewServer` 方法中完成所有依赖的初始化和注入：
1. 初始化数据库连接
2. 创建 HTTP 客户端
3. 初始化名称解析器（ZooKeeper）
4. 初始化工厂并注入外部服务
5. 初始化 API 层
6. 启动监控指标收集（server.go:63）

### 配置管理
配置包括数据库连接信息、内部 API 地址、ZooKeeper 路径、HTTP 客户端配置和 API 配置。提供参数验证和默认值设置功能。

### 生命周期管理
继承自 `app.Application`，使用框架提供的生命周期管理功能。`Start` 方法调用 `StartAndServe` 启动 HTTP 服务器。

### 监控集成
启动 Prometheus 系统指标收集，记录服务器级别的监控数据（server.go:91）。

## 外部依赖

- **app.Application**: 应用基础框架，提供生命周期管理
- **db.Database**: 数据库连接
- **api.API**: API 处理器
- **factory.Factory**: 外部服务工厂
- **nameresolver**: 服务发现和名称解析
- **prometheus**: 监控指标收集
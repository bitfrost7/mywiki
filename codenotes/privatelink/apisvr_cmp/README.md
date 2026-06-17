# apisvr 项目概览

## 项目描述

apisvr 是 UCloud PrivateLink 服务的对外 API 网关，为公有云 2.0 版本提供私有网络连接服务。

## 核心职责

- 提供 PrivateLink 终端节点服务和终端节点的创建、查询、更新、删除等 API 接口
- 管理终端节点连接的生命周期，包括连接接受、拒绝和属性更新
- 处理白名单权限控制和跨渠道访问校验
- 集成 VPC、LB、L4、计费等外部服务，实现资源申请和配额管理

## 技术栈

- **语言**: Go 1.18
- **Web 框架**: Gin (github.com/gin-gonic/gin)
- **数据库**: MySQL + GORM (gorm.io/gorm)
- **监控**: Prometheus
- **配置管理**: JSON 配置文件
- **外部服务集成**: VPC、LB、L4、计费、账户、资源管理

## 目录结构

```
apisvr/
├── api/          # HTTP API 处理器（26个接口文件）
├── db/           # 数据库模型和查询（自动生成）
├── factory/      # 外部服务集成工厂
├── cmd/          # 应用入口点
├── prometheus/   # 监控指标收集
└── server.go     # 服务器初始化和启动
```
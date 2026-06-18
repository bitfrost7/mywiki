# privatelink-l4fe — L4 转发引擎服务

> 代码注释文档。基于图分析（graph.json）社区聚类和源文件分析生成。

## 项目概述

`privatelink-l4fe` 是一个 **L4 转发引擎（Layer 4 Forwarding Engine）Go 服务**，属于 UCloud PrivateLink 产品体系。它的核心职责是：

1. **接收 gRPC 请求**：通过 `ListL4Gw` RPC 查询一组 L4 Gateway 的完整配置
2. **从 MySQL 数据库读取数据**：关联查询 `t_service`、`t_vpc_endpoint`、`t_service_snatips` 三张表
3. **组装并返回 L4 Gateway 视图**：将数据转换为 protobuf 定义的 `L4GwView` 结构，包含 fore IP、FNAT IP、转发组(fore/backend/FNAT groups)和规则(rules)

## 技术栈

| 组件 | 用途 |
|------|------|
| **Go 1.18** | 开发语言 |
| **gRPC** | API 通信协议 |
| **GORM + gen** | ORM 框架及代码生成 |
| **MySQL** | 持久化存储 |
| **zap** | 日志 |
| **Prometheus** | 指标采集 |
| **Kaniko** | 容器镜像构建 |
| **GitLab CI** | CI/CD |

## 项目结构

```
privatelink-l4fe/
├── cmd/privatelinkl4fe/main.go    # 入口：CLI 命令分发
├── server.go                       # Server 引导、Config 定义
├── api/
│   └── grpc_api.go                 # gRPC API 层 — 核心业务逻辑
├── mygorm/
│   ├── database.go                 # 数据库初始化、代码生成入口
│   ├── db/
│   │   ├── gen.go                  # Query 聚合、事务、读写分离
│   │   ├── t_service.gen.go        # t_service 表 DAO（生成）
│   │   ├── t_vpc_endpoint.gen.go   # t_vpc_endpoint 表 DAO（生成）
│   │   ├── t_service_snatips.gen.go# t_service_snatips 表 DAO（生成）
│   │   └── t_service_whitelist.gen.go # t_service_whitelist 表 DAO（生成）
│   └── model/
│       ├── privatelink.go          # Data 聚合结构体（手动编写）
│       ├── t_service.gen.go        # TService 模型（生成）
│       ├── t_vpc_endpoint.gen.go   # TVpcEndpoint 模型（生成）
│       ├── t_service_snatips.gen.go# TServiceSnatip 模型（生成）
│       └── t_service_whitelist.gen.go # TServiceWhitelist 模型（生成）
├── Dockerfile / Dockerfile-{amd64,arm64}  # 多架构构建
├── .gitlab-ci.yml                  # CI/CD 流水线
├── .golangci.yml                   # Linter 配置
├── go.mod / go.sum
└── README.md                       # GitLab 默认模板（无实质内容）
```

## 图分析社区总览

图分析将代码划分为 **17 个社区**（11 个主要社区 + 6 个薄社区），分组如下：

| 社区编号 | 社区名称 | 节点数 | 对应源文件 |
|---------|---------|--------|-----------|
| 0 | Service Data Access | 71 | `mygorm/db/t_service.gen.go` |
| 1 | VPC Endpoint Data Access | 71 | `mygorm/db/t_vpc_endpoint.gen.go` |
| 2 | Service SNAT IP Data Access | 70 | `mygorm/db/t_service_snatips.gen.go` |
| 3 | Service Whitelist Data Access | 70 | `mygorm/db/t_service_whitelist.gen.go` |
| 4 | Database Query Operations | 30 | `mygorm/db/gen.go` |
| 5 | Application Server Configuration | 23 | `server.go`, `mygorm/database.go`, `cmd/main.go` |
| 6 | gRPC API Layer | 14 | `api/grpc_api.go` |
| 7 | Private Link Data Models | 6 | `mygorm/model/privatelink.go` |
| 8 | Code Quality Tools | 5 | `.gitlab-ci.yml`, `.golangci.yml` |
| 9 | Service Table Schema | 4 | `mygorm/model/t_service.gen.go` |
| 10 | VPC Endpoint Table Schema | 4 | `mygorm/model/t_vpc_endpoint.gen.go` |
| 11 | Build Image Definitions | 3 | `.gitlab-ci.yml` |
| 12 | Manual Build Images | 3 | `.gitlab-ci.yml` |
| 13 | Service SNAT Table Schema | 3 | `mygorm/model/t_service_snatips.gen.go` |
| 14 | Service Whitelist Table Schema | 3 | `mygorm/model/t_service_whitelist.gen.go` |
| 15 | Master Branch Template | 1 | `.gitlab-ci.yml` |
| 16 | Build Image Testing | 1 | `.gitlab-ci.yml` |

## 调用链

```
main.go:runServer()
  └─► server.go:NewServer()
        ├─► mygorm/database.go:New()           ← 初始化 GORM DB
        └─► api/grpc_api.go:NewGrpcAPI()       ← 注册 gRPC 服务
              └─► grpc_api.go:ListL4Gw()        ← RPC 处理
                    └─► grpc_api.go:getDataFromDB()
                          ├─► db/gen.go:Transaction()
                          ├─► t_vpc_endpoint.gen.go ← 查询 t_vpc_endpoint
                          ├─► t_service.gen.go      ← 查询 t_service
                          └─► t_service_snatips.gen.go ← 查询 t_service_snatips
```

## 各模块文档

| 文档 | 对应社区 | 说明 |
|------|---------|------|
| [modules/01-服务数据访问层.md](modules/01-服务数据访问层.md) | Community 0 | t_service DAO |
| [modules/02-VPC端点数据访问层.md](modules/02-VPC端点数据访问层.md) | Community 1 | t_vpc_endpoint DAO |
| [modules/03-服务SNAT-IP数据访问层.md](modules/03-服务SNAT-IP数据访问层.md) | Community 2 | t_service_snatips DAO |
| [modules/04-服务白名单数据访问层.md](modules/04-服务白名单数据访问层.md) | Community 3 | t_service_whitelist DAO |
| [modules/05-数据库查询操作层.md](modules/05-数据库查询操作层.md) | Community 4 | Query 聚合、事务 |
| [modules/06-应用服务器配置.md](modules/06-应用服务器配置.md) | Community 5 | Server、Config、DB init |
| [modules/07-gRPC-API层.md](modules/07-gRPC-API层.md) | Community 6 | 核心业务逻辑 |
| [modules/08-PrivateLink数据模型.md](modules/08-PrivateLink数据模型.md) | Community 7 | Data 聚合结构体 |
| [modules/09-代码质量工具.md](modules/09-代码质量工具.md) | Community 8 | Linter、CI 测试 |
| [modules/10-数据表Schema定义.md](modules/10-数据表Schema定义.md) | Communities 9,10,13,14 | 四张表的 ORM 模型 |
| [modules/11-构建与部署.md](modules/11-构建与部署.md) | Communities 11,12,15,16 | Docker、CI/CD |

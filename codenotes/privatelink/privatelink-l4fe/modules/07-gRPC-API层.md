# 模块 07：gRPC API 层 — gRPC API Layer

## 概述

该模块对应图分析 **Community 6「gRPC API Layer」**（14 个节点，内聚度 0.19——**最高**），是服务的**核心业务逻辑层**。它实现了 `ListL4Gw` RPC，执行数据查询、聚合和 L4 网关视图的构建。

## 源文件

- **`api/grpc_api.go`** — 全部 API 层代码（手工编写，262 行）

## 核心结构体

### GrpcAPI (`api/grpc_api.go:14-18`)

```go
type GrpcAPI struct {
    *zap.SugaredLogger          // 日志（别名 "grpc_api"）
    pb.GwWatchServer            // 嵌入 protobuf 定义的 Server
    query *db.Query             // 数据库查询入口
}
```

### NewGrpcAPI() (`api/grpc_api.go:20-24`)

```go
func NewGrpcAPI(l *zap.Logger, grpc *grpc.Server, query *db.Query) *GrpcAPI
```

初始化过程：
1. 创建 `SugaredLogger`（name="grpc_api"）
2. 将自身注册为 `GwWatchServer` 的 gRPC 服务实现
3. 保存 `query` 引用供后续查询使用

## 核心业务逻辑

### ListL4Gw() (`api/grpc_api.go:26-199`)

这是服务唯一的 RPC handler，处理流程分为两步：

#### 第一步：数据查询 (`getDataFromDB()`)

**函数**: `grpc_api.go:201-262`

在单个数据库事务中查询三张表：

```go
err := g.query.Transaction(func(tx *db.Query) error {
    // 1. 查询 VPC Endpoints
    vpcEndpoints, err = tx.TVpcEndpoint.WithContext(ctx).Select().Where(
        tx.TVpcEndpoint.ServiceID.In(serviceIDs...),
        tx.TVpcEndpoint.ConnectStatus.Eq(1),
        tx.TVpcEndpoint.DeleteTime.Eq(0),
    ).Find()

    // 2. 查询 Services
    services, err = tx.TService.WithContext(ctx).Select().Where(
        tx.TService.ServiceID.In(serviceIDs...),
        tx.TService.DeleteTime.Eq(0),
    ).Find()

    // 3. 查询 SNAT IPs
    serviceSnatips, err = tx.TServiceSnatip.WithContext(ctx).Select().Where(
        tx.TServiceSnatip.ServiceID.In(serviceIDs...),
        tx.TServiceSnatip.DeleteTime.Eq(0),
    ).Find()
})
```

数据通过 ServiceID 关联，组装成 `map[string]*model.Data`：

```go
data[serviceID] = &model.Data{
    Service:        service,        // 来自 t_service
    VpcEndpoints:   [...],          // 来自 t_vpc_endpoint
    ServiceSnatips: [...],          // 来自 t_service_snatips
}
```

#### 第二步：构建 L4Gw 视图 (`grpc_api.go:32-191`)

对每个 Service ID，依次构建：

1. **foreIPs**（行 41-57）：遍历 VPC Endpoint，收集 IPv4/IPv6 地址
2. **fnatips**（行 59-66）：遍历 SNAT IP，关联 Service 的 TunnelID 和 AccountID
3. **foreGroups**（行 68-109）：每个 Endpoint 一个 GwGroup
4. **fnatGroups**（行 111-133）：所有 SNAT IP 在一个组中
5. **backendGroups**（行 135-157）：Service 自身 IP 作为一个组
6. **rules**（行 159-174）：每个 Fore Endpoint 生成一条 FullNAT 规则

**FullNAT 规则示例**：

```
Fore Endpoint (client facing) ──FullNAT──► FNAT Group (SNAT) + Backend Group (DNAT)
  10.10.1.2:any                    │            │
                                   │            └─► Service IP: 172.16.0.1
                                   │
                                   └─► SNAT IP: 10.20.0.1
```

## 数据聚合结构

`Data` 结构 (`model/privatelink.go:8-12`) 是 API 层的**数据集合容器**：

```go
type Data struct {
    Service        *TService
    VpcEndpoints   []*TVpcEndpoint
    ServiceSnatips []*TServiceSnatip
}
```

## 图分析洞察

- **社区内聚度**: 0.19 — **整个系统中最高**，表明该社区内部耦合紧密
- **核心节点**: `ListL4Gw()` 和 `getDataFromDB()` 是整个系统的业务逻辑核心
- **桥接作用**: GrpcAPI 通过 `query` 字段连接到 Community 4（Database Query Operations）
- **日志**: 使用 zap 的 SugaredLogger，在关键路径输出 debug 日志（`resp.String()` 和 `data`）
- **数据一致性**: 错误的 ServiceID 关联会记录警告但不中断请求（行 248, 256）

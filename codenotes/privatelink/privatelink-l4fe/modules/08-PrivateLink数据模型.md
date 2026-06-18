# 模块 08：PrivateLink 数据模型 — Private Link Data Models

## 概述

该模块对应图分析 **Community 7「Private Link Data Models」**（6 个节点，内聚度 0.33），包含手动编写的聚合数据模型。

## 源文件

- **`mygorm/model/privatelink.go`** — 聚合结构体（手工编写，39 行）

## 核心结构体

### Data (`model/privatelink.go:8-12`)

```go
type Data struct {
    Service        *TService           // 服务信息（来自 t_service）
    VpcEndpoints   []*TVpcEndpoint     // VPC 端点列表（来自 t_vpc_endpoint）
    ServiceSnatips []*TServiceSnatip   // SNAT IP 列表（来自 t_service_snatips）
}
```

这是一个**聚合结构体**，将三张表的数据按 ServiceID 关联在一起。在 `api/grpc_api.go:getDataFromDB()` 中被组装，用于后续的 L4Gw 视图构建。

### String() (`model/privatelink.go:14-39`)

```go
func (d Data) String() string
```

提供人类可读的调试输出，打印：
- Service 的 `ServiceID` 和 `Description`
- 每个 VpcEndpoint 的 `EndpointID` 和 `ServiceID`
- 每个 ServiceSnatip 的 `ServiceID` 和 `IP`

用于 `api/grpc_api.go:259` 的 `g.Debug(data)` 日志输出。

## 图分析洞察

- **内聚度**: 0.33 — 非常高，因为结构体内部字段高度关联
- **仅 4 个模型节点**: `Data`、`TService`、`TServiceSnatip`、`TVpcEndpoint`
- **注意**: `TServiceWhitelist` 虽然生成了模型，但不在 `Data` 结构体中，且在 `getDataFromDB()` 中未被查询

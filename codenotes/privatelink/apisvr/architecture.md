# apisvr - architecture

> 自动生成文档 | 系统: [[privatelink]] | 时间: 2026-06-17 22:22
路由类型: action
> **置信度**: 见文档末尾统计 | **验证状态**: ✓

---


# 架构设计

## 整体架构
**单体应用（Monolithic）** 或 **分层架构（Layered）**【推测】【判断依据：代码事实列表显示所有路由处理函数（Handler）均位于 `api/` 目录下，且直接调用 `db/` 目录中的数据库操作函数（如 `db/db.go` 中的 `CreateVPCEndpoint`）。这表明业务逻辑（`api/`）和数据访问（`db/`）紧密耦合，部署在一个进程中，符合单体应用特征。同时，`api/` 和 `db/` 的分离也体现了简单的逻辑分层。】

## 路由机制
**Action 字段分发（action_dispatch）**（来源：路由机制事实）
- 所有请求通过 JSON 中的 `Action` 字段路由到对应的处理函数。
- 所有接口通常通过 POST 发送到根路径 `/`。
- 路由映射示例：`ActionCreateVPCEndpoint` → `CreateVPCEndpoint` @ `db/db.go:250-250`。

## 核心模块
| 模块 | 文件位置 | 职责 |
|------|----------|------|
| API 处理模块 | `api/*.go` | 接收并处理特定 Action 的请求，包含请求结构体定义、业务逻辑和验证。例如，`CreateVPCEndpoint` 处理 `ActionCreateVPCEndpoint` 请求。 |
| 数据库操作模块 | `db/db.go` | 提供与数据库交互的核心函数，如 `CreateVPCEndpoint`, `DescribeVPCEndpointServices`。部分 Action 直接路由到此模块的函数。 |
| 路由分发模块 | 【需确认】 | 【推测】包含一个中央的 `switch req.Action { ... }` 语句，负责将请求分发到对应的处理函数。具体文件位置未知。 |

## 数据流
基于路由映射和函数调用关系【推测】：
1.  **入口**：客户端发送 POST 请求到 `/`，请求体 JSON 中包含 `Action` 字段（如 `ActionCreateVPCEndpoint`）。
2.  **路由**：中央路由分发器（位置需确认）根据 `Action` 字段的值，通过 `switch` 语句将请求分发到对应的处理函数。
3.  **处理**：
    - 对于映射到 `api/` 目录下函数的 Action（如 `ActionCreateVPCEndpointServiceConfiguration`），由对应的 `api/*.go` 文件中的函数（如 `CreateVPCEndpointServiceConfiguration`）处理。这些函数通常会调用 `db/` 模块的函数（如 `createServiceInDB`）进行数据持久化。
    - 对于直接映射到 `db/db.go` 中函数的 Action（如 `ActionDescribeVPCEndpointServices`），则直接由 `db/db.go` 中的函数（如 `DescribeVPCEndpointServices`）处理。
4.  **响应**：处理函数执行完毕后，将结果返回给客户端。

## 关键接口
| 接口 | 位置 | 说明 |
|------|------|------|
| `AcceptVPCEndpointConnectionReq` | `api/AcceptVPCEndpointConnection.go:11:0-28:1` | 处理 `ActionAcceptVPCEndpointConnection` 请求的输入参数结构体。 |
| `CreateVPCEndpointReq` | `api/CreateVPCEndpoint.go:18:0-56:1` | 处理 `ActionCreateVPCEndpoint` 请求的输入参数结构体。 |
| `CreateVPCEndpointServiceConfigurationReq` | `api/CreateVPCEndpointServiceConfiguration.go:18:0-81:1` | 处理 `ActionCreateVPCEndpointServiceConfiguration` 请求的输入参数结构体。 |
| `DescribeVPCEndpointConnectionsReq` | `api/DescribeVPCEndpointConnections.go:12:0-39:1` | 处理 `ActionDescribeVPCEndpointConnections` 请求的输入参数结构体。 |

---

## 置信度统计

| 等级 | 数量 |
|------|------|
| 高置信度 (≥0.9) | 313 |
| 中置信度 (0.6-0.9) | 370 |
| 低置信度 (0.3-0.6) | 0 |
| 不确定 (<0.3) | 0 |

- **平均置信度**: 0.80
- **需人工审查**: 0 个事实

*置信度基于来源可信度、完整性、一致性和可验证性计算*

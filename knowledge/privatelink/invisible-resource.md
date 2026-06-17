---
tags: [privatelink, apisvr, architecture, resource]
created: 2026-06-17
updated: 2026-06-17
source: git@git.ucloudadmin.com:unetworks/privatelink/apisvr.git
status: reviewed
---

# 不可见资源（Invisible Resource）方案

## 背景

privatelink 支持创建"不可见"的资源——即普通用户看不到，仅内部系统/运营平台使用的服务（Service）和终端节点（VPC Endpoint）。

## 数据模型

两张核心表通过 `visible_type` 字段区分可见性：

| 表 | 字段 | GORM |
|---|---|---|
| `t_service` | `visible_type` | `gorm:"column:visible_type;not null;default:2"` |
| `t_vpc_endpoint` | `visible_type` | `gorm:"column:visible_type;not null;default:2"` |

### 枚举值

| 值 | 常量 | 含义 |
|---|---|---|
| `1` | `UresourceInvisible` | 不可见资源（内部系统使用） |
| `2` | `UresourceVisible` | 可见资源（用户默认，开放给所有用户） |

定义位置：`factory/uresource/impl.go:22-27`

## 请求链路

```
客户端请求
  │
  ├→ Header: X-Ucloud-ApiMetadata
  │
  ▼
parseAPIMetadata(c *gin.Context) → (context.Context, uint32)    ← api/api.go:246
  │
  ├→ 从 Header 提取 apiMetadata 字符串
  ├→ SDK: apigateway.ParseAPIMetadata(apiMetadata)
  ├→ SDK: apiMD.WantToCreateInvisibleResource()
  │
  ├─ true  → invisible = UresourceInvisible (1)
  └─ false → invisible = UresourceVisible  (2)
```

**关键**：`WantToCreateInvisibleResource()` 由外部 SDK 包 `apigateway` 实现，privatelink 只消费其结果。

## DB 查询时的可见性过滤

所有查询方法接受 `invisible uint32` 参数。非零时追加 `VisibleType` 条件：

```go
// db/db.go:138-139
if invisible != 0 {
    conds = append(conds, t.VisibleType.Eq(invisible))
}
```

涉及 ~15 个查询方法：

| 方法 | 对象 |
|---|---|
| `GetServices` / `GetServicesWithDeleted` | 服务 |
| `GetVPCEndpoints` / `GetVPCEndpointsWithDeleted` | 终端节点 |
| `DescribeVPCEndpoints` | 端点描述 |
| `DescribeVPCEndpointServiceConfigurations` | 服务配置 |
| `GetVPCEndpointConnection` | 连接信息 |

### 特殊场景

- `db/db.go:413` 有硬编码 `t.VisibleType.Eq(2)`，强制只查可见资源（即使调用方传了 invisible 参数也忽略）
- 创建时：`CreateVPCEndpointServiceConfiguration.go:345` 将 `invisible` 值直接写入 `VisibleType` 字段

## 安全边界

- **不暴露给普通用户** — 用户侧的 API 网关不透传 `X-Ucloud-ApiMetadata` header
- **仅内部系统使用** — 运营管理平台通过 SDK 设置 `apiMetadata` 标记
- **默认可见** — gorm default `2`，不传 apiMetadata 时默认创建可见资源

## 涉及文件

| 文件 | 角色 |
|---|---|
| `api/api.go:246` | parseAPIMetadata — 从请求提取 invisible 标识 |
| `api/CreateVPCEndpointServiceConfiguration.go:345` | 创建服务时写入 VisibleType |
| `api/CreateVPCEndpoint.go:328` | 创建端点时写入 VisibleType |
| `factory/uresource/impl.go:22-27` | 常量定义 |
| `db/db.go:129-635` | 15 个查询方法的 invisible 过滤 |
| `db/model/t_service.gen.go:30` | Service 模型 |
| `db/model/t_vpc_endpoint.gen.go:29` | VPC Endpoint 模型 |

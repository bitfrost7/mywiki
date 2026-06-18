# 模块: 资源可见性 API 处理器

> 社区 #12, #13 — 10 节点 · Set Resource Invisible + Set Resource Visible

---

## 概述

本模块包含两个核心 API 处理器：`SetResourceInvisible` 和 `SetResourceVisible`。它们负责管理 PrivateLink 资源的可见性状态——即控制 VPC 端点（Endpoint）和端点服务（EndpointService）是否对用户可见。操作分两步执行：（1）通过 UResource HTTP API 设置/删除资源标签 `general.Invisible`；（2）更新数据库中对应行的 `visible_type` 字段。

---

## 文件索引

### SetResourceInvisible — 设置不可见

**`api/SetResourceInvisible.go:1-87`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `SetResourceInvisibleRequest` | `:11` | 请求结构体：`ResourceId`（必填）+ `ResourceType`（必填，`oneof=Endpoint EndpointService`） |
| `SetResourceInvisibleResponse` | `:17` | 响应结构体：嵌入 `*RespBase` |
| `API.SetResourceInvisible()` | `:22` | **入口函数**：按 ResourceType 分支处理 |

**处理流程**（**`api/SetResourceInvisible.go:22-87`**）：

```
SetResourceInvisible()
  │
  ├─ ResourceType == "Endpoint"
  │   ├─ a.db.GetVPCEndpoints(ctx, resourceId, 0, 0)          :31
  │   │   → 查询 t_vpc_endpoint 表 (delete_time=0)
  │   │   → 校验：len==0 → ResourceNotFoundErr
  │   │   → 校验：len>1  → InternalServerErr
  │   ├─ a.fac.UResource.SetInvisibleLabel(ctx, resourceId)   :46
  │   │   → HTTP POST → UResource 系统 → 添加 general.Invisible=true
  │   └─ a.db.UpdateEndpointInvisibleType(ctx, resourceId, 1) :52
  │       → UPDATE t_vpc_endpoint SET visible_type=1
  │
  └─ ResourceType == "EndpointService"
      ├─ a.db.GetServices(ctx, resourceId, 0, 0)              :60
      │   → 查询 t_service 表 (delete_time=0)
      ├─ a.fac.UResource.SetInvisibleLabel(ctx, resourceId)   :74
      │   → HTTP POST → UResource 系统
      └─ a.db.UpdateEndpointServiceInvisibleType(ctx, resourceId, 1) :80
          → UPDATE t_service SET visible_type=1
```

### SetResourceVisible — 取消不可见

**`api/SetResourceVisible.go:1-85`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `SetResourceVisibleRequest` | `:11` | 请求结构体：与 `SetResourceInvisibleRequest` 结构相同 |
| `SetResourceVisibleResponse` | `:17` | 响应结构体：嵌入 `*RespBase` |
| `API.SetResourceVisible()` | `:22` | **入口函数**：与 Invisible 对称，但调用 `DeleteResourceLabel` 和设置 `visible_type=2` |

**处理流程**（**`api/SetResourceVisible.go:22-85`**）：

```
SetResourceVisible()
  │
  ├─ ResourceType == "Endpoint"
  │   ├─ a.db.GetVPCEndpoints(ctx, resourceId, 0, 0)          :30
  │   ├─ a.fac.UResource.DeleteResourceLabel(ctx, resourceId)  :45
  │   │   → HTTP POST → UResource 系统 → 删除 general.Invisible 标签
  │   └─ a.db.UpdateEndpointInvisibleType(ctx, resourceId, 2) :51
  │       → UPDATE t_vpc_endpoint SET visible_type=2
  │
  └─ ResourceType == "EndpointService"
      ├─ a.db.GetServices(ctx, resourceId, 0, 0)              :58
      ├─ a.fac.UResource.DeleteResourceLabel(ctx, resourceId)  :72
      └─ a.db.UpdateEndpointServiceInvisibleType(ctx, resourceId, 2) :78
          → UPDATE t_service SET visible_type=2
```

---

## 可见性状态说明

**`factory/uresource/impl.go:8-10`** 定义了可见性常量：

| 常量 | 值 | 说明 |
|------|-----|------|
| `UresourceAll` | 0 | 全部类型资源 |
| `UresourceInvisible` | 1 | **不可见**——设置了 `general.Invisible=true` 标签 |
| `UresourceVisible` | 2 | **可见**——未设置或已删除不可见标签 |

流程对应关系：

| 操作 | UResource 操作 | DB visible_type 新值 |
|------|---------------|---------------------|
| SetResourceInvisible | 添加标签 `general.Invisible=true` | `1` (Invisible) |
| SetResourceVisible | 删除标签 `general.Invisible` | `2` (Visible) |

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `a.db.GetVPCEndpoints` | Database Operations (M06) | 查询端点信息 |
| `a.db.GetServices` | Database Operations (M06) | 查询服务信息 |
| `a.db.UpdateEndpointInvisibleType` | Database Operations (M06) | 更新端点 visible_type |
| `a.db.UpdateEndpointServiceInvisibleType` | Database Operations (M06) | 更新服务 visible_type |
| `a.fac.UResource.SetInvisibleLabel` | Resource Label Operations (M08) | 添加不可见标签 |
| `a.fac.UResource.DeleteResourceLabel` | Resource Label Operations (M08) | 删除不可见标签 |
| `ResourceTypeEndpoint` | API Core Framework (M02) | 资源类型常量 `api/convert.go:5` |
| `ResourceTypeEndpointService` | API Core Framework (M02) | 资源类型常量 `api/convert.go:6` |

---

## 设计要点

- **两阶段提交风格**：先操作外部系统（UResource），再操作数据库。如果 UResource 调用成功但 DB 更新失败，会导致状态不一致——但当前代码没有实现补偿/回滚机制
- **幂等性**：`GetVPCEndpoints` 校验资源是否存在和唯一后再操作，避免因并发导致异常
- **资源类型枚举校验**：`ResourceType` 字段使用 `validate:"required,oneof=Endpoint EndpointService"` 确保只接受合法值

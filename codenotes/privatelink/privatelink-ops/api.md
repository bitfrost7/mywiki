# privatelink-ops — API 接口文档

> 自动生成 | 基于源代码分析

---

## 概述

privatelink-ops 使用 **单端点 JSON RPC 风格** 设计。所有请求均通过 `POST /` 发送，请求体中包含 `Action` 字段指定具体操作，服务端据此分发到对应的处理函数。

---

## 通用请求/响应格式

### 请求基类

**`api/base.go:8-11`** — `ReqBase`：

```json
{
    "Action": "SetResourceInvisible",
    "request_uuid": "可选-请求追踪ID"
}
```

### 响应基类

**`api/base.go:13-17`** — `RespBase`：

```json
{
    "Action": "SetResourceInvisibleResponse",
    "RetCode": 0,
    "Message": "Success"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `Action` | string | 响应动作名 = 请求 Action + "Response" |
| `RetCode` | int | 返回码，0 表示成功 |
| `Message` | string | 返回消息 |

---

## 错误码

**`api/error.go:8-41`** 定义了全局错误码：

| 错误变量 | RetCode | Message |
|----------|---------|---------|
| `nil` | 0 | Success |
| `MissingActionErr` | 160 | Key parameter Action is missing |
| `ActionNotFoundErr` | 161 | Action not found |
| `RequestParamsErr` | 230 | The parameter is invalid... |
| `InternalServerErr` | 500 | Internal Server Error |
| `ResourceNotFoundErr` | 217803 | The resource does not exist or has been deleted |

---

## API 动作列表

### 1. SetResourceInvisible — 设置资源不可见

为指定资源（Endpoint 或 EndpointService）添加 `general.Invisible=true` 标签，并更新数据库中的 `visible_type` 为 1（不可见）。

**请求体**：

**`api/SetResourceInvisible.go:11-15`** — `SetResourceInvisibleRequest`

```json
{
    "Action": "SetResourceInvisible",
    "ResourceId": "ucs-xxxx",
    "ResourceType": "Endpoint"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ResourceId` | string | ✅ | 资源 ID |
| `ResourceType` | string | ✅ | 资源类型，枚举值：`Endpoint` / `EndpointService` |

**处理流程**（**`api/SetResourceInvisible.go:22-87`**）：

1. 解析输入 → 校验参数
2. 根据 `ResourceType` 分支处理：
   - `Endpoint`：查询 `t_vpc_endpoint` 表确认资源存在 → 调用 UResource 添加不可见标签 → 更新 `t_vpc_endpoint.visible_type=1`
   - `EndpointService`：查询 `t_service` 表确认资源存在 → 调用 UResource 添加不可见标签 → 更新 `t_service.visible_type=1`
3. 返回成功响应

---

### 2. SetResourceVisible — 取消资源不可见

移除指定资源的 `general.Invisible` 标签，并将数据库中的 `visible_type` 更新为 2（可见）。

**请求体**：

**`api/SetResourceVisible.go:11-15`** — `SetResourceVisibleRequest`

```json
{
    "Action": "SetResourceVisible",
    "ResourceId": "ucs-xxxx",
    "ResourceType": "Endpoint"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `ResourceId` | string | ✅ | 资源 ID |
| `ResourceType` | string | ✅ | 资源类型，枚举值：`Endpoint` / `EndpointService` |

**处理流程**（**`api/SetResourceVisible.go:22-85`**）：

1. 解析输入 → 校验参数
2. 查询数据库确认资源存在且唯一
3. 调用 UResource 删除 `general.Invisible` 标签
4. 更新数据库 `visible_type=2`
5. 返回成功响应

---

### 3. AddUserConfig — 新增用户配置

为指定用户添加配置项。

**请求体**：

**`api/AddUserConfig.go:14-22`** — `AddUserConfigRequest`

```json
{
    "Action": "AddUserConfig",
    "TopOrganizationId": 10001,
    "OrganizationId": 20001,
    "ResourceId": "ucs-xxxx",
    "ConfigKey": "disable_limit_bandwidth",
    "ConfigValue": "true",
    "OperatorName": "admin"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `TopOrganizationId` | uint32 | ❌ | 顶级组织 ID（CompanyID） |
| `OrganizationId` | uint32 | ❌ | 组织 ID（AccountID） |
| `ResourceId` | string | ❌ | 资源 ID |
| `ConfigKey` | string | ✅ | 配置键 |
| `ConfigValue` | string | ✅ | 配置值 |
| `OperatorName` | string | ✅ | 操作人 |

**处理流程**（**`api/AddUserConfig.go:29-55`**）：

1. 解析输入 → 校验必填字段
2. 构造 `TUserConfig` 模型（含 `InsertTime` 时间戳）
3. 调用 `db.AddUserConfig()` 写入数据库
4. 返回成功响应

---

### 4. DeleteUserConfig — 删除用户配置

删除指定用户的指定配置项。

**请求体**：

**`api/DeleteUserConfig.go:10-17`** — `DeleteUserConfigRequest`

```json
{
    "Action": "DeleteUserConfig",
    "TopOrganizationId": 10001,
    "OrganizationId": 20001,
    "ResourceId": "ucs-xxxx",
    "ConfigKey": "disable_limit_bandwidth",
    "OperatorName": "admin"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `TopOrganizationId` | uint32 | ❌ | 顶级组织 ID |
| `OrganizationId` | uint32 | ❌ | 组织 ID |
| `ResourceId` | string | ❌ | 资源 ID |
| `ConfigKey` | string | ✅ | 配置键 |
| `OperatorName` | string | ✅ | 操作人 |

**处理流程**（**`api/DeleteUserConfig.go:24-37`**）：

1. 解析输入 → 校验必填字段
2. 调用 `db.DeleteUserConfig()` 按复合条件删除（CompanyID + AccountID + ResourceID + ConfigKey）
3. 返回成功响应

---

### 5. UpdateUserConfig — 更新用户配置

更新指定用户的配置值。

**请求体**：

**`api/UpdateUserConfig.go:10-18`** — `UpdateUserConfigRequest`

```json
{
    "Action": "UpdateUserConfig",
    "TopOrganizationId": 10001,
    "OrganizationId": 20001,
    "ResourceId": "ucs-xxxx",
    "ConfigKey": "disable_limit_bandwidth",
    "ConfigValue": "false",
    "OperatorName": "admin"
}
```

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `TopOrganizationId` | uint32 | ❌ | 顶级组织 ID |
| `OrganizationId` | uint32 | ❌ | 组织 ID |
| `ResourceId` | string | ❌ | 资源 ID |
| `ConfigKey` | string | ✅ | 配置键 |
| `ConfigValue` | string | ✅ | 新配置值 |
| `OperatorName` | string | ✅ | 操作人 |

**处理流程**（**`api/UpdateUserConfig.go:25-38`**）：

1. 解析输入 → 校验必填字段
2. 调用 `db.UpdateUserConfig()` 按复合条件更新 `ConfigVal` 和 `OperatorName`
3. 返回成功响应

---

## 请求分发机制

**`api/api.go:85-130`** — `handle()` 函数：

```
POST /  →  [Gin Router]
            │
            1. 读取原始 Body
            2. 解析出 ReqBase（获取 Action）
            3. 设置请求上下文（RequestUUID 或新建 Context）
            4. Action 匹配分发
               ├─ SetResourceInvisible  → SetResourceInvisible()
               ├─ SetResourceVisible    → SetResourceVisible()
               ├─ AddUserConfig         → AddUserConfig()
               ├─ DeleteUserConfig      → DeleteUserConfig()
               ├─ UpdateUserConfig      → UpdateUserConfig()
               └─ default               → ActionNotFoundErr
            5. 返回 JSON 响应
```

---

## 验证机制

**`api/api.go:59-68`** — `InitValidate()`：使用 `go-playground/validator.v9` 初始化验证器。

**`api/api.go:162-185`** — `parseInput()`：每个 API handler 调用此函数：
1. JSON 解析绑定到结构体
2. `a.validate.Struct(in)` 校验结构体 tag
3. 校验失败时返回翻译后的英文错误消息

资源类型枚举校验：**`api/SetResourceInvisible.go:14`** 中使用 `validate:"required,oneof=Endpoint EndpointService"`。

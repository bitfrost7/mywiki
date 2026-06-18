# 模块: 用户配置 CRUD API 处理器

> 社区 #11, #14 — 10 节点 · Delete User Config + Update User Config + AddUserConfig

---

## 概述

本模块包含三个用户配置的 CRUD API 处理器：`AddUserConfig`、`DeleteUserConfig`、`UpdateUserConfig`。它们操作 `t_user_config` 数据表，为指定用户（公司级 + 账户级）和资源存储配置键值对。配置的读取由下游服务负责（如 bwregister 从 DB 读取全量配置到内存缓存）。

---

## 文件索引

### AddUserConfig — 新增配置

**`api/AddUserConfig.go:1-55`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `AddUserConfigRequest` | `:14` | 请求结构体：`TopOrganizationId`, `OrganizationId`, `ResourceId`, `ConfigKey`（必填）, `ConfigValue`（必填）, `OperatorName`（必填） |
| `AddUserConfigResponse` | `:24` | 响应结构体：嵌入 `*RespBase` |
| `API.AddUserConfig()` | `:29` | **入口函数**：解析输入 → 调用 `addUserConfigInDB` → 返回响应 |
| `addUserConfigInDB()` | `:44` | 构造 `TUserConfig` 模型（含 `InsertTime` 时间戳）→ 调用 `db.AddUserConfig()` |

**调用链**（**`api/AddUserConfig.go:29-55`**）：

```go
AddUserConfig() → parseInput() → addUserConfigInDB()
  ├─ 构造 model.TUserConfig {
  │     CompanyID:    req.TopOrganizationId,
  │     AccountID:    req.OrganizationId,
  │     ResourceID:   req.ResourceId,
  │     ConfigKey:    req.ConfigKey,
  │     ConfigVal:    req.ConfigValue,
  │     OperatorName: req.OperatorName,
  │     InsertTime:   uint32(time.Now().Unix()),
  │   }
  └─ a.db.AddUserConfig(ctx, userConfig) → INSERT INTO t_user_config
```

### DeleteUserConfig — 删除配置

**`api/DeleteUserConfig.go:1-37`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `DeleteUserConfigRequest` | `:10` | 请求结构体：`TopOrganizationId`, `OrganizationId`, `ResourceId`, `ConfigKey`（必填）, `OperatorName`（必填） |
| `DeleteUserConfigResponse` | `:19` | 响应结构体：嵌入 `*RespBase` |
| `API.DeleteUserConfig()` | `:24` | **入口函数**：解析输入 → 按复合条件删除 → 返回响应 |

**删除逻辑**（**`api/DeleteUserConfig.go:24-37`**）：

```go
DeleteUserConfig() → parseInput()
  └─ a.db.DeleteUserConfig(ctx,
       req.TopOrganizationId,    // CompanyID
       req.OrganizationId,       // AccountID
       req.ResourceId,           // ResourceID
       req.ConfigKey,             // ConfigKey
     )
     → DELETE FROM t_user_config
       WHERE company_id=? AND account_id=?
       AND resource_id=? AND config_key=?
```

**注意**：`DeleteUserConfig` 执行的是**物理删除（DELETE）**，而非软删除。这意味着数据不可恢复。

### UpdateUserConfig — 更新配置

**`api/UpdateUserConfig.go:1-38`**

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `UpdateUserConfigRequest` | `:10` | 请求结构体：`TopOrganizationId`, `OrganizationId`, `ResourceId`, `ConfigKey`（必填）, `ConfigValue`（必填）, `OperatorName`（必填） |
| `UpdateUserConfigResponse` | `:20` | 响应结构体：嵌入 `*RespBase` |
| `API.UpdateUserConfig()` | `:25` | **入口函数**：解析输入 → 复合条件更新 → 返回响应 |

**更新逻辑**（**`api/UpdateUserConfig.go:25-38`**）：

```go
UpdateUserConfig() → parseInput()
  └─ a.db.UpdateUserConfig(ctx,
       req.TopOrganizationId,    // CompanyID
       req.OrganizationId,       // AccountID
       req.ResourceId,           // ResourceID
       req.ConfigKey,            // ConfigKey
       req.ConfigValue,          // 新值
       req.OperatorName,         // 操作人
     )
     → UPDATE t_user_config
       SET config_val=?, operator_name=?
       WHERE company_id=? AND account_id=?
       AND resource_id=? AND config_key=?
```

---

## 数据库操作

本模块的 DB 操作定义在 **`db/db.go`**：

| 方法 | 行号 | 操作类型 |
|------|------|----------|
| `AddUserConfig()` | `:161` | INSERT — 写入新配置行 |
| `DeleteUserConfig()` | `:176` | DELETE — 按复合主键删除 |
| `UpdateUserConfig()` | `:189` | UPDATE — 按复合主键更新 `config_val` 和 `operator_name` |

所有方法都在事务上下文中注入 `session_id`（通过 `ncontext.NewSessionIDToContext`），用于日志追踪。

---

## 配置键说明

虽然本模块不限制 `ConfigKey` 的具体值，但在实际使用中，常见的配置键包括：

| 配置键 | 说明 |
|--------|------|
| `disable_limit_bandwidth` | 禁用带宽限速（在 bwregister 服务中使用） |

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `a.db.AddUserConfig` | Database Operations (M06) | 数据库写入操作 |
| `a.db.DeleteUserConfig` | Database Operations (M06) | 数据库删除操作 |
| `a.db.UpdateUserConfig` | Database Operations (M06) | 数据库更新操作 |
| `parseInput()` | API Core Framework (M02) | 参数解析与校验 |
| `ReqBase` | API Core Framework (M02) | 请求基类继承 |

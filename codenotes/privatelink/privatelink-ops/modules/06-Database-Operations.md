# 模块: 数据库业务操作

> 社区 #6 — 35 节点 · API Request Handlers

---

## 概述

本模块是数据库操作的核心实现，定义 `Database` 结构体、数据库连接初始化和所有业务查询方法。作为 API 层和 GORM Gen 查询层之间的桥梁，它将 5 个数据表的查询对象封装为高层业务方法（如 `GetVPCEndpoints`、`UpdateEndpointInvisibleType`、`AddUserConfig` 等）。同时本模块负责日志提取（RequestUUID + SessionID）和 GORM 日志级别配置。

---

## 文件索引

**`db/db.go:1-208`** — 数据库操作核心

### 配置与初始化

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `DefaultConnMaxLifetime` | `:22` | 默认连接最大生命周期：1 小时 |
| `DefaultMaxIdleConns` | `:23` | 默认最大空闲连接数：100 |
| `Config` | `:26` | 数据库配置：`DSN`、`ConnMaxLifetime`（小时）、`MaxIdleConns` |
| `Database` | `:32` | 数据库结构体：封装 `*query.Query` |
| `NewDatabase()` | `:43` | **构造函数**：初始化 GORM + 配置日志 + 连接池 |

**初始化流程**（**`db/db.go:43-77`**）：

```
NewDatabase(zapLogger, cfg)
  │
  ├─ logger = zapgorm2.New(zapLogger)       :44
  │     → 将 zap 日志适配为 GORM logger
  ├─ logger.Context = extract                :45
  │     → 注入 RequestUUID + SessionID 到 DB 日志
  ├─ 根据日志级别设置 GORM 日志模式          :48-57
  │     Debug/Info → Info 级别
  │     Warn       → Warn 级别
  │     Error      → Error 级别
  ├─ gorm.Open(mysql.Open(cfg.DSN), ...)     :59
  │     → 打开 MySQL 连接
  ├─ sqlDB.SetConnMaxLifetime(...)            :71
  ├─ sqlDB.SetMaxIdleConns(...)               :72
  └─ return &Database{db: query.Use(gormdb)} :74
      → query.Use() 初始化所有表查询对象
```

### 日志提取函数

**`db/db.go:36-41`** — `extract()`

从 Context 中提取 `RequestUUID` 和 `SessionID`，注入到 GORM 日志的 zap 字段中。这样每条 SQL 日志都能追踪到对应的请求链路。

### 业务查询方法

#### VPC 端点查询

**`db/db.go:79-108`** — `GetVPCEndpoints()`

| 参数 | 说明 |
|------|------|
| `endpointID` | 端点 ID（必选） |
| `accountID` | 账户 ID 过滤（0 表示不限制） |
| `invisible` | 可见性状态过滤（0 表示不限制） |

```go
conds := []gen.Condition{
    t.EndpointID.Eq(endpointID),           // :83
    t.DeleteTime.Eq(0),                     // :84 仅查询未删除
}
if accountID != 0 { conds = append(conds, t.AccountID.Eq(accountID)) }       // :86-87
if invisible != 0 { conds = append(conds, t.VisibleType.Eq(invisible)) }     // :88-89

// 返回精选列
t.WithContext(ctx).Select(
    t.EndpointID, t.ServiceID, t.CompanyID, t.AccountID,
    t.VnetID, t.SubnetworkID, t.TunnelID,
    t.Ipv4, t.Ipv6, t.Mac,
    t.ConnectBw, t.ConnectStatus, t.VisibleType, t.InsertTime,
).Where(conds...).Find()
```

#### 服务查询

**`db/db.go:110-141`** — `GetServices()`

与 `GetVPCEndpoints` 类似，按 `ServiceID` 查询 `t_service` 表，支持 `accountID` 和 `invisible` 过滤。

返回列：`ServiceID`, `CompanyID`, `AccountID`, `Description`, `AutoAccept`, `Payer`, `ConnectBw`, `VnetID`, `SubnetworkID`, `TunnelID`, `IP`, `ResourceType`, `ResourceID`, `VisibleType`, `InsertTime`

#### 可见性更新

**`db/db.go:143-150`** — `UpdateEndpointServiceInvisibleType()`

```go
t.WithContext(ctx).
    Where(t.ServiceID.Eq(serviceID)).
    Update(t.VisibleType, invisible)   // invisible = 1 (Invisible) 或 2 (Visible)
```

**`db/db.go:152-159`** — `UpdateEndpointInvisibleType()`

```go
t.WithContext(ctx).
    Where(t.EndpointID.Eq(endpointID)).
    Update(t.VisibleType, invisible)
```

#### 用户配置 CRUD

**`db/db.go:161-174`** — `AddUserConfig()`

```go
t.WithContext(ctx).Select(
    t.CompanyID, t.AccountID, t.ResourceID,
    t.ConfigKey, t.ConfigVal, t.OperatorName, t.InsertTime,
).Create(userConfig)
```

**`db/db.go:176-187`** — `DeleteUserConfig()`

按四元组复合条件删除：
```go
conds := []gen.Condition{
    t.CompanyID.Eq(companyId),
    t.AccountID.Eq(accountId),
    t.ResourceID.Eq(resourceId),
    t.ConfigKey.Eq(cfgKey),
}
t.WithContext(ctx).Where(conds...).Delete()
```

**`db/db.go:189-208`** — `UpdateUserConfig()`

按四元组复合条件更新 `config_val` 和 `operator_name`：
```go
t.WithContext(ctx).
    Select(t.ConfigVal, t.OperatorName).
    Where(conds...).UpdateColumnSimple(
        t.ConfigVal.Value(cfgVal),
        t.OperatorName.Value(operatorName),
    )
```

---

## 方法摘要

| 方法 | 行号 | 操作 | 表 |
|------|------|------|-----|
| `GetVPCEndpoints()` | `:79` | SELECT | t_vpc_endpoint |
| `GetServices()` | `:110` | SELECT | t_service |
| `UpdateEndpointServiceInvisibleType()` | `:143` | UPDATE | t_service |
| `UpdateEndpointInvisibleType()` | `:152` | UPDATE | t_vpc_endpoint |
| `AddUserConfig()` | `:161` | INSERT | t_user_config |
| `DeleteUserConfig()` | `:176` | DELETE | t_user_config |
| `UpdateUserConfig()` | `:189` | UPDATE | t_user_config |

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `Database` | API Core Framework (M02) | `API.db` 字段调用所有业务方法 |
| `query.Use()` | Database Query Layer (M05) | 初始化 GORM Gen 查询对象 |
| `ncontext.NewSessionIDToContext()` | Context Utilities (M10) | 注入 SessionID 用于日志追踪 |
| `model.*` | Database Models (M07) | 使用自动生成的表模型 |

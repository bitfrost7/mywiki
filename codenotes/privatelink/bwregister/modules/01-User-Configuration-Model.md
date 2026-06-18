# 模块: User Configuration Model

> 社区 #0 — 20 节点 · 凝聚力 0.06

---

## 概述

用户配置模型封装了 `t_user_config` 数据表的 ORM 模型与查询层。该表存储针对特定用户（公司+账户级别）的配置键值对，用于控制带宽限速等功能。配置以内存缓存方式加载，按 `(companyID, accountID)` 组合键匹配。

---

## 文件索引

### 数据表模型

**`db/model/t_user_config.gen.go`** — gorm gen 自动生成（L11-28）

| 结构体 | 行号 | 说明 |
|--------|------|------|
| `TableNameTUserConfig` | `:11` | 常量，表名 `t_user_config` |
| `TUserConfig` | `:14` | 用户配置数据模型 |

**TUserConfig 字段**：

| 字段 | 类型 | 说明 |
|------|------|------|
| `ID` | uint32 | 主键自增 |
| `CompanyID` | uint32 | 公司 ID |
| `AccountID` | uint32 | 账户 ID |
| `ConfigKey` | string | 配置键（如 `disable_limit_bandwidth`） |
| `ConfigVal` | string | 配置值 |
| `OperatorName` | string | 操作人 |
| `InsertTime` | uint32 | 创建时间 |
| `UpdateTime` | time.Time | 更新时间 |

### 查询层

**`db/query/t_user_config.gen.go`** — gorm gen 自动生成的查询对象

| 类型 | 说明 |
|------|------|
| `tUserConfig` | 查询结构体（包内私有） |
| `ITUserConfigDo` | 查询接口（公开） |
| `newTUserConfig()` | 构造函数 |

### 业务使用

**`task/user_config.go`** — 用户配置的业务逻辑（L1-60）

| 函数/变量 | 行号 | 说明 |
|-----------|------|------|
| `UserConfig` | `:14` | 全局内存缓存 `map[string]map[string]string` |
| `SyncUserConfig()` | `:16` | 从 DB 同步所有用户配置到内存缓存 |
| `getKey()` | `:35` | 生成复合键 `"{companyID}-{accountID}"` |
| `CheckUserConfig()` | `:39` | 按优先级精确→公司级→全局级查询用户配置 |
| `CheckDisableLimitBandwidth()` | `:57` | 检查指定用户是否禁用了带宽限速 |

### 数据库查询

**`db/db.go:152`** — `Database.GetUserConfig()` 从 `t_user_config` 表查询所有配置：

```go
func (d *Database) GetUserConfig(ctx context.Context) ([]*model.TUserConfig, error) {
    t := d.db.TUserConfig
    results, err := t.WithContext(ctx).Select(
        t.CompanyID, t.AccountID, t.ConfigKey,
        t.ConfigVal, t.OperatorName, t.InsertTime, t.UpdateTime,
    ).Find()
    // ...
}
```

---

## 关键常量

**`task/user_config.go:11`**：
- `DisableLimitBandwidth = "disable_limit_bandwidth"` — 用于检查是否禁用带宽限速的配置键

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `ITUserConfigDo` | Database Transaction Context (C3) | 通过 `queryCtx.TUserConfig` 桥接 |
| `Use()` | Database Connection Manager (C8) | 通过 `query.Use(gormDB)` 桥接 |
| `SyncUserConfig()` | Bandwidth Traffic Manager (C7) | 任务层从 DB 读取配置 |
| `CheckDisableLimitBandwidth()` | Bandwidth Traffic Manager (C7) | 在限速计算中调用检查 |

---

## 配置匹配优先级

`CheckUserConfig()` 在 `task/user_config.go:44-53` 实现了三级匹配策略：

1. **精确匹配**：`companyID-accountID`（完全匹配公司和账户）
2. **公司级匹配**：`companyID-0`（匹配整个公司）
3. **全局匹配**：`0-0`（全局默认值）

这个设计使得配置可以灵活地按粒度覆盖。

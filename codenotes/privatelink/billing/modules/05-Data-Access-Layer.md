# billing — module_05_Data_Access_Layer

> 自动生成文档 | 社区 6 | 系统: billing | 时间: 2026-06-18

---

# Data Access Layer — 数据访问层（GORM Gen 入口）

## 1. 模块职责

本模块是 **GORM Gen 自动生成**的查询入口，负责：
- **查询结构聚合**：将 5 张表的查询结构聚合到 `Query` 对象
- **读写分离**：`ReadDB()` / `WriteDB()` 方法支持数据库读写分离
- **事务管理**：`Transaction()` / `Begin()` / `Commit()` / `Rollback()` 完整事务支持
- **上下文注入**：`WithContext()` 为所有查询注入 `context.Context`

## 2. 主要类型/函数清单

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `Use` | `db/query/gen.go:18-27` | 初始化入口，传入 `*gorm.DB` 返回 `*Query` |
| `Query` | `db/query/gen.go:29-37` | 查询根对象，持有 5 张表的查询结构体 |
| `Available` | `db/query/gen.go:39` | 检查 DB 是否可用 |
| `clone` | `db/query/gen.go:41-50` | 克隆 Query 对象（事务时使用） |
| `ReadDB` | `db/query/gen.go:52-54` | 切换到读库（读写分离） |
| `WriteDB` | `db/query/gen.go:56-58` | 切换到写库 |
| `ReplaceDB` | `db/query/gen.go:60-69` | 替换底层 `*gorm.DB` 实例 |
| `queryCtx` | `db/query/gen.go:71-77` | 带 Context 的查询对象，每个表对应一个 `IT*Do` 接口 |
| `WithContext` | `db/query/gen.go:79-87` | 注入 Context 返回 `*queryCtx` |
| `Transaction` | `db/query/gen.go:89-91` | 执行事务（闭包模式） |
| `Begin` | `db/query/gen.go:93-96` | 开启事务（手动模式） |
| `QueryTx` | `db/query/gen.go:98-101` | 事务查询对象 |
| `Commit` | `db/query/gen.go:103-105` | 提交事务 |
| `Rollback` | `db/query/gen.go:107-109` | 回滚事务 |
| `SavePoint` | `db/query/gen.go:111-113` | 设置保存点 |
| `RollbackTo` | `db/query/gen.go:115-117` | 回滚到保存点 |

## 3. 表查询结构映射

`Query` 对象包含 5 张表的查询结构体（`db/query/gen.go:32-36`）：

| 字段 | 类型 | 对应表 |
|------|------|--------|
| `TBillingInfo` | `tBillingInfo` | `t_billing_info` |
| `TConnectInfo` | `tConnectInfo` | `t_connect_info` |
| `TService` | `tService` | `t_service` |
| `TTrafficInfo` | `tTrafficInfo` | `t_traffic_info` |
| `TVpcEndpoint` | `tVpcEndpoint` | `t_vpc_endpoint` |

`queryCtx` 对象提供带 Context 的查询接口（`db/query/gen.go:71-77`）：

| 字段 | 类型 | 说明 |
|------|------|------|
| `TBillingInfo` | `ITBillingInfoDo` | 计费信息表查询接口 |
| `TConnectInfo` | `ITConnectInfoDo` | 连接信息表查询接口 |
| `TService` | `ITServiceDo` | 服务表查询接口 |
| `TTrafficInfo` | `ITTrafficInfoDo` | 流量信息表查询接口 |
| `TVpcEndpoint` | `ITVpcEndpointDo` | VPC 端点表查询接口 |

## 4. 关键实现逻辑

### 4.1 读写分离

- `ReadDB()` 使用 `dbresolver.Read` 将查询路由到读库
- `WriteDB()` 使用 `dbresolver.Write` 将查询路由到写库
- 底层通过 GORM 的 `dbresolver` 插件实现，需要在 DB 初始化时注册

### 4.2 事务机制

两种事务模式：

1. **闭包模式**（推荐）：`db.Transaction(func(tx *query.Query) error { ... })` — 自动 Commit/Rollback
2. **手动模式**：`tx := db.Begin()` → `tx.Commit()` / `tx.Rollback()` — 支持 SavePoint

## 5. 涉及的源文件

- `db/query/gen.go`（全部，117 行）— 自动生成，不可编辑

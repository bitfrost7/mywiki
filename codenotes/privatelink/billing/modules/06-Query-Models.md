# billing — module_06_Query_Models

> 自动生成文档 | 社区 0, 1, 2, 3, 4 | 系统: billing | 时间: 2026-06-18

---

# Query Models — GORM 查询模型（自动生成）

## 1. 模块职责

本模块包含 **GORM Gen 自动生成**的每表查询结构（Data Object），每张表对应一个独立的文件。GORM Gen 生成的每个 `t*Do` 对象提供了类型安全的字段选择器、条件构建器和链式查询方法，业务代码通过 `db/db.go` 中的 `Database` 结构体间接使用这些查询接口。

## 2. 文件清单

| 文件 | 社区 | 对应表 | 主要结构体 |
|------|------|--------|-----------|
| `db/query/t_billing_info.gen.go` | C0 | `t_billing_info` | `tBillingInfo`, `tBillingInfoDo`, `ITBillingInfoDo` |
| `db/query/t_connect_info.gen.go` | C4 | `t_connect_info` | `tConnectInfo`, `tConnectInfoDo`, `ITConnectInfoDo` |
| `db/query/t_service.gen.go` | C1 | `t_service` | `tService`, `tServiceDo`, `ITServiceDo` |
| `db/query/t_traffic_info.gen.go` | C2 | `t_traffic_info` | `tTrafficInfo`, `tTrafficInfoDo`, `ITTrafficInfoDo` |
| `db/query/t_vpc_endpoint.gen.go` | C3 | `t_vpc_endpoint` | `tVpcEndpoint`, `tVpcEndpointDo`, `ITVpcEndpointDo` |

## 3. 自动生成的结构体模式

每个 `*_info.gen.go` 文件包含以下标准结构：

| 类型 | 说明 |
|------|------|
| `tXxx` | 表查询主结构体，嵌入 `*gorm.DB`，包含 `Table()`、`As()`、`GetFieldByName()` 等方法 |
| `tXxxDo` | DO 查询执行对象，包含 `Debug()`、`WithContext()`、`Where()`、`Find()`、`Create()` 等链式方法 |
| `ITXxxDo` | DO 查询接口，定义 `tXxxDo` 的所有公开方法 |
| 各字段方法 | 类型安全的字段选择器，如 `t.ItemID`、`t.StartTime` 等 |

## 4. 使用示例

```go
// 在 db/db.go 中通过 Database 间接使用:
t := d.db.TBillingInfo  // 获取 tBillingInfo 实例
result, err := t.WithContext(ctx).
    Where(t.State.Eq("init")).
    Find()
```

## 5. 涉及的源文件

- `db/query/t_billing_info.gen.go` — 自动生成，不可编辑
- `db/query/t_connect_info.gen.go` — 自动生成，不可编辑
- `db/query/t_service.gen.go` — 自动生成，不可编辑
- `db/query/t_traffic_info.gen.go` — 自动生成，不可编辑
- `db/query/t_vpc_endpoint.gen.go` — 自动生成，不可编辑

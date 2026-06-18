# billing — 外部 API 接口

> 自动生成文档 | 系统: billing | 时间: 2026-06-18
> 接口类型: JSON HTTP POST · Action 字段路由
> **置信度**: 高 | **验证状态**: ✓

---

# UBill 计费系统 API

billing 不对外提供 HTTP API，而是作为**客户端**调用 UBill 计费系统的 REST API 进行扣费与订单查询。

## 调用方式

所有请求通过 `factory/ubill/impl.go` 中初始化的 HTTP Client 发送到 `InternalAPIURL` 配置地址。

- 请求方法: POST
- Content-Type: application/json
- 公共参数: `Backend` (固定为 `"UBill"`) + `Action` (API 名称) + `request_uuid`

## API 列表

### PostPaid — 后付费扣费

| 属性 | 值 |
|------|-----|
| Action | `PostPaid` |
| Backend | `UBill` |
| 位置 | `factory/ubill/basic.go:97-108` |
| 请求结构 | `PostPaidRequest` @ `factory/ubill/basic.go:14-27` |
| 响应结构 | `PostPaidResponse` @ `factory/ubill/basic.go:34-37` |

**业务描述**：执行后付费扣费操作。根据 Item ID 前缀区分 Endpoint 与 Endpoint Service 的产品类型和计费小类，生成扣费订单。

**请求参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| TopOrganizationId | uint32 | 账户ID（顶层组织ID） |
| OrganizationId | uint32 | 项目ID |
| ProductType | uint32 | 产品类型：390(endpoint) / 389(endpoint service) |
| RegionId | uint32 | 可用区ID |
| ChargeType | uint32 | 计费方式：102(后付费) |
| Quantity | float64 | 计费周期: 固定1 |
| ActivityId | uint32 | 活动ID（可选） |
| OutItemId | string | 资源长ID |
| OrderDetail | array | 购买详情 [{ProductId, Multiple}] |
| StartTime | uint32 | 开始时间（unix时间戳） |
| EndTime | uint32 | 结束时间（unix时间戳） |

**响应参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| RetCode | int | 返回码（0=成功） |
| Message | string | 错误信息 |
| OrderNo | string | 订单号 |

---

### GetPostPaidItemBillInfo — 查询订单详情

| 属性 | 值 |
|------|-----|
| Action | `GetPostPaidItemBillInfo` |
| Backend | `UBill` |
| 位置 | `factory/ubill/basic.go:110-118` |
| 请求结构 | `GetPostPaidItemBillInfoRequest` @ `factory/ubill/basic.go:39-45` |
| 响应结构 | `GetPostPaidItemBillInfoResponse` @ `factory/ubill/basic.go:47-59` |

**业务描述**：查询指定资源在时间范围内的所有订单（已支付/未支付/未出账），用于重试计费时判断订单是否已存在。

**请求参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| TopOrganizationId | uint32 | 账户ID |
| OutItemId | string | 资源ID |
| StartTime | uint32 | 订单起始时间 |
| EndTime | uint32 | 订单截止时间 |

**响应参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| RetCode | int | 返回码 |
| Message | string | 错误信息 |
| PaidDetail | array | 已支付订单列表 [{OrderNo, StartTime, EndTime, OrderState}] |
| UnpaidDetail | array | 未支付订单列表 [{OrderNo, StartTime, EndTime, OrderState}] |
| UnbilledDetail | array | 未出账订单列表 [{OrderNo, StartTime, EndTime, OrderState}] |

---

### GetUnpaidOrderDetailInfo — 查询未支付订单详情

| 属性 | 值 |
|------|-----|
| Action | `GetUnpaidOrderDetailInfo` |
| Backend | `UBill` |
| 位置 | `factory/ubill/basic.go:120-128` |
| 请求结构 | `GetUnpaidOrderDetailInfoRequest` @ `factory/ubill/basic.go:61-65` |
| 响应结构 | `GetUnpaidOrderDetailInfoResponse` @ `factory/ubill/basic.go:67-75` |

**业务描述**：根据订单号列表查询未支付订单的详细信息，用于二次确认订单支付状态。

**请求参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| TopOrganizationId | uint32 | 账户ID |
| OrderNos | []string | 订单号列表 |

**响应参数**：

| 字段 | 类型 | 说明 |
|------|------|------|
| RetCode | int | 返回码 |
| Message | string | 错误信息 |
| OrderInfos | array | 订单详情 [{OrderNo, OrderDetail: [{ProductId, Multiple}]}] |

---

## 产品常量定义

定义在 `factory/ubill/impl.go:7-22`：

| 常量 | 值 | 说明 |
|------|-----|------|
| ServiceBackend | `"UBill"` | 网关注册ID |
| EndpointProductType | 390 | Endpoint 产品类型 |
| EndpointInstanceProductID | 3900001 | Endpoint 实例费计费小类 |
| EndpointTrafficProductID | 3900002 | Endpoint 流量费计费小类 |
| EndpointServiceProductType | 389 | Endpoint Service 产品类型 |
| EndpointServiceInstanceProductID | 3890001 | Service 实例费计费小类 |
| EndpointServiceTrafficProductID | 3890002 | Service 流量费计费小类 |
| ChargeType | 102 | 后付费方式编码 |
| Quantity | 1 | 计费周期固定值 |

---

## 公共数据结构

定义在 `factory/common/common.go:3-36`：

| 结构体 | 字段 | 说明 |
|--------|------|------|
| `BaseRequest` | Backend, Action, RequestUUID | 所有请求的公共基类 |
| `BaseResponse` | Action, RetCode, Message | 所有响应的公共基类 |
| `IBaseRequest` | GetAction(), GetBackend() | 请求接口 |
| `IBaseResponse` | GetRetCode() | 响应接口 |

# billing — module_04_Factory_Layer

> 自动生成文档 | 社区 7, 10, 11, 12 | 系统: billing | 时间: 2026-06-18

---

# Factory Layer — 外部计费接口封装模块

## 1. 模块职责

本模块是 billing 服务**调用 UBill 计费系统的 HTTP 客户端封装**，负责：
- **UBill HTTP 客户端初始化**：配置 API 地址和连接池
- **请求/响应数据结构定义**：后付费扣费、订单查询等 API 的 DTO
- **API 调用封装**：流量后付费、实例后付费、订单详情查询
- **监控埋点**：记录对外 API 调用的延迟、成功率、QPS
- **商品常量管理**：Endpoint/Service 的产品类型和计费小类 ID

## 2. 子模块划分

| 文件 | 社区 | 职责 |
|------|------|------|
| `factory/factory.go` | C10 | Factory 结构体定义与初始化入口 |
| `factory/ubill/impl.go` | C10 | UBillImpl 结构体定义、常量管理 |
| `factory/ubill/basic.go` | C7 | 请求/响应 DTO + 基础 API 方法（PostPaid / GetPostPaidItemBillInfo / GetUnpaidOrderDetailInfo） |
| `factory/ubill/expand.go` | C12 | 业务扩展 API（TrafficPostPaid / InstancePostPaid / TrafficOrderDetail / InstanceOrderDetail） |
| `factory/common/common.go` | C11 | 公共基类（BaseRequest / BaseResponse）与接口定义 |

## 3. 主要函数/类型清单

### 3.1 factory/factory.go

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `Factory` | `factory/factory.go:8-10` | 工厂对象，持有 `UBillImpl` 实例 |
| `InitFactory` | `factory/factory.go:12-16` | 初始化 Factory（创建 UBillImpl） |

### 3.2 factory/ubill/impl.go

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `ServiceBackend` | `factory/ubill/impl.go:8` | 网关注册 ID = "UBill" |
| `EndpointProductType` | `factory/ubill/impl.go:10` | Endpoint 产品类型 = 390 |
| `EndpointInstanceProductID` | `factory/ubill/impl.go:12` | Endpoint 实例费小类 = 3900001 |
| `EndpointTrafficProductID` | `factory/ubill/impl.go:13` | Endpoint 流量费小类 = 3900002 |
| `EndpointServiceProductType` | `factory/ubill/impl.go:15` | Service 产品类型 = 389 |
| `EndpointServiceInstanceProductID` | `factory/ubill/impl.go:17` | Service 实例费小类 = 3890001 |
| `EndpointServiceTrafficProductID` | `factory/ubill/impl.go:18` | Service 流量费小类 = 3890002 |
| `ChargeType` | `factory/ubill/impl.go:20` | 后付费方式 = 102 |
| `Quantity` | `factory/ubill/impl.go:21` | 计费周期 = 1 |
| `UBillImpl` | `factory/ubill/impl.go:24-28` | UBill 客户端结构体 |
| `NewUBillImpl` | `factory/ubill/impl.go:31-37` | 创建 UBillImpl 实例 |

### 3.3 factory/ubill/basic.go — 基础 API 方法

| 函数/类型 | 代码位置 | 说明 |
|-----------|----------|------|
| `PostPaidRequest` | `factory/ubill/basic.go:14-27` | 后付费扣费请求结构体 |
| `OrderDetailPostPaid` | `factory/ubill/basic.go:29-32` | 订单详情子结构体 |
| `PostPaidResponse` | `factory/ubill/basic.go:34-37` | 后付费扣费响应结构体 |
| `GetPostPaidItemBillInfoRequest` | `factory/ubill/basic.go:39-45` | 订单查询请求结构体 |
| `GetPostPaidItemBillInfoResponse` | `factory/ubill/basic.go:47-59` | 订单查询响应结构体 |
| `GetUnpaidOrderDetailInfoRequest` | `factory/ubill/basic.go:61-65` | 未支付订单详情请求 |
| `GetUnpaidOrderDetailInfoResponse` | `factory/ubill/basic.go:67-75` | 未支付订单详情响应 |
| `ApiRequest` | `factory/ubill/basic.go:78-80` | 底层 HTTP POST 调用 |
| `APIRequestWithMetrics` | `factory/ubill/basic.go:82-95` | 带 Prometheus 埋点的 API 调用封装 |
| `PostPaid` | `factory/ubill/basic.go:97-108` | 执行后付费扣费 |
| `GetPostPaidItemBillInfo` | `factory/ubill/basic.go:110-118` | 查询资源订单详情 |
| `GetUnpaidOrderDetailInfo` | `factory/ubill/basic.go:120-128` | 查询未支付订单详情 |

### 3.4 factory/ubill/expand.go — 业务 API 方法

| 函数 | 代码位置 | 说明 |
|------|----------|------|
| `TrafficPostPaid` | `factory/ubill/expand.go:8-39` | 流量费后付费：根据 itemId 前缀选择产品类型 |
| `InstancePostPaid` | `factory/ubill/expand.go:41-72` | 实例费后付费：根据 itemId 前缀选择产品类型 |
| `TrafficOrderDetail` | `factory/ubill/expand.go:74-121` | 流量费订单详情查询（含已支付+未支付判断） |
| `InstanceOrderDetail` | `factory/ubill/expand.go:123-170` | 实例费订单详情查询（含已支付+未支付判断） |

### 3.5 factory/common/common.go — 公共基类

| 类型 | 代码位置 | 说明 |
|------|----------|------|
| `BaseRequest` | `factory/common/common.go:4-8` | 请求基类（Backend, Action, RequestUUID） |
| `BaseResponse` | `factory/common/common.go:10-14` | 响应基类（Action, RetCode, Message） |
| `IBaseRequest` | `factory/common/common.go:29-32` | 请求接口 |
| `IBaseResponse` | `factory/common/common.go:34-36` | 响应接口 |

## 4. 关键实现逻辑

### 4.1 带监控的 API 调用（`APIRequestWithMetrics` @ `factory/ubill/basic.go:82-95`）

```
1. 请求前: ClientRequestSentTotal++ (标签: api, backend, action)
2. 记录 startTime
3. 执行 i.ApiRequest() — 底层 HTTP POST
4. 请求后:
   ├── ClientResponseReceivedTotal++ (标签: api, backend, action, retCode)
   ├── ClientResponseDuration.Observe(delay) (标签: action, "http", backend)
   └── 返回结果
```

### 4.2 商品类型选择逻辑（`TrafficPostPaid` / `InstancePostPaid` @ `factory/ubill/expand.go`）

根据 `itemId` 的前缀选择对应的产品类型和计费小类：

```
itemId 前缀判断:
  ├── "epsrv" 开头 → EndpointService 产品
  │   ├── ProductType = 389
  │   └── ProductId = 3890001(实例) / 3890002(流量)
  └── 其他 ("ep" 开头) → Endpoint 产品
      ├── ProductType = 390
      └── ProductId = 3900001(实例) / 3900002(流量)
```

### 4.3 订单详情查询逻辑（`TrafficOrderDetail` / `InstanceOrderDetail` @ `factory/ubill/expand.go`）

```
1. 调用 GetPostPaidItemBillInfo 获取所有订单
2. 从 PaidDetail 中筛选匹配 startTime/endTime 的订单号
3. 从 UnpaidDetail 中筛选匹配 startTime/endTime 的订单号
4. 合并订单号列表，调用 GetUnpaidOrderDetailInfo 获取详情
5. 在详情中查找匹配 productId 的订单项
6. 匹配成功 → 返回 OrderNo (代表已存在订单)
7. 匹配失败 → 返回 "" (代表需要重新扣费)
```

此逻辑用于重试场景的**幂等性保证**：重试时先查询 UBill 是否有已存在的订单，避免重复扣费。

## 5. 涉及的源文件

- `factory/factory.go`（全部，16 行）
- `factory/ubill/impl.go`（全部，37 行）
- `factory/ubill/basic.go`（全部，128 行）
- `factory/ubill/expand.go`（全部，170 行）
- `factory/common/common.go`（全部，36 行）

# billing — module_03_Billing_Logic

> 自动生成文档 | 社区 9 | 系统: billing | 时间: 2026-06-18

---

# Billing Logic — 计费业务逻辑模块

## 1. 模块职责

本模块是 billing 服务的**核心计费引擎**，负责：
- **流量后付费**：统计上小时流量数据，生成订单并调用 UBill 扣费
- **实例后付费**：统计上小时有效连接数，生成实例费订单并调用 UBill 扣费
- **流量重试**：对失败的流量订单进行周期性重试（先查询是否已支付）
- **实例重试**：对失败的实例订单进行周期性重试

## 2. 常量定义

定义在 `task/billing.go:12-37`：

| 常量 | 值 | 说明 |
|------|-----|------|
| `SuccessState` | `"success"` | 订单成功状态 |
| `InitState` | `"init"` | 订单初始状态 |
| `TrafficBilling` | 1 | 流量计费类型 |
| `InstanceBilling` | 2 | 实例计费类型 |
| `ServiceTrafficRecord` | 10 | Service 流量仅记录不落单 |
| `ServiceInstanceRecord` | 11 | Service 实例仅记录不落单 |
| `NoTrafficRecord` | 12 | 流量为 0 仅记录 |
| `PayerEndpointInt` | 1 | Endpoint 方付费 |
| `PayerEndpointServiceInt` | 0 | Service 方付费 |
| `Hour` | 3600 | 1 小时秒数 |
| `Day` | 86400 | 1 天秒数 |
| `MB` | 8×1024×1024 | bit→MB 转换基数 |

## 3. 主要函数清单

| 函数名 | 代码位置 | 说明 |
|--------|----------|------|
| `TrafficBilling` | `task/billing.go:39-121` | 流量计费主流程：查询流量 → 分流 → 创建订单 → 扣费 |
| `buildServiceTrafficInfo` | `task/billing.go:123-155` | 构建 Service 付费模式的流量订单（聚合 + 记录） |
| `InstanceBilling` | `task/billing.go:157-249` | 实例计费主流程：查询连接 → 付费方 → 创建订单 → 扣费 |
| `InstanceMultiple` | `task/billing.go:252-258` | 计算实例倍数（不足 1 小时按 1 小时） |
| `TrafficReBilling` | `task/rebilling.go:12-45` | 流量失败订单重试 |
| `InstanceReBilling` | `task/rebilling.go:47-79` | 实例失败订单重试 |

## 4. 关键实现逻辑

### 4.1 流量计费（`TrafficBilling` @ `task/billing.go:39-121`）

```
输入: startTime, endTime (上小时时间戳)
流程:
  1. db.GetAllTrafficInfosLastInterval() — 获取上小时所有流量记录
  2. 遍历每条流量记录:
     ├── Payer=0 (Service付费):
     │   ├── buildServiceTrafficInfo() — 流量聚合到 Service 维度
     │   └── 每条 Endpoint 生成 ServiceTrafficRecord(仅记录)
     └── Payer=1 (Endpoint付费):
         └── 直接生成 TrafficBilling 订单
           ├── TrafficSum = (Out + In) / MB
           └── TrafficSum=0 → NoTrafficRecord(仅记录)
  3. db.CreateBillingInfo() — 批量写入订单
  4. 遍历可计费订单:
     ├── fac.UBillImpl.TrafficPostPaid() — UBill 扣费
     └── db.BillingOrder() — 更新订单状态
  5. Prometheus 埋点: BillingOrderCounter / TaskStatusCounter
```

**关键处理逻辑**：
- **Service 聚合**：`buildServiceTrafficInfo`（`task/billing.go:123-155`）将同一 Service 下多个 Endpoint 的流量合计到 Service 维度，同时为每个 Endpoint 生成一条 `ServiceTrafficRecord`（仅记录不扣费）
- **零流量过滤**：`TrafficSum == 0` 时标记为 `NoTrafficRecord`，不发起扣费，但保留记录

### 4.2 实例计费（`InstanceBilling` @ `task/billing.go:157-249`）

```
输入: startTime, endTime (上小时时间戳)
流程:
  1. db.GetAllConnectInfo() — 获取有效连接
  2. db.GetAllEndpointPayerInfo() — 获取付费方信息
  3. 建立 payerInfoMap (endpoint_id → EndpointPayerInfo)
  4. 遍历有效连接:
     ├── 从 payerInfoMap 获取付费方
     ├── 计算 InstanceMultiple (不足1h→1)
     ├── Payer=0 (Service付费):
     │   ├── 聚合到 Service 维度 (累加 Multiple)
     │   └── Endpoint 生成 ServiceInstanceRecord(仅记录)
     └── Payer=1 (Endpoint付费):
         └── 直接生成 InstanceBilling 订单
  5. db.CreateBillingInfo() — 批量写入
  6. 遍历可计费订单:
     ├── fac.UBillImpl.InstancePostPaid() — UBill 扣费
     └── db.BillingOrder() — 更新订单状态
```

### 4.3 实例倍数计算（`InstanceMultiple` @ `task/billing.go:252-258`）

```
(endTime - startTime) / Hour
  → 结果 ≤ 1 则返回 1（不足1小时按1小时计费）
  → 否则返回实际小时数
```

### 4.4 流量重试（`TrafficReBilling` @ `task/rebilling.go:12-45`）

```
输入: rebillTime, rebillCycle, reBillingTimeOut
流程:
  1. context.WithTimeout — 超时控制 (默认为配置的 ReBillingTimeOut 秒)
  2. db.ReBillingWithOrderPaid() — 事务内处理失败订单
     ├── 查询 [rebillTime - rebillCycle*Day, rebillTime) 范围内
     │   state != "success" 且 type = TrafficBilling 的订单
     └── 对每个订单:
         ├── fac.UBillImpl.TrafficOrderDetail() — 先查询是否已支付
         ├── 已支付 → 直接更新状态 (幂等)
         └── 未支付 → fac.UBillImpl.TrafficPostPaid() 重新扣费
  3. Prometheus 埋点: ReBillingOrderCounter / TaskStatusCounter
```

### 4.5 实例重试（`InstanceReBilling` @ `task/rebilling.go:47-79`）

逻辑与流量重试相同，区别在于：
- 查询 `type = InstanceBilling` 的失败订单
- 调用 `InstanceOrderDetail` 查询已支付状态
- 调用 `InstancePostPaid` 重新扣费

## 5. 涉及的源文件

- `task/billing.go`（全部，258 行）
- `task/rebilling.go`（全部，79 行）

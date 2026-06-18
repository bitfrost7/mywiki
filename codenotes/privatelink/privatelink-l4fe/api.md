# API 文档 — gRPC

## 接口定义

服务在编译时依赖 `git.ucloudadmin.com/l4fwd/proto` 包中的 protobuf 定义。

### RPC: ListL4Gw

**原型**：`rpc ListL4Gw(ListL4GwRequest) returns (ListL4GwReply)`

**文件**：`api/grpc_api.go`（实现）、`proto` 依赖包（定义）

**用途**：批量查询 L4 Gateway 的完整配置视图。

---

### 请求参数

**`ListL4GwRequest`**（定义见 proto 包）

| 字段 | 类型 | 说明 |
|------|------|------|
| `object_ids` | `repeated string` | 要查询的 Service ID 列表 |

---

### 响应参数

**`ListL4GwReply`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `views` | `map<string, L4GwView>` | key = object_id（Service ID），value = 该服务的 L4 网关视图 |

**`L4GwView`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `l4_gw` | `L4Gw` | L4 网关配置（v2 格式） |
| `state` | `L4GwState` | 查询状态：`SUCCESS` / `MISSED` |

**`L4Gw` (v2)**

| 字段 | 类型 | 说明 |
|------|------|------|
| `version` | `uint32` | 固定为 `2` |
| `gw2` | `L4Gw2` | v2 版本的网关配置 |

**`L4Gw2`** — 核心配置结构

| 字段 | 类型 | 说明 |
|------|------|------|
| `object_id` | `string` | Service ID |
| `account_id` | `uint32` | 所属账户 ID |
| `fore_ips` | `repeated Address` | 前端 VIP 列表（来自 VPC Endpoint 的 IP） |
| `fnat_ips` | `repeated Address` | FNAT SNAT IP 列表 |
| `fore_groups` | `repeated GwGroup` | 前端转发组（每个 Endpoint 一个组） |
| `backend_groups` | `repeated GwGroup` | 后端转发组（Service 本身） |
| `fnat_groups` | `repeated GwGroup` | FNAT 转发组（SNAT IPs） |
| `rules` | `repeated GwRule` | FullNAT 转发规则 |

**`Address`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `ip` | `string` | IPv4 或 IPv6 地址 |
| `tun_id` | `uint32` | 隧道 ID |
| `account_id` | `uint32` | 账户 ID |

**`GwGroup`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 组 ID（格式：`<service_id>-f`/`<service_id>-b`/`<endpoint_id>`） |
| `endpoints` | `repeated GwEndpoint` | 组成员 |
| `scheduler` | `uint32` | 调度算法（固定 1） |

**`GwEndpoint`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | Endpoint ID（如 `<group_id>-ipv4`） |
| `ip` | `string` | IP 地址 |
| `tun_id` | `uint32` | 隧道 ID |
| `min_port` | `uint32` | 最小端口（fore: 1, fnat: 1025, backend: 1） |
| `max_port` | `uint32` | 最大端口（固定 65535） |
| `protocol` | `uint32` | 协议（固定 255 = 任意） |
| `mac` | `string` | MAC 地址 |
| `weight` | `uint32` | 权重（固定 0） |
| `nexthop` | `string` | 下一跳（空字符串） |
| `disabled` | `bool` | 是否禁用（false） |
| `down` | `bool` | 是否宕机（false） |
| `backup` | `bool` | 是否备份（false） |

**`GwRule`**

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `string` | 规则 ID |
| `action` | `uint32` | 动作（3 = fullnat） |
| `endpoint_id` | `string` | 关联 Endpoint ID |
| `target_src_type` | `uint32` | 源目标类型（2 = group） |
| `target_src_id` | `string` | 源目标 ID（指向 FNAT 组） |
| `target_dst_type` | `uint32` | 目标类型（2 = group） |
| `target_dst_id` | `string` | 目标 ID（指向 Backend 组） |

---

## 状态码

| 状态 | 说明 |
|------|------|
| `SUCCESS` | 查询成功，返回完整 L4Gw 配置 |
| `MISSED` | 该 ID 在数据库中不存在 |

---

## 调用流程

参见 [architecture.md](architecture.md) 中的详细调用链说明。

### 单次 RPC 处理的步骤（`grpc_api.go:26-199`）

1. **数据查询**：通过 `getDataFromDB()` 在单个数据库事务中查询三张表
2. **组装 Fore IP 列表**：遍历 VPC Endpoint，将 IPv4/IPv6 加入 `foreIPs`
3. **组装 FNAT IP 列表**：遍历 Service SNAT IP 加入 `fnatips`
4. **组装 Fore Groups**：每个 Endpoint 一个 GwGroup，内含 IPv4/IPv6 两个 GwEndpoint
5. **组装 FNAT Group**：所有 SNAT IP 组成一个组，端口范围从 1025 开始
6. **组装 Backend Group**：Service 自身 IP 作为一个组
7. **组装 Rules**：每个 Fore Endpoint 生成一条 FullNAT 规则，将流量 SNAT 到 FNAT 组、DNAT 到 Backend 组
8. **返回响应**：将所有视图组装为 `ListL4GwReply`

---

## 错误处理

- 数据库查询失败 → 返回 gRPC 错误
- 部分 Endpoint/SNAT IP 找不到对应 Service → 日志警告但不中断
- 请求的 Service ID 在数据库中不存在 → 返回 `MISSED` 状态

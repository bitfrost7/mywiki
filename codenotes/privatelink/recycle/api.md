# recycle — HTTP API 文档

> 自动生成文档 | 系统: recycle | 时间: 2026-06-18

---

## 概述

recycle 服务通过单个 HTTP POST `/` 端点接收请求，所有请求以 JSON 格式提交，通过 `Action` 字段进行路由分发。由 Gin 框架驱动（`github.com/gin-gonic/gin`），仅 master 节点处理 API 请求。

**重要说明**：HTTP API 仅处理 **VPC Endpoint** 的回收操作。Endpoint Service 的回收仅由 cron 定时任务触发，无 HTTP API 入口。

## 基础信息

| 项目 | 说明 |
|------|------|
| HTTP 方法 | `POST` |
| 路径 | `/` |
| 内容类型 | `application/json` |
| 框架 | Gin (`github.com/gin-gonic/gin`) |
| Master 限制 | 仅 master 节点返回正常响应，follower 返回 `"Server is not master, cant reply"`（`server.go:123-127`） |

## 请求结构体

### 通用请求头 (`ReqBase`)

定义于 `api/api.go:32-35`

```json
{
  "Action": "string",
  "request_uuid": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `Action` | string | 是 | API 名称（`CloseEndpoint` / `RecycleEndpoint` / `DeleteEndpoint`） |
| `request_uuid` | string | 否 | 请求 UUID，为空时由 `ucontext.NewRequestID()` 自动生成（`api/api.go:67-69`） |

### 通用响应头 (`RespBase`)

定义于 `api/api.go:37-42`

```json
{
  "request_uuid": "string",
  "Action": "string",
  "RetCode": 0,
  "Message": "string"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `request_uuid` | string | 请求 UUID（回显） |
| `Action` | string | 响应 API 名称（`Action + "Response"`，如 `CloseEndpointResponse`） |
| `RetCode` | int | 返回码，0 表示成功 |
| `Message` | string | 错误描述信息 |

## API 列表

### 1. CloseEndpoint — 停服

**Action**: `CloseEndpoint`
**Action 路由**：`api/api.go:75`
**源码位置**：`api/recycle.go:19-27`

**请求**：
```json
{
  "Action": "CloseEndpoint",
  "request_uuid": "optional-uuid"
}
```

**处理逻辑**：
1. 解析请求体（`api/recycle.go:21-24`），调用 `parseInput()`
2. 调用 `Task.CloseEndpointWithDelay()`（`api/recycle.go:26`）
   - 触发批量停服扫描流程（`task/recycle_endpoint.go:13-33`）
   - 扫描 URecycleV2 中标记为待停服的 Endpoint（`factory/urecycle/expand.go:8-19`）
   - 按 RegionId 过滤（`task/recycle_endpoint.go:26-28`），按延迟时间校验（`task/recycle_endpoint.go:29`）
   - 执行停服：更新 DB（`db/db.go:93-118`） + 通知 URecycleV2（`factory/urecycle/expand.go:92-106`）

**响应**：
```json
{
  "request_uuid": "uuid",
  "Action": "CloseEndpointResponse",
  "RetCode": 0,
  "Message": "Success"
}
```

---

### 2. RecycleEndpoint — 恢复

**Action**: `RecycleEndpoint`
**Action 路由**：`api/api.go:77`
**API 方法名**：`RecoverEndpoint`（命名不一致，路由 `RecycleEndpoint` → 方法 `RecoverEndpoint`）
**源码位置**：`api/recycle.go:30-38`

**请求**：
```json
{
  "Action": "RecycleEndpoint",
  "request_uuid": "optional-uuid"
}
```

**处理逻辑**：
1. 解析请求体（`api/recycle.go:32-35`），调用 `parseInput()`
2. 调用 `Task.RecoverEndpoint()`（`api/recycle.go:37`）
   - 触发批量恢复扫描流程（`task/recycle_endpoint.go:55-87`）
   - 扫描 URecycleV2 中可恢复的 Endpoint（`factory/urecycle/expand.go:36-48`）
   - 更新 DB 状态（`db/db.go:120-168`）→ 更新 close_status=0 + 若 connect_status=1 则重建连接记录
   - 通知 URecycleV2（`factory/urecycle/expand.go:124-138`）

**注意**：API Action 名称为 `RecycleEndpoint`，但在路由分发时映射到 `RecoverEndpoint` 方法（`api/api.go:77-78`），二者对应同一业务操作。文档和代码中均存在此命名不一致。

**响应**：
```json
{
  "request_uuid": "uuid",
  "Action": "RecycleEndpointResponse",
  "RetCode": 0,
  "Message": "Success"
}
```

---

### 3. DeleteEndpoint — 删除

**Action**: `DeleteEndpoint`
**Action 路由**：`api/api.go:79`
**源码位置**：`api/recycle.go:41-49`

**请求**：
```json
{
  "Action": "DeleteEndpoint",
  "request_uuid": "optional-uuid"
}
```

**处理逻辑**：
1. 解析请求体（`api/recycle.go:43-46`），调用 `parseInput()`
2. 调用 `Task.DeleteEndpoint()`（`api/recycle.go:48`）
   - 触发批量删除扫描流程（`task/recycle_endpoint.go:90-122`）
   - 扫描 URecycleV2 中待删除的 Endpoint（`factory/urecycle/expand.go:64-76`）
   - 调用 PrivateLink API 执行网络删除（`factory/privatelink/expand.go:8-23`）
   - 通知 URecycleV2 回收完成（`factory/urecycle/expand.go:156-170`）

**响应**：
```json
{
  "request_uuid": "uuid",
  "Action": "DeleteEndpointResponse",
  "RetCode": 0,
  "Message": "Success"
}
```

## 错误码

定义于 `api/code.go:14-30`

| RetCode | 错误常量 | Message |
|---------|----------|---------|
| 0 | `nil` | `Success` |
| 160 | `MissingActionErr` | `Key parameter Action is missing, please provide the complete parameters` |
| 161 | `ActionNotFoundErr` | `Action not found` |
| 230 | `RequestParamsErr` | `The parameter is invalid, please check the input parameters. %s` |
| 500 | `InternalServerErr` | `Internal Server Error` |

**错误码查找逻辑**（`api/api.go:119-125`）：
1. 精确匹配 `ErrCodeDefine[err]`
2. 未命中则返回 `InternalServerErr` 对应的 500

**错误消息格式化**（`api/api.go:127-133`）：
1. 查找 `ErrCodeDescribe[err]` 获取格式化字符串
2. 传入 `params...` 进行 `fmt.Sprintf` 格式化

## 请求流程

```
Client → POST / (JSON Body)
            │
            ├── 1. Api.Handel() @ api/api.go:45-85
            │       ├── 读取请求体 (io.ReadAll, L47)
            │       ├── 重新设置 c.Request.Body (NopCloser, L54)
            │       ├── 解析 JSON → ReqBase (L59)
            │       ├── 生成/提取 request_uuid (L66-69)
            │       ├── ctx = ucontext.RequestIDToContext(ctx, uuid) (L70)
            │       └── switch Action (L74-83):
            │               ├── "CloseEndpoint"  → CloseEndpoint() → Task.CloseEndpointWithDelay()
            │               ├── "RecycleEndpoint" → RecoverEndpoint() → Task.RecoverEndpoint()
            │               └── "DeleteEndpoint" → DeleteEndpoint() → Task.DeleteEndpoint()
            │
            ├── 2. 调用对应 Task 方法（触发批量扫描）
            │
            └── 3. Reply(c, resp) → JSON 响应 (L84)

注意：所有 Action 未匹配的分支返回 "action not found" (L82)
```

## API 路由注册

API 路由注册于 `server.go:118-130`：

```go
gin.SetMode(gin.ReleaseMode)
g := gin.New()
s.api = api.NewApi(ctx, s.t)
g.POST("/", func(c *gin.Context) {
    if !s.isMaster() {
        api.Reply(c, "Server is not master, cant reply")
        return
    }
    s.api.Handel(c)
})
s.InitHttpServer(g)
```

**关键点**：
- 仅 master 节点处理 API 请求（`server.go:123-127`），通过 `atomic.CompareAndSwapUint32` 判定
- 非 master 节点返回 `"Server is not master, cant reply"` 文本响应（非 JSON 格式）
- 三个 API 的请求结构体（`CloseRequest` / `RecoverRequest` / `DeleteRequest`）均嵌入 `ReqBase`，无额外字段（`api/recycle.go:6-16`）

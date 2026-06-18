# recycle — module_02_API 请求处理

> 自动生成文档 | 社区 C6 (api/api.go, api/recycle.go) + C14 (factory/common/common.go) + C28 (api/code.go)
> 系统: recycle | 时间: 2026-06-18

---

# API 请求处理 — API Request Handling

## 1. 模块职责

本模块是 recycle 服务的**HTTP API 入口层**，社区 C6 / C14 / C28 共 4 个源文件，负责：

- **请求接收与解析**：读取 HTTP POST 请求体，JSON 反序列化（`api/api.go:45-85`）
- **Action 路由分发**：根据 `Action` 字段分发到对应的回收处理方法（`api/api.go:74-83`）
- **错误码管理**：统一错误码定义与错误消息格式化（`api/code.go:7-31`）
- **请求/响应结构体定义**：通用请求头 `ReqBase`、响应头 `RespBase` 及外部 API 公共结构 `common.BaseRequest/BaseResponse`

## 2. 主要函数/类型清单

### api/api.go（社区 C6，133 行）

| 类型/函数 | 代码位置 | 类型 | 说明 |
|-----------|----------|------|------|
| `GinContextKey` | `api/api.go:17` | 变量 | 存储在 `gin.Context` 中的 `context.Context` 键名 |
| `Api` | `api/api.go:19-22` | 结构体 | API 处理器，持有 `context.Context` 和 `*task.Task` 引用 |
| `NewApi` | `api/api.go:24-29` | 函数 | 创建 Api 实例 |
| `ReqBase` | `api/api.go:32-35` | 结构体 | 通用请求头：`Action` + `request_uuid` |
| `RespBase` | `api/api.go:37-42` | 结构体 | 通用响应头：`request_uuid` + `Action` + `RetCode` + `Message` |
| `Handel` | `api/api.go:45-85` | 方法 | **请求主入口**：读取 Body → 解析 JSON → context 注入 → Action 分发 |
| `extractContext` | `api/api.go:87-93` | 函数 | 从 `gin.Context` 提取 `context.Context` |
| `Reply` | `api/api.go:95-97` | 函数 | 返回 JSON 响应（`c.JSON(http.StatusOK, resp)`） |
| `parseInput` | `api/api.go:99-108` | 函数 | 解析请求体到具体结构体，返回错误描述 |
| `GenResponse` | `api/api.go:110-117` | 方法 `ReqBase` | 生成标准响应（Action 名 + RetCode + Message） |
| `GenRetCode` | `api/api.go:119-125` | 函数 | 从 `ErrCodeDefine` 映射表获取 RetCode |
| `GenMessage` | `api/api.go:127-133` | 函数 | 从 `ErrCodeDescribe` 映射表获取 Message（支持 `fmt.Sprintf` 格式化） |

### api/recycle.go（社区 C6 + C15，50 行）

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `CloseRequest` | `api/recycle.go:6-8` | 停服请求（嵌入 `ReqBase`，无额外字段） |
| `RecoverRequest` | `api/recycle.go:10-12` | 恢复请求（嵌入 `ReqBase`，无额外字段） |
| `DeleteRequest` | `api/recycle.go:14-16` | 删除请求（嵌入 `ReqBase`，无额外字段） |
| `CloseEndpoint` | `api/recycle.go:19-28` | Action=`CloseEndpoint` handler，调用 `Task.CloseEndpointWithDelay()` |
| `RecoverEndpoint` | `api/recycle.go:30-38` | Action=`RecycleEndpoint` handler（命名不一致），调用 `Task.RecoverEndpoint()` |
| `DeleteEndpoint` | `api/recycle.go:41-50` | Action=`DeleteEndpoint` handler，调用 `Task.DeleteEndpoint()` |

### api/code.go（社区 C28，31 行）

| 变量 | 代码位置 | RetCode | 说明 |
|------|----------|---------|------|
| `MissingActionErr` | `api/code.go:9` | 160 | 缺少 Action 参数 |
| `ActionNotFoundErr` | `api/code.go:10` | 161 | Action 不存在 |
| `RequestParamsErr` | `api/code.go:11` | 230 | 请求参数错误（含格式化描述） |
| `InternalServerErr` | `api/code.go:12` | 500 | 内部服务错误 |
| `ErrCodeDefine` | `api/code.go:14-21` | — | `error` → `RetCode` 映射表（`api/api.go:119-125` 使用） |
| `ErrCodeDescribe` | `api/code.go:23-30` | — | `error` → 错误消息字符串映射表（`api/api.go:127-133` 使用） |

### factory/common/common.go（社区 C14，36 行）

| 类型/函数 | 代码位置 | 说明 |
|-----------|----------|------|
| `BaseRequest` | `factory/common/common.go:4-8` | 外部 API 通用请求结构体（`Backend` + `Action` + `RequestUUID`） |
| `BaseResponse` | `factory/common/common.go:10-14` | 外部 API 通用响应结构体（`Action` + `RetCode` + `Message`） |
| `GetAction` | `factory/common/common.go:17-19` | 获取 Action 名称 |
| `GetBackend` | `factory/common/common.go:21-23` | 获取 Backend 名称（如 `"URecycleV2"` / `"PrivateLink"` / `"UResource"`） |
| `GetRetCode` | `factory/common/common.go:25-27` | 获取返回码 |
| `IBaseRequest` | `factory/common/common.go:29-32` | 请求接口：`GetAction()` + `GetBackend()` |
| `IBaseResponse` | `factory/common/common.go:34-36` | 响应接口：`GetRetCode()` |

## 3. 关键实现逻辑

### 3.1 请求分发流程（`Handel` @ `api/api.go:45-85`）

```
POST / → Handel(c *gin.Context)
  │
  ├── 1. io.ReadAll(c.Request.Body)           — 读取原始 Body (L47)
  │      └── 重新设置 c.Request.Body (NopCloser) (L54)
  │
  ├── 2. c.ShouldBindBodyWith(req, JSON)      — 解析为 ReqBase (L59)
  │
  ├── 3. uuid = req.RequestUUID 或 自动生成   — request_id 处理 (L66-69)
  │      └── ctx = ucontext.RequestIDToContext(ctx, uuid) (L70)
  │      └── c.Set(GinContextKey, ctx)  (L71)
  │
  ├── 4. switch req.Action:                   — Action 路由分发 (L74-83)
  │      ├── "CloseEndpoint"   → a.CloseEndpoint(c)
  │      ├── "RecycleEndpoint" → a.RecoverEndpoint(c)    ← 注意命名不一致
  │      ├── "DeleteEndpoint"  → a.DeleteEndpoint(c)
  │      └── default           → "action not found"
  │
  └── 5. Reply(c, resp)                       — JSON 响应 (L84)
```

### 3.2 Action 路由映射

| Action 名称（请求中） | 处理方法 | 调用的 Task 方法 | 说明 |
|----------------------|----------|-----------------|------|
| `CloseEndpoint` | `CloseEndpoint` @ `api/recycle.go:19` | `t.CloseEndpointWithDelay()` | 批量扫描待停服 Endpoint |
| `RecycleEndpoint` | `RecoverEndpoint` @ `api/recycle.go:30` | `t.RecoverEndpoint()` | **命名不一致**：Action 名 `Recycle`，方法名 `Recover` |
| `DeleteEndpoint` | `DeleteEndpoint` @ `api/recycle.go:41` | `t.DeleteEndpoint()` | 批量扫描待删除 Endpoint |

### 3.3 外部 API 通用结构（`factory/common/common.go`）

所有外部系统 API 请求/响应继承此结构：

```go
BaseRequest {                     BaseResponse {
    Backend     string  // 网关注册ID        Action  string  // API 名称
    Action      string  // API 名称         RetCode int     // 0=成功
    RequestUUID string  // 请求UUID         Message string  // 错误信息
}                                   }
```

三个后端常量：`"URecycleV2"`（`factory/urecycle/impl.go:13`）、`"PrivateLink"`（`factory/privatelink/impl.go:6`）、`"UResource"`（`factory/uresource/impl.go:8`）

### 3.4 错误码机制（`api/code.go:14-30`）

**RetCode 查找优先级**（`api/api.go:119-125`）：
1. 精确匹配 `ErrCodeDefine[err]`
2. 未命中 → 返回 `InternalServerErr` 对应的 500

**错误消息格式化**（`api/api.go:127-133`）：
1. 查找 `ErrCodeDescribe[err]` 获取格式化字符串
2. 传入 `params...` 进行 `fmt.Sprintf` 格式化（如传入请求参数校验错误描述）

## 4. 涉及的源文件

- `api/api.go`（全部，133 行）
- `api/recycle.go`（全部，50 行）
- `api/code.go`（全部，31 行）
- `factory/common/common.go`（全部，36 行）

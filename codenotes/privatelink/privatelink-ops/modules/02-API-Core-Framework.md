# 模块: API 核心框架

> 社区 #5, #10, #30, #31 — 39 节点 · 凝聚系数中

---

## 概述

本模块是 privatelink-ops 的 API 核心框架，提供 Gin 路由注册、请求解析与 Action 分发、参数校验（Validator）、请求/响应基类、错误码定义和资源类型常量等基础设施。所有 API 请求都经过此框架的统一处理管线。

---

## 文件索引

### 路由与请求分发

**`api/api.go:1-185`** — API 核心

| 结构体/函数 | 行号 | 说明 |
|-------------|------|------|
| `GinContextKey` | `:25` | Gin Context 中存储应用上下文的 Key |
| 动作常量 | `:28-32` | 5 个 API Action 名称：`SetResourceInvisible`、`SetResourceVisible`、`AddUserConfig`、`DeleteUserConfig`、`UpdateUserConfig` |
| `API` | `:35` | API 核心结构体：聚合 `Application`（日志/配置）、`Database`、`Factory`、校验器和翻译器 |
| `NewAPI()` | `:43` | 构造函数：初始化校验器 + 注册路由 |
| `InitValidate()` | `:59` | 初始化 `go-playground/validator`：注册 JSON tag 名解析、注册英文翻译器 |
| `jsonKey()` | `:70` | 提取 struct 的 `json` tag 名称用于校验错误消息 |
| `InitRouter()` | `:78` | 初始化 Gin 引擎：`gin.ReleaseMode` → `gin.New()` → `POST /` 注册 `handle` 函数 |
| `handle()` | `:85` | **核心分发函数**：读取 Body → 解析 `ReqBase` → 设置 Context → Action 匹配分发 |
| `handleRequestUUID()` | `:132` | 将客户端提供的 `RequestUUID` 注入到应用上下文中，用于请求追踪 |
| `extractContext()` | `:139` | 从 Gin Context 中提取应用 Context |
| `reply()` | `:147` | 统一响应输出：记录日志 → `c.JSON(http.StatusOK, msg)` |
| `parseInput()` | `:162` | **统一参数解析**：JSON 绑定 → Struct 校验 → 返回错误描述 |

**分发逻辑**（**`api/api.go:115-128`**）：

```go
switch req.Action {
case ActionSetResourceInvisible:  resp = a.SetResourceInvisible(c)
case ActionSetResourceVisible:    resp = a.SetResourceVisible(c)
case ActionAddUserConfig:         resp = a.AddUserConfig(c)
case ActionDeleteUserConfig:      resp = a.DeleteUserConfig(c)
case ActionUpdateUserConfig:      resp = a.UpdateUserConfig(c)
default:                          resp = GenResponse(ActionNotFoundErr)
}
```

### 请求/响应基类

**`api/base.go:1-51`** — 基类型与响应生成

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `ReqBase` | `:8` | 请求基类：`Action`（必填）+ `RequestUUID`（可选） |
| `RespBase` | `:13` | 响应基类：`Action` + `RetCode` + `Message` |
| `ReqBase.GenResponse()` | `:20` | 基于请求 Action 生成响应（Action = 请求Action + "Response"） |
| `GenResponse()` | `:29` | 静态响应生成函数 |
| `GenRetCode()` | `:37` | 查 `ErrCodeDefine` 映射表获取错误码 |
| `GenMessage()` | `:45` | 查 `ErrCodeDescribe` 映射表获取错误消息 |

### 错误码定义

**`api/error.go:1-41`** — 全局错误变量与映射

| 错误变量 | 行号 | RetCode | 说明 |
|----------|------|---------|------|
| `MissingActionErr` | `:10` | 160 | 缺少 Action 参数 |
| `ActionNotFoundErr` | `:11` | 161 | Action 未找到 |
| `RequestParamsErr` | `:12` | 230 | 请求参数错误 |
| `InternalServerErr` | `:13` | 500 | 服务内部错误 |
| `ResourceNotFoundErr` | `:16` | 217803 | 资源不存在（PrivateLink 专用，范围 217801-218000） |
| `ErrCodeDefine` | `:18` | — | 错误 → RetCode 映射表 |
| `ErrCodeDescribe` | `:30` | — | 错误 → 描述消息映射表 |

### 资源类型常量

**`api/convert.go:1-7`** — 资源类型枚举

| 常量 | 行号 | 说明 |
|------|------|------|
| `ResourceTypeEndpoint` | `:5` | `"Endpoint"` — VPC 端点 |
| `ResourceTypeEndpointService` | `:6` | `"EndpointService"` — 端点服务 |

---

## 请求处理管线

```
Client → POST /
  │
  ▼
Gin Engine (api/api.go:78 InitRouter)
  │ POST /
  ▼
handle() :85
  │
  ├─ 1. io.ReadAll(c.Request.Body) :86
  │    → 读取原始 Body，并重新注入以便后续绑定
  │
  ├─ 2. c.ShouldBindBodyWith(req, binding.JSON) :98
  │    → 解析出 ReqBase.Action + ReqBase.RequestUUID
  │
  ├─ 3. 上下文设置 :105-109
  │    ├─ RequestUUID 非空 → handleRequestUUID() 注入 UUID 到 Context
  │    └─ RequestUUID 为空 → 新建 Context
  │
  ├─ 4. Action 分发 :115-128 (switch)
  │
  └─ 5. reply(c, resp) :129 → JSON 输出 + 日志记录
```

### 参数校验流程

```
parseInput(c, in) :162
  │
  ├─ 1. c.ShouldBindBodyWith(in, binding.JSON) :164
  │    → JSON 反序列化到对应 Request 结构体
  │
  ├─ 2. a.validate.Struct(in) :171
  │    → 按 struct tag 校验字段
  │    → 校验失败：遍历 ValidationErrors
  │      → 英文翻译 → 返回 RequestParamsErr + 错误描述
  │
  └─ 3. 校验成功 → 返回 ("", nil)
```

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `API.db` | Database Operations (M06) | 通过 `Database` 指针调用所有 DB 方法 |
| `API.fac.UResource` | Resource Label Operations (M08) | 调用资源标签管理接口 |
| `API.Application` | Application Server (M01) | 继承 cnat2 应用框架的日志、配置能力 |
| `SetResourceInvisible()` | Resource Visibility (M04) | 可见性操作的分发入口 |
| `AddUserConfig()` | User Config Handlers (M03) | 用户配置操作的分发入口 |

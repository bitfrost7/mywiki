# 模块: 上下文工具

> 社区 #6（部分）— 5 节点 · SessionID Context 管理

---

## 概述

本模块提供 SessionID 的上下文注入与提取工具，用于在请求处理、数据库操作和 HTTP 调用之间传递链路追踪 ID。SessionID 在每次数据库查询和 UResource API 调用时自动注入，确保日志中能够关联同一请求的所有操作。

---

## 文件索引

**`ncontext/ncontext.go:1-31`**

| 类型/变量/函数 | 行号 | 说明 |
|----------------|------|------|
| `contextKey` | `:9` | Context key 类型（基于 int 的私有类型，避免 key 冲突） |
| `SessionID` | `:12` | 日志字段名常量：`"session_id"` |
| `KeyForSessionID` | `:14` | Context key 值：`contextKey(100)` |
| `SessionIDToContext()` | `:17` | **注入 SessionID**：将指定 sessionID 写入 Context |
| `NewSessionIDToContext()` | `:21` | **生成并注入新 SessionID**：调用 `ucontext.NewRequestID()` 生成 UUID 并注入 |
| `ExtractSessionIDFromCtx()` | `:25` | **提取 SessionID**：从 Context 读取；不存在时返回空字符串 |

---

## 使用场景

### 1. 数据库操作日志（db/db.go）

**`db/db.go:36-41`** — `extract()` 函数：

```go
func extract(ctx context.Context) []zapcore.Field {
    fields := make([]zapcore.Field, 0, 2)
    fields = append(fields, zap.Any(ucontext.RequestUUID, ucontext.ExtractRequestIDFromCtx(ctx)))
    fields = append(fields, zap.Any(ncontext.SessionID, ncontext.ExtractSessionIDFromCtx(ctx)))
    return fields
}
```

该函数在 `NewDatabase()`（**`db/db.go:45`**）中设为 `logger.Context`，使得每条 GORM 执行的 SQL 日志都会自动带上 `request_uuid` 和 `session_id` 字段。

### 2. 数据库业务方法（db/db.go）

每个 Database 业务方法（例如 `GetVPCEndpoints()` 在 **`db/db.go:80`**）都会调用：

```go
ctx = ncontext.NewSessionIDToContext(ctx)
```

在查询执行前注入一个新的 SessionID，确保数据库操作的日志有独立的追踪标识。

### 3. UResource API 调用（factory/uresource/basic.go）

**`factory/uresource/basic.go:51`** 和 **`:67`**：

```go
ctx = ncontext.SessionIDToContext(ctx, req.RequestUUID)
```

在调用 UResource API 前将请求的 `RequestUUID` 作为 SessionID 注入到 Context 中，传递给 HTTP Client。

### 4. HTTP Client 日志（httpclient/httpclient.go）

**`httpclient/httpclient.go:137`**：

```go
l := ucontext.Logger(ctx).With(zap.String(ncontext.SessionID, ncontext.ExtractSessionIDFromCtx(ctx)))
```

从 Context 提取 SessionID，注入到 HTTP 请求日志中。

---

## 数据流

```
HTTP Request → api.handle()
  │
  ├─ 生成/注入 RequestUUID 到 Context (api/api.go:106-109)
  │
  ├─ Database 操作
  │   └─ NewSessionIDToContext(ctx) — 生成新 SessionID
  │       └─ GORM 日志 → 自动输出 request_uuid + session_id
  │
  └─ UResource API 调用
      └─ SessionIDToContext(ctx, req.RequestUUID) — 传递 RequestUUID
          └─ HTTP Client PostCtx → 日志输出 session_id
```

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `NewSessionIDToContext()` | Database Operations (M06) | 所有 DB 方法调用此函数注入 SessionID |
| `SessionIDToContext()` | Resource Label Operations (M08) | UResource API 调用前注入 SessionID |
| `ExtractSessionIDFromCtx()` | HTTP Client (M09) | HTTP 日志中提取 SessionID |
| `ExtractSessionIDFromCtx()` | Database Operations (M06) | DB 日志 `extract()` 中提取 SessionID |

---

## 设计要点

- **私有 Key 类型**：使用自定义 `contextKey`（基于 int）而非字符串，避免与其他包在 Context 中产生 key 冲突
- **双重追踪**：同时支持 `RequestUUID`（来自 `cnat2/app` 框架）和 `SessionID`（本模块），前者用于跨服务追踪，后者用于单请求内追踪
- **自动生成**：`NewSessionIDToContext()` 使用 `ucontext.NewRequestID()` 生成 UUID v4，无需调用方关心 ID 生成

# 模块: 资源标签操作

> 社区 #19, #20, #32 — 8 节点 · Resource Label Operations + Common Request Types

---

## 概述

本模块是 privatelink-ops 与外部资源管理系统 UResource 的集成层，负责管理资源的不可见标签。它通过 HTTP Client 调用 UResource 系统的 `IAddResourceLabel` 和 `IDeleteResourceLabel` API 来实现标签的添加和删除。资源标签用于控制资源在用户界面上的可见性。

---

## 文件索引

### 通用请求/响应类型

**`factory/common/common.go:1-15`** — UResource API 通用基类

| 类型 | 行号 | 说明 |
|------|------|------|
| `BaseRequest` | `:4` | 通用请求基类：`Backend`（网关注册 ID）、`Action`（API 名称）、`RequestUUID`（请求追踪） |
| `BaseResponse` | `:10` | 通用响应基类：`Action`、`Retcode`（int32）、`Message`（错误信息） |

**注意**：`BaseResponse.Retcode` 是 `int32`，与 `api/base.go` 中的 `RespBase.RetCode`（int）类型不同。

### 资源系统 API 请求构造

**`factory/uresource/basic.go:1-74`** — UResource API 请求/响应结构体 + 调用方法

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| `IAddResourceLabelRequest` | `:13` | 添加标签请求：`AuthKey` + `ResourceIds`（[]string）+ `LabelInfos`（[]*LabelInfo） |
| `LabelInfo` | `:20` | 标签信息：`Key` + `Value` |
| `IAddResourceLabelResponse` | `:25` | 添加标签响应：嵌入 `BaseResponse` |
| `IDeleteResourceLabelRequest` | `:29` | 删除标签请求：`AuthKey` + `ResourceIds` + `DeletedLabels`（标签 Key 列表） |
| `IDeleteResourceLabelResponse` | `:35` | 删除标签响应：嵌入 `BaseResponse` |
| `ResourceImpl.APIRequest()` | `:40` | 通用 API 调用：`i.cli.PostCtx(ctx, i.url, req, resp)` |
| `ResourceImpl.IAddResourceLabel()` | `:44` | **添加标签**：设置 `Action="IAddResourceLabel"`、`Backend="UResource"` → 调用 APIRequest |
| `ResourceImpl.IDeleteResourceLabel()` | `:60` | **删除标签**：设置 `Action="IDeleteResourceLabel"`、`Backend="UResource"` → 调用 APIRequest |

**请求构造流程**（以 `IAddResourceLabel` 为例，**`factory/uresource/basic.go:44-58`**）：

```go
func (i *ResourceImpl) IAddResourceLabel(ctx context.Context, req *IAddResourceLabelRequest) (*IAddResourceLabelResponse, error) {
    req.Action = "IAddResourceLabel"       // :45 — 设置 UResource API 名称
    req.Backend = i.backend                // :46 — "UResource"
    req.AuthKey = ""                       // :47 — 当前为空（待补充）
    if req.RequestUUID == "" {
        req.RequestUUID = ucontext.NewRequestID()  // :49 — 自动生成追踪 ID
    }
    ctx = ncontext.SessionIDToContext(ctx, req.RequestUUID)  // :51 — 注入 SessionID
    resp := &IAddResourceLabelResponse{}
    err := i.APIRequest(ctx, req, resp)    // :53 — HTTP POST 调用
    return resp, nil
}
```

### 标签业务操作

**`factory/uresource/expand.go:1-41`** — 高层业务接口

| 函数 | 行号 | 说明 |
|------|------|------|
| `ResourceImpl.SetInvisibleLabel()` | `:8` | **设置不可见标签**：添加 `general.Invisible=true` 标签到资源 |
| `ResourceImpl.DeleteResourceLabel()` | `:28` | **删除不可见标签**：移除资源的 `general.Invisible` 标签 |

**SetInvisibleLabel 实现**（**`factory/uresource/expand.go:8-26`**）：

```go
func (i *ResourceImpl) SetInvisibleLabel(ctx context.Context, resourceID string) error {
    req := &IAddResourceLabelRequest{
        ResourceIds: []string{resourceID},
        LabelInfos: []*LabelInfo{
            {Key: "general.Invisible", Value: "true"},
        },
    }
    resp, err := i.IAddResourceLabel(ctx, req)
    if err != nil { return err }
    if resp.Retcode != 0 { return errors.New(resp.Message) }
    return nil
}
```

**DeleteResourceLabel 实现**（**`factory/uresource/expand.go:28-41`**）：

```go
func (i *ResourceImpl) DeleteResourceLabel(ctx context.Context, resourceID string) error {
    req := &IDeleteResourceLabelRequest{
        ResourceIds:   []string{resourceID},
        DeletedLabels: []string{"general.Invisible"},
    }
    resp, err := i.IDeleteResourceLabel(ctx, req)
    if err != nil { return err }
    if resp.Retcode != 0 { return errors.New(resp.Message) }
    return nil
}
```

---

## 调用链

```
Resource Visibility Handlers (M04)
  │
  ├─ a.fac.UResource.SetInvisibleLabel(ctx, resourceId)
  │     └─ expand.go:8
  │          └─ IAddResourceLabel(ctx, req)
  │               └─ basic.go:44
  │                    └─ APIRequest(ctx, req, resp)
  │                         └─ basic.go:40
  │                              └─ httpclient.PostCtx() → HTTP POST
  │                                   → UResource API (内部系统)
  │
  └─ a.fac.UResource.DeleteResourceLabel(ctx, resourceId)
        └─ expand.go:28
             └─ IDeleteResourceLabel(ctx, req)
                  └─ basic.go:60
                       └─ APIRequest(ctx, req, resp)
                            └─ httpclient.PostCtx() → HTTP POST
                                 → UResource API (内部系统)
```

---

## ResourceImpl 结构体

**`factory/uresource/impl.go:18-31`**：

```go
type ResourceImpl struct {
    url     string                      // UResource API 基 URL
    backend string                      // 固定为 "UResource"
    cli     *httpclient.HTTPClient      // HTTP 客户端
}
```

`NewUResourceImpl()`（`:25`）在 `server.go:64` 中由 `NewServer` 调用初始化。

---

## 跨模块连接

| 桥接节点 | 目标模块 | 说明 |
|----------|----------|------|
| `ResourceImpl.APIRequest` | HTTP Client (M09) | 通过 `httpclient.PostCtx()` 发送 HTTP 请求 |
| `SetInvisibleLabel` | Resource Visibility (M04) | 可见性操作调用此方法 |
| `DeleteResourceLabel` | Resource Visibility (M04) | 可见性操作调用此方法 |
| `BaseRequest` | — | UResource API 通用请求基类 |
| `ncontext.SessionIDToContext` | Context Utilities (M10) | 注入 SessionID |

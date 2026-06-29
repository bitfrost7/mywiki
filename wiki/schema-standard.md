# mywiki Wiki Page Schema 标准

> Wiki 下所有页面的元信息（Metadata）和内容结构规范。
> 所有 agent 产出的页面必须符合此标准。

---

## 1. Metadata 块（`%%...%%`）

每页顶部必须包含 `%%...%%` 块，格式：

### 概况页（overview / architecture）

```markdown
%% state: pending-review | confidence: 7 | type: concept | sources: privatelink/apisvr | stage: L1 | agent: writer | created: 2026-06-24 %%
```

### 接口详情页（interfaces/）

```markdown
%% state: pending-review | confidence: 7 | type: api | sources: privatelink/apisvr | action: CreateVPCEndpoint | stage: L1 | agent: reader | created: 2026-06-24 %%
```

### 模块详解页（modules/）

```markdown
%% state: pending-review | confidence: 7 | type: module | sources: privatelink/apisvr | module: db-layer | stage: L1 | agent: reader | created: 2026-06-24 %%
```

### 字段说明

| 字段 | 必须 | 可选值 | 说明 |
|------|:----:|--------|------|
| `state` | ✅ | `draft` / `pending-review` / `reviewed` / `published` | 状态 |
| `confidence` | ✅ | `1`–`10` | 置信度 |
| `type` | ✅ | `concept` / `api` / `module` / `architecture` / `interfaces` / `overview` | 页面类型 |
| `sources` | ✅ | 来源标识 | 如 `privatelink/apisvr` |
| `stage` | ✅ | `L1` / `L2` | 编译阶段 |
| `agent` | ✅ | `analyst` / `reader` / `writer` / `auditor` / `linker` / `scenario` | 产出的 agent |
| `action` | ⚠️ | 接口名 | 仅 type=api 需要 |
| `module` | ⚠️ | 模块名 | 仅 type=module 需要 |
| `ast_community` | ❌ | 社区编号 | 引用的 graph.json 社区 |
| `created` | ❌ | YYYY-MM-DD | 创建日期 |

---

## 2. 页面类型模板

### overview.md

```markdown
%% state: pending-review | confidence: 7 | type: overview | sources: privatelink/<service> | stage: L1 | agent: writer | created: 2026-06-24 %%

# <Service> — <中文描述>

## 定位
<服务在业务中的角色>

## 技术栈
| 层 | 技术 | 节点数 |
|-------|------|:------:|
| API | Gin + gRPC | 363 |

## 核心功能
- <功能 1>
- <功能 2>

## 服务结构
```
<目录树>
```

## AST 指标
| 指标 | 值 |
|------|:--:|
| 节点 | 1215 |
| 边 | 2233 |
| 社区 | 74 |
| God 节点 | Logger (47 边) |

## 相关页面
- [[privatelink/<service>/architecture]]
- [[privatelink/<service>/interfaces]]
```

### architecture.md

```markdown
%% state: pending-review | confidence: 7 | type: architecture | sources: privatelink/<service> | stage: L1 | agent: writer | created: 2026-06-24 %%

# 架构 — <service>

## 分层架构
| 层 | 组件 | 职责 |
|-------|------|------|

## 启动链
```
<启动时序>
```

## 关键节点
| 节点 | 边数 | 角色 |
|------|:----:|------|

## 相关页面
- [[privatelink/<service>/overview]]
```

### interfaces.md（索引页）

```markdown
%% state: pending-review | confidence: 7 | type: interfaces | sources: privatelink/<service> | stage: L1 | agent: writer | created: 2026-06-24 %%

# <Service> — 接口文档

## 接口分组

### 1. VPC 终端节点管理
| 接口 | 方法 | 说明 |
|------|------|------|
| [[privatelink/<service>/interfaces/CreateVPCEndpoint\|CreateVPCEndpoint]] | POST | 创建终端节点 |
| ...

### 2. <组名>
...
```

### interfaces/<Action>.md（接口详情）

```markdown
%% state: pending-review | confidence: 7 | type: api | sources: privatelink/<service> | action: <Action> | stage: L1 | agent: reader | created: 2026-06-24 %%

# <Action>

## 描述
<接口功能说明>

## 调用方式
| 字段 | 值 |
|------|:--:|
| Action | <Action> |
| 协议 | HTTP/gRPC |
| 方法 | POST |
| 来源 | `<source_file>` |

## 请求结构
| 字段 | 类型 | 必填 | 说明 |
|------|------|:----:|------|
| <字段> | <类型> | ✅/❌ | <说明> |

## 响应结构
| 字段 | 类型 | 说明 |
|------|------|------|

## 业务逻辑
<一串描述接口内部逻辑的步骤>

## AST 引用
- 社区: [[Community N]]
- God 节点: <关联节点>

## 相关接口
- [[privatelink/<service>/interfaces/<Action2>]]
```

### modules/<name>.md（模块详解）

```markdown
%% state: pending-review | confidence: 7 | type: module | sources: privatelink/<service> | module: <name> | stage: L1 | agent: reader | created: 2026-06-24 %%

# <Module> — <描述>

## 职责
<该层在架构中的角色>

## 核心结构
| 结构体/接口 | 职责 | AST 引用 |
|------------|------|----------|

## 关键流程
<流程说明或时序>

## 相关页面
- [[privatelink/<service>/architecture]]
```

---

## 3. 目录结构规范

```
Wiki/privatelink/<service>/
├── overview.md                   # 概况
├── architecture.md               # 架构
├── interfaces.md                 # 接口目录索引
├── interfaces/
│   ├── CreatXPCEndpoint.md      # 每个接口一个文件
│   ├── DeleteVPCEndpoint.md
│   └── ...
└── modules/
    ├── db-layer.md               # 数据库层
    ├── factory-layer.md          # 工厂层
    ├── server-lifecycle.md       # 生命周期
    └── ...
```

---

## 4. 交叉引用规范

- 跨页面引用：`[[privatelink/<service>/<page>]]` 或 `[[privatelink/<service>/interfaces/<Action>|<显示名>]]`
- 引用 AST 社区：`[[Community N]]`
- 引用外部资源：用 `[描述](URL)`，不用 `[[` 语法

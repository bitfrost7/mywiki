# 模块: Main Configuration Loader

> 社区 #9 — 7 节点 · 凝聚力 0.36

---

## 概述

主配置加载模块是 bwregister 的 CLI 入口，处理命令行参数解析、JSON 配置加载和命令分发。该模块实现了 `start`、`dumpcfg`、`version` 三个子命令，是服务启动的初始入口。

---

## 文件索引

**`cmd/main.go`** — 主入口与 CLI（L1-88）

| 类型/函数 | 行号 | 说明 |
|-----------|------|------|
| 包级变量 `cfgPath` | `:16` | 配置路径（默认 `conf/bwregister.json`） |
| `main()` | `:18` | CLI 入口，参数解析与命令分发 |
| `runServer()` | `:43` | 启动服务：加载配置 → NewServer → Start |
| `loadConfig()` | `:53` | 读取 JSON 配置文件并反序列化 |
| `dumpConfig()` | `:65` | 输出默认配置模板 |
| `showVersion()` | `:73` | 输出版本信息 |
| `usage()` | `:77` | 输出使用帮助 |
| `init()` | `:86` | 注册 Prometheus 版本指标 |

---

## CLI 命令处理

**`main()` 在 `cmd/main.go:18-41`**：

```
OS Arguments
  │
  ├── -c <path> → 设置 cfgPath (默认 conf/bwregister.json)
  └── args[0]   → 子命令调度 (switch):
       ├── "start"    → runServer()
       ├── "dumpcfg"  → dumpConfig()
       ├── "version"  → showVersion()
       └── default    → usage()
```

### start 命令

**`cmd/main.go:43-51`**：

```go
func runServer() {
    cfg, err := loadConfig()               // 读取 JSON 配置
    s := bwregister.NewServer(cfg)         // 创建 Server
    s.Start()                              // 启动（cron + gRPC）
}
```

### dumpcfg 命令

**`cmd/main.go:65-71`**：创建一个带默认值的 `Config` 空对象并用 JSON 输出：

```go
func dumpConfig() {
    cfg := &bwregister.Config{
        ApplicationConfig: app.ApplicationConfig{},
    }
    b, _ := json.MarshalIndent(cfg, "", "  ")
    fmt.Println(string(b))
}
```

### version 命令

**`cmd/main.go:73-75`**：

```go
func showVersion() {
    fmt.Println(version.Print("bwregister"))
}
```

使用 `prometheus/common/version` 打印包含构建信息的版本字符串。

---

## 配置加载

**`loadConfig()` 在 `cmd/main.go:53-63`**：

```go
func loadConfig() (*bwregister.Config, error) {
    b, err := ioutil.ReadFile(cfgPath)     // 读取文件
    cfg := &bwregister.Config{}
    err = json.Unmarshal(b, cfg)           // JSON 反序列化
    return cfg, nil
}
```

配置路径通过 `-c` 参数指定，默认读取 `conf/bwregister.json`。

---

## Config 验证

`server.go:34-47` 中的 `VerifyParams()` 验证必填参数不为空：

```go
func (c *Config) VerifyParams() error {
    if c.RegisterZKPath == "" || c.RegisterSpec == "" || ... || c.DBConfig.DSN == "" {
        return errors.New("empty config")
    }
    return nil
}
```

---

## Prometheus 初始化

**`cmd/main.go:86-88`**：

```go
func init() {
    prometheus.MustRegister(version.NewCollector("privatelink_bwregister"))
}
```

在程序启动时自动注册版本收集器，将构建信息暴露为 Prometheus 指标。

---

## 使用示例

```
# 启动服务（后台）
bwregister -c conf/bwregister.json start

# 输出默认配置模板
bwregister dumpcfg

# 输出版本信息
bwregister version

# 查看帮助
bwregister
```

---

## 跨模块连接

| 桥接节点 | 目标社区 | 说明 |
|----------|----------|------|
| `runServer()` | Application Server Setup (C5) | 调用 `NewServer(cfg)` |
| `loadConfig()` | Application Server Setup (C5) | 返回 `*bwregister.Config` |
| `dumpConfig()` | 工具链 | 输出配置模板 |
| `Config` | Application Server Setup (C5) | 配置跨模块共享 |

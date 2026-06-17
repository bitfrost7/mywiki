# Knowledge Generator V2 优化方案

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Knowledge Generator V2                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  输入: 代码仓库 (Go/C/...)                                               │
│                    │                                                    │
│                    ▼                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 1: AST 提取层 (100% 确定性)                                  │  │
│  │                                                                   │  │
│  │  GoASTExtractor ──→ Tree-sitter ──→ CodeFacts                    │  │
│  │       │                              (函数/类型/位置)            │  │
│  │       │                                                           │  │
│  │  RouterExtractor ──→ RouteFacts (路由映射表)                       │  │
│  │       │                                                           │  │
│  │       └── 支持: Gin REST / Action 字段分发 / gRPC / ...            │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                    │                                                    │
│                    ▼                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 2: 置信度引擎 (可量化不确定性)                                │  │
│  │                                                                   │  │
│  │  评分维度:                                                        │  │
│  │  ├─ 来源可信度 (AST=1.0 > 静态分析=0.85 > LLM=0.4)               │  │
│  │  ├─ 完整性 (必需字段是否齐全)                                      │  │
│  │  ├─ 一致性 (与其他事实是否冲突)                                    │  │
│  │  └─ 可验证性 (代码位置是否可检查)                                  │  │
│  │                                                                   │  │
│  │  输出: (Fact, ConfidenceScore, UncertaintyFlag)                  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                    │                                                    │
│                    ▼                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 3: 文档生成层 (防幻觉设计)                                    │  │
│  │                                                                   │  │
│  │  CautiousPromptBuilder:                                           │  │
│  │  ├─ 提供完整事实列表 (不给猜测空间)                                │  │
│  │  ├─ 明确禁止编造 (❌ 禁止假设 REST 路由)                            │  │
│  │  ├─ 要求标注不确定性 (【推测】【需确认】)                          │  │
│  │  └─ 区分"代码事实"vs"LLM推断"                                     │  │
│  │                                                                   │  │
│  │  LLM Generation ──→ Raw Document                                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                    │                                                    │
│                    ▼                                                    │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Layer 4: 验证层 (后验检查)                                          │  │
│  │                                                                   │  │
│  │  OutputVerifier:                                                  │  │
│  │  ├─ 实体对齐检查 (提到的函数是否存在于事实列表?)                    │  │
│  │  ├─ 代码位置验证 (行号是否在文件范围内?)                           │  │
│  │  ├─ 路由路径验证 (REST 路径是否有路由注册支持?)                     │  │
│  │  └─ 特殊检查: Action 路由系统 ❌ 禁止 REST 描述                    │  │
│  │                                                                   │  │
│  │  输出: VerificationResult (is_valid, hallucinations[], fixes[])  │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                    │                                                    │
│                    ▼                                                    │
│  输出: Markdown 文档 (带置信度标注 + 验证批注)                            │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心问题解决

### 问题 1: LLM 编造 REST 路由（apisvr 案例）

**根本原因**:
- V1 Prompt 提供表格示例 `| /api/v1/... | GET | ... |`
- LLM 看到示例后强行填充，即使代码中没有 REST 路由
- 缺乏路由类型检测，不知道实际是 Action 字段分发

**V2 解决方案**:
```python
# 1. 先检测路由类型 (100% 确定)
route_type = detect_route_type(repo_path)  # 'action_dispatch'

# 2. 提取实际路由映射 (从 switch/case)
routes = ActionRouterExtractor().extract_routes(repo_path)
# → [RouteFact(ActionCreateVPCEndpoint → CreateVPCEndpoint, 置信度=1.0)]

# 3. 构建专用 Prompt (明确禁止 REST 描述)
prompt = """
【关键事实】此项目使用 **Action 字段路由**，不是 REST。
【绝对禁止】❌ 禁止生成 "| /api/v1/... | GET | ... |" 表格
【必须遵守】✅ 只描述 Action 字段分发机制

路由映射事实：
  ✓ ActionCreateVPCEndpoint → CreateVPCEndpoint @ api.go:74

【输出格式】
| Action 字段 | Handler | 位置 |
|-------------|---------|------|
| ActionCreateVPCEndpoint | CreateVPCEndpoint | api.go:74 |
"""

# 4. 后验验证 (兜底)
verifier = OutputVerifier(repo_path)
if '/api/' in generated_doc and route_type == 'action':
    # 检测到编造，触发修正
    doc = add_correction_notice(doc, "编造 REST 路径，实际为 Action 路由")
```

---

### 问题 2: 置信度量化

**评分公式**:
```python
Confidence = 0.4 × Source + 0.2 × Completeness + 0.2 × Consistency + 0.2 × Verifiability

# 来源基础分
SOURCE_BASE = {
    FactSource.AST_EXTRACTED:    1.0,   # 直接 AST 解析
    FactSource.STATIC_ANALYSIS:    0.85,  # 静态分析推导
    FactSource.HEURISTIC:          0.6,   # 启发式规则
    FactSource.LLM_INFERRED:       0.4,   # LLM 推断（低）
    FactSource.UNKNOWN:            0.2,   # 来源不明
}
```

**等级划分**:
| 分数 | 等级 | 处理方式 |
|------|------|---------|
| 0.9-1.0 | HIGH | 直接使用，无需标注 |
| 0.6-0.9 | MEDIUM | 标注【推测】 |
| 0.3-0.6 | LOW | 标注【需确认】 |
| 0-0.3 | UNCERTAIN | 标注【需人工审查】或省略 |

---

### 问题 3: 跨文件分析（Action 路由检测）

**挑战**: apisvr 的 handler 定义在 `api/*.go`，路由注册在 `server.go` 或 `api.go`

**解决方案**:
```python
class ActionRouterExtractor:
    def extract_routes(self, repo_path: Path) -> List[RouteFact]:
        # Step 1: 收集所有 Action 常量 (全局扫描)
        action_constants = {}
        for go_file in repo_path.rglob("*.go"):
            facts = GoASTExtractor().extract(go_file, repo_path)
            for f in facts:
                if f.fact_type == 'const' and f.name.startswith('Action'):
                    action_constants[f.name] = f

        # Step 2: 扫描路由注册文件 (优先级排序)
        target_files = [
            repo_path / "api.go",
            repo_path / "server.go",
            repo_path / "router.go",
        ]

        # Step 3: 正则匹配 switch/case 模式
        for file in target_files:
            content = file.read_text()
            # 匹配: case ActionXxx: resp = handler()
            for match in re.finditer(r'case\s+(Action\w+)\s*:\s*(?:resp\s*=\s*)?(\w+)\(', content):
                action_name = match.group(1)
                handler_name = match.group(2)

                # Step 4: 交叉验证 handler 存在性
                handler_loc = self._find_handler_location(handler_name)

                yield RouteFact(
                    path_or_action=action_name,
                    handler_name=handler_name,
                    handler_location=handler_loc,  # 跨文件关联
                    confidence=1.0 if handler_loc else 0.7,
                )
```

---

## 3. 模块化设计

### 3.1 接口层 (`core/interfaces.py`)

```python
class IASTExtractor(ABC):
    """AST 提取器接口"""
    @abstractmethod
    def extract(self, file_path: Path, repo_root: Path) -> List[CodeFact]: ...

class IRouterExtractor(ABC):
    """路由提取器接口"""
    @abstractmethod
    def detect_route_type(self, repo_path: Path) -> Optional[str]: ...
    @abstractmethod
    def extract_routes(self, repo_path: Path) -> List[RouteFact]: ...

class IConfidenceEngine(ABC):
    """置信度引擎接口"""
    @abstractmethod
    def score_fact(self, fact: CodeFact, context: Dict) -> float: ...
```

### 3.2 扩展点

**新增语言支持** (如 C++):
```python
# core/extractors/cpp_extractor.py
class CppASTExtractor(IASTExtractor):
    def can_handle(self, file_path: Path) -> bool:
        return file_path.suffix in ['.cpp', '.hpp', '.cc']

    def extract(self, file_path: Path, repo_root: Path) -> List[CodeFact]:
        # 使用 tree-sitter-cpp
        ...

# 注册
ExtractorRegistry.register('cpp', CppASTExtractor())
```

**新增路由类型** (如 gRPC):
```python
# core/extractors/router_extractors.py
class GRPCRouterExtractor(IRouterExtractor):
    def detect_route_type(self, repo_path: Path) -> Optional[str]:
        # 检查 .proto 文件和 grpc.Register
        ...

# 注册
ExtractorRegistry.register_router('grpc', GRPCRouterExtractor())
```

---

## 4. 关键改进对比

| 维度 | V1 (旧 Pipeline) | V2 (新架构) |
|------|-----------------|-------------|
| **路由识别** | ❌ 无检测，假设 REST | ✅ 自动检测 (Gin/Action/gRPC/...) |
| **事实来源** | ❌ LLM 直接读代码 | ✅ AST 提取 → 结构化事实 |
| **编造控制** | ❌ Prompt 示例诱导 | ✅ 明确禁止 + 专用 Prompt |
| **置信度** | ❌ 无 | ✅ 4 维度评分 + 等级标注 |
| **后验验证** | ❌ 无 | ✅ 实体/位置/路由验证 |
| **错误修正** | ❌ 无 | ✅ 检测到编造后自动标记 |
| **不确定性** | ❌ 隐藏 | ✅ 明确标注【推测】【需确认】 |
| **模块化** | ❌ 单一脚本 | ✅ 接口化，可扩展 |

---

## 5. 实施路径

### Phase 1: 核心基础设施 (1-2 周)
- [ ] 安装 Tree-sitter 依赖
- [ ] 实现 `GoASTExtractor`
- [ ] 实现 `ActionRouterExtractor`
- [ ] 实现 `ConfidenceEngine`
- [ ] 集成测试 apisvr

### Phase 2: 防幻觉系统 (2-3 周)
- [ ] 实现 `CautiousPromptBuilder`
- [ ] 实现 `OutputVerifier`
- [ ] 添加路由类型特殊检查
- [ ] 验证 apisvr 不再产生 REST 编造

### Phase 3: 多语言扩展 (2-3 周)
- [ ] 实现 `CASTExtractor`
- [ ] 验证 C 项目提取准确性
- [ ] 文档和示例

### Phase 4: 工程化 (1-2 周)
- [ ] 缓存优化 (避免重复提取)
- [ ] 并行处理 (多文件并发)
- [ ] CI/CD 集成
- [ ] 幻觉率监控仪表板

---

## 6. 质量保证指标

| 指标 | 目标 | 测量方式 |
|------|------|---------|
| 路由类型识别准确率 | 100% | 人工抽查 10 个仓库 |
| 代码位置标注准确率 | ≥95% | 随机抽样 50 个标注验证 |
| 置信度 ≥0.9 的事实占比 | ≥60% | 统计所有生成 |
| 幻觉检出率 | ≥80% | 人工标注幻觉，对比检测 |
| 人工审查需求 | ≤20% 文档 | 统计【需确认】标注数量 |

---

## 7. 文件清单

```
_tools/
├── core/
│   ├── interfaces.py                 # 核心接口定义
│   ├── extractors/
│   │   ├── __init__.py
│   │   ├── go_extractor.py           # Go AST 提取 (Tree-sitter)
│   │   ├── c_extractor.py            # C AST 提取 (待实现)
│   │   └── router_extractors.py      # 路由提取器 (Gin/Action/...)
│   ├── confidence/
│   │   ├── __init__.py
│   │   ├── engine.py                 # 置信度引擎
│   │   └── verifier.py               # 输出验证器
│   └── generator/
│       ├── __init__.py
│       ├── prompt_builder.py         # 谨慎 Prompt 构建
│       ├── doc_assembler.py          # 文档组装
│       └── pipeline_v2.py            # 新 Pipeline 主控
│
└── OPTIMIZATION_PLAN.md              # 本文档
```

---

## 8. 立即执行

### 安装依赖
```bash
# 在你的 mise 环境中
pip install tree-sitter tree-sitter-go tree-sitter-c
```

### 测试 apisvr
```bash
python -m core.generator.pipeline_v2 \
    --system privatelink \
    --repo apisvr \
    --repo-path ~/.cache/mywiki-repos/apisvr
```

### 验证改进
1. 检查 `api.md` 是否为 Action 路由描述（非 REST）
2. 检查置信度统计脚注
3. 检查是否有编造路由的警告

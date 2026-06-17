#!/usr/bin/env python3
"""
谨慎的 Prompt 构建器

核心原则：
1. 只提供从代码提取的事实，不提供格式假设
2. 明确禁止编造
3. 要求标注不确定性
"""

from typing import List, Dict, Optional
from pathlib import Path

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import IPromptBuilder, CodeFact, RouteFact, FactSource, ConfidenceLevel


class CautiousPromptBuilder(IPromptBuilder):
    """
    谨慎的 Prompt 构建器

    防止 LLM 编造的关键设计：
    - 提供完整事实列表，不给 LLM 猜测空间
    - 明确禁止假设和推断
    - 要求对不确定内容标注【需确认】
    """

    def __init__(self):
        self.base_rules = """
【绝对禁止】
1. ❌ 禁止编造不存在的代码位置、函数名、API 路径
2. ❌ 禁止假设常见设计模式（如假设 REST 路由）
3. ❌ 禁止将推断内容表述为事实
4. ❌ 禁止填充表格中的未知单元格

【必须遵守】
1. ✅ 只描述【事实列表】中明确提供的内容
2. ✅ 不确定时明确标注【需确认】或【未知】
3. ✅ 每个关键声明必须标注代码来源（文件:行号）
4. ✅ 区分"代码事实"和"你的推断"

【输出要求】
- 置信度高的内容：正常描述
- 置信度中等的内容：标注【推测】
- 置信度低或缺失的内容：标注【需确认】或省略
"""

    def build_overview_prompt(self, facts: List[CodeFact]) -> str:
        """构建项目概览 Prompt"""

        # 分类事实
        funcs = [f for f in facts if f.fact_type in ['function', 'method']]
        types = [f for f in facts if f.fact_type.startswith('type_')]
        routes = [f for f in facts if isinstance(f, RouteFact)]

        # 获取包信息
        packages = set()
        for f in facts:
            if 'package' in f.metadata:
                packages.add(f.metadata['package'])

        facts_text = self._format_facts(facts[:20])  # 限制数量避免超长

        return f"""你是一个资深软件架构师，为代码仓库生成项目概览文档。

{self.base_rules}

【代码事实列表】
以下是从代码 AST 提取的 100% 确定的事实：

{facts_text}

【任务】
基于以上事实，生成项目概览：
1. 一句话描述项目职责（基于包名和主要函数推断，标注【推测】）
2. 核心技术栈（基于导入的包和类型推断，标注来源）
3. 主要模块划分（基于文件结构和类型，必须标注每个推断的来源文件）
4. 关键接口/函数清单（只列出事实列表中的，带代码位置）

【输出格式】
```markdown
# {{项目名}}

## 项目描述
{{一句话描述}}【推测：基于 xxx.go 中的函数推断】

## 技术栈
- {{技术}}（来源：import 语句在 {{文件}}）

## 模块划分
| 模块 | 文件位置 | 说明 |
|------|----------|------|
| {{模块名}} | {{文件:行号}} | {{基于事实的描述}} |

## 关键接口
| 函数/类型 | 位置 | 职责（【推测】标注）|
|-----------|------|-------------------|
```

【警告】
如果事实列表不足以支撑某个章节，请明确说明：
"【本节信息不足，需补充分析 {{文件路径}}】"
"""

    def build_architecture_prompt(
        self,
        facts: List[CodeFact],
        routes: List[RouteFact]
    ) -> str:
        """构建架构文档 Prompt"""

        # 分析路由类型
        route_types = set(r.route_type for r in routes)
        route_type_desc = self._describe_route_type(route_types, routes)

        facts_text = self._format_facts(facts[:30])
        routes_text = self._format_routes(routes)

        return f"""你是一个软件架构师，为代码仓库生成架构设计文档。

{self.base_rules}

【路由机制事实】
{route_type_desc}

详细路由映射：
{routes_text}

【代码事实列表】
{facts_text}

【任务】
基于以上事实，分析架构：
1. 整体架构模式（分层/微服务/事件驱动等）【必须标注判断依据】
2. 核心模块划分及职责（每个模块必须关联到具体文件）
3. 数据流概览（基于路由映射和函数调用关系）
4. 关键接口定义（带代码位置）

【重要】
- 如果路由类型是 'action'（Action 字段分发），**绝对禁止**描述为 REST 路由
- 对于 Action 路由，描述格式必须是：
  "请求通过 Action 字段（如 ActionCreateVPCEndpoint）分发到对应的 handler 函数"

【输出格式】
```markdown
# 架构设计

## 整体架构
{{架构模式}}【判断依据：{{依据}}】

## 路由机制
{{路由类型描述}}（来源：{{路由注册文件}}）

## 核心模块
| 模块 | 文件位置 | 职责 |
|------|----------|------|
| {{模块}} | {{文件.go:行号}} | {{职责}} |

## 数据流
{{基于事实的数据流描述}}

## 关键接口
| 接口 | 位置 | 说明 |
|------|------|------|
| {{接口名}} | {{文件:行号}} | {{说明}} |
```

【禁止示例】
❌ "API 采用 RESTful 设计，路径为 /api/v1/..."
  （如果是 Action 路由，这是编造）

✅ "API 通过 Action 字段路由，映射如下：ActionCreateVPCEndpoint → CreateVPCEndpoint"
  （与路由事实一致）
"""

    def build_api_prompt(
        self,
        routes: List[RouteFact],
        handlers: List[CodeFact]
    ) -> str:
        """构建 API 文档 Prompt"""

        # 判断路由类型
        if not routes:
            return self._build_api_prompt_no_routes(handlers)

        route_type = routes[0].route_type if routes else 'unknown'

        if route_type == 'action':
            return self._build_action_api_prompt(routes, handlers)
        elif route_type == 'rest':
            return self._build_rest_api_prompt(routes, handlers)
        else:
            return self._build_generic_api_prompt(routes, handlers)

    def _build_action_api_prompt(
        self,
        routes: List[RouteFact],
        handlers: List[CodeFact]
    ) -> str:
        """Action 字段路由的专用 Prompt"""

        routes_text = self._format_routes(routes)

        return f"""你是一个 API 文档工程师，生成 API 文档。

{self.base_rules}

【关键事实】
此项目使用 **Action 字段路由**，不是 REST 路由。
请求通过 JSON 中的 "Action" 字段分发，而非 URL 路径。

【路由映射事实】（100% 来自代码）
{routes_text}

【任务】
基于以上事实，生成 API 文档：

1. 路由机制说明（必须是 Action 字段分发）
2. 每个 Action 的说明：
   - Action 常量名（如 ActionCreateVPCEndpoint）
   - 对应的 handler 函数
   - handler 的文件位置
   - 请求/响应结构（如果有）

【输出格式】
```markdown
# API 文档

## 路由机制
所有请求通过 POST 发送到 `/`，通过请求体中的 `Action` 字段路由。

来源：{{路由注册文件}}

## Action 列表

### {{Action 名}}
| 属性 | 值 |
|------|-----|
| Action 字段 | {{ActionCreateXXX}} |
| Handler | {{HandlerName}} |
| 位置 | {{handler.go:行号}} |
| 请求结构 | {{ReqStruct}}【如有】 |
| 响应结构 | {{RespStruct}}【如有】 |

{{业务描述}}【基于函数名和代码推断，标注【推测】】
```

【绝对禁止】
❌ 不要生成 "| /api/v1/... | GET | ... |" 这样的表格
❌ 不要编造 REST 路径
❌ 不要猜测 HTTP 方法（Action 路由通常是 POST）

【示例】
✅ 正确：
| Action 字段 | Handler | 位置 |
|-------------|---------|------|
| ActionCreateVPCEndpoint | CreateVPCEndpoint | api/endpoint.go:74 |

❌ 错误：
| 接口路径 | 方法 | Handler |
|---------|------|---------|
| /api/v1/vpc-endpoint | POST | CreateVPCEndpoint |
  （编造了 REST 路径，实际代码中没有）
"""

    def _build_rest_api_prompt(
        self,
        routes: List[RouteFact],
        handlers: List[CodeFact]
    ) -> str:
        """REST 路由的 Prompt"""

        routes_text = self._format_routes(routes)

        return f"""你是一个 API 文档工程师，生成 API 文档。

{self.base_rules}

【路由映射事实】（100% 来自代码）
{routes_text}

【任务】
基于以上事实，生成 REST API 文档。

【输出格式】
```markdown
# API 文档

| 路径 | 方法 | Handler | 位置 | 描述 |
|------|------|---------|------|------|
| {{路径}} | {{方法}} | {{Handler}} | {{文件:行号}} | {{描述}}【推测】 |
```

【要求】
- 只使用事实列表中的路径
- 每个路径必须有代码来源
- 不确定的描述标注【推测】
"""

    def _build_api_prompt_no_routes(self, handlers: List[CodeFact]) -> str:
        """未检测到路由时的 Prompt"""

        handlers_text = self._format_facts(handlers[:15])

        return f"""你是一个 API 文档工程师。

{self.base_rules}

【警告】
未找到明确的路由注册代码。以下 handler 函数存在，但无法确定路由方式：

{handlers_text}

【任务】
列出发现的 handler 函数，但**明确标注**：
"【路由方式未确定，需检查 server.go 或 router.go】"

【输出格式】
```markdown
# API 文档

## ⚠️ 路由方式未确定
未在代码中找到明确的路由注册（如 gin.GET/POST 或 switch Action）。
请人工检查以下文件：
- server.go
- router.go
- main.go

## 发现的 Handler 函数
| Handler | 位置 | 备注 |
|---------|------|------|
| {{name}} | {{file:line}} | 【需确认路由方式】 |
```
"""

    def _build_generic_api_prompt(
        self,
        routes: List[RouteFact],
        handlers: List[CodeFact]
    ) -> str:
        """通用 API Prompt（路由类型未知）"""
        return self._build_api_prompt_no_routes(handlers)

    # ═══════════════════════════════════════════════════════════════════════
    # 辅助方法
    # ═══════════════════════════════════════════════════════════════════════

    def _format_facts(self, facts: List[CodeFact], max_items: int = 30) -> str:
        """格式化事实列表为文本"""
        lines = []

        for i, f in enumerate(facts[:max_items]):
            confidence_marker = "✓" if f.confidence > 0.8 else "~" if f.confidence > 0.5 else "?"
            line = f"  {confidence_marker} [{f.fact_type}] {f.name} @ {f.location}"

            # 添加关键元数据
            if f.metadata.get('receiver'):
                line += f" (receiver: {f.metadata['receiver']})"
            if f.metadata.get('is_action'):
                line += " [Action常量]"

            lines.append(line)

        if len(facts) > max_items:
            lines.append(f"  ... 还有 {len(facts) - max_items} 个事实 ...")

        return "\n".join(lines) if lines else "  （无事实数据）"

    def _format_routes(self, routes: List[RouteFact]) -> str:
        """格式化路由列表"""
        if not routes:
            return "  （未找到路由映射）"

        lines = []
        for r in routes[:20]:  # 限制数量
            confidence_marker = "✓" if r.confidence > 0.8 else "~" if r.confidence > 0.5 else "?"

            if r.route_type == 'action':
                line = f"  {confidence_marker} {r.path_or_action} → {r.handler_name} @ {r.location}"
            else:
                line = f"  {confidence_marker} {r.method} {r.path_or_action} → {r.handler_name} @ {r.location}"

            if r.metadata.get('extracted_from'):
                line += f" (来源: {r.metadata['extracted_from']})"

            lines.append(line)

        return "\n".join(lines)

    def _describe_route_type(self, route_types: set, routes: List[RouteFact]) -> str:
        """描述路由类型"""
        if not routes:
            return "未找到路由注册代码"

        if 'action' in route_types:
            return """路由类型: **Action 字段分发** (action_dispatch)
- 请求通过 JSON 中的 "Action" 字段路由
- 典型代码: `switch req.Action { case ActionXxx: ... }`
- 所有接口通常通过 POST 发送到根路径 `/`
- 严禁描述为 RESTful 路径"""

        if 'rest' in route_types:
            return f"""路由类型: **REST** (gin_rest)
- 使用 Gin 框架的标准路由注册
- 支持 GET/POST/PUT/DELETE 等方法
- 每个 handler 有明确的 URL 路径"""

        return f"未知路由类型: {route_types}"


if __name__ == "__main__":
    # 测试
    from interfaces import CodeLocation

    builder = CautiousPromptBuilder()

    test_facts = [
        CodeFact(
            id="f1",
            fact_type="function",
            name="CreateVPCEndpoint",
            location=CodeLocation("api/endpoint.go", 74, 100),
            source_code="func CreateVPCEndpoint(...)",
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={'receiver': '*API'}
        ),
        CodeFact(
            id="f2",
            fact_type="const",
            name="ActionCreateVPCEndpoint",
            location=CodeLocation("api/actions.go", 10, 15),
            source_code="const ActionCreateVPCEndpoint = ...",
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            metadata={'is_action': True}
        ),
    ]

    test_routes = [
        RouteFact(
            id="r1",
            fact_type="route",
            name="ActionCreateVPCEndpoint",
            location=CodeLocation("api/endpoint.go", 74, 100),
            source_code="",
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            route_type='action',
            path_or_action='ActionCreateVPCEndpoint',
            method='POST',
            handler_name='CreateVPCEndpoint',
        )
    ]

    prompt = builder.build_api_prompt(test_routes, test_facts)
    print("=== API Prompt 预览 ===")
    print(prompt[:1500])
    print("\n... [truncated]")

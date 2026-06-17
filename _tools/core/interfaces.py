#!/usr/bin/env python3
"""
核心接口定义 - 确定性代码知识提取系统

所有模块均实现这些接口，确保可替换性和可测试性。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Protocol
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════════════════════════════════

class FactSource(Enum):
    """事实来源类型 - 决定置信度基础"""
    AST_EXTRACTED = "ast_extracted"      # AST直接提取，最高置信度
    STATIC_ANALYSIS = "static_analysis"  # 静态分析推导
    LLM_INFERRED = "llm_inferred"        # LLM推断
    HEURISTIC = "heuristic"              # 启发式规则
    UNKNOWN = "unknown"                  # 来源不明


class ConfidenceLevel(Enum):
    """置信度等级"""
    HIGH = (0.9, 1.0, "✓ 高置信度 - 可直接使用")
    MEDIUM = (0.6, 0.9, "~ 中等置信度 - 建议复核")
    LOW = (0.3, 0.6, "⚠ 低置信度 - 需人工确认")
    UNCERTAIN = (0.0, 0.3, "✗ 不确定 - 必须人工审查")

    def __init__(self, min_val: float, max_val: float, description: str):
        self.min_val = min_val
        self.max_val = max_val
        self.description = description


@dataclass
class CodeLocation:
    """代码位置 - 精确到行列"""
    file: str           # 相对路径
    start_line: int
    end_line: int
    start_col: int = 0
    end_col: int = 0

    def __str__(self) -> str:
        if self.start_col or self.end_col:
            return f"{self.file}:{self.start_line}:{self.start_col}-{self.end_line}:{self.end_col}"
        return f"{self.file}:{self.start_line}-{self.end_line}"


@dataclass
class CodeFact:
    """代码事实 - 系统的基础数据单元"""
    # 标识
    id: str                                    # 唯一标识符
    fact_type: str                             # 类型: function/type/route/struct/...
    name: str                                  # 名称

    # 位置
    location: CodeLocation                     # 代码位置
    source_code: str                           # 原始代码片段

    # 分类
    source: FactSource = FactSource.AST_EXTRACTED
    confidence: float = 1.0                    # 0.0-1.0

    # 关系
    related_facts: List[str] = field(default_factory=list)  # 关联事实ID
    parent_id: Optional[str] = None           # 父级事实

    # 元数据
    metadata: Dict[str, Any] = field(default_factory=dict)
    extracted_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "fact_type": self.fact_type,
            "name": self.name,
            "location": str(self.location),
            "source": self.source.value,
            "confidence": self.confidence,
            "source_code_preview": self.source_code[:200] if self.source_code else "",
            "metadata": self.metadata,
        }


@dataclass
class RouteFact(CodeFact):
    """路由事实 - 特殊的代码事实"""
    route_type: str = ""           # rest/action/grpc/...
    path_or_action: str = ""       # 路径或Action名
    method: str = ""               # GET/POST/或空
    handler_name: str = ""         # 处理函数名
    middleware: List[str] = field(default_factory=list)


@dataclass
class DocumentSection:
    """文档章节 - 带置信度的生成内容"""
    title: str
    content: str
    source_facts: List[str]          # 基于哪些事实ID生成
    confidence: float = 1.0
    requires_verification: bool = False

    def render(self) -> str:
        """渲染为 Markdown"""
        confidence_emoji = "✓" if self.confidence > 0.9 else "~" if self.confidence > 0.6 else "⚠"
        header = f"## {self.title}"
        if self.requires_verification:
            header += " 【需验证】"
        return f"{header}\n\n{self.content}\n\n*{confidence_emoji} 置信度: {self.confidence:.2f}*\n"


# ═══════════════════════════════════════════════════════════════════════════
# 抽象接口
# ═══════════════════════════════════════════════════════════════════════════

class IASTExtractor(ABC):
    """
    AST 提取器接口

    从源代码提取结构化事实，100%确定性，无LLM参与。
    """

    @abstractmethod
    def can_handle(self, file_path: Path) -> bool:
        """检查是否能处理此文件类型"""
        pass

    @abstractmethod
    def extract(self, file_path: Path, repo_root: Path) -> List[CodeFact]:
        """
        从文件提取代码事实

        Returns:
            List[CodeFact]: 提取的事实列表，每个都带精确位置
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> List[str]:
        """返回支持的语言列表，如 ['go', 'c', 'cpp']"""
        pass


class IRouterExtractor(ABC):
    """
    路由提取器接口（专门处理路由识别）

    不同的框架/模式有不同的路由提取器实现。
    """

    @abstractmethod
    def detect_route_type(self, repo_path: Path) -> Optional[str]:
        """
        检测仓库使用的路由类型

        Returns:
            'gin_rest', 'action_dispatch', 'grpc', 'http_mux', None, ...
        """
        pass

    @abstractmethod
    def extract_routes(self, repo_path: Path) -> List[RouteFact]:
        """
        提取所有路由映射

        必须跨文件分析（handler 定义和路由注册可能在不同文件）
        """
        pass


class IConfidenceEngine(ABC):
    """
    置信度引擎接口

    为事实和生成内容打分，标记不确定性。
    """

    @abstractmethod
    def score_fact(self, fact: CodeFact, context: Dict[str, Any]) -> float:
        """
        为单个事实打分

        Returns:
            float: 0.0-1.0
        """
        pass

    @abstractmethod
    def classify_confidence(self, score: float) -> ConfidenceLevel:
        """将分数归类为等级"""
        pass

    @abstractmethod
    def flag_uncertainties(self, facts: List[CodeFact]) -> List[CodeFact]:
        """
        标记不确定的事实

        对低置信度事实添加标记，供后续处理。
        """
        pass


class IPromptBuilder(ABC):
    """
    Prompt 构建器接口

    基于事实构建结构化 Prompt，确保 LLM 不编造。
    """

    @abstractmethod
    def build_overview_prompt(self, facts: List[CodeFact]) -> str:
        """构建项目概览 Prompt"""
        pass

    @abstractmethod
    def build_architecture_prompt(self, facts: List[CodeFact], routes: List[RouteFact]) -> str:
        """构建架构文档 Prompt"""
        pass

    @abstractmethod
    def build_api_prompt(self, routes: List[RouteFact], handlers: List[CodeFact]) -> str:
        """构建 API 文档 Prompt"""
        pass


@dataclass
class VerificationResult:
    """验证结果"""
    is_valid: bool
    hallucinations: List[str]          # 检测到的编造内容
    confidence_drop: float             # 置信度下降值
    suggested_fixes: List[str]         # 建议修正


class IOutputVerifier(ABC):
    """
    输出验证器接口

    验证 LLM 生成内容是否与原始事实一致。
    """

    @abstractmethod
    def verify(self, generated_text: str, source_facts: List[CodeFact]) -> VerificationResult:
        """
        验证生成内容

        Returns:
            VerificationResult: 包含幻觉检测结果
        """
        pass


class IDocumentAssembler(ABC):
    """
    文档组装器接口

    将验证后的内容组装为最终文档。
    """

    @abstractmethod
    def assemble(self, sections: List[DocumentSection], output_path: Path) -> Path:
        """
        组装文档

        Returns:
            Path: 生成的文档路径
        """
        pass


# ═══════════════════════════════════════════════════════════════════════════
# 工厂与注册机制
# ═══════════════════════════════════════════════════════════════════════════

class ExtractorRegistry:
    """
    提取器注册表

    支持动态注册不同语言的提取器。
    """

    _extractors: Dict[str, IASTExtractor] = {}
    _router_extractors: Dict[str, IRouterExtractor] = {}

    @classmethod
    def register(cls, language: str, extractor: IASTExtractor):
        cls._extractors[language] = extractor

    @classmethod
    def register_router(cls, route_type: str, extractor: IRouterExtractor):
        cls._router_extractors[route_type] = extractor

    @classmethod
    def get(cls, file_path: Path) -> Optional[IASTExtractor]:
        suffix = file_path.suffix.lstrip('.')
        return cls._extractors.get(suffix)

    @classmethod
    def get_router_extractor(cls, route_type: str) -> Optional[IRouterExtractor]:
        return cls._router_extractors.get(route_type)

    @classmethod
    def detect_route_type(cls, repo_path: Path) -> Optional[str]:
        """自动检测路由类型"""
        for route_type, extractor in cls._router_extractors.items():
            if extractor.detect_route_type(repo_path):
                return route_type
        return None


# ═══════════════════════════════════════════════════════════════════════════
# 使用示例
# ═══════════════════════════════════════════════════════════════════════════

def example_usage():
    """使用示例 - 展示接口如何协作"""

    # 1. 注册提取器
    # ExtractorRegistry.register('go', GoASTExtractor())
    # ExtractorRegistry.register('c', CASTExtractor())
    # ExtractorRegistry.register_router('gin_rest', GinRouterExtractor())
    # ExtractorRegistry.register_router('action_dispatch', ActionRouterExtractor())

    # 2. 提取代码事实
    # extractor = ExtractorRegistry.get(Path("handler.go"))
    # facts = extractor.extract(Path("handler.go"), repo_root)

    # 3. 置信度评分
    # engine = ConfidenceEngine()
    # for fact in facts:
    #     fact.confidence = engine.score_fact(fact, {})

    # 4. 构建 Prompt
    # prompt_builder = CautiousPromptBuilder()
    # prompt = prompt_builder.build_api_prompt(routes, handlers)

    # 5. 生成并验证
    # llm_output = llm_client.generate(prompt)
    # result = verifier.verify(llm_output, source_facts)

    # 6. 组装文档
    # assembler = MarkdownAssembler()
    # final_path = assembler.assemble(sections, output_path)

    pass


if __name__ == "__main__":
    # 测试数据模型
    fact = CodeFact(
        id="func_create_endpoint",
        fact_type="function",
        name="CreateVPCEndpoint",
        location=CodeLocation("api/endpoint.go", 74, 264),
        source_code="func (a *API) CreateVPCEndpoint(c *gin.Context) {...}",
        source=FactSource.AST_EXTRACTED,
        confidence=1.0,
        metadata={"receiver": "API", "params": ["*gin.Context"], "returns": ["CommonResponse"]}
    )
    print(fact.to_dict())

#!/usr/bin/env python3
"""
置信度引擎 - 为代码事实和生成内容打分

评分维度：
1. 来源可信度（AST > 静态分析 > LLM推断）
2. 完整性（是否有缺失信息）
3. 一致性（与其他事实是否矛盾）
4. 可验证性（能否通过代码验证）
"""

from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from enum import Enum

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import (
    IConfidenceEngine, CodeFact, RouteFact, FactSource,
    ConfidenceLevel, CodeLocation
)


@dataclass
class ConfidenceFactors:
    """置信度分解因子"""
    source_score: float = 1.0      # 来源可信度
    completeness: float = 1.0      # 完整性
    consistency: float = 1.0        # 一致性
    verifiability: float = 1.0    # 可验证性

    def calculate(self) -> float:
        """计算综合置信度"""
        # 加权平均
        weights = [0.4, 0.2, 0.2, 0.2]
        scores = [self.source_score, self.completeness, self.consistency, self.verifiability]
        return sum(w * s for w, s in zip(weights, scores))


class ConfidenceEngine(IConfidenceEngine):
    """
    置信度引擎

    为每个代码事实计算置信度分数，并标记不确定性。
    """

    # 来源基础分
    SOURCE_BASE_SCORE = {
        FactSource.AST_EXTRACTED: 1.0,
        FactSource.STATIC_ANALYSIS: 0.85,
        FactSource.HEURISTIC: 0.6,
        FactSource.LLM_INFERRED: 0.4,
        FactSource.UNKNOWN: 0.2,
    }

    def __init__(self):
        self._fact_index: Dict[str, CodeFact] = {}
        self._conflicts: List[tuple] = []

    def score_fact(self, fact: CodeFact, context: Dict[str, Any]) -> float:
        """
        为单个事实打分
        """
        factors = ConfidenceFactors()

        # 1. 来源可信度
        factors.source_score = self.SOURCE_BASE_SCORE.get(fact.source, 0.2)

        # 2. 完整性检查
        factors.completeness = self._check_completeness(fact)

        # 3. 一致性检查（需要其他事实）
        factors.consistency = self._check_consistency(fact)

        # 4. 可验证性
        factors.verifiability = self._check_verifiability(fact)

        # 计算综合分数
        final_score = factors.calculate()

        # 记录评分详情
        fact.metadata['_confidence_factors'] = {
            'source': factors.source_score,
            'completeness': factors.completeness,
            'consistency': factors.consistency,
            'verifiability': factors.verifiability,
        }
        fact.metadata['_confidence_calculation'] = final_score

        return round(final_score, 3)

    def classify_confidence(self, score: float) -> ConfidenceLevel:
        """将分数归类为置信度等级"""
        for level in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM,
                      ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
            if level.min_val <= score <= level.max_val:
                return level
        return ConfidenceLevel.UNCERTAIN

    def flag_uncertainties(self, facts: List[CodeFact]) -> List[CodeFact]:
        """
        标记不确定的事实

        为低置信度事实添加【需确认】标记。
        """
        flagged = []

        for fact in facts:
            level = self.classify_confidence(fact.confidence)

            if level in [ConfidenceLevel.LOW, ConfidenceLevel.UNCERTAIN]:
                fact.metadata['_requires_verification'] = True
                fact.metadata['_uncertainty_reason'] = self._explain_uncertainty(fact)

            flagged.append(fact)

        return flagged

    def index_facts(self, facts: List[CodeFact]):
        """建立事实索引，用于一致性检查"""
        for fact in facts:
            self._fact_index[fact.id] = fact

    def _check_completeness(self, fact: CodeFact) -> float:
        """检查事实完整性"""
        issues = 0
        max_issues = 3

        # 检查必需字段
        if not fact.name or fact.name == 'unknown':
            issues += 1
        if fact.location.start_line == 0:
            issues += 1
        if not fact.source_code:
            issues += 1

        # 特定类型的完整性检查
        if isinstance(fact, RouteFact):
            if not fact.handler_name:
                issues += 1
            if not fact.path_or_action:
                issues += 1

        # 检查元数据完整性
        if fact.fact_type == 'function':
            if 'params' not in fact.metadata or not fact.metadata['params']:
                issues += 0.5
            if 'returns' not in fact.metadata:
                issues += 0.5

        # 计算分数
        return max(0.0, 1.0 - (issues / max_issues))

    def _check_consistency(self, fact: CodeFact) -> float:
        """检查与其他事实的一致性"""
        if not self._fact_index:
            return 1.0  # 无其他事实可比较

        conflicts = 0

        # 检查同名事实的位置是否冲突
        for other_id, other in self._fact_index.items():
            if other.name == fact.name and other_id != fact.id:
                # 同名但位置不同 - 可能是重载（Go 不支持）或冲突
                if other.location.file != fact.location.file:
                    conflicts += 0.5  # 可能是不同包的同名函数

        # 检查路由事实的 handler 是否存在
        if isinstance(fact, RouteFact):
            handler_exists = any(
                f.name == fact.handler_name and f.fact_type in ['function', 'method']
                for f in self._fact_index.values()
            )
            if not handler_exists:
                conflicts += 0.8  # handler 不存在，严重不一致

        return max(0.0, 1.0 - conflicts)

    def _check_verifiability(self, fact: CodeFact) -> float:
        """检查可验证性"""
        score = 1.0

        # 文件是否存在
        if not Path(fact.location.file).exists():
            score *= 0.5  # 文件不存在，难以验证

        # 行号是否合理
        if fact.location.start_line <= 0:
            score *= 0.7

        # 源代码片段是否足够
        if len(fact.source_code) < 20:
            score *= 0.8

        return score

    def _explain_uncertainty(self, fact: CodeFact) -> str:
        """解释为什么置信度低"""
        reasons = []

        factors = fact.metadata.get('_confidence_factors', {})

        if factors.get('source', 1.0) < 0.6:
            reasons.append("来源可靠性低")

        if factors.get('completeness', 1.0) < 0.7:
            reasons.append("信息不完整")

        if factors.get('consistency', 1.0) < 0.8:
            reasons.append("与其他事实不一致")

        if factors.get('verifiability', 1.0) < 0.8:
            reasons.append("难以验证")

        if isinstance(fact, RouteFact) and not fact.handler_name:
            reasons.append("未找到对应的 handler")

        return "; ".join(reasons) if reasons else "未知原因"


class ConfidenceScorer:
    """
    为 LLM 生成内容打分

    在生成后评估内容质量。
    """

    def __init__(self, engine: ConfidenceEngine):
        self.engine = engine

    def score_generation(
        self,
        generated_text: str,
        source_facts: List[CodeFact],
        content_type: str  # 'overview' | 'architecture' | 'api' | 'module'
    ) -> float:
        """
        为 LLM 生成内容打分

        评分标准：
        1. 与源事实的匹配度（关键）
        2. 格式规范性
        3. 完整性
        4. 幻觉率（编造成分）
        """
        factors = {
            'fact_match': self._check_fact_match(generated_text, source_facts),
            'format_compliance': self._check_format(generated_text, content_type),
            'completeness': self._check_content_completeness(generated_text, source_facts, content_type),
            'hallucination_rate': self._estimate_hallucination(generated_text, source_facts),
        }

        # 权重：事实匹配最重要
        weights = {
            'fact_match': 0.4,
            'format_compliance': 0.2,
            'completeness': 0.2,
            'hallucination_rate': 0.2,
        }

        score = sum(factors[k] * weights[k] for k in factors)
        return round(score, 3)

    def _check_fact_match(self, text: str, facts: List[CodeFact]) -> float:
        """检查文本与事实的匹配度"""
        matches = 0
        total = len(facts)

        for fact in facts:
            # 检查关键信息是否在文本中
            if fact.name in text:
                matches += 1
            elif isinstance(fact, RouteFact):
                if fact.handler_name in text or fact.path_or_action in text:
                    matches += 0.8

        return matches / total if total > 0 else 0.5

    def _check_format(self, text: str, content_type: str) -> float:
        """检查格式合规性"""
        score = 1.0

        # 检查 Markdown 格式
        if not text.startswith('#'):
            score *= 0.9

        # 检查表格（API 和架构文档需要）
        if content_type in ['api', 'architecture']:
            if '|' not in text:
                score *= 0.7  # 缺少表格

        # 检查代码位置标注
        if '`' not in text and content_type != 'overview':
            score *= 0.8  # 缺少代码引用

        return score

    def _check_content_completeness(self, text: str, facts: List[CodeFact], content_type: str) -> float:
        """检查内容完整性"""
        expected_sections = {
            'overview': ['项目', '描述', '技术栈'],
            'architecture': ['架构', '模块', '数据流'],
            'api': ['接口', '方法', '处理函数'],
            'db': ['表名', '字段', '类型'],
        }

        sections = expected_sections.get(content_type, [])
        found = sum(1 for s in sections if s in text)

        return found / len(sections) if sections else 0.8

    def _estimate_hallucination(self, text: str, facts: List[CodeFact]) -> float:
        """
        估算幻觉率

        反向分数：越高表示幻觉越少
        """
        hallucination_signals = [
            # 过于具体但无来源的信息
            r'/api/v\d+/[\w-]+',  # 详细 REST 路径（可能是编的）
            r'默认.*端口.*\d{4,5}',  # 端口号细节
            r'版本.*v\d+\.\d+',  # 版本号细节
        ]

        suspicion = 0
        for pattern in hallucination_signals:
            import re
            matches = re.findall(pattern, text)
            suspicion += len(matches) * 0.1

        # 检查是否有事实支持
        unsupported_claims = 0
        lines = text.split('\n')
        for line in lines:
            if 'api' in line.lower() or 'endpoint' in line.lower():
                # 检查是否有代码位置标注
                if '`' not in line and 'file' not in line.lower():
                    unsupported_claims += 0.05

        hallucination_score = min(1.0, suspicion + unsupported_claims)
        return 1.0 - hallucination_score  # 返回置信度（反向）


# 便捷函数

def calculate_batch_confidence(facts: List[CodeFact]) -> Dict[str, Any]:
    """批量计算置信度，返回统计信息"""
    engine = ConfidenceEngine()
    engine.index_facts(facts)

    scores = []
    levels = {level: 0 for level in ConfidenceLevel}

    for fact in facts:
        score = engine.score_fact(fact, {})
        fact.confidence = score
        scores.append(score)

        level = engine.classify_confidence(score)
        levels[level] += 1

    return {
        'mean': sum(scores) / len(scores) if scores else 0,
        'min': min(scores) if scores else 0,
        'max': max(scores) if scores else 0,
        'distribution': {k.name: v for k, v in levels.items()},
        'needs_review': levels[ConfidenceLevel.LOW] + levels[ConfidenceLevel.UNCERTAIN],
    }


if __name__ == "__main__":
    # 测试
    from interfaces import CodeLocation

    test_facts = [
        CodeFact(
            id="test1",
            fact_type="function",
            name="CreateVPCEndpoint",
            location=CodeLocation("api/endpoint.go", 74, 100),
            source_code="func CreateVPCEndpoint(...)",
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
        ),
        CodeFact(
            id="test2",
            fact_type="route",
            name="ActionCreateEndpoint",
            location=CodeLocation("server.go", 42, 45),
            source_code="",
            source=FactSource.LLM_INFERRED,  # 低可信度来源
            confidence=0.4,
        ),
    ]

    engine = ConfidenceEngine()
    engine.index_facts(test_facts)

    for fact in test_facts:
        score = engine.score_fact(fact, {})
        level = engine.classify_confidence(score)
        print(f"  {fact.name}: {score} ({level.name})")

#!/usr/bin/env python3
"""
输出验证器 - 检测 LLM 生成内容的幻觉

验证策略：
1. 实体对齐：检查提到的函数/类型是否存在于代码事实中
2. 代码位置验证：检查标注的行号是否真实存在
3. 路由路径验证：检查 REST 路径是否有路由注册支持
4. 属性验证：检查描述的类型/参数是否与代码一致
"""

import re
from typing import List, Dict, Set, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import IOutputVerifier, CodeFact, RouteFact, VerificationResult, FactSource


@dataclass
class EntityClaim:
    """文本中提到的实体声明"""
    entity_type: str  # 'function' | 'type' | 'route' | 'file'
    name: str
    claimed_location: Optional[str]  # 声称的位置
    context: str  # 上下文


class OutputVerifier(IOutputVerifier):
    """
    输出验证器

    对比 LLM 生成内容与源代码事实，检测不一致。
    """

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self._fact_lookup: Dict[str, CodeFact] = {}
        self._name_to_facts: Dict[str, List[CodeFact]] = {}

    def _build_index(self, facts: List[CodeFact]):
        """建立事实索引"""
        for fact in facts:
            self._fact_lookup[fact.id] = fact

            # 按名称索引
            if fact.name not in self._name_to_facts:
                self._name_to_facts[fact.name] = []
            self._name_to_facts[fact.name].append(fact)

    def verify(self, generated_text: str, source_facts: List[CodeFact]) -> VerificationResult:
        """
        验证生成内容
        """
        self._build_index(source_facts)

        hallucinations = []
        confidence_drops = []

        # 1. 提取文本中提到的实体
        claims = self._extract_claims(generated_text)

        # 2. 验证每个声明
        for claim in claims:
            is_valid, reason = self._verify_claim(claim, source_facts)
            if not is_valid:
                hallucinations.append(f"{claim.name}: {reason}")
                confidence_drops.append(0.2)  # 每个幻觉降低 0.2

        # 3. 检查 REST 路径声明（高风险区域）
        path_hallucinations = self._check_route_paths(generated_text, source_facts)
        hallucinations.extend(path_hallucinations)

        # 4. 检查代码位置标注
        location_issues = self._check_code_locations(generated_text)
        hallucinations.extend(location_issues)

        # 计算最终置信度
        total_drop = sum(confidence_drops) + len(path_hallucinations) * 0.3 + len(location_issues) * 0.15
        confidence_drop = min(0.9, total_drop)

        # 生成建议修正
        suggested_fixes = self._suggest_fixes(hallucinations, generated_text)

        return VerificationResult(
            is_valid=len(hallucinations) == 0,
            hallucinations=hallucinations,
            confidence_drop=confidence_drop,
            suggested_fixes=suggested_fixes
        )

    def _extract_claims(self, text: str) -> List[EntityClaim]:
        """从文本提取实体声明"""
        claims = []

        # 匹配函数引用：CreateVPCEndpoint
        func_pattern = r'(?:func|函数)\s+`?(\w+)`?'
        for match in re.finditer(func_pattern, text, re.IGNORECASE):
            name = match.group(1)
            context = text[max(0, match.start() - 50):match.end() + 50]
            claims.append(EntityClaim('function', name, None, context))

        # 匹配代码位置：`file.go:123` 或 file.go:123
        location_pattern = r'`?(\w+\.go):(\d+)`?'
        for match in re.finditer(location_pattern, text):
            file_name = match.group(1)
            line_no = int(match.group(2))

            # 查找这个位置提到的实体
            surrounding = text[max(0, match.start() - 100):min(len(text), match.end() + 100)]

            # 尝试提取函数名（通常在位置标注前）
            func_match = re.search(r'(\w+)\s+`?' + re.escape(match.group(0)), surrounding)
            if func_match:
                claims.append(EntityClaim(
                    'function',
                    func_match.group(1),
                    f"{file_name}:{line_no}",
                    surrounding
                ))

        return claims

    def _verify_claim(self, claim: EntityClaim, facts: List[CodeFact]) -> Tuple[bool, str]:
        """验证单个声明"""

        # 检查名称是否存在
        matching_facts = self._name_to_facts.get(claim.name, [])

        if not matching_facts:
            return False, f"未找到名为 '{claim.name}' 的代码实体"

        # 如果声明了位置，验证位置
        if claim.claimed_location:
            claimed_file, claimed_line = self._parse_location(claim.claimed_location)

            # 检查是否有事实匹配这个位置
            location_match = False
            for fact in matching_facts:
                if (claimed_file in fact.location.file and
                    abs(fact.location.start_line - claimed_line) <= 5):  # 允许 5 行误差
                    location_match = True
                    break

            if not location_match:
                actual_locations = [f.location for f in matching_facts]
                return False, f"位置不匹配。声称: {claim.claimed_location}, 实际: {actual_locations}"

        return True, "OK"

    def _check_route_paths(self, text: str, facts: List[CodeFact]) -> List[str]:
        """
        专门检查 REST 路径声明

        这是最容易产生幻觉的地方。
        """
        issues = []

        # 匹配 REST 路径模式
        path_patterns = [
            r'`(/api/[\w\-/]+)`',  # `/api/v1/endpoint`
            r'\|(/api/[\w\-/]+)\|',  # 表格中的路径
            r'路径[：:]\s*[`\']?(/[\w\-/]+)',  # "路径: /api/..."
        ]

        declared_paths = set()
        for pattern in path_patterns:
            for match in re.finditer(pattern, text):
                declared_paths.add(match.group(1))

        if not declared_paths:
            return issues  # 没有声明路径，无需检查

        # 获取实际的路由事实
        actual_routes = [f for f in facts if isinstance(f, RouteFact)]
        actual_paths = set()

        for route in actual_routes:
            if route.route_type == 'rest':
                actual_paths.add(route.path_or_action)
            elif route.route_type == 'action':
                # Action 路由不应该有 REST 路径
                pass

        # 检查每个声明的路径
        for path in declared_paths:
            if path not in actual_paths:
                # 检查是否有 Action 路由（说明这是 Action 分发系统）
                has_action_routes = any(r.route_type == 'action' for r in actual_routes)

                if has_action_routes:
                    issues.append(
                        f"编造 REST 路径 '{path}'。实际使用 Action 字段路由，"
                        f"不应有 REST 路径声明。"
                    )
                else:
                    issues.append(
                        f"未验证的 REST 路径 '{path}'。未在路由注册中找到。"
                    )

        return issues

    def _check_code_locations(self, text: str) -> List[str]:
        """检查代码位置标注是否真实"""
        issues = []

        # 匹配 file.go:123 格式
        location_pattern = r'`?(\w+\.go):(\d+)(?:-(\d+))?`?'

        for match in re.finditer(location_pattern, text):
            file_name = match.group(1)
            start_line = int(match.group(2))

            # 构建完整路径
            file_path = self.repo_path / file_name
            if not file_path.exists():
                # 尝试在子目录中找
                found = False
                for subdir in ['api', 'internal', 'cmd', 'db']:
                    alt_path = self.repo_path / subdir / file_name
                    if alt_path.exists():
                        file_path = alt_path
                        found = True
                        break
                if not found:
                    issues.append(f"文件不存在: {file_name}")
                    continue

            # 检查行号是否合理
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    lines = f.readlines()
                    if start_line > len(lines):
                        issues.append(
                            f"行号超出范围: {file_name}:{start_line} (文件共 {len(lines)} 行)"
                        )
            except Exception as e:
                issues.append(f"无法验证 {file_name}: {e}")

        return issues

    def _parse_location(self, location_str: str) -> Tuple[str, int]:
        """解析位置字符串"""
        parts = location_str.split(':')
        if len(parts) >= 2:
            return parts[0], int(parts[1])
        return location_str, 0

    def _suggest_fixes(self, hallucinations: List[str], original_text: str) -> List[str]:
        """生成修正建议"""
        fixes = []

        for h in hallucinations:
            if "REST 路径" in h and "Action 字段路由" in h:
                fixes.append(
                    "将 REST 路径改为 Action 字段描述，例如："
                    "'ActionCreateVPCEndpoint 分发到 CreateVPCEndpoint handler'"
                )
            elif "位置不匹配" in h:
                fixes.append("修正代码位置标注，使用 AST 提取的精确位置")
            elif "未找到" in h:
                fixes.append("删除或确认该实体名称，可能是拼写错误或已删除的代码")
            elif "行号超出范围" in h:
                fixes.append("更新行号，代码可能已修改")

        if not fixes and hallucinations:
            fixes.append("建议人工复核生成内容，标注【需验证】")

        return fixes


# 便捷函数

def quick_verify(
    generated_text: str,
    repo_path: Path,
    source_facts: List[CodeFact]
) -> Tuple[bool, List[str]]:
    """
    快速验证生成内容

    Returns:
        (是否通过, 问题列表)
    """
    verifier = OutputVerifier(repo_path)
    result = verifier.verify(generated_text, source_facts)

    return result.is_valid, result.hallucinations


if __name__ == "__main__":
    # 测试
    test_text = """
# API 文档

| 接口路径 | 方法 | 处理函数 |
|---------|------|---------|
| /api/v1/users | GET | GetUsers |

GetUsers 在 `api/users.go:45` 实现。
"""

    from interfaces import CodeLocation

    # 模拟事实：实际是 Action 路由，不是 REST
    test_facts = [
        RouteFact(
            id="route1",
            fact_type="route",
            name="ActionGetUsers",
            location=CodeLocation("api.go", 50, 55),
            source_code="case ActionGetUsers: resp = a.GetUsers(c)",
            source=FactSource.AST_EXTRACTED,
            confidence=1.0,
            route_type='action',
            path_or_action='ActionGetUsers',
            method='POST',
            handler_name='GetUsers',
        )
    ]

    # 创建临时目录作为 repo_path
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        verifier = OutputVerifier(Path(tmpdir))
        result = verifier.verify(test_text, test_facts)

        print(f"验证结果: {'通过' if result.is_valid else '未通过'}")
        print(f"幻觉检测: {result.hallucinations}")
        print(f"置信度下降: {result.confidence_drop}")
        print(f"建议修正: {result.suggested_fixes}")

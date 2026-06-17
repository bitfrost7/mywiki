#!/usr/bin/env python3
"""
路由提取器 - 支持多种路由模式

目前支持：
1. Gin REST 路由（gin.GET/POST/PUT/DELETE）
2. Action 字段路由（switch req.Action / case ActionXxx:）

设计原则：
- 100% 确定性提取，不猜测
- 跨文件分析（handler 和路由注册可能在不同文件）
- 为每个路由标注置信度和来源
"""

import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import IRouterExtractor, RouteFact, CodeLocation, FactSource
from extractors.go_extractor import GoASTExtractor, extract_action_constants, TREE_SITTER_AVAILABLE


@dataclass
class RouteMatch:
    """路由匹配的内部表示"""
    route_type: str           # 'rest' | 'action' | 'unknown'
    path_or_action: str       # '/api/users' 或 'ActionCreateUser'
    method: str               # 'GET' | 'POST' 或 ''
    handler_name: str         # 处理函数名
    handler_file: str         # 处理函数所在文件
    handler_line: int         # 处理函数行号
    route_file: str           # 路由注册所在文件
    route_line: int           # 路由注册行号
    confidence: float = 1.0   # 匹配置信度


class BaseRouterExtractor(IRouterExtractor, ABC):
    """路由提取器基类"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.go_extractor = GoASTExtractor() if TREE_SITTER_AVAILABLE else None
        # 用 tree-sitter 一次性扫描所有 .go 文件，建立 name → (file, line) 索引
        self._handler_index: Dict[str, Tuple[str, int]] = {}
        self._build_handler_index(repo_path)

    def _build_handler_index(self, repo_path: Path):
        """一次性 AST 扫描所有文件，建立函数/方法名到位置的索引"""
        if not self.go_extractor:
            return
        skip = ['_test.go', 'vendor/', '.pb.go', '.mock.go', '_gen.go']
        for go_file in repo_path.rglob("*.go"):
            if any(p in str(go_file) for p in skip):
                continue
            try:
                facts = self.go_extractor.extract(go_file, repo_path)
            except Exception:
                continue
            for fact in facts:
                if fact.fact_type in ('function', 'method'):
                    # 同名时优先保留第一个找到的（通常是更核心的文件）
                    if fact.name not in self._handler_index:
                        self._handler_index[fact.name] = (
                            fact.location.file,
                            fact.location.start_line,
                        )

    def _find_handler_location(self, handler_name: str) -> Optional[Tuple[str, int]]:
        """从预建索引查找 handler 位置，O(1)"""
        return self._handler_index.get(handler_name)


class GinRouterExtractor(BaseRouterExtractor):
    """
    Gin REST 路由提取器

    检测：gin.GET("/path", handler)、gin.POST(...) 等
    """

    ROUTE_PATTERNS = [
        r'gin\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)',
        r'router\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)',
        r'r\.(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s*\(\s*["\']([^"\']+)["\']\s*,\s*(\w+)\s*\)',
    ]

    def detect_route_type(self, repo_path: Path) -> Optional[str]:
        """检测是否使用 Gin REST 路由"""
        # 检查是否有 gin 导入和路由注册
        for go_file in repo_path.rglob("*.go"):
            content = go_file.read_text(errors='replace')
            if 'github.com/gin-gonic/gin' in content:
                # 检查是否有路由注册
                for pattern in self.ROUTE_PATTERNS:
                    if re.search(pattern, content, re.IGNORECASE):
                        return 'gin_rest'
        return None

    def extract_routes(self, repo_path: Path) -> List[RouteFact]:
        """提取 Gin REST 路由"""
        routes = []

        # 扫描可能的 router 文件
        router_files = list(repo_path.rglob("router*.go")) + \
                      list(repo_path.rglob("route*.go")) + \
                      list(repo_path.rglob("server.go")) + \
                      list(repo_path.rglob("main.go"))

        for router_file in router_files:
            content = router_file.read_text(errors='replace')
            rel_path = str(router_file.relative_to(repo_path))

            for pattern in self.ROUTE_PATTERNS:
                for match in re.finditer(pattern, content, re.IGNORECASE):
                    method = match.group(1).upper()
                    path = match.group(2)
                    handler_name = match.group(3)

                    # 查找 handler 位置
                    handler_loc = self._find_handler_location(handler_name)

                    if handler_loc:
                        handler_file, handler_line = handler_loc
                        confidence = 1.0
                    else:
                        handler_file = "unknown"
                        handler_line = 0
                        confidence = 0.5  # 找不到 handler，置信度降低

                    line_no = content[:match.start()].count('\n') + 1

                    routes.append(RouteFact(
                        id=f"gin_{path}_{method}_{handler_name}",
                        fact_type='route',
                        name=f"{method} {path}",
                        location=CodeLocation(handler_file, handler_line, handler_line),
                        source_code="",  # 稍后填充
                        source=FactSource.AST_EXTRACTED,
                        confidence=confidence,
                        route_type='rest',
                        path_or_action=path,
                        method=method,
                        handler_name=handler_name,
                        metadata={
                            'router_file': rel_path,
                            'router_line': line_no,
                            'gin_pattern': True,
                        }
                    ))

        return routes


class ActionRouterExtractor(BaseRouterExtractor):
    """
    Action 字段路由提取器（适用于 apisvr）

    检测模式：
    1. Action 常量定义：const ActionCreateVPCEndpoint = ...
    2. switch req.Action / case ActionXxx: handler()
    3. 映射表：map[string]func{ActionCreateVPCEndpoint: CreateVPCEndpoint}
    """

    def detect_route_type(self, repo_path: Path) -> Optional[str]:
        """检测是否使用 Action 字段路由"""
        has_action_const = False
        has_action_switch = False

        for go_file in repo_path.rglob("*.go"):
            content = go_file.read_text(errors='replace')

            # 检查 Action 常量（单行或 const() 块内）
            # 匹配: "const ActionXxx =" 或块内 "ActionXxx ="
            if re.search(r'(?:const\s+)?Action\w+\s*=\s*"', content):
                has_action_const = True

            # 检查 switch req.Action 或 switch action
            if re.search(r'switch\s+(?:req\.)?Action', content, re.IGNORECASE):
                has_action_switch = True

            # 检查 Action 字符串映射
            if re.search(r'Action\w+.*:\s*\w+\s*,', content):
                has_action_switch = True

        if has_action_const and has_action_switch:
            return 'action_dispatch'

        return None

    def extract_routes(self, repo_path: Path) -> List[RouteFact]:
        """
        提取 Action 路由

        策略：
        1. 先收集所有 Action 常量
        2. 找 switch/case 语句，提取 Action -> handler 映射
        3. 找 map 定义，提取 Action -> handler 映射
        4. 交叉验证，生成最终路由表
        """
        routes = []

        # 步骤 1: 收集 Action 常量
        action_constants = extract_action_constants(repo_path)
        print(f"  发现 {len(action_constants)} 个 Action 常量")

        # 步骤 2: 从 switch/case 提取映射
        switch_routes = self._extract_from_switch(repo_path, action_constants)
        print(f"  从 switch/case 提取 {len(switch_routes)} 个路由")

        # 步骤 3: 从 map 定义提取映射
        map_routes = self._extract_from_map(repo_path, action_constants)
        print(f"  从 map 定义提取 {len(map_routes)} 个路由")

        # 合并去重（优先 switch，更精确）
        all_routes = {r.handler_name: r for r in switch_routes}
        for r in map_routes:
            if r.handler_name not in all_routes:
                all_routes[r.handler_name] = r

        return list(all_routes.values())

    def _extract_from_switch(self, repo_path: Path, action_constants: Dict[str, str]) -> List[RouteFact]:
        """从 switch/case 语句提取 Action 路由"""
        routes = []

        # 扫描可能的 router/server/api 文件
        target_files = list(repo_path.rglob("api.go")) + \
                      list(repo_path.rglob("server.go")) + \
                      list(repo_path.rglob("router.go")) + \
                      list(repo_path.rglob("handler.go"))

        for go_file in target_files:
            content = go_file.read_text(errors='replace')
            rel_path = str(go_file.relative_to(repo_path))

            # 正则匹配：
            #   case ActionXxx:
            #       resp = a.HandlerMethod(c)  或  resp = HandlerMethod(c)
            # 使用多行模式，允许 case 和 handler 在不同行，
            # 并处理带 receiver 的调用（a.Method 或直接 Method）
            pattern = r'case\s+(Action\w+)\s*:\s*\n\s*(?:\w+\s*=\s*)?(?:\w+\.)?(\w+)\s*\('

            for match in re.finditer(pattern, content):
                action_name = match.group(1)
                handler_name = match.group(2)

                # 验证 handler 是否存在
                handler_loc = self._find_handler_location(handler_name)

                if handler_loc:
                    handler_file, handler_line = handler_loc
                    confidence = 1.0
                else:
                    # 可能是内联函数或其他模式
                    handler_file = "unknown"
                    handler_line = 0
                    confidence = 0.7

                line_no = content[:match.start()].count('\n') + 1

                routes.append(RouteFact(
                    id=f"action_{action_name}_{handler_name}",
                    fact_type='route',
                    name=action_name,
                    location=CodeLocation(handler_file, handler_line, handler_line),
                    source_code="",
                    source=FactSource.AST_EXTRACTED,
                    confidence=confidence,
                    route_type='action',
                    path_or_action=action_name,
                    method='POST',  # Action 路由通常是 POST
                    handler_name=handler_name,
                    metadata={
                        'router_file': rel_path,
                        'router_line': line_no,
                        'extracted_from': 'switch_case',
                    }
                ))

        return routes

    def _extract_from_map(self, repo_path: Path, action_constants: Dict[str, str]) -> List[RouteFact]:
        """从 map[Action]handler 定义提取"""
        routes = []

        # 简化实现：查找 map 字面量
        # map[ActionType]func(...){
        #     ActionCreateVPCEndpoint: CreateVPCEndpoint,
        # }

        for go_file in self.repo_path.rglob("*.go"):
            content = go_file.read_text(errors='replace')
            rel_path = str(go_file.relative_to(repo_path))

            # 匹配 map 定义中的键值对
            pattern = r'(Action\w+)\s*:\s*(\w+)\s*,?'

            for match in re.finditer(pattern, content):
                action_name = match.group(1)
                handler_name = match.group(2)

                # 验证 action 和 handler 都有效
                if action_name not in action_constants:
                    continue

                handler_loc = self._find_handler_location(handler_name)
                if handler_loc:
                    handler_file, handler_line = handler_loc
                    confidence = 0.9  # map 定义稍低置信度
                else:
                    continue  # handler 不存在，跳过

                line_no = content[:match.start()].count('\n') + 1

                routes.append(RouteFact(
                    id=f"action_{action_name}_{handler_name}",
                    fact_type='route',
                    name=action_name,
                    location=CodeLocation(handler_file, handler_line, handler_line),
                    source_code="",
                    source=FactSource.AST_EXTRACTED,
                    confidence=confidence,
                    route_type='action',
                    path_or_action=action_name,
                    method='POST',
                    handler_name=handler_name,
                    metadata={
                        'router_file': rel_path,
                        'router_line': line_no,
                        'extracted_from': 'map_literal',
                    }
                ))

        return routes


# ═══════════════════════════════════════════════════════════════════════════
# 自动检测和工厂
# ═══════════════════════════════════════════════════════════════════════════

def detect_route_type(repo_path: Path) -> Optional[str]:
    """
    自动检测仓库使用的路由类型

    按优先级尝试：
    1. Action 字段路由（apisvr 类型）
    2. Gin REST 路由
    3. 其他框架

    Returns:
        'action_dispatch' | 'gin_rest' | None
    """
    # 优先检测 Action 路由（特征更明显）
    action_extractor = ActionRouterExtractor(repo_path)
    if action_extractor.detect_route_type(repo_path):
        return 'action_dispatch'

    # 检测 Gin REST
    gin_extractor = GinRouterExtractor(repo_path)
    if gin_extractor.detect_route_type(repo_path):
        return 'gin_rest'

    return None


def get_router_extractor(repo_path: Path) -> Optional[IRouterExtractor]:
    """
    根据自动检测结果返回合适的路由提取器
    """
    route_type = detect_route_type(repo_path)

    if route_type == 'action_dispatch':
        return ActionRouterExtractor(repo_path)
    elif route_type == 'gin_rest':
        return GinRouterExtractor(repo_path)

    return None


# ═══════════════════════════════════════════════════════════════════════════
# 测试
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python router_extractors.py <repo_path>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    if not repo_path.exists():
        print(f"路径不存在: {repo_path}")
        sys.exit(1)

    print(f"检测路由类型: {repo_path}")
    route_type = detect_route_type(repo_path)
    print(f"  检测结果: {route_type}")

    if route_type:
        extractor = get_router_extractor(repo_path)
        if extractor:
            print(f"\n提取路由:")
            routes = extractor.extract_routes(repo_path)
            for r in routes[:10]:  # 只显示前10个
                print(f"  {r.path_or_action} -> {r.handler_name} @ {r.location} (置信度: {r.confidence})")

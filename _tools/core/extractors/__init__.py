#!/usr/bin/env python3
"""
AST 提取器模块

提供基于 Tree-sitter 的多语言代码事实提取。
"""

from .go_extractor import GoASTExtractor
from .router_extractors import (
    GinRouterExtractor,
    ActionRouterExtractor,
    detect_route_type,
    get_router_extractor,
)

# C 提取器（待实现）
# from .c_extractor import CASTExtractor

__all__ = [
    'GoASTExtractor',
    # 'CASTExtractor',  # 待实现
    'GinRouterExtractor',
    'ActionRouterExtractor',
    'detect_route_type',
    'get_router_extractor',
]

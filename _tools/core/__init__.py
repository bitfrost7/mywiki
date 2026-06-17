#!/usr/bin/env python3
"""
Core - 确定性代码知识提取系统

包含：
- extractors: AST 提取器 (Go/C/...)
- confidence: 置信度引擎
- generator: 文档生成器
"""

# 避免循环导入，不在顶层导入
# 各子模块自行导入

__all__ = [
    'CodeFact', 'RouteFact', 'FactSource', 'ConfidenceLevel',
    'DocumentSection', 'CodeLocation',
]

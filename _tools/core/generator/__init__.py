#!/usr/bin/env python3
"""
文档生成器模块

基于事实生成知识库文档，确保不编造。
"""

from .prompt_builder import CautiousPromptBuilder
from .doc_assembler import MarkdownAssembler
from .pipeline_v2 import KnowledgeGenerator

__all__ = [
    'CautiousPromptBuilder',
    'MarkdownAssembler',
    'KnowledgeGenerator',
]

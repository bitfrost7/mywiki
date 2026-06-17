#!/usr/bin/env python3
"""
Markdown 文档组装器

将生成的章节组装为最终文档。
"""

from pathlib import Path
from typing import List

# 处理导入路径
import sys
from pathlib import Path
core_path = Path(__file__).parent.parent
if str(core_path) not in sys.path:
    sys.path.insert(0, str(core_path))

from interfaces import IDocumentAssembler, DocumentSection


class MarkdownAssembler(IDocumentAssembler):
    """Markdown 文档组装器"""

    def assemble(self, sections: List[DocumentSection], output_path: Path) -> Path:
        """组装文档"""
        lines = []

        for section in sections:
            lines.append(section.render())
            lines.append("\n---\n")

        # 写入文件
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("\n".join(lines), encoding='utf-8')

        return output_path

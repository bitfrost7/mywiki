#!/usr/bin/env python3
"""
Knowledge Generator V2 - 启动器

正确处理导入路径，支持命令行直接运行。

用法:
    python run_pipeline_v2.py --system privatelink --repo apisvr
"""

import sys
import os
from pathlib import Path

# 添加 core 目录到 Python 路径
core_path = Path(__file__).parent / 'core'
sys.path.insert(0, str(core_path))

# 现在可以正常导入
try:
    from generator.pipeline_v2 import main
    exit(main())
except ImportError as e:
    print(f"导入错误: {e}")
    print("\n请确保已安装依赖:")
    print("  pip install tree-sitter tree-sitter-go")
    exit(1)

#!/usr/bin/env python3
"""
Knowledge Generator V2 - 主入口

修复导入路径，支持命令行直接运行。
"""

import sys
import os

# 添加 core 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

# 现在可以导入
from generator.pipeline_v2 import main

if __name__ == "__main__":
    exit(main())

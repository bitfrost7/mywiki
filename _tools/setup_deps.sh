#!/bin/bash
# 安装 Knowledge Generator V2 依赖
# tree-sitter 需要安装在 mise 管理的 python 3.11 环境中

# 找到 mise python 3.11 的路径
PYTHON311=$(mise which python 2>/dev/null || echo "")
if [ -z "$PYTHON311" ]; then
    PYTHON311=$(ls ~/.local/share/mise/installs/python/3.11.*/bin/python3.11 2>/dev/null | head -1)
fi

if [ -z "$PYTHON311" ]; then
    echo "错误: 找不到 mise python 3.11，请先运行: mise install python@3.11"
    exit 1
fi

echo "使用 Python: $PYTHON311"
echo ""
echo "安装 Tree-sitter 依赖..."
$PYTHON311 -m pip install tree-sitter tree-sitter-go

echo ""
echo "验证安装..."
$PYTHON311 -c "
from tree_sitter import Language, Parser
from tree_sitter_go import language as go_lang
lang = Language(go_lang())
parser = Parser(lang)
print('✓ Tree-sitter 安装成功')
"

echo ""
echo "现在可以运行:"
echo "  export LLM_API_KEY=your_key"
echo "  $PYTHON311 _tools/run_pipeline_v2.py --system privatelink --repo apisvr"

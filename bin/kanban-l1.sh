#!/bin/bash
# mywiki L1/L2/L3 编译管线 — Orchestrator 入口
#
# 分层:
#   脚本 (bin/analyze.sh):  L1 枚举 — 确定性的
#   LLM (analyst worker):   L2 分组 + L3 业务流/概念 — 有价值的
#   LLM (writer/reviewer):  写文档 + 审查
#
# 用法: ./bin/kanban-l1.sh apisvr

set -euo pipefail

SVC="${1:?用法: $0 <service-name>}"
VAULT="$HOME/Documents/Code/work/mywiki"
AST_DIR="$VAULT/raw/assets/ast/privatelink/$SVC/graphify-out"
GRAPH_JSON="$AST_DIR/graph.json"

if [ ! -f "$GRAPH_JSON" ]; then
  echo "❌ graph.json 不存在: $GRAPH_JSON"
  echo "→ 先运行: python3 bin/sync_code.py --repo privatelink/$SVC"
  exit 1
fi

echo "═══ mywiki L1/L2/L3 编译管线 — $SVC ═══"
echo ""

# ── Step 1: L1 枚举（脚本，确定性） ──
echo "① [脚本] L1 枚举..."
L1_JSON=$(bash "$VAULT/bin/analyze.sh" "$GRAPH_JSON" | python3 -c "import sys,json;print(json.dumps(json.load(sys.stdin)))") || {
  echo "❌ 分析失败"; exit 1
}
ACTION_COUNT=$(echo "$L1_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['action_count'])")
MODULE_COUNT=$(echo "$L1_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['module_count'])")
echo "   ✓ $ACTION_COUNT 个接口, $MODULE_COUNT 个模块"
echo ""

# ── Step 2: 创建 analyst 卡（LLM 做 L2+L3） ──
echo "② [LLM] 创建 analyst 卡..."
ANALYST_ID=$(hermes kanban create "analyst: $SVC" \
  --assignee analyst --skill analyst-sk \
  --workspace "dir:$VAULT" \
  --body "service=$SVC
graph_json=$GRAPH_JSON
source_dir=$VAULT/raw/assets/repo/privatelink/$SVC
output_dir=$VAULT/Wiki/privatelink/$SVC
templates_dir=$VAULT/templates
discuss_path=$VAULT/raw/assets/privatelink/$SVC/discuss
l1_json=$L1_JSON" \
  --json 2>/dev/null | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])" 2>/dev/null || echo "")

echo "   ✓ $ANALYST_ID"
echo ""

hermes kanban dispatch > /dev/null 2>&1 || true

echo "═══ 管线已启动 ═══"
echo ""
echo "analyst → writer ×N → reviewer ×N → synthesis → final-review ×4"
echo ""
echo "跟踪:"
echo "  hermes kanban list"
echo "  hermes kanban tail $ANALYST_ID"

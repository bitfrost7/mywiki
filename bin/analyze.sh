#!/bin/bash
# analyze.sh — L1 枚举: 读 graph.json → 输出 actions/modules JSON
# 用法: bash analyze.sh <graph-json-path>
# 输出: {"actions":[...], "action_files":{...}, "modules":[...]}

set -euo pipefail
GRAPH_JSON="${1:?}"

python3 - "$GRAPH_JSON" << 'PYEOF'
import json, sys
with open(sys.argv[1]) as f:
    g = json.load(f)
nodes = g.get('nodes', [])
actions, action_files = {}, {}
modules = set()
noise = {'proto','vendor','third_party','mock','mocks','test','tests','docs','example'}

for n in nodes:
    sf = n.get('source_file') or ''
    label = n.get('label') or ''
    if sf.endswith('.go') and sf.startswith('api/') and label.endswith('Req'):
        a = sf[4:-3]
        if a not in actions:
            actions[a] = sf
    if sf.endswith('.go'):
        top = sf.split('/')[0]
        if top not in ('api','') and top not in noise and '.' not in top:
            modules.add(top)

print(json.dumps({
    'actions': sorted(actions.keys()),
    'action_count': len(actions),
    'action_files': {a: actions[a] for a in sorted(actions)},
    'modules': sorted(modules),
    'module_count': len(modules),
}, indent=2))
PYEOF

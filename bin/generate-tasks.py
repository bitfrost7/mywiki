#!/usr/bin/env python3
"""Generate task.json from l1_json output.

Called by mywiki-code-import workflow's generate_tasks step.

Usage:
  python3 bin/generate-tasks.py <vault> <service> [l1_json_file]

If l1_json_file is omitted, reads from stdin (piped from analyze.sh).
If task.json already exists, just reads and prints it.
"""
import json, os, sys

vault = sys.argv[1]
service = sys.argv[2]
task_file = f"{vault}/raw/assets/privatelink/{service}/task.json"

# If task.json already exists, just re-read it
if os.path.isfile(task_file):
    with open(task_file) as f:
        print(json.dumps(json.load(f)))
    sys.exit(0)

# Read l1_json from file or stdin
if len(sys.argv) >= 4:
    with open(sys.argv[3]) as f:
        l1 = json.load(f)
else:
    l1 = json.load(sys.stdin)

tasks = []
for a in l1.get("actions", []):
    src = l1.get("action_files", {}).get(a, f"api/{a}.go")
    tasks.append({
        "title": f"interfaces/{a}",
        "skill": "interface-sk",
        "action": a,
        "doc_files": [f"interfaces/{a}.md"],
        "source_files": [src],
    })
for m in l1.get("modules", []):
    tasks.append({
        "title": f"modules/{m}",
        "skill": "module-sk",
        "action": "",
        "doc_files": [f"modules/{m}.md"],
        "source_files": [],
    })

os.makedirs(f"{vault}/raw/assets/privatelink/{service}", exist_ok=True)
with open(task_file, "w") as f:
    json.dump({"tasks": tasks}, f, indent=2)

print(json.dumps({"tasks": tasks}))

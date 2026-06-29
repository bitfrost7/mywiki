#!/usr/bin/env python3
"""
mywiki 管线编排器 — 确定性的流程编排，Agent 只做内容。

流程:
  ① analyze.sh → l1_json
  ② 创建 analyst 卡 → 等待完成 → 产出 task.json
  ③ 读 task.json，批量创 writer + reviewer 卡（parent 链）
  ④ 轮询所有 reviewer → done
  ⑤ 检查 discuss → 有 open 则创 fix + re-review
  ⑥ 重复④⑤ 直到全部 resolved
"""

import json, os, subprocess, sys, time, argparse, signal

BASE = os.path.expanduser("~/Documents/Code/work/mywiki")
DISCUSS_BIN = os.path.join(BASE, "bin/discuss")
ANALYZE_SH  = os.path.join(BASE, "bin/analyze.sh")
WS = "dir:" + BASE
POLL_INTERVAL = 15  # 秒

# 跟踪所有创建的卡，用于 Ctrl-C 清理
_all_card_ids = []

def cleanup(signum=None, frame=None):
    """中断时清理所有已创建的板子"""
    if not _all_card_ids:
        sys.exit(1)
    print(f"\n\n⚠️  收到中断，清理 {len(_all_card_ids)} 张卡...")
    for cid in _all_card_ids:
        # reclaim 先（如果是 running）
        subprocess.run(["hermes", "kanban", "reclaim", cid],
                       capture_output=True)
        subprocess.run(["hermes", "kanban", "archive", cid],
                       capture_output=True)
    print("✅ 清理完成")
    sys.exit(1)

signal.signal(signal.SIGINT, cleanup)

# ── helpers ──

def hermes(*args):
    """运行 hermes CLI 命令，返回 stdout"""
    r = subprocess.run(["hermes"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"⚠️  hermes 返回 {r.returncode}: {r.stderr.strip()}", file=sys.stderr)
    return r.stdout.strip()

def hermes_json(*args):
    """运行 hermes CLI 命令，返回解析后的 JSON"""
    r = subprocess.run(["hermes"] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        print(f"⚠️  hermes JSON 返回 {r.returncode}: {r.stderr.strip()}", file=sys.stderr)
        return {}
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        return {}

def card_status(card_id):
    """返回卡的状态字符串（done/ready/running/blocked/archived 等）"""
    r = subprocess.run(["hermes", "kanban", "show", card_id],
                       capture_output=True, text=True)
    for line in r.stdout.split("\n"):
        if line.strip().startswith("status:"):
            return line.strip().split(":", 1)[1].strip()
    return "unknown"

def discuss(*args):
    env = os.environ.copy()
    env["HERMES_PROFILE"] = "admin"  # 编排脚本是可信的
    r = subprocess.run([DISCUSS_BIN] + list(args), capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

# ── 步骤 ──

def step1_analyze(service):
    """① 确定性分析 → l1_json"""
    graph_json = os.path.join(BASE, f"raw/assets/ast/privatelink/{service}/graphify-out/graph.json")
    if not os.path.exists(graph_json):
        print(f"❌ graph.json 不存在: {graph_json}")
        print(f"   先运行: python3 bin/sync_code.py --repo privatelink/{service}")
        sys.exit(1)

    r = subprocess.run(["bash", ANALYZE_SH, graph_json], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"❌ analyze.sh 失败: {r.stderr}")
        sys.exit(1)
    l1 = json.loads(r.stdout)
    print(f"① 分析完成: {l1['action_count']} 接口, {l1['module_count']} 模块")
    return l1

def step2_generate_tasks(service, l1_json, discuss_path):
    """② 从 l1_json 生成 task.json"""
    task_json_path = os.path.join(BASE, f"raw/assets/privatelink/{service}/task.json")

    # 缓存命中
    if os.path.exists(task_json_path):
        print(f"② 读取缓存 task.json")
        with open(task_json_path) as f:
            tasks_full = json.load(f)
        tasks = tasks_full.get("tasks", tasks_full if isinstance(tasks_full, list) else [])
        print(f"   读入 {len(tasks)} 个任务")
        return tasks, discuss_path

    # init discuss
    print(f"② 初始化 discuss 数据库...")
    rc, out, err = discuss("init", discuss_path, service)
    print(f"   {'✅' if rc==0 else '⚠️'} {out}")

    # 生成 task.json
    print(f"   生成 task.json...")
    tasks = []
    for action in l1_json.get("actions", []):
        src = l1_json.get("action_files", {}).get(action, f"api/{action}.go")
        tasks.append({
            "id": f"t_{len(tasks)+1}",
            "title": f"interfaces/{action}",
            "skill": "interface-sk",
            "actions": [action],
            "modules": [],
            "doc_files": [f"interfaces/{action}.md"],
            "source_files": [src],
            "line_count": 0,
        })
    for mod in l1_json.get("modules", []):
        tasks.append({
            "id": f"t_{len(tasks)+1}",
            "title": f"modules/{mod}",
            "skill": "module-sk",
            "actions": [],
            "modules": [mod],
            "doc_files": [f"modules/{mod}.md"],
            "source_files": [],
            "line_count": 0,
        })
    with open(task_json_path, "w") as f:
        json.dump({"tasks": tasks, "generated_by": "orchestrate.py", "service": service}, f, indent=2)
    print(f"   ✅ {len(tasks)} 个任务, 已缓存到 task.json")
    return tasks, discuss_path

def step3_batch_create(tasks, discuss_path, service):
    """③ 批量创 writer + reviewer 卡"""
    print(f"\n③ 批量创建 writer + reviewer 卡...")
    card_map = {}  # task_id → {writer_id, review_id}

    for t in tasks:
        title = t.get("title", "")
        skill = t.get("skill", "interface-sk")

        # 创建 writer 卡
        body = (
            f"action={title.split('/')[-1]}\n"
            f"output_dir={BASE}/Wiki/privatelink/{service}\n"
            f"source_dir={BASE}/raw/assets/repo/privatelink/{service}\n"
            f"templates_dir={BASE}/templates\n"
            f"discuss_path={discuss_path}\n"
        )
        if t.get("source_files"):
            body += f"src_file={t['source_files'][0]}\n"
        if t.get("modules"):
            body += f"module={t['modules'][0]}\n"

        w = hermes_json("kanban", "create", f"writer: {title}",
            "--assignee", "writer",
            "--skill", skill,
            "--workspace", WS,
            "--body", body,
            "--json")
        wid = w.get("id", "")

        # 加 add-doc
        for doc in t.get("doc_files", []):
            discuss("add-doc", discuss_path, doc)

        # 创建 reviewer 卡（parent = writer）
        # 取第一个 doc_file 给 reviewer
        first_doc = (t.get("doc_files") or [None])[0]
        review_body = f"discuss_path={discuss_path}"
        if first_doc:
            review_body += f"\ndoc_file={first_doc}"

        r = hermes_json("kanban", "create", f"review: {title}",
            "--assignee", "reviewer",
            "--skill", "review-sk",
            "--workspace", WS,
            "--body", review_body,
            "--parent", wid,
            "--json")
        rid = r.get("id", "")

        card_map[t["id"]] = {"writer": wid, "review": rid, "title": title}
        _all_card_ids.extend([wid, rid])
        print(f"   {title:40s} writer={wid} → review={rid}")

    return card_map

def step4_poll_reviews(card_map):
    """④ 轮询所有 reviewer → done"""
    review_ids = [v["review"] for v in card_map.values()]
    print(f"\n④ 等待 {len(review_ids)} 个 reviewer 完成...")
    timeout = 3600  # 1 小时
    waited = 0
    while waited < timeout:
        done = 0
        for rid in review_ids:
            s = card_status(rid)
            if s == "done":
                done += 1
        if done == len(review_ids):
            print(f"   ✅ 全部 {done} 个 reviewer 完成")
            return True
        print(f"   ⏳ {done}/{len(review_ids)} done ({waited}s)", end="\r")
        time.sleep(POLL_INTERVAL)
        waited += POLL_INTERVAL
    print(f"\n❌ reviewer 超时")
    return False

def step5_check_and_fix(discuss_path, service):
    """⑤ 检查 discuss → 有 open 则创 fix + re-review"""
    rc, out, err = discuss("verify", discuss_path)
    if rc == 0:
        print(f"\n⑤ ✅ 全部讨论已解决")
        return False  # 没有需要修的

    # 有 open/fixed 的 discuss
    print(f"\n⑤ ⚠️  有未解决的讨论")

    # 获取 open 的 discuss（用 list --status open）
    rc, out, err = discuss("list", discuss_path)
    if rc != 0 or not out:
        print(f"   ⚠️  无法获取 discuss 列表: {err}")
        return False

    # 解析 discuss 列表，找到 open 和 fixed 的
    open_ids = []
    fixed_ids = []
    for line in out.split("\n"):
        # 格式: dsc_001 open interfaces/CreateVPCEndpoint.md ...
        parts = line.strip().split()
        if len(parts) >= 2:
            did = parts[0].strip()
            st = parts[1].strip()
            if st in ("open",):
                open_ids.append(did)
            elif st in ("fixed",):
                fixed_ids.append(did)

    # 先处理 open 的（需要 writer fix）
    for did in open_ids:
        # 找对应的 doc_file（从 discuss 输出提取）
        doc_file = ""
        for line in out.split("\n"):
            if line.startswith(did):
                parts = line.strip().split()
                if len(parts) >= 3:
                    doc_file = parts[2].strip()
                break

        body = f"discuss_ids={did}\n"
        if doc_file:
            body += f"doc_file={doc_file}\n"
        body += f"discuss_path={discuss_path}\n"

        # 只创建 fix 卡，reviewer 由 fix 完成后触发
        w = hermes_json("kanban", "create", f"fix: {doc_file or did}",
            "--assignee", "writer",
            "--skill", "fix-sk",
            "--workspace", WS,
            "--body", body,
            "--json")
        wid = w.get("id", "")
        print(f"   fix: {did} → {wid}")
        _all_card_ids.append(wid)

        # 创建 re-review 卡（parent = fix）
        r = hermes_json("kanban", "create", f"re-review: {doc_file or did}",
            "--assignee", "reviewer",
            "--skill", "review-sk",
            "--workspace", WS,
            "--body", f"doc_file={doc_file}\ndiscuss_path={discuss_path}\nfix_base_path={doc_file}.bak\ndiscuss_ids={did}",
            "--parent", wid,
            "--json")
        rid = r.get("id", "")
        print(f"   re-review: {did} → {rid}")
        _all_card_ids.append(rid)

    # fixed 的不需要操作（等 reviewer 再审）

    return True  # 还有需要继续的

# ── main ──

def main():
    parser = argparse.ArgumentParser(description="mywiki 管线编排器")
    parser.add_argument("service", help="服务名，如 apisvr")
    args = parser.parse_args()

    service = args.service
    discuss_path = os.path.join(BASE, f"raw/assets/privatelink/{service}/discuss")
    task_json_path = os.path.join(BASE, f"raw/assets/privatelink/{service}/task.json")

    # 确保目录存在
    os.makedirs(os.path.join(BASE, f"Wiki/privatelink/{service}/interfaces"), exist_ok=True)
    os.makedirs(os.path.join(BASE, f"Wiki/privatelink/{service}/modules"), exist_ok=True)
    os.makedirs(os.path.join(BASE, f"Wiki/privatelink/{service}/flows"), exist_ok=True)
    os.makedirs(os.path.dirname(discuss_path), exist_ok=True)

    print(f"╔═══ mywiki 管线 — {service} ═══╗\n")

    # ① 确定性分析
    l1 = step1_analyze(service)

    # ② analyst 卡 → task.json
    tasks, discuss_path = step2_generate_tasks(service, l1, discuss_path)

    # ③ 批量创卡
    card_map = step3_batch_create(tasks, discuss_path, service)

    # ④ ⑤ ⑥ 循环
    max_cycles = 10
    for cycle in range(1, max_cycles + 1):
        print(f"\n── 循环 {cycle} ──")

        # ④ 等 reviewer
        ok = step4_poll_reviews(card_map)
        if not ok:
            break

        # ⑤ 检查 discuss
        has_more = step5_check_and_fix(discuss_path, service)
        if not has_more:
            print(f"\n🎉 全部完成！")
            break

        # 下一次循环的 card_map 是 fix/re-review
        # 重新获取
        time.sleep(5)
        # card_map 在上次的 fix 中已创建新的

    else:
        print(f"\n⚠️  达到最大循环次数 {max_cycles}")

    print(f"\n╚═══ 管线结束 ═══╝")

if __name__ == "__main__":
    main()

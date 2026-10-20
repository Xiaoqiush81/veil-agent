"""Run hide/delete/restart checks on the already isolated fictional memories."""
import json
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / ".local-tmp" / "serein-017" / "src"))

from run_experiment import Proxy, close_ombre, ombre_context, setup_serein
from budget_proxy import ledger_line_count


def strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)


def recall_serein(runtime, query):
    response = runtime["client"].post("/v1/recall", json={
        "query": query, "mode": "surface", "method": "semantic",
        "min_cosine": 0, "limit": 100, "with_evidence": True})
    if response.is_error:
        raise RuntimeError(f"Serein recall failed ({response.status_code}): {response.text[:300]}")
    body = response.json()
    ids = set()
    def walk(value):
        if isinstance(value, dict):
            for key in ("id", "item_id", "memory_id"):
                if isinstance(value.get(key), str):
                    ids.add(value[key])
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)
    walk(body)
    return {"ids": sorted(ids), "text": "\n".join(strings(body)), "body_keys": sorted(body)}


def check_serein(proxy, results):
    event = next(item for item in results["serein"]["peter"]["memories"]
                 if item["kind"] == "event")
    target = event["id"]
    query = "为什么想和爸爸重走旧港路线，后来争执和和好是怎样的？"
    runtime = setup_serein(proxy, "peter")
    before = recall_serein(runtime, query)
    archived = runtime["client"].post("/api/fact-events/status", json={
        "item_id": target, "status": "archived"})
    archived.raise_for_status()
    runtime["client"].__exit__(None, None, None)

    runtime = setup_serein(proxy, "peter")
    after_archive = recall_serein(runtime, query)
    restored = runtime["client"].post("/api/fact-events/status", json={
        "item_id": target, "status": "active"})
    restored.raise_for_status()
    after_restore = recall_serein(runtime, query)
    deleted = runtime["client"].post("/api/fact-events/delete", json={"item_id": target})
    deleted.raise_for_status()
    runtime["client"].__exit__(None, None, None)

    runtime = setup_serein(proxy, "peter")
    after_restart = recall_serein(runtime, query)
    state = runtime["client"].post("/api/fact-events/status", json={
        "item_id": target, "status": "active"})
    delete_irreversible = state.status_code == 400
    runtime["client"].__exit__(None, None, None)
    return {"system": "Serein", "target_id": target,
        "archived_status": archived.json().get("item", {}).get("status"),
        "found_before": target in before["ids"],
        "found_while_archived_after_restart": target in after_archive["ids"],
        "found_after_restore": target in after_restore["ids"],
        "found_after_delete_and_restart": target in after_restart["ids"],
        "delete_result": deleted.json().get("status"),
        "restore_after_delete_rejected": delete_irreversible,
        "limitation": "Event 的归档/删除可验证；Serein 没有供该 Event 再次整理的等价命令，本次未将无新输入的空 pipeline 当成重新整理通过。"}


def check_ombre(proxy, results):
    runtime = ombre_context(proxy, "ghost")
    candidates = [item for item in runtime["memories"]
                  if "青绿" in item["content"] or "外婆" in item["content"]]
    if not candidates:
        args = {"title": "生命周期隔离测试：门廊风铃",
                "content": "虚构校园的门廊风铃挂在西侧入口，雨天会被收进木盒。",
                "why_remembered": "仅用于单独验证隐藏、删除和重启行为。"}
        saved = runtime["backend"].call("hold", args)
        runtime["memory"].record_native(args, saved)
        candidates = [{"id": runtime["memory"].created_id(saved),
                       "title": args["title"], "content": args["content"]}]
        seeded_for_lifecycle = True
    else:
        seeded_for_lifecycle = False
    target = candidates[0]
    query = "门廊风铃挂在哪里？"
    needle = "门廊风铃"
    before = "\n".join(item["content"] for item in runtime["memory"].context(query))
    ask_hide = runtime["memory"].command("/forget " + target["id"])
    hide = runtime["memory"].command("/forget " + target["id"] + " 确认")
    runtime["memory"].supplement()
    hidden_key = bool(runtime["memory"].state["entries"].get(target["id"], {}).get("hidden"))
    close_ombre(runtime)

    runtime = ombre_context(proxy, "ghost")
    hidden_after_restart = "\n".join(item["content"] for item in runtime["memory"].context(query))
    restore = runtime["memory"].command("/restore " + target["id"])
    restored = "\n".join(item["content"] for item in runtime["memory"].context(query))
    ask_delete = runtime["memory"].command("/delete " + target["id"])
    delete = runtime["memory"].command("/delete " + target["id"] + " 确认")
    deleted_key = bool(runtime["memory"].state["entries"].get(target["id"], {}).get("deleted"))
    close_ombre(runtime)

    runtime = ombre_context(proxy, "ghost")
    extra_turns = [
        ("我今天绕社区花园散步，看见薄荷长了新叶。", "那片新叶看起来应该很精神。"),
        ("花园北边的长椅刚刷成了白色，路面有点湿。", "下次走那边我会留意地面。"),
        ("管理员说周末会补种一排迷迭香。", "那这周末花园会多一点香味。"),
        ("我把小铲子放回工具柜了，标签写着三号格。", "好，我会按三号格找。"),
    ]
    for index, (user_text, assistant_text) in enumerate(extra_turns, 1):
        request_id = f"exp017-lifecycle-{index}"
        runtime["store"].append("ghost/chat.jsonl", {"role": "user", "content": user_text, "request_id": request_id})
        runtime["store"].append("ghost/chat.jsonl", {"role": "assistant", "content": assistant_text, "request_id": request_id})
    runtime["memory"].supplement()
    reorg_hidden_key = bool(runtime["memory"].state["entries"].get(target["id"], {}).get("hidden"))
    reorg_deleted_key = bool(runtime["memory"].state["entries"].get(target["id"], {}).get("deleted"))
    close_ombre(runtime)

    runtime = ombre_context(proxy, "ghost")
    after_reorg_restart = "\n".join(item["content"] for item in runtime["memory"].context(query))
    forbidden_restore = runtime["memory"].command("/restore " + target["id"])
    listed = runtime["memory"].command("/memory")
    close_ombre(runtime)
    return {"system": "Ombre", "target_id": target["id"], "title": target["title"],
        "seeded_lifecycle_canary_via_native_hold": seeded_for_lifecycle,
        "found_before": needle in before, "hide_confirmation": "确认请输入" in ask_hide,
        "hide_result": hide, "hidden_flag_after_auto_supplement": hidden_key and reorg_hidden_key,
        "found_after_hide_restart": needle in hidden_after_restart,
        "restore_result": restore, "found_after_restore": needle in restored,
        "delete_confirmation": "确认请输入" in ask_delete, "delete_result": delete,
        "deleted_flag_after_auto_supplement": deleted_key and reorg_deleted_key,
        "found_after_delete_reorg_restart": needle in after_reorg_restart,
        "restore_after_delete": forbidden_restore,
        "absent_from_memory_list": target["id"] not in listed,
        "reorganization_turns": 4}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ombre-only", action="store_true")
    options = parser.parse_args()
    result_path = ROOT / ".local-tmp" / "experiment-017" / "runtime" / "results.json"
    results = json.loads(result_path.read_text(encoding="utf-8"))
    proxy = Proxy("meter.jsonl")
    ledger_start = ledger_line_count(ROOT / ".local-tmp" / "experiment-017" / "runtime" / "meter.jsonl")
    try:
        if options.ombre_only:
            previous_path = ROOT / ".local-tmp" / "experiment-017" / "runtime" / "lifecycle.json"
            previous = json.loads(previous_path.read_text(encoding="utf-8"))
            report = {"serein": previous.get("serein"), "ombre": check_ombre(proxy, results)}
            ranges = list(previous.get("ledger_ranges", []))
        else:
            report = {"serein": check_serein(proxy, results),
                      "ombre": check_ombre(proxy, results)}
            ranges = []
        ranges.append([ledger_start, ledger_line_count(
            ROOT / ".local-tmp" / "experiment-017" / "runtime" / "meter.jsonl")])
        report["ledger_ranges"] = ranges
        report["budget"] = {"paid_calls": proxy.meter.paid_requests,
                            "free_model_calls": proxy.meter.free_requests,
                            "committed_cny": str(proxy.meter.committed),
                            "reserved_cny": str(proxy.meter.pending)}
        output = ROOT / ".local-tmp" / "experiment-017" / "runtime" / "lifecycle.json"
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=True))
    finally:
        proxy.close()


if __name__ == "__main__":
    main()


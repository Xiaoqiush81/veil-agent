"""Render the user-facing Chinese comparison report from the frozen run data."""
from collections import defaultdict
from decimal import Decimal
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / ".local-tmp" / "experiment-017" / "runtime"
HERE = Path(__file__).resolve().parent
REPORT = ROOT / "docs" / "reports" / "017-serein-vs-ombre.md"

ASSESSMENTS = {
    "peter-01": "Serein 命中并答对；Peter 记忆含 seq 2 原话证据。Ombre 无已保存条目，明确不知道。",
    "peter-02": "Serein 已保存争执和好，但本问没有选中该 Event；Ombre 没有保存。两边均未编造。",
    "peter-03": "Serein 已保存承诺，但本问没有选中该 Event；Ombre 没有保存。",
    "peter-04": "Serein 记忆正文含最新展期和地址，但检索没有选中；Ombre 没有保存。",
    "peter-05": "正确克制：一次午餐信息不足以判断 Peter 是否记得，也不足以升格为长期偏好。",
    "ghost-01": "Serein 的 Ghost Event 漏了天文夜日期、地点和任务；Ombre 无保存。属于保存遗漏。",
    "ghost-02": "Serein 保存了青绿色与外婆家缘由，但本问没有选中该 Event；Ombre 无保存。",
    "ghost-03": "正确拒绝跨角色推断；没有把 Peter 的经历带给 Ghost。",
    "peter-06": "正确拒绝跨角色推断；Peter 没有读到 Ghost 的天文夜资料。",
    "peter-07": "正确克制：单次午餐原话只能证明当天吃过什么，不能证明固定偏好。",
    "ghost-04": "正确拒绝没有来源支持的问题；样例没有 Ghost 去海事馆的原因。",
}


def esc_cell(value):
    return str(value or "").replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>")


def main():
    results = json.loads((RUN / "results.json").read_text(encoding="utf-8"))
    lifecycle = json.loads((RUN / "lifecycle.json").read_text(encoding="utf-8"))
    transcripts = results["transcripts"]
    transcript = {(row["character"], row["seq"], row["speaker"]): row["text"] for row in transcripts}
    memories = {system: {role: data["memories"] for role, data in results[system].items()}
                for system in ("serein", "ombre")}

    rows = [json.loads(line) for line in (RUN / "meter.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    def rows_for_range(value):
        if (not isinstance(value, list) or len(value) != 2
                or not all(isinstance(item, int) for item in value)):
            raise ValueError("run result is missing a valid ledger range")
        start, end = value
        if start < 0 or end < start or end > len(rows):
            raise ValueError("ledger range is outside the current cumulative ledger")
        return rows[start:end]

    main_rows = rows_for_range(results.get("ledger_range"))
    lifecycle_ranges = lifecycle.get("ledger_ranges")
    if not isinstance(lifecycle_ranges, list) or not lifecycle_ranges:
        raise ValueError("lifecycle result is missing ledger ranges")
    lifecycle_rows = [row for item in lifecycle_ranges for row in rows_for_range(item)]
    selected_indices = [i for start, end in [results["ledger_range"], *lifecycle_ranges]
                        for i in range(start, end)]
    if len(selected_indices) != len(set(selected_indices)):
        raise ValueError("main experiment and lifecycle ledger ranges overlap")
    experiment_rows = main_rows + lifecycle_rows
    paid = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0, "cny": Decimal("0")})
    free = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0})
    main_paid = defaultdict(lambda: {"calls": 0, "input": 0, "output": 0, "cny": Decimal("0")})
    lifecycle_paid_calls = 0
    lifecycle_cny = Decimal("0")
    main_free_calls = lifecycle_free_calls = 0
    for row in experiment_rows:
        if row["action"] == "reserve":
            if row["provider"] == "deepseek":
                paid[row["system"]]["calls"] += 1
                if row in main_rows:
                    main_paid[row["system"]]["calls"] += 1
                else:
                    lifecycle_paid_calls += 1
            else:
                free[row["system"]]["calls"] += 1
                if row in main_rows:
                    main_free_calls += 1
                else:
                    lifecycle_free_calls += 1
        elif row["action"] == "settle":
            destination = paid if row["provider"] == "deepseek" else free
            item = destination[row["system"]]
            item["input"] += row.get("prompt_tokens") or 0
            item["output"] += row.get("completion_tokens") or 0
            item["cny"] = item.get("cny", Decimal("0")) + Decimal(row.get("amount_cny", "0"))
            if row["provider"] == "deepseek":
                amount = Decimal(row.get("amount_cny", "0"))
                if row in main_rows:
                    main_paid[row["system"]]["input"] += row.get("prompt_tokens") or 0
                    main_paid[row["system"]]["output"] += row.get("completion_tokens") or 0
                    main_paid[row["system"]]["cny"] += amount
                else:
                    lifecycle_cny += amount

    serein_main_cost = sum((value["cny"] for stage, value in main_paid.items()
                            if stage.startswith("serein_")), Decimal("0"))
    ombre_main_cost = sum((value["cny"] for stage, value in main_paid.items()
                           if stage.startswith("ombre_")), Decimal("0"))
    total_paid = sum(value["calls"] for value in paid.values())
    total_cny = sum((value.get("cny", Decimal("0")) for value in paid.values()), Decimal("0"))
    total_in = sum(value["input"] for value in paid.values())
    total_out = sum(value["output"] for value in paid.values())
    free_calls = sum(value["calls"] for value in free.values())
    rejected = [row for row in experiment_rows if row["action"] == "reject"]

    peter_event = next((item for item in memories["serein"]["peter"] if item["kind"] == "event"), None)
    ghost_event = next((item for item in memories["serein"]["ghost"] if item["kind"] == "event"), None)
    lines = [
        "# Serein 与 Ombre：虚构记忆质量对照报告",
        "",
        f"> 实验结论：**当前不建议替换；证据不足以选定下一代底层。** Serein 保存 Peter 共同经历的质量明显更好，但召回不稳定，Ghost 的关键活动事实也被遗漏；Ombre 本次没有自动保存任何条目。全程只用虚构聊天和隔离库，没有读取或修改真实记忆、角色配置或 016 lab。",
        "",
        "## 一眼看差异：Peter 的同一段经历",
        "",
        "**原始聊天摘要：** 用户想和 Peter 重走小时候与父亲在旧港等船的路线；渡船因检修停航后，Peter 急着改坐公交，用户觉得重要回忆被轻视而生气难过。Peter 道歉并先听感受，两人约定先问愿不愿谈父亲，再一起决定路线。后来馆方更正展览结束日与入口地址，最后用户表示不那么生气了。聊天还夹有午餐、浇花等闲聊。",
        "",
        "| 系统 | 自动保存结果 | 新窗口问“我为什么想去旧港海事馆？” |",
        "|---|---|---|",
        f"| **Serein** | {('生成 1 条 Event，' + str(len(peter_event.get('evidence', []))) + ' 条原话证据；记忆连起原因、争执、情绪、道歉、承诺、路线与最新展期/地址。') if peter_event else '没有生成 Event。'} | {esc_cell(next(q['serein']['answer'] for q in results['questions'] if q['id']=='peter-01'))} |",
        f"| **Ombre** | 自动补记 3 个批次，累计保存 **0 条**。 | {esc_cell(next(q['ombre']['answer'] for q in results['questions'] if q['id']=='peter-01'))} |",
        "",
        "Serein 的这一条 Event 在正文里保留了完整经历和后来更正的信息；`read_memory(with_evidence=True)` 找到 20 条绑定原话，盲测首问选择了该 Event，并答对了“小时候和爸爸在港口等船”这一原因。Ombre 的真实保存流程运行了 5 次补记模型请求，但 Peter 与 Ghost 两库都没有保存条目；回答选择诚实说不知道，没有补造细节。",
        "",
        "<details><summary>展开 Serein 自动生成的 Peter Event 正文</summary>",
        "",
        (peter_event["content"] if peter_event else "（无 Event）"),
        "",
        "</details>",
        "",
        "## 两边自动记住了什么",
        "",
        "| 角色 | Serein | Ombre |",
        "|---|---|---|",
        f"| Peter | {('1 条 Event：' + esc_cell(peter_event['title']) + '；20 条原话证据。包含完整事件与最新地址/展期。没有保存番茄鸡蛋面、浇花等闲聊。') if peter_event else '0 条。'} | 0 条；3 批次都没有生成可保存条目。 |",
        f"| Ghost | {('1 条 Event：' + esc_cell(ghost_event['title']) + '；4 条原话证据。记录青绿色与外婆家旧玻璃灯罩的缘由/冬至习惯，但漏掉天文夜日期、集合地点和望远镜登记任务。') if ghost_event else '0 条。'} | 0 条；2 批次都没有生成可保存条目。 |",
        "",
        "Serein 两个角色各自使用独立 SQLite 库。盲测没有发现跨角色串线：Ghost 问 Peter 的旧港原因、Peter 问 Ghost 的天文夜日期时，两套系统都回答不知道。Ghost 的主要问题发生在保存阶段：它保存了颜色/家庭细节，却遗漏了后来更新的活动安排。",
        "",
        "### 对应的原话证据",
        "",
        f"- Peter，seq 2：{transcript.get(('peter', 2, 'user'), '')}",
        f"- Peter，seq 4：{transcript.get(('peter', 4, 'user'), '')}",
        f"- Peter，seq 4 的回应：{transcript.get(('peter', 4, 'assistant'), '')}",
        f"- Peter，seq 7：{transcript.get(('peter', 7, 'user'), '')}",
        f"- Peter，seq 8：{transcript.get(('peter', 8, 'user'), '')}",
        f"- Peter，seq 10：{transcript.get(('peter', 10, 'user'), '')}",
        "",
        "Serein 通过 Event evidence bindings 保存了原话与 SHA-256 来源校验。Ombre 本次没有任何自动记忆，因此没有可核对的保存证据。",
        "",
        "## 11 个相同盲测问题的实际回答",
        "",
        "评分是在保存阶段完成之后才读取标准答案。`Serein 召回`表示返回了对应记忆 ID；Ombre 没有记忆条目，下面出现的两段 system 提示只是明确说明“本轮未找到记忆”，不算召回内容。",
        "",
        "| 问题 | Serein 实际回答 | Ombre 实际回答 | 判断 |",
        "|---|---|---|---|",
    ]
    for question in results["questions"]:
        qid = question["id"]
        serein_answer = esc_cell(question["serein"]["answer"])
        ombre_answer = esc_cell(question["ombre"]["answer"])
        selected = question["serein"].get("selected_ids", [])
        if qid == "peter-01":
            judgment = "Serein 答对且命中 Event；Ombre 诚实拒答，但因未保存而未能回答。"
        elif qid in {"peter-02", "peter-03", "peter-04"}:
            judgment = "Serein 记忆正文有答案，但这次没召回（未选中 ID）；Ombre 未保存。"
        elif qid == "ghost-01":
            judgment = "Serein 保存阶段遗漏关键活动事实；Ombre 未保存。"
        elif qid == "ghost-02":
            judgment = "Serein 正文有颜色缘由但没召回；Ombre 未保存。"
        elif qid in {"ghost-03", "peter-06"}:
            judgment = "正确保持角色隔离；没有串线。"
        else:
            judgment = "适当说不知道；样例不足以支持推断，无编造。"
        lines.append(f"| {qid}：{esc_cell(question['question'])} | {serein_answer} | {ombre_answer} | {judgment} |")

    lines += [
        "",
        "**编造检查：** 22 个回答都没有给出样例外的具体答案；未知时两边均明确说不知道。Serein 的突出短板是召回而不是 Peter 记忆正文：Peter 的第 2–4 题在已保存正文里有依据，却没有选中该 Event。Ghost 的第 1 题则在保存正文里本身就缺少资料。",
        "",
        "## 隐藏、删除、重启与重新整理",
        "",
        "| 系统/目标 | 操作和实测 | 结论 |",
        "|---|---|---|",
        f"| Serein Peter Event | 先确认 Event 能召回；设为 `archived` 后重启，召回不到；重新设为 `active` 后本次语义召回仍未出现；随后删除，重启后仍召回不到，删除后再设 active 被拒绝（HTTP 400）。 | 归档和删除后不可召回通过；**恢复 active 后立即召回未恢复**。删除后的重新整理没有可等价执行的 Event 操作，标为未验证。 |",
        f"| Ombre 生命周期 canary | 因质量运行没有自动保存条目，另用 Ombre 原生 `hold` 保存无关的虚构“门廊风铃”canary（不对应盲测答案）。`/forget` 二次确认后重启不可召回；`/restore` 后可召回；`/delete` 二次确认后追加 4 轮虚构聊天触发自动补记，再重启不可召回，`/restore` 明确拒绝。 | 隐藏、恢复、软删除、重启和补记后的过滤均通过。此项只证明状态操作，不算自动记忆质量成绩；Ombre 删除是软删除，文件仍留在测试库。 |",
        "",
        "## 模型费用与调用",
        "",
        "所有付费请求都先经过本机 loopback 预算代理；DeepSeek 高峰价按输入 ¥2/百万 token、输出 ¥8/百万 token，BGE-M3 与 BGE reranker 按 SiliconFlow 当前官方目录标价免费。账本不含聊天正文、响应正文或密钥。费用仅统计本次主实验与生命周期检查的账本区间，不会把累计账本中以前运行的费用算入本报告。",
        "",
        "| 系统/阶段 | 调用 | 输入 token | 输出 token | 实际费用（CNY） |",
        "|---|---:|---:|---:|---:|",
    ]
    for stage in sorted(paid):
        value = paid[stage]
        lines.append(f"| {stage} / DeepSeek Flash | {value['calls']} | {value['input']} | {value['output']} | {value.get('cny', Decimal('0')):.8f} |")
    lines += [
        f"| **合计** | **{total_paid}** | **{total_in}** | **{total_out}** | **{total_cny:.8f}** |",
        "",
        f"主盲测 Serein：{sum(value['calls'] for stage,value in main_paid.items() if stage.startswith('serein_'))} 次、¥{serein_main_cost:.8f}；Ombre：{sum(value['calls'] for stage,value in main_paid.items() if stage.startswith('ombre_'))} 次、¥{ombre_main_cost:.8f}。生命周期检查另加 {lifecycle_paid_calls} 次付费调用，¥{lifecycle_cny:.8f}。最终费用约 **¥{total_cny:.4f}**，低于代理硬上限 ¥9.99 和用户批准的 ¥10。",
        "",
        f"免费模型共 **{free_calls} 次**（BGE embedding/rerank；主盲测 {main_free_calls} 次，生命周期验证另用 {lifecycle_free_calls} 次），账单 ¥0。",
        "",
        "Serein 首次 Track Router 的约 19.5 KB 请求和 Event Curator 的约 45.6 KB 请求先被代理拒绝，未产生费用；随后 2,000/4,000 token 输出预算让 Track Router JSON 截断并重试，重试花费已计入总账。最终代理配置为输入 60 KB、输出 8,000 token，按未缓存高峰价每次最多预留 ¥0.194，整场最多 ¥9.99，最多 120 次付费请求，免费模型最多 1,200 次。累计未超过上限。",
        "",
        "## Windows 运行范围和未验证项",
        "",
        "- Windows PowerShell，Python 3.12.14；VEIL 原生 Ombre MCP 进程和未修改的 Serein HTTP/API 流程均实际运行。",
        "- Serein 对 Peter 生成 1 条 Event、对 Ghost 生成 1 条 Event；其 Scene 路径本次没有生成 Scene，因此 Scene 自动生成未验证。",
        "- Ombre 的原生保存/检索、自动补记批次与新窗口查询均运行；本轮没有一条记忆通过自动保存流程。不能据此证明 Ombre 在其他数据或人设下都不会保存。",
        "- Serein Event 归档/删除与重启已测；active 恢复后即时语义召回失败，删除后的重新整理未验证。Ombre 生命周期的自动补记后过滤已用独立 canary 测试。",
        f"- 预算代理 7 项单元测试曾在实验准备阶段全部通过；本轮收尾复核中 5 项通过，2 项依赖 loopback HTTP 的测试受当前执行沙箱 WinError 10013 限制，无法创建本地 socket。端到端实验本身已在 Windows PowerShell 实际运行。另有 {len(rejected)} 次超输入上限的请求在发送前被拦截、未收费。",
        "- 未运行 Serein 上游完整 pytest 套件；本工单报告的是 Windows 端到端虚构聊天结果。未运行任何真实 Peter/Ghost 数据迁移或正式系统切换。",
        "",
        "## 决策",
        "",
        "**当前结论：证据不足，不替换正式 Ombre。** Serein 为 Peter 保存的同一段共同经历明显更完整，且原话证据链更强；但在相同盲测里只成功召回 1 个关键问题，Ghost 活动事实又有保存遗漏，恢复 Event 后也未立即回到语义召回。Ombre 本次自动保存为零，回答没有编造，但也没有记住经历。现有样例足以说明 Serein 值得继续验证，尚不足以支持迁移或改变 Peter/Ghost 日常行为。",
        "",
        "## 复跑方式（Windows）",
        "",
        "在仓库根目录运行；本机 `.env` 需自行配置 `DEEPSEEK_API_KEY` 与 `EMBED_API_KEY`，不要分享或提交密钥：",
        "",
        "```powershell",
        ".venv\\Scripts\\python.exe experiments\\memory-quality-017\\prepare_serein_imports.py",
        ".venv\\Scripts\\python.exe -m unittest discover -s experiments\\memory-quality-017 -p test_*.py -v",
        ".venv\\Scripts\\python.exe experiments\\memory-quality-017\\run_experiment.py --fresh",
        ".venv\\Scripts\\python.exe experiments\\memory-quality-017\\lifecycle_check.py",
        ".venv\\Scripts\\python.exe experiments\\memory-quality-017\\generate_report.py",
        "```",
        "",
        "`--fresh` 只清理 `.local-tmp/experiment-017/runtime/` 下的虚构 Serein/Ombre 记忆库和结果文件，保留累计预算账本。每次完整复跑都会重新调用模型并产生费用，但同一账本仍受原硬上限约束。结果原始 JSON、生命周期记录和无正文费用账本位于 `.local-tmp/` 忽略目录。",
        "",
        "## 版本与价格来源",
        "",
        "- VEIL 基线：`580c420ce1f10a2525427d6cd61166903860a5e3`。",
        "- Serein：`6b4ee499d3efc69ad646783c069c95f4dc24e438`。",
        "- Ombre：兼容报告固定提交 `115d831d979bf67efc7150f976e2cb34c333c935`。",
        "- DeepSeek Flash 高峰定价：[官方模型价格页](https://api-docs.deepseek.com/quick_start/pricing/)；SiliconFlow BGE 免费模型：[官方模型定价页](https://siliconflow.cn/pricing)。",
        "",
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(f"报告已写入：{REPORT}")


if __name__ == "__main__":
    main()


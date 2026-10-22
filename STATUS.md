# 当前状态

更新：2026-10-22 12:05 UTC · Codex。

## 当前目标与现状

- **067 能力变化通知可靠交付：** PR #102 已于 `12fdb3586f91614cb38a0144344aebedda04d513` 合并；GitHub CI 通过，Lan 的 Windows 实际体验验收仍待执行。
- **068 Windows 真实运行验证：** PR #104 仍在审，基于 main `c45504c`；隔离虚构角色的 Windows 验证不能代替真实聊天、记忆读写或 Lan 体验验收。
- **069 breath_search 失败阶段诊断：** PR #106 已合入 main `c45504c`。为避免重放未确认的检索，MCP 会返回 `MemoryToolError/unknown`，并以固定的 HTTP、MCP 初始化、工具执行或恢复阶段记录在角色私有诊断中，聊天提示不含私人内容。
- **068 当前能力认知与能力面板一致性：** PR #105，代码修复提交 `7af7547`，分支 `ticket/068-live-capability-awareness`。旧实现请求级红测确认模型请求缺当前清单；动态当前快照由实际工具 schema、授权策略和运行状态生成，网页与模型同源。PR 已列出按 GitHub 合并记录可核实的能力与修补时间线，并注明本机实际启用日期不能由 PR 推断。Cubic 首轮 5 项及第二轮 2 项实质问题均标记解决；第二轮角色目录重定向安全问题先用虚构角色红测复现再修正，UTC 测试收紧。该提交四组 Windows/Ubuntu Python 3.11/3.12 测试、`audit`、`scanner-report-smoke` 及依赖安全均通过；本地全套 365 项通过、3 项可选跳过，`git diff --check` 通过。GitHub `VEIL Main Protection` ruleset 的 6 项 required checks 均已满足；Cubic check 仍显示运行中。Lan 的 Windows 体验验收未执行。

## 下一步

工单 068：等 Cubic 最新 head review check 完成；之后核对状态文档提交触发的最新 required checks，并按已读到的 `VEIL Main Protection` ruleset 合并。Lan 的 Windows 体验验收仍待做。工单 069 已独立合入 main，不混入本单实现。

## Lan 的体验验收

1. **067 待验收：** 给 Peter 增加 `lab_file_digest` 与 `move_lab_file`，确认面板和 Peter 收到同一完整英文更新，之后多轮不重复。
2. **068 施工中：** 打开能力面板确认当前真实能力和权限；问 Peter “What tools can you use right now, and what are their limits?”，确认回答无需搜索文件且与面板一致。
3. **069 待验收：** 正常连续与 Peter 聊天并询问已记住的事项，确认不会再出现不含阶段的检索失败；若出现检索故障，保留角色私有诊断供 agent 判断，勿发送聊天或记忆正文。

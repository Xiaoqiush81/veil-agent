# 当前状态

更新：2026-10-22 11:30 UTC · Codex。

## 当前目标与现状

- **067 能力变化通知可靠交付：** PR #102 已于 `12fdb3586f91614cb38a0144344aebedda04d513` 合并；最新 GitHub CI（Ubuntu/Windows、Python 3.11/3.12）通过，Cubic 实质意见已处理。Lan 的 Windows 实际体验验收仍待执行，验收重点为新增两项 Lab 工具后 Peter 主动收到完整更新、面板正文相同且后续不重复。
- **068 当前能力认知与能力面板一致性：** 分支 `ticket/068-live-capability-awareness`，基于 main `12fdb3586f91614cb38a0144344aebedda04d513`。旧实现请求级红测已失败，确认模型请求没有当前能力清单。现已将同一份动态快照接入最终模型消息和“能力记录”面板；带日期的 `capability_updates` 继续作为变更历史单独呈现与注入。请求、页面、授权过滤、移除和服务不可用定向测试通过；全仓 360 项 unittest 通过（3 项可选测试跳过）。PR、GitHub CI 与 Cubic 审查尚未完成，Windows 体验验收未执行。

## 下一步

工单 068：复查完整 diff 与能力历史日期边界，提交并推送分支、创建 PR，运行 GitHub CI 并处理 Cubic 实质意见；核对 main 实际质量门禁。合并后请 Lan 完成下面的 Windows 体验验收。

## Lan 的体验验收

1. **067 待验收：** 给 Peter 增加 `lab_file_digest` 与 `move_lab_file`，确认面板和 Peter 收到同一完整英文更新，之后多轮不重复。
2. **068 施工中：** 打开能力面板确认当前真实能力和权限；问 Peter “What tools can you use right now, and what are their limits?”，确认回答无需搜索文件且与面板一致。

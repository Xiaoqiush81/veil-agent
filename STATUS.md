# 当前状态

更新：2026-10-22 UTC · Codex。

## 当前目标与现状

- **067 能力变化通知可靠交付：** PR #102 已合入 main；对应提交 `12fdb3586f91614cb38a0144344aebedda04d513`。head `83a8a091f77cf28ba03ebb512693fa067967c77e` 的 Tests #934 与 Dependency security #65 成功；Cubic 实质意见已处理。Windows 真人体验仍待验收。
- **068 Windows 真实运行验证：** 分支 `ticket/068-windows-runtime-validation`，PR #104，基于 main `12fdb3586f91614cb38a0144344aebedda04d513`。使用虚构角色与隔离目录，未访问或修改 `data/peter`，未调用模型或付费服务。
- **开发端已验证：** Windows Node 24.22.0、npm 11.19.1 按 lockfile 安装 Electron 45.0.0。`desktop/npm test` 2 项通过；`desktop/npm run test:windows` 真实打开 Electron 窗口并通过历史显示、单次发送、拒绝审批、收起/重开、缩放和沙箱检查。Python 离线回归 350 项通过、3 项跳过；隔离 Ombre 恢复门禁 1 项通过。
- **真实 Windows 服务验证：** 虚构角色 Python 服务、Ombre 子进程及固定版本文件系统 MCP 实际启动；桌面 backend 认证复用成功。服务退出重启后记忆和文件能力重新就绪；MCP 对虚构 Lab 文件创建、读取、追加成功，并拒绝目录穿越。服务重启前后聊天文件字节一致。
- **尚未验证：** Electron 窗口与真实 Python Agent 合并链路、模型回复、聊天内记忆写入/检索、模型驱动工具调用、自主活动调度、长期运行、桌面备份/恢复。未复现阻断产品故障，无生产代码修复。第四阶段仍进行中；不得启动第五阶段。

## 下一步

合并 PR #104 后，请 Lan 按下方三步在本机隔离虚构角色上验收；据验收结果继续补足未覆盖的 Windows 场景。

## Lan 的体验验收

1. 从仓库根目录打开 `.local-tmp/ticket-067-runtime/.local-tmp/`，先双击 `Start Fictional Agent.bat`，再双击 `Start Fictional Desktop.bat`。该虚构角色及数据已由开发端预先准备在 `.local-tmp/ticket-067-runtime`，只使用离线占位模型地址和 `data/runtime-fixture`。桌面形象出现后先右键选择“更换 Agent 文件夹”，在文件选择框中选 `.local-tmp/ticket-067-runtime`（其中有 `start-web.bat` 和虚构角色配置）；确认后再点击形象打开聊天。若该隔离目录不存在，停止验收，不要选择 Peter 的目录。确认虚构历史显示，输入 `/cost`、`/memory`、`/autonomy` 查看本地状态，不要发普通聊天。
2. 输入 `/memory` 和 `/autonomy`，确认本地状态可读取；桌面 Memory / Ombre 入口显示不可用提示。
3. 在 Agent 控制台按 `Ctrl+C` 停止服务，再双击 Agent 启动器；在桌面形象上点右键，选“重新连接聊天”。确认虚构历史保留、账本无重复记录。不要操作真实 Peter 的服务或目录。
- **PR #106 / 069 失败阶段诊断：** PR #106 已合并到 main，提交 `c45504c11e4b74f9803506741c4fd9db1b8dc34b`；GitHub Tests 和 Dependency security 通过。真实 Windows 聊天验收仍未完成。
- **069 Ombre 重启后的检索失败：** 安全诊断序列确认了故障路径：`breath_search` 连接被拒（`ConnectError`），Ombre 重启成功，但原调用仍以 `unknown` 失败。原因已定位到恢复后没有重发这次确定未送达的调用。
- **PR #107 修复范围：** 只在连接被拒且 Ombre 重启经验证成功时补发一次；异常组内所有原因都必须证明未送达。任何可能已到达服务的调用不重放；补发失败保持 `unknown`，写入结果不明保护不变。健康响应清零连续恢复计数，累计恢复次数保留。
- **PR #107 当前状态：** 基于 main `c45504c`，head `7fe426a`。Dependency security 已通过；Tests 仍在运行。Cubic 指出的两项实质安全问题已在该 head 修正，两个评论线程已解决。实际 Windows 验收尚未完成。
- **068 Windows 验证：** PR #104 仍打开，基于较早的 `12fdb358`；不与本次记忆故障修复混在一起。


1. 确认 PR #107 最新 head 上所有必需 CI 完成并通过，复核 Cubic 实质意见及仓库分支保护。
2. 满足门禁后合并 PR #107。
3. 合并后只做正常聊天体验验收：连续对话、询问一条已保存信息、重启后继续聊天和检索。无需人为关闭服务或反复触发故障；如遇异常，只需告知 agent，不发送聊天正文或私人记忆日志。


1. 连续与 Peter 正常聊天，确认检索异常不会挡住回复。
2. 询问一条已经保存的事实，确认 Peter 能从记忆中准确检索。
3. 重启 Peter 后继续聊天并再次询问已有事实。
4. 无需主动制造故障；故障诊断由 agent 使用隔离虚构数据处理。

# 当前状态

更新：2026-10-22 UTC · Codex。

## 当前目标与现状

- **065 main 自动更新安全恢复：** PR #101 已合并至 main，merge commit `2f97bc21422562b8ff4fd3a8e9e39af72019ea13`。PR head `b0158c72c2fe0efd26c5173c6c6e22e18b56231a` 的 Tests #915 与 Dependency security #56 均成功；Cubic 的两项实质意见已修复并解决。旧 handoff 已过时，本次记录已纠正。
- **067 Windows 真实运行验证：** 分支 `ticket/067-windows-runtime-validation`，PR #103，基于 main `2f97bc21422562b8ff4fd3a8e9e39af72019ea13`。使用全新虚构角色和独立数据目录；未访问或修改 Peter 的真实数据，没有模型请求或费用。合并前以 PR #103 最新提交的必要 CI、Cubic 与保护状态为准。
- **开发端已验证：** Windows Node 24.22.0、npm 11.19.1 按现有 lockfile 安装 Electron 45.0.0。桌面 `npm test` 2 项通过；`npm run test:windows` 真实打开 Electron 窗口并通过历史显示、单次发送、拒绝审批、收起/重开、缩放和沙箱检查。项目 Python 离线回归 350 项通过、3 项按配置跳过；隔离 Ombre 子进程恢复门禁 1 项通过。
- **真实 Windows 服务验证：** `web_launcher.py` 为虚构角色启动真实 Python 服务；桌面 backend 通过认证复用了该服务。启用本地 Ombre 和固定版本文件系统 MCP 后，服务重启仍报告两项能力就绪，虚构聊天文件 SHA-256 保持不变。Windows MCP 实际完成虚构 Lab 文件创建、读取、追加，并拒绝目录穿越。服务通过认证退出接口正常关闭。
- **边界：** Electron 窗口 smoke 使用虚构 HTTP 服务；真实 Electron 窗口与真实 Python Agent 的合并链路尚未验收。未发送普通聊天消息，避免触发供应商请求。桌面端记忆入口仍为 Coming Soon。自主活动调度、长期运行、模型驱动工具调用及桌面备份/恢复未在真实窗口完成；内部假数据回归通过不替代这些场景。
- 未复现阻断验证的产品故障，本次没有生产代码修复。第四阶段仍进行中，未启动第五阶段；Lan 真人验收未完成。

## 下一步

核对 PR #103 最新提交的 Cubic 与必需 CI；合并后按下方步骤只用本机隔离虚构角色进行真人体验，再补足尚未覆盖的 Windows 场景。

## Lan 的体验验收

1. 双击本机隔离目录里的“Start Fictional Agent.bat”，再双击“Start Fictional Desktop.bat”；确认窗口显示虚构历史，发送 `/cost` 并看到本地账本结果。只输入 `/cost`、`/memory`、`/autonomy` 等本地命令，不输入普通聊天内容。
2. 输入 `/memory`，确认记忆服务正常返回空列表；桌面 Memory / Ombre 入口显示不可用提示。
3. 通过聊天已有的“退出服务”正常关闭 Agent，再双击隔离 Agent 启动器，并从桌面菜单选择“重新连接聊天”；确认虚构历史仍在且 `/cost` 没有重复记录。

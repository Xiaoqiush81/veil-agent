# 工单 068｜Windows 真实运行验证与第四阶段启动

## 目标

让 Lan 能分清 Peter 的 Windows 桌面、服务、记忆和文件功能哪些已有真实运行证据，哪些仍需真人验收。

## 当前状态

基于 main `12fdb3586f91614cb38a0144344aebedda04d513`。复用仓库现有 Electron smoke、Windows Node 测试、Python 离线回归和固定版本 Ombre 恢复门禁；未增加测试框架、付费服务或生产代码。

隔离虚构角色下，Windows 实际启动了 Python 网页服务、Ombre 子进程和固定版本文件系统 MCP。服务认证连接、退出、重启后记忆和工具能力重新就绪，虚构聊天文件在重启前后字节不变。实际 MCP 完成 Lab 内创建、读取、追加，并拒绝目录穿越。真实 Electron 窗口针对现有虚构 HTTP 服务通过 smoke；桌面 backend 也单独成功连接了实际 Python Agent 服务。

自动验证：桌面后端 2 项、Electron Windows smoke 通过；Python 离线回归 350 项通过、3 项跳过；隔离 Ombre 故障恢复门禁 1 项通过。未使用真实人设、聊天、记忆或密钥；没有发送普通聊天或模型请求。

尚未验证 Electron 窗口与真实 Python Agent 的合并链路、模型回复、聊天内记忆写入/检索、模型驱动的工具调用、自主活动调度、长时间运行，以及桌面备份/恢复。未复现阻断验证的产品故障，因此没有生产代码修复。第四阶段仍在进行，Lan 真人验收仍待完成。

## 验收步骤

1. 在本机文件管理器打开 `E:\Peter-Agent\VEIL\veil-agent\.local-tmp\ticket-067-runtime\.local-tmp\`，先双击 `Start Fictional Agent.bat`，再双击 `Start Fictional Desktop.bat`。该目录是本次已准备好的隔离虚构角色；启动器只使用离线占位模型地址和 `data/runtime-fixture`，不访问 `data/peter`。确认虚构历史显示；输入 `/cost`，确认本地账本可读。
2. 输入 `/memory` 和 `/autonomy`，确认服务返回当前状态；桌面 Memory / Ombre 入口继续显示不可用。
3. 在 Agent 黑色控制台按 `Ctrl+C` 停止服务，再双击同一 Agent 启动器；在桌面形象上点右键，选择“重新连接聊天”。确认历史保留、命令没有重复写入。不要输入普通聊天内容，也不要关闭或修改真实 Peter 的服务和目录。

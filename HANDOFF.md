# 交接

- 当前工单为 068 Windows 真实运行验证，分支 `ticket/068-windows-runtime-validation`，基于 main `12fdb3586f91614cb38a0144344aebedda04d513`。066 曾被并行工单占用，067 现已由 PR #102 能力通知工单使用；本工单统一顺延到 068。原 067 运行验证 PR #103 不再使用，后续以 #104 为准。
- PR #102 已合入 main；合入提交为 `12fdb3586f91614cb38a0144344aebedda04d513`。head `83a8a091f77cf28ba03ebb512693fa067967c77e` 的 Tests #934、Dependency security #65 成功，Cubic 意见已处理。
- 开发端 Windows 证据：Electron fake-service smoke、桌面后端 2 项、Python 离线回归 350 项（跳过 3 项）、Ombre 隔离恢复门禁 1 项；实际启动、退出、重启了虚构角色 Python Agent/Ombre/MCP，后端认证复用成功，MCP 虚构文件 CRUD 和目录穿越拒绝均通过，聊天文件重启前后字节一致。
- 未触碰 `data/peter`，未调用模型或付费服务。Electron 窗口到真实 Python Agent 合并链路、聊天模型与记忆集成、模型驱动工具、自主调度、长时间运行和桌面备份恢复仍未验证。虚构角色配置及数据留在本机忽略目录，不能提交。
- 原 PR #103 因 main 更新且工单编号冲突被新 PR #104 取代。新 PR 最新 head 的 CI 与 Cubic 尚待核验；合并后按 STATUS 的三步交给 Lan 真人验收。第四阶段仍进行中，未启动第五阶段。

## 下一个窗口第一步

动态读取 PR #104 当前 head、Cubic 审查、必需 CI 和 main 保护状态。实质风险修完并满足门禁后合并；再请 Lan 使用 STATUS 中的隔离启动器完成体验验收。
- 当前目标：处理 069 Ombre 重启后自动记忆检索仍失败。PR #107 由诊断阶段和故障表现定位到恢复后没有补发确定未送达的调用；未把私人聊天或记忆内容写入仓库。
- PR #107 在 `ticket/069-retry-unsent-memory-calls`。代码仅在连接被拒且 Ombre 重启经验证成功后补发一次；异常组的所有成员都必须证明未送达。可能已到达服务的调用不重放，补发失败仍返回 `unknown` 以保留结果不明写入保护。健康回复清零连续恢复计数，累计计数保留。
- Cubic 的两项实质意见已在代码提交 `7fe426a` 修复，内联线程已解决。STATUS/HANDOFF 文档更新后会产生新 head；CI 需按最新 head 重新核对。
- CI 工作流覆盖 Windows/Ubuntu、Python 3.11/3.12，运行隔离 Ombre 生命周期恢复及完整离线测试。当前执行结果以最新 PR head 的 GitHub 检查为准。
- 本机一次 MCP 测试在测试构造阶段因当前受限运行时无法创建 Windows asyncio Proactor socketpair 而卡住；这不是 Ombre 检索的产品结果，也不能替代 CI。不要重复跑这个受阻路径。
- 下一步：确认最新 head 的必需 CI、Cubic 实质意见和实际分支保护；全部通过后合并 PR #107。合并后只请 Lan 做正常聊天、已存记忆回忆、重启后继续聊天的体验验收，不要求她制造故障或传聊天/记忆正文。

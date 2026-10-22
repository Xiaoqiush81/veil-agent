# 当前状态

更新：2026-10-22 UTC · Codex。

## 当前目标与现状

- **063 GitHub 强制质量门禁：** 分支 `ticket/063-github-quality-gates`，基于最新 main `8f59d04dadf7bf6f99000e85c46fb7dbf4db5cd4`。PR #99 已创建并开放。该 PR 的 CI 与 Cubic 评审以当前 GitHub PR 页面为准；每次新提交都必须核对新 SHA 的检查结果。现有 `Tests` 工作流对所有 PR 运行 Windows/Linux × Python 3.11/3.12 全套回归；`Dependency security` 对所有 PR 运行依赖审计和扫描器样例验证。候选必需检查为四个 `offline-chat` 矩阵作业、`audit`、`scanner-report-smoke`。分支保护要求需从 GitHub 实际配置确认；当前连接器没有读取或修改 Branch Protection / Rulesets 的操作，因此 main 保护状态未知，失败拦截、修复放行和缺项拦截场景尚未验证。
- **阶段二退出核对：** 自动回归覆盖记忆隐藏/检索/历史/角色隔离（`test_native_memory.py`、`test_memory.py`）；MCP 恢复与不确定写入（`test_mcp_recovery.py`、`test_ombre_runtime_recovery_live.py`）；自主任务执行、检查点与重启恢复（`test_long_tasks.py`、`test_autonomy.py`）；文件权限和实际结果（`test_tools.py`、`test_lab.py`）；备份校验、失败回滚和数据完整性（`test_backup_restore.py`）。PR #98 已合并至 main，合并提交 `8f59d04dadf7bf6f99000e85c46fb7dbf4db5cd4`。其 PR head `1d09780d50b39eb7fa2d69c5b960c59fc87f7950` 的 Tests run #885（四平台）和 Dependency security run #43 均成功。阶段二自动回归退出条件满足；Windows 真人体验仍待 Lan 验收。
- **Cubic 流程：** #98 的 Cubic 实质意见均已解决；其 GitHub review 为 `COMMENTED`，不视为 GitHub 必需检查。

## 等 Lan 定的事

请在 PR 可见后通过 GitHub 仓库设置核实并启用 `main` 的分支保护：要求 PR、上述六项检查，要求分支与最新 main 同步，并对管理员启用保护，禁止绕过。当前连接器虽显示 admin 权限，但没有规则读写操作；在获得该设置证据前不标记门禁已启用。

## 下一步

取得 main 保护配置证据，再按隔离 PR 验证失败阻断、修复后放行和必要检查缺失仍阻断；执行前核对 PR #99 最新 SHA 的 CI 与 Cubic 状态。

## Lan 的体验验收

1. 查看一项必要检查失败时 GitHub 禁用合并的页面。
2. 查看修复后新提交的必需检查通过、合并入口恢复，以及有一项检查缺失时仍被阻止。
3. 查看 main 的实际保护设置；另按 062 的 Windows 验收步骤确认虚构记忆写入、待核实状态和重启后的角色隔离。

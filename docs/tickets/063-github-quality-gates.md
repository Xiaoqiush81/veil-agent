# 工单 063：GitHub 强制质量门禁

## 目标

让关键回归和依赖安全检查成为 `main` 合并前的实际门禁，并能证明失败时阻断、修复后放行。

## 当前状态

从最新 `main` `8f59d04dadf7bf6f99000e85c46fb7dbf4db5cd4` 开工。前置 PR #98 已合并；PR head `1d09780d50b39eb7fa2d69c5b960c59fc87f7950` 的 Tests #885 与 Dependency security #43 成功。自动回归退出条件已满足，Windows 体验仍待验收。

复用现有 GitHub Actions 与原生 Branch Protection / Rulesets，不引入依赖或复制第三方实现。当前 Tests 工作流对每个 PR 无路径过滤，执行 Windows/Linux × Python 3.11/3.12 的整套测试；Dependency security 对每个 PR 运行 `audit` 与 `scanner-report-smoke`。稳定的候选 required checks 为 `offline-chat (windows-latest, 3.11)`、`offline-chat (windows-latest, 3.12)`、`offline-chat (ubuntu-latest, 3.11)`、`offline-chat (ubuntu-latest, 3.12)`、`audit`、`scanner-report-smoke`（以 GitHub 当前展示名称为准）。Windows desktop 工作流按 desktop 路径触发，不作为所有 PR 的 required check。

GitHub 仓库连接显示当前身份具 admin 权限，但本次可用接口没有读取或修改 branch protection / rulesets 的操作；本机没有 `gh` CLI，直接 REST 地址也无法经现有浏览器接口访问。因此 `main` 当前保护配置未知，未能安全验证或修改。Cubic 在 #98 以 `COMMENTED` review 提交审查并完成实质意见；它不是可假定存在的 required status check。

## 验收步骤

1. 在隔离验证 PR 中让一个必要检查失败，确认 GitHub 禁用正常合并；修复并推送新提交，确认最新提交检查通过后恢复可合并。
2. 确认有必需检查未完成、取消或未运行时仍不能合并，且 `main` 的 Branch Protection / Rulesets 要求 PR、六项自动检查、最新提交通过并禁止管理员绕过。
3. 在 GitHub 页面查看失败、修复后放行和 `main` 保护证据；Lan 按 `STATUS.md` 的场景完成 Windows 体验验收。

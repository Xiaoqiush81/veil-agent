# 065 安全恢复 main 自动更新

## 目标

Lan 双击更新器时，即使本地 `main` 被误推进到工单提交，也能自动保留恢复分支、同步 GitHub 最新 `main`，并回到原工单分支。

## 当前状态

旧更新器只执行快进更新；本地 `main` 与 `origin/main` 分叉时必然退出。2026-10-22 的实例由本地 `main` 上执行 `git pull --ff-only origin ticket/062-memory-write-reconciliation` 引起，原 3 个提交已保存在 `backup-main-before-update-20261022-1430`。已查 GitHub 的通用安全更新脚本，没有适合直接引入且同时满足 Windows、stash、工单分支和 `.worktrees` 约束的实现，因此少量修改现有 `update-main.cmd`：失败时先建立 `backup/main-before-update-<旧 SHA>`，再对齐 `origin/main`，最后返回原分支；隔离 Git 仓库回归覆盖该场景。

## 验收步骤

1. 在任意 `ticket/*` 分支双击 `update-main.cmd`。
2. 看到 `Update completed successfully` 和 `Returning to ticket/...`，窗口不再出现 `Not possible to fast-forward`。
3. 再双击一次，确认仍能正常完成且回到同一工单分支。

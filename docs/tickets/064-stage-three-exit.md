# 工单 064：第三阶段正式退出核对

## 目标

让 Lan 能从 GitHub 证据确认 `main` 的六项质量门禁确实会拦截失败或缺失检查，并在修复后的最新提交全部通过时恢复放行。

## 当前状态

PR #99 已合并为 `d4641390f3fa8df0b97697d18ac601a14086d8b0`；其最终 head `8a27740f5256420c44ceaa6621cbda93248588af` 的 Tests #898 四个平台作业、Dependency security #49 两个作业全部成功，Cubic 最新复核为 No issues found。复用现有 GitHub Actions、#99 合并记录和 GitHub 原生 Ruleset，不新增依赖或生产实现。

GitHub Rulesets API 显示 `VEIL Main Protection`（ID `25620335`）处于 active，目标为默认分支，要求 PR、严格同步最新分支和六项检查；同时禁止删除与非快进更新，未配置绕过主体。#99 在该 Ruleset 建立前已合并，不能单独证明保护的运行期拦截。

PR #100 的隔离 head `16dc2ac85d176ada9008aad7918cdd77e11cac69` 加入一次性虚构失败探针：Tests #901 的 `offline-chat (ubuntu-latest, 3.11)` 失败，`offline-chat (windows-latest, 3.11)` 被取消，另两项当时未完成；Dependency security #50 成功。GitHub 同时报告 `mergeable_state: unstable`，证明失败、取消或未完成的必需检查没有放行。探针随后删除；最新提交只保留文档，需由六项必需检查与 Cubic 重新核验后才合并。

## 验收步骤

1. 查看本 PR 的虚构探针提交，确认必要检查失败且 GitHub 禁止合并。
2. 查看随后删除探针的最新提交，确认六项必要检查全部通过后恢复可合并；检查尚未完成时仍禁止合并。
3. 查看 `VEIL Main Protection` 页面与本 PR 最终 diff，确认保护仍为 active、没有绕过主体，且最终只包含退出记录，没有生产代码改动。

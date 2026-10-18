---
name: handoff
description: 停下工作、换窗口或交给别的 agent 之前，更新 STATUS.md 和 HANDOFF.md，让下一位直接接上。
---

# 交接更新

`STATUS.md` 每个 PR 都要更新，和代码在同一个 PR 里；`HANDOFF.md` 在窗口结束或换人时更新。进度只记在 `main` 上的 `STATUS.md`，不在别处另存。

## STATUS.md（只写当前正确的状态）

- 更新时间（UTC）和谁更新的。
- 当前目标：一句话。
- 现状：做到哪了，在哪个分支 / PR。
- 等 lan 定的事（没有就删掉这一节）。
- 下一步：一件具体的事。
- 验收步骤：lan 在 Windows 上做的 1–3 步。

已经不成立的内容直接删，不留“之前的方案”。

## HANDOFF.md

- 上一位停在哪：分支、PR、做到第几步、卡在哪、哪里没验证。
- 下一个窗口第一步做什么。
- 背景：只留仍然成立、新 agent 不知道就会走弯路的事实。
- 注意：坑和还没解决的问题。

写完自己读一遍：一个从没见过这个项目的 agent，只读 `AGENTS.md`、`STATUS.md`、`HANDOFF.md`，能不能马上开工？

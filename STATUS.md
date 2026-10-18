# 当前状态

更新：2026-10-18 21:50 UTC · Claude

## 当前目标

阶段一 · 大块 1：Peter 能在 Windows 终端里文字聊天，关掉再开还能接上刚才的话。

## 现状

- 仓库刚重建，只有协作文件（本 PR）。还没有任何程序代码。
- 路线：[重建计划](https://claude.ai/code/artifact/0c29eb8c-d095-4575-9449-18e3f0efdd00)。复用依据：[参考仓库调查](https://claude.ai/code/artifact/25befcb0-c4db-4927-a29b-cc459951d1ba)。

## 已定（lan 2026-10-18）

- 技术栈：Python。
- Peter 先用 DeepSeek，配置里一行可换 GPT。
- 花费上限：¥10/天、¥300/月，不设请求次数上限。

## 下一步

写工单 `docs/tickets/002-text-chat.md`，开分支 `ticket/002-text-chat`。

## 大块 1 的验收步骤（lan 在 Windows 上做）

1. 双击启动，和 Peter 聊几句。
2. 关掉窗口，重新打开。
3. 问“我们刚才聊到哪了”，他能说对。

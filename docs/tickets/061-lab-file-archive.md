# 工单 061：Peter Lab 文件归档

## 目标

Peter 可以自主把 lab 中暂时不用的普通文件移入 `lab/archive/`，完整查阅并恢复到 lab 内其他位置。

## 当前状态

从 main `560bf6028dd5bc4b912c54eb8f50c01d76ed1602` 建立独立分支 `ticket/061-lab-archive`，与 PR #96 的 060 分支分离。现有 `FilesystemTools` 已提供 lab 路径重检、链接/junction 拦截、角色能力清单及日记独立追加授权；MCP 自带 `move_file` 仍禁止。按 reuse-first 在 GitHub 搜索安全移动/不可覆盖/链接边界，未找到同时满足本单 Windows、本地单文件与权限边界约束的成熟可直接复用组件；复用工单 016 的工具循环与标准库方案，不增加依赖或模型调用。实现依据为固定 CPython v3.12.12 的 [`Doc/library/os.rst`](https://github.com/python/cpython/blob/v3.12.12/Doc/library/os.rst) 中 `os.rename` / `os.link` 约定：Windows 的 `os.rename` 遇到已有目标必定失败，POSIX 不用会覆盖目标的 `os.rename`，改用独占硬链接创建后移除源路径。实现与虚构回归已加入；当前环境的 Python 命令是不可启动的 Windows App Execution Alias，本地测试尚未运行。

## 验收步骤

1. 让 Peter 把小游戏 v1、v2 归档，确认原工作目录只留 v3，`archive/play/` 中两份文件内容和大小完整。
2. 让 Peter 阅读归档 v1 并移回 lab 原目录或其他目录；随后制造同名目标冲突，确认目标原文件和源文件都保留。
3. 验证删除、移出 lab、普通目录间移动、目录/链接移动及成长日记移动均被拒绝；重启后归档仍在且可读取和恢复。

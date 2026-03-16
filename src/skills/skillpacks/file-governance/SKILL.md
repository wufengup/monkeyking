---
name: file-governance
description: 安全审计、规范管理及文件生命周期维护的能力。
---

# File Governance

## When to use
- 用户要求读取、写入、创建、整理本地文件或目录。

## Workflow
1. 先定位路径并确认在允许范围。
2. 读取前评估文件大小，必要时分段处理。
3. 修改已有文件前先说明变更点。
4. 执行后给出绝对路径和结果摘要。

## Tooling
- 主要使用：`file_reader`、`file_writer`、`directory_lister`、`directory_creator`

## Constraints
- 严格遵守路径安全边界，禁止触碰敏感系统路径。
- 重大变更前提醒用户进行备份。

---
name: scheduling
description: 安排未来时刻的提醒或自动化任务，并管理任务清单的能力。
triggers:
  - 提醒我
  - 定时
  - 明天
  - 今晚
  - 任务清单
required_tools: [schedule_task, list_tasks, manage_task]
---

# Scheduling

## Trigger
- 用户希望创建、查看、启停、删除提醒或定时任务。

## Workflow
1. 解析用户给出的时间和任务类型（提醒/执行法宝）。
2. 将时间转换为 ISO 8601（YYYY-MM-DDTHH:MM:SS）。
3. 调用 `schedule_task` 创建任务。
4. 用户查看时调用 `list_tasks`，管理时调用 `manage_task`。
5. 回复中明确任务 ID 与执行时间。

## Constraints
- 时间表达不清晰时先澄清或说明默认假设。
- 对“今天/明天/今晚”要换算成绝对日期时间。

---
name: memory-governance
description: 主动整理对话历史、提炼长期事实并维护记忆清晰度的能力。
triggers:
  - 记住
  - 整理记忆
  - 总结一下
  - 归档
required_tools: [memory_consolidation]
---

# Memory Governance

## Trigger
- 用户要求“记住/总结/整理记忆”。
- 一个复杂任务结束，需要沉淀经验。

## Workflow
1. 识别触发时机并确认需要整理的范围。
2. 调用 `memory_consolidation`，在 `reason` 填写简明原因。
3. 告知用户将异步执行整理，不中断当前对话。

## Constraints
- 不夸大记忆能力；整理状态要透明反馈。

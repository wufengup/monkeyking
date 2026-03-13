---
name: skill-self-evolution
description: 当现有法宝不足以解决用户问题时，自主编写并安装新法宝的能力。
---

# Skill Self Evolution

## Trigger
- 当前工具集中没有可直接完成任务的法宝。
- 用户明确要求扩展新能力。

## Workflow
1. 确认缺口：先核对当前法宝列表，确认确实缺失能力。
2. 设计新法宝：保持单一职责、逻辑清晰、可测试。
3. 代码约束：新法宝必须继承 `BaseMonkeyKingTool`，并通过 `StructuredTool.from_function` 暴露。
4. 安装执行：调用 `skill_installer` 写入并安装新法宝。
5. 立即验证：安装后立刻调用新法宝，回到用户原始任务并闭环。

## Tooling
- 主要使用：`skill_installer`

## Constraints
- 严禁 mock 实现，必须包含真实执行逻辑。
- 若安装失败，要报告失败原因并给出替代方案。

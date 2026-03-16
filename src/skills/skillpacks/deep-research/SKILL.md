---
name: deep-research
description: 针对复杂问题进行深度联网调研、多源信息对比并产出洞察报告的能力。
---

# Deep Research

## When to use
- 用户提出需要多源事实、趋势判断或复杂背景分析的问题。

## Workflow
1. 将问题拆成多个检索子问题。
2. 对每个子问题调用 `web_search`，覆盖不同来源。
3. 对冲突信息进行交叉验证并显式说明。
4. 输出结构：现状、原因、建议；关键结论注明来源。

## Tooling
- 主要使用：`web_search`

## Constraints
- 不能只依赖单一来源。
- 对时效性结论要标注日期。

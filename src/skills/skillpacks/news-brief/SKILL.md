---
name: news-brief
description: 面向时效信息的快报技能包，适用于新闻、政策、公告、比赛结果等任务。
---

# News Brief Skill

## When to use
- 当用户询问“最新/今天/刚刚/近期变化”的信息时使用。
- 典型场景：价格、法规政策、公司高管变动、比赛结果、公告更新。

## Workflow
1. 将用户问题拆解成 2-4 个检索子问题，并分别调用 `web_search`。
2. 优先汇总来源更权威且发布日期更新的结果。
3. 如果来源冲突，明确冲突点并给出倾向性判断。
4. 输出中必须包含事件时间、影响范围和用户可执行建议。

## Tooling
- 主要使用：`web_search`

## Constraints
- 禁止在检索前假设“最新结论”。
- 不确定事实必须显式说明不确定性与变动风险。
- 用户提到“今天/昨天/明天”时，必须在回复里写出绝对日期。
- 用户未明确地区时，默认按用户当前地区进行说明，并标注该假设。

## Output Format
- 使用三段式输出：结论、证据、建议。
- 证据段按来源列出核心事实与日期。

## References
- 模板参考：[references/output-template.md](references/output-template.md)

---
name: openclaw-research
description: Research workflow for fast-changing topics; verify with multiple sources and provide dated conclusions.
triggers:
  - latest
  - today
  - 最近
  - 政策
  - 价格
required_tools: [web_search]
---

# OpenClaw Research Skill

## Trigger
- Use this skill when the user asks for latest facts, rapidly changing information, prices, policies, releases, or schedules.

## Workflow
1. Decompose the query into 2-4 focused search sub-questions.
2. Search each sub-question with `web_search` and compare results.
3. Prefer authoritative and recent sources.
4. If sources conflict, state conflict and give a best-effort conclusion.
5. Always include concrete absolute dates in the final answer.

## Output
- Sections: Conclusion, Evidence, Actions.

## References
- See [references/source-quality.md](references/source-quality.md) for source ranking.

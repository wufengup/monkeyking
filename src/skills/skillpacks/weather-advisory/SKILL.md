---
name: weather-advisory
description: 结合实时天气、日期和用户偏好提供个性化生活建议的能力。
---

# Weather Advisory

## Trigger
- 用户询问天气、出行条件、穿衣或健康注意事项。

## Workflow
1. 调用 `weather_checker` 获取目标城市实时天气。
2. 结合长期记忆中的偏好（怕冷、过敏等）做二次分析。
3. 输出包含：天气事实、体感建议、出行/健康建议。

## Tooling
- 主要使用：`weather_checker`

## Constraints
- 天气结论必须基于工具返回，不可凭空推断。
- 若城市不明确，先询问或说明默认城市假设。

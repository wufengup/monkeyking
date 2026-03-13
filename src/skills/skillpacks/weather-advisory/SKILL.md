---
name: weather-advisory
description: 结合实时天气、日期和用户偏好提供个性化生活建议的能力。
---

# Weather Advisory

## Trigger
- 用户询问天气、出行条件、穿衣或健康注意事项。

## Workflow
1. 优先调用 `weather_checker_multi_platform` 获取目标城市实时天气（默认高德，必要时可对比 OpenWeatherMap）。
2. 需要未来天气时调用 `weather_forecast`；可按 `days` 或 `date` 查询。
3. 结合长期记忆中的偏好（怕冷、过敏等）做二次分析。
4. 输出包含：天气事实、体感建议、出行/健康建议。

## Tooling
- 主要使用：`weather_checker_multi_platform`、`weather_forecast`

## Constraints
- 天气结论必须基于工具返回，不可凭空推断。
- 若城市不明确，先询问或说明默认城市假设。

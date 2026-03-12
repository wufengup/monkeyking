from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class WeatherAdvisorySkill(BaseMonkeyKingSkill):
    """
    大圣的神通：天气咨询。
    这不仅仅是查天气，更是结合大圣的洞察力为用户提供生活建议。
    """
    
    @property
    def name(self) -> str:
        return "WeatherAdvisorySkill"

    @property
    def description(self) -> str:
        return "结合实时天气、日期和用户偏好提供个性化生活建议的能力。"

    @property
    def sop(self) -> str:
        return """
施展【天气咨询】神通的步骤：
1. **获取基础信息**：
    - 调用 `weather_checker` 获取目标城市的实时天气。
    - 检索用户的长期记忆（Memory），看是否有关于该城市的偏好或健康注意事项（如：怕冷、对花粉过敏等）。
2. **多维分析**：
    - 分析气温：决定是大圣的“毫毛变衣”还是“火眼金睛避暑”。
    - 分析天气状况：如遇雨雪，建议用户避行；如晴空万里，建议用户出行。
3. **大圣式建议**：
    - 结合教员的远见，给出关于该天气下长期健康或工作计划的宏观建议。
    - 结合乔布斯的产品思维，给出关于穿搭或出行体验的细节建议。
    - 始终使用大圣的豪迈语气进行回复。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["weather_checker"]

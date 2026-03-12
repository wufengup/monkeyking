from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class MemoryGovernanceSkill(BaseMonkeyKingSkill):
    """
    大圣的神通：记忆治理。
    指导大圣如何主动管理自己的 Session 总结和长期记忆。
    """
    
    @property
    def name(self) -> str:
        return "MemoryGovernanceSkill"

    @property
    def description(self) -> str:
        return "主动整理对话历史、提炼长期事实并维护大脑（Memory）清晰度的能力。"

    @property
    def sop(self) -> str:
        return """
施展【记忆治理】神通的步骤：
1. **识别时机**：
    - 当用户显式要求“记住”、“整理记忆”或“总结一下”时。
    - 当一个复杂任务（如炼制法宝、深度调研）圆满完成，需要归档经验时。
2. **动用法宝**：
    - 调用 `memory_consolidation` 法宝。
    - 在 `reason` 参数中简齐地说明为什么要整理（例如：“用户要求记录行为模式”、“完成百度搜索法宝炼制”）。
3. **告知用户**：
    - 明确告知用户你正在进行“异步闭关”整理记忆。
    - 承诺整理完成后，这些经验将永久刻在你的长期记忆中。
4. **即时反馈**：
    - 即使在后台整理，也要给用户一个正面的口头回复，不能让对话中断。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["memory_consolidation"]

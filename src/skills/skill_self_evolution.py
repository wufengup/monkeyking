from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class SkillSelfEvolution(BaseMonkeyKingSkill):
    """
    大圣的神通：自我进化。
    当现有的法宝无法满足需求时，大圣会通过此神通自行炼制并安装新的法宝。
    """
    
    @property
    def name(self) -> str:
        return "SkillSelfEvolution"

    @property
    def description(self) -> str:
        return "当现有法宝不足以解决用户问题时，自主编写并安装新法宝的能力。"

    @property
    def sop(self) -> str:
        return """
施展【自我进化】神通的步骤：
1. **洞察缺失**：分析用户请求，确认当前可用法宝列表中确实没有能直接完成任务的法宝。
2. **构思法宝**：
    - 设计一个功能单一、逻辑清晰的原子化工具类。
    - 确保它继承自 `BaseMonkeyKingTool`。
    - 使用 `StructuredTool.from_function` 封装。
    - 严禁 Mock，必须包含真实逻辑（如调用 API、处理文件等）。
3. **炼制与安装**：
    - 调用基础法宝 `skill_installer`。
    - 传入设计好的 `file_name` 和完整的 Python `code`。
4. **验证成果**：
    - 安装成功后，立即调用这个新炼成的法宝来处理用户最初的任务。
    - 给出最终结果，完成闭环。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["skill_installer"]

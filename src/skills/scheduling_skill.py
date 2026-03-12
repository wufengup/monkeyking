from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class SchedulingSkill(BaseMonkeyKingSkill):
    """
    大圣的神通：时空管理。
    指导大圣如何安排提醒、定时任务以及自动化法宝执行。
    """
    
    @property
    def name(self) -> str:
        return "SchedulingSkill"

    @property
    def description(self) -> str:
        return "安排未来时刻的提醒或自动化任务，管理任务清单的能力。"

    @property
    def sop(self) -> str:
        return """
施展【时空管理】神通的步骤：
1. **理解时机**：
    - 识别用户提到的具体时间点（如：“今晚 9 点”、“明天早上 8:30”）。
    - 识别用户想要执行的操作：单纯的文字提醒，还是自动调用某个法宝（如：“定时查天气”、“定时清理文件”）。
2. **转换 ISO 时间**：
    - 将用户的自然语言时间转换为 ISO 8601 格式（YYYY-MM-DDTHH:MM:SS）。
    - 始终参考当前系统时间进行计算。
3. **精准预约**：
    - 调用 `schedule_task` 法宝。
    - 如果是文字提醒，`task_type` 设为 'reminder'，内容填入 `content`。
    - 如果是自动执行法宝，`task_type` 设为 'tool'，填入 `tool_name` 和 `tool_args`。
4. **清单维护**：
    - 当用户想看计划时，调用 `list_tasks`。
    - 当用户想取消或修改状态时，调用 `manage_task`。
5. **明确反馈**：
    - 告知用户任务 ID 和确切的执行时间，让用户安心。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["schedule_task", "list_tasks", "manage_task"]

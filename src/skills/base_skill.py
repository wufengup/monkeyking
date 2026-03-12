from abc import ABC, abstractmethod
from typing import List, Optional

class BaseMonkeyKingSkill(ABC):
    """
    MonkeyKing 神通 (Skill) 基类。
    Skill 是高层次的业务逻辑、工作流或领域知识 (SOP)。
    它不直接执行代码，而是作为一套“操作指南”注入到大圣的大脑中，指导他如何组合使用 Tools。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """神通的名称，例如: SkillSelfEvolution"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """对该神通的简短描述，用于让大模型了解何时该“施展”此神通"""
        pass

    @property
    @abstractmethod
    def sop(self) -> str:
        """
        Standard Operating Procedure (标准作业程序)。
        详细描述执行该技能的步骤、注意事项和最佳实践。
        这部分内容会被动态注入到 System Prompt 中。
        """
        pass

    @property
    def required_tools(self) -> List[str]:
        """执行该神通通常需要配合使用的法宝 (Tools) 列表"""
        return []

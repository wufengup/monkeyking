from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import os

class SkillInstallerInput(BaseModel):
    capability_type: str = Field(description="安装类型：'tool' (法宝) 或 'skill' (神通)")
    skill_name: Optional[str] = Field(None, description="当类型为 'skill' 时，神通的分类目录名（例如：'text_processing'）")
    file_name: str = Field(description="新能力的文件名（小写下划线，例如 weather_tool）")
    code: str = Field(description="新能力的完整 Python 代码。如果是法宝，必须继承 BaseMonkeyKingTool；如果是神通，必须继承 BaseMonkeyKingSkill。")

class SkillInstallerTool(BaseMonkeyKingTool):
    """
    技能安装工具：
    支持大圣通过编写代码自主扩展技能。
    """
    
    # 我们需要在运行时设置 manager 的引用，或者通过类方法访问
    _tool_manager = None

    @property
    def name(self) -> str:
        return "skill_installer"

    @property
    def description(self) -> str:
        return "为 MonkeyKing 安装新技能（法宝或神通）。传入类型、文件名、代码等参数即可完成安装。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=SkillInstallerInput
        )

    def _run(self, capability_type: str, file_name: str, code: str, skill_name: Optional[str] = None) -> str:
        """调用 CapabilityManager 进行安装"""
        if not self._tool_manager:
            return "错误：CapabilityManager 未初始化，无法安装法宝。"
        
        if capability_type == "tool":
            return self._tool_manager.install_new_tool(file_name, code)
        elif capability_type == "skill":
            if not skill_name:
                return "错误：安装神通时必须提供 skill_name 作为目录名。"
            return self._tool_manager.install_new_skill(skill_name, file_name, code)
        else:
            return f"错误：不支持的类型 '{capability_type}'。请选择 'tool' 或 'skill'。"

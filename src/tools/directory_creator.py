from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from pathlib import Path
import os

class DirectoryCreatorInput(BaseModel):
    directory_path: str = Field(description="需要创建的目录路径，必须是用户目录下的绝对路径或相对于用户目录的路径。")

class DirectoryCreatorTool(BaseMonkeyKingTool):
    """
    内置目录创建工具：
    安全红线：仅限在用户主目录 (~/) 下创建目录。
    """
    @property
    def name(self) -> str:
        return "directory_creator"

    @property
    def description(self) -> str:
        return "在用户主目录下创建新目录。安全起见，无法在主目录以外创建任何内容。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=DirectoryCreatorInput
        )

    def _run(self, directory_path: str) -> str:
        """执行目录创建逻辑，包含安全检查"""
        try:
            target_path = Path(directory_path).expanduser().resolve()
            user_home = Path.home().resolve()
            
            # 安全检查：路径必须在用户主目录下
            if not str(target_path).startswith(str(user_home)):
                return f"错误：禁止在用户主目录以外的路径 '{directory_path}' 创建目录。这是安全红线。"
            
            if target_path.exists():
                return f"提示：路径 '{directory_path}' 已经存在，无需重复创建。"
            
            # 创建目录
            target_path.mkdir(parents=True, exist_ok=True)
            return f"成功：已为您在主目录下创建目录 '{directory_path}'。"
                
        except Exception as e:
            return f"创建目录时发生错误: {str(e)}"

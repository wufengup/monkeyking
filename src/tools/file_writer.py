from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from pathlib import Path
import os

class FileWriterInput(BaseModel):
    file_path: str = Field(description="需要创建或写入的文件路径，必须是用户目录下的绝对路径或相对于用户目录的路径。")
    content: str = Field(description="要写入文件的内容。")
    confirmed: bool = Field(default=False, description="用户是否已经确认要覆盖已存在的文件。默认为 False。")

class FileWriterTool(BaseMonkeyKingTool):
    """
    内置文件写入工具：
    安全红线 1：仅限在用户主目录 (~/) 下操作。
    安全红线 2：变更已存在的文件必须获得用户确认。
    """
    @property
    def name(self) -> str:
        return "file_writer"

    @property
    def description(self) -> str:
        return "在用户主目录下创建文件并写入内容。如果文件已存在，必须在 confirmed 参数中传入 True 才能覆盖。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=FileWriterInput
        )

    def _run(self, file_path: str, content: str, confirmed: bool = False) -> str:
        """执行文件写入逻辑，包含安全检查和覆盖确认"""
        try:
            target_path = Path(file_path).expanduser().resolve()
            user_home = Path.home().resolve()
            
            # 1. 安全检查：路径必须在用户主目录下
            if not str(target_path).startswith(str(user_home)):
                return f"错误：禁止在用户主目录以外的路径 '{file_path}' 进行文件操作。这是安全红线。"
            
            # 2. 覆盖确认检查
            if target_path.exists():
                if not confirmed:
                    return (
                        f"警告：文件 '{file_path}' 已经存在。俺老孙不敢擅自改动他人财物！\n"
                        "请你明确告诉我要'确认覆盖'，然后我才能帮你动手。"
                    )
            
            # 确保父目录存在
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 3. 执行写入
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            status = "覆盖并更新" if confirmed and target_path.exists() else "创建"
            return f"成功：已为您在主目录下{status}了文件 '{file_path}'。"
                
        except Exception as e:
            return f"文件操作失败: {str(e)}"

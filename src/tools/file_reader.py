from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from pathlib import Path
import os

class FileReaderInput(BaseModel):
    file_path: str = Field(description="需要读取的文件路径，必须是用户目录下的绝对路径或相对于用户目录的路径。")

class FileReaderTool(BaseMonkeyKingTool):
    """
    内置文件读取工具：
    安全红线：仅限读取用户主目录 (~/) 下的文件。
    """
    @property
    def name(self) -> str:
        return "file_reader"

    @property
    def description(self) -> str:
        return "读取用户主目录下的文件内容。安全起见，无法访问主目录以外的文件。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=FileReaderInput
        )

    def _run(self, file_path: str) -> str:
        """执行文件读取逻辑，包含安全检查"""
        try:
            target_path = Path(file_path).expanduser().resolve()
            user_home = Path.home().resolve()
            
            # 安全检查：路径必须在用户主目录下
            if not str(target_path).startswith(str(user_home)):
                return f"错误：禁止访问用户主目录以外的路径 '{file_path}'。这是安全红线。"
            
            if not target_path.exists():
                return f"错误：文件 '{file_path}' 不存在。"
            
            if not target_path.is_file():
                return f"错误：'{file_path}' 不是一个文件。"
            
            # 读取文件内容 (简单实现，实际可根据需要添加长度限制)
            with open(target_path, 'r', encoding='utf-8') as f:
                content = f.read(10000) # 限制读取前 10000 字符
                if len(content) == 10000:
                    content += "\n... (文件内容过长，已截断)"
                return content
                
        except Exception as e:
            return f"读取文件时发生错误: {str(e)}"

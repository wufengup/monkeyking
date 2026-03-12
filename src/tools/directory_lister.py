from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from pathlib import Path
import os

class DirectoryListerInput(BaseModel):
    directory_path: str = Field(description="需要查看的目录路径，必须是用户目录下的绝对路径或相对于用户目录的路径。默认为用户主目录。")

class DirectoryListerTool(BaseMonkeyKingTool):
    """
    内置目录列表工具：
    安全红线：仅限查看用户主目录 (~/) 下的目录。
    """
    @property
    def name(self) -> str:
        return "directory_lister"

    @property
    def description(self) -> str:
        return "查看指定目录下的文件和子目录列表。安全起见，无法查看主目录以外的路径。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=DirectoryListerInput
        )

    def _run(self, directory_path: str = "~") -> str:
        """执行目录列表逻辑，包含安全检查"""
        try:
            target_path = Path(directory_path).expanduser().resolve()
            user_home = Path.home().resolve()
            
            # 安全检查：路径必须在用户主目录下
            if not str(target_path).startswith(str(user_home)):
                return f"错误：禁止访问用户主目录以外的路径 '{directory_path}'。这是安全红线。"
            
            if not target_path.exists():
                return f"错误：目录 '{directory_path}' 不存在。"
            
            if not target_path.is_dir():
                return f"错误：'{directory_path}' 不是一个目录。"
            
            # 列出目录内容
            contents = os.listdir(target_path)
            if not contents:
                return f"目录 '{directory_path}' 是空的。"
            
            # 格式化输出
            result = []
            for item in sorted(contents):
                item_path = target_path / item
                prefix = "[DIR] " if item_path.is_dir() else "[FILE]"
                result.append(f"{prefix} {item}")
            
            return f"目录 '{directory_path}' 下的内容：\n" + "\n".join(result)
                
        except Exception as e:
            return f"获取目录列表时发生错误: {str(e)}"

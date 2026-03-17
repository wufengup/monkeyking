from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import os

class FileDeleterInput(BaseModel):
    file_path: str = Field(description="需要删除的文件路径，必须是用户目录下的绝对路径或相对于用户目录的路径")

class FileDeleterTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "file_deleter"
    @property
    def description(self) -> str: return "删除用户主目录下的指定文件"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=FileDeleterInput)
    def _run(self, file_path: str) -> str:
        user_home = os.path.expanduser("~")
        full_path = os.path.abspath(os.path.join(user_home, file_path))
        if not full_path.startswith(user_home):
            return f"错误：无法访问主目录以外的文件 {file_path}"
        if os.path.exists(full_path) and os.path.isfile(full_path):
            os.remove(full_path)
            return f"成功删除文件：{full_path}"
        else:
            return f"文件不存在或不是普通文件：{full_path}"

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import os

class ToolCleanerInput(BaseModel):
    tool_file_name: str = Field(description="需要清理的工具文件名（包含.py后缀）")

class ToolCleaner(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "tool_cleaner"
    @property
    def description(self) -> str: return "清理指定的MonkeyKing工具文件"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=ToolCleanerInput)
    def _run(self, tool_file_name: str) -> str:
        # 使用相对路径或通过项目根目录动态获取，避免硬编码绝对路径
        current_file_dir = os.path.dirname(os.path.abspath(__file__))
        tool_dir = current_file_dir
        tool_path = os.path.abspath(os.path.join(tool_dir, tool_file_name))
        
        if not os.path.exists(tool_path):
            return f"工具文件 {tool_file_name} 不存在"
        
        # 安全检查：确保清理的文件确实在工具目录下
        if not tool_path.startswith(os.path.abspath(tool_dir)):
            return "安全限制：只能清理工具目录下的文件"
        
        os.remove(tool_path)
        return f"已成功清理工具文件：{tool_file_name}"

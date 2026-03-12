from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool

class CurrentDateToolInput(BaseModel):
    pass

class CurrentDateTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "current_date_tool"
    @property
    def description(self) -> str: return "获取当前的日期，格式为YYYY-MM-DD"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=CurrentDateToolInput)
    def _run(self) -> str:
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
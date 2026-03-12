from pydantic import BaseModel
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from datetime import datetime

class CurrentTimeToolInput(BaseModel):
    pass

class CurrentTimeTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "current_time_tool"
    @property
    def description(self) -> str: return "获取当前的时间，格式为HH:MM:SS"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=CurrentTimeToolInput)
    def _run(self) -> str:
        now = datetime.now()
        return now.strftime("%H:%M:%S")
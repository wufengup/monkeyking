from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import subprocess
from datetime import datetime, timedelta
import time

class ReminderToolInput(BaseModel):
    hour: int = Field(description="提醒时间的小时部分（24小时制）")
    minute: int = Field(description="提醒时间的分钟部分")
    content: str = Field(description="提醒的内容")

class ReminderTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "reminder_tool"
    @property
    def description(self) -> str: return "设置指定时间的提醒，到点后发送系统通知（适配macOS iTerm）"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=ReminderToolInput)
    def _run(self, hour: int, minute: int, content: str) -> str:
        # 获取当前时间
        now = datetime.now()
        # 构造提醒时间
        reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        # 如果提醒时间已过，设置为明天同一时间
        if reminder_time < now:
            reminder_time += timedelta(days=1)
        # 计算等待时间
        wait_seconds = (reminder_time - now).total_seconds()
        # 等待到提醒时间
        time.sleep(wait_seconds)
        # 使用osascript发送通知（适配macOS）
        subprocess.run([
            "osascript",
            "-e",
            f'display notification "{content}" with title "大圣提醒" subtitle "时间到啦！" sound name "default"'
        ])
        return f"已触发提醒：{content}"

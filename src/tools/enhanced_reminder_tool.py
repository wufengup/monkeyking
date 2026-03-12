from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import time
from datetime import datetime
import os
import subprocess

class EnhancedReminderInput(BaseModel):
    hour: int = Field(description="提醒时间的小时部分（24小时制）")
    minute: int = Field(description="提醒时间的分钟部分")
    content: str = Field(description="提醒的内容")
    sound: str = Field(default="default", description="提醒声音（可选：default、submarine、glass等系统内置声音）")
    title: str = Field(default="大圣提醒", description="通知标题")
    subtitle: str = Field(default="重要通知", description="通知副标题")

class EnhancedReminderTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "enhanced_reminder_tool"
    @property
    def description(self) -> str: return "设置带自定义样式和声音的提醒，到点发送系统通知"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=EnhancedReminderInput)
    def _run(self, hour: int, minute: int, content: str, sound: str = "default", title: str = "大圣提醒", subtitle: str = "重要通知") -> str:
        try:
            # 计算等待时间
            now = datetime.now()
            target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 限制：如果等待时间超过 5 秒，则改为“后台预约”模式，不阻塞主线程
            wait_seconds = (target_time - now).total_seconds()
            
            # 如果是过去的时间，顺延到明天
            if wait_seconds < 0:
                wait_seconds += 86400
            
            # 核心改进：大圣不能真睡（time.sleep），否则整个 Agent 进程都会卡死！
            # 我们改为使用 'at' 命令或者简单的 nohup 异步执行
            notification_script = f'display notification "{content}" with title "{title}" subtitle "{subtitle}" sound name "{sound}"'
            
            # 立即测试一次通知权限
            test_cmd = ["osascript", "-e", 'display notification "提醒法宝已就绪" with title "大圣法宝"']
            subprocess.run(test_cmd, check=True)

            # 真正的异步执行逻辑
            cmd = f'sleep {int(wait_seconds)} && osascript -e \'{notification_script}\''
            subprocess.Popen(f'nohup sh -c "{cmd}" > /dev/null 2>&1 &', shell=True)
            
            return f"✅ 成功：大圣已施展‘分身术’，将在 {hour}:{minute} 准时提醒你。你可以继续吩咐其他事，不用等俺！"
        except Exception as e:
            return f"❌ 失败：施展提醒法宝时出了点岔子：{str(e)}。请确保俺老孙有发送通知的权限。"

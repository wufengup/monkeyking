from typing import Optional, Type, Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from datetime import datetime

# --- 1. 新增定时任务法宝 ---
class ScheduleTaskInput(BaseModel):
    task_type: str = Field(description="任务类型：'reminder' (提醒) 或 'tool' (执行法宝)")
    execute_at: str = Field(description="执行时间，格式为 ISO (如: 2026-03-12T21:25:00)")
    content: str = Field(default="", description="提醒内容（针对 reminder 类型）")
    tool_name: Optional[str] = Field(default=None, description="要执行的法宝名称（针对 tool 类型）")
    tool_args: Optional[Dict[str, Any]] = Field(default={}, description="法宝调用参数（针对 tool 类型）")

class ScheduleTaskTool(BaseMonkeyKingTool):
    """新增定时任务"""
    _scheduler = None
    @property
    def name(self) -> str: return "schedule_task"
    @property
    def description(self) -> str: return "预约一个未来的定时任务（提醒或执行法宝）。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=ScheduleTaskInput)
    def _run(self, task_type: str, execute_at: str, content: str = "", tool_name: str = None, tool_args: dict = {}) -> str:
        if not self._scheduler: return "错误：时空管理器未就绪。"
        try:
            # 校验时间格式
            datetime.fromisoformat(execute_at)
            task_id = self._scheduler.add_task(task_type, execute_at, content, tool_name=tool_name, tool_args=tool_args)
            return f"✅ 成功：任务已排期！ID: {task_id}，预计在 {execute_at} 准时动身。"
        except Exception as e:
            return f"❌ 失败：排期出了点岔子：{str(e)}"

# --- 2. 查看任务列表法宝 ---
class ListTasksTool(BaseMonkeyKingTool):
    """查看所有定时任务"""
    _scheduler = None
    @property
    def name(self) -> str: return "list_tasks"
    @property
    def description(self) -> str: return "查看大圣当前的定时任务清单（包括提醒和法宝执行）。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description)
    def _run(self) -> str:
        if not self._scheduler: return "错误：时空管理器未就绪。"
        tasks = self._scheduler.list_tasks()
        if not tasks: return "大圣的行程单上目前空空如也。"
        
        res = "📋 大圣定时任务清单：\n"
        for t in tasks:
            status = "🟢 开启" if t.get("enabled") else "🔴 关闭"
            exec_status = " (已执行)" if t.get("executed") else ""
            res += f"- [{t['id']}] {status}{exec_status} | 类型: {t['type']} | 时间: {t['execute_at']} | 内容: {t.get('content') or t.get('tool_name')}\n"
        return res

# --- 3. 启停/删除任务法宝 ---
class ManageTaskInput(BaseModel):
    task_id: str = Field(description="任务 ID")
    action: str = Field(description="操作：'enable' (开启), 'disable' (关闭), 'delete' (删除)")

class ManageTaskTool(BaseMonkeyKingTool):
    """管理定时任务"""
    _scheduler = None
    @property
    def name(self) -> str: return "manage_task"
    @property
    def description(self) -> str: return "开启、关闭或删除一个已有的定时任务。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=ManageTaskInput)
    def _run(self, task_id: str, action: str) -> str:
        if not self._scheduler: return "错误：时空管理器未就绪。"
        if action == "enable":
            success = self._scheduler.toggle_task(task_id, True)
        elif action == "disable":
            success = self._scheduler.toggle_task(task_id, False)
        elif action == "delete":
            success = self._scheduler.delete_task(task_id)
        else:
            return "错误：不支持的操作类型。"
        
        return f"✅ 成功：已对任务 {task_id} 执行了 {action} 操作。" if success else f"❌ 失败：没找到任务 {task_id}。"

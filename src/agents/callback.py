from abc import ABC, abstractmethod
from typing import Any, Dict, List

class AgentCallback(ABC):
    """
    Agent 执行过程中的回调接口。
    """
    @abstractmethod
    def on_thought(self, thought: str):
        """当 Agent 有新的思考内容时触发"""
        pass

    @abstractmethod
    def on_tool_start(self, tool_name: str, tool_args: Dict[str, Any]):
        """当工具开始执行时触发"""
        pass

    @abstractmethod
    def on_tool_end(self, tool_name: str, output: str):
        """当工具执行结束时触发"""
        pass

    @abstractmethod
    def on_error(self, error: Exception):
        """当执行出错时触发"""
        pass

from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool

class MemoryConsolidationInput(BaseModel):
    reason: str = Field(description="触发记忆整理的原因（如：用户显式要求、对话轮次达到阈值等）")

class MemoryConsolidationTool(BaseMonkeyKingTool):
    """
    记忆整理法宝：
    支持大圣主动触发 Session 总结和长期记忆提炼。
    """
    
    _agent_ref = None # 在运行时设置对 agent 的引用

    @property
    def name(self) -> str:
        return "memory_consolidation"

    @property
    def description(self) -> str:
        return "主动触发记忆整理流程。将当前会话总结存入历史，并提炼关键信息到长期记忆中。建议在用户显式要求整理记忆或任务告一段落时使用。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=MemoryConsolidationInput
        )

    def _run(self, reason: str) -> str:
        """调用 Agent 的整理逻辑"""
        if not self._agent_ref:
            return "错误：Agent 引用未初始化，无法施展此法宝。"
        
        # 触发 Agent 的异步整理逻辑
        # 注意：这里我们通过 agent 暴露的接口来触发
        success = self._agent_ref.trigger_memory_consolidation(reason)
        if success:
            return f"成功：大圣已开启异步闭关，正在根据‘{reason}’整理记忆。总结将自动存入历史，提炼将存入长期记忆。"
        else:
            return "失败：记忆整理流程未能启动，可能当前没有需要整理的内容。"

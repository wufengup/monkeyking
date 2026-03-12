from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from langchain_core.tools import BaseTool as LangChainBaseTool

class BaseMonkeyKingTool(ABC):
    """MonkeyKing 工具基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass

    @abstractmethod
    def to_langchain_tool(self) -> LangChainBaseTool:
        """转换为 LangChain 兼容的工具格式"""
        pass

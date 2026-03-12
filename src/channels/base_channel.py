from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from src.agents.assistant_agent import AssistantAgent

class BaseChannel(ABC):
    """
    所有交互渠道的基类。
    """
    def __init__(self, agent: Optional[AssistantAgent] = None):
        self.agent = agent or AssistantAgent()

    @abstractmethod
    async def handle_webhook(self, request_data: Dict[str, Any]) -> Any:
        """
        处理 Webhook 回调。
        """
        pass

    @abstractmethod
    async def send_message(self, target_id: str, content: str) -> bool:
        """
        发送消息到该渠道。
        """
        pass

    @property
    @abstractmethod
    def channel_name(self) -> str:
        """
        渠道名称。
        """
        pass

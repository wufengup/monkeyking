from abc import ABC, abstractmethod
from typing import Any, Optional
from src.agents.assistant_agent import AssistantAgent

class BaseChannel(ABC):
    """
    交互渠道基类。
    """
    def __init__(self, agent: Optional[AssistantAgent] = None):
        self.agent = agent

    @property
    @abstractmethod
    def channel_name(self) -> str:
        pass

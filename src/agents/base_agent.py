from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseAgent(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, input_data: Dict[str, Any]) -> str:
        pass

    def __repr__(self):
        return f"<Agent: {self.name}>"

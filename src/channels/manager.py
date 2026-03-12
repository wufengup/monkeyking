from typing import Dict, Optional, Type
from src.channels.base_channel import BaseChannel
from src.channels.feishu_channel import FeishuChannel
from src.agents.assistant_agent import AssistantAgent

class ChannelManager:
    """
    交互渠道管理器。
    """
    def __init__(self, agent: Optional[AssistantAgent] = None):
        self.agent = agent or AssistantAgent()
        self.channels: Dict[str, BaseChannel] = {
            "feishu": FeishuChannel(self.agent)
            # 未来可以添加 "dingtalk": DingTalkChannel(self.agent)
        }

    def get_channel(self, channel_name: str) -> Optional[BaseChannel]:
        """
        获取指定渠道。
        """
        return self.channels.get(channel_name)

    def register_channel(self, channel_name: str, channel_instance: BaseChannel):
        """
        动态注册新渠道。
        """
        self.channels[channel_name] = channel_instance

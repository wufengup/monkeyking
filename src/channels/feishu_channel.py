import httpx
import json
import logging
import asyncio
import functools
from typing import Any, Dict, Optional
from src.channels.base_channel import BaseChannel
from src.utils.config import LLMConfig
from src.agents.assistant_agent import AssistantAgent

# 飞书 SDK 相关
import lark_oapi as lark
from lark_oapi.api.im.v1 import P2ImMessageReceiveV1, CreateMessageRequest, CreateMessageRequestBody, CreateMessageResponse
from lark_oapi.ws import Client as WSClient

logger = logging.getLogger(__name__)

class FeishuChannel(BaseChannel):
    """
    飞书交互渠道，支持 Webhook 和 WebSocket 长连接模式。
    """
    def __init__(self, agent: Optional[AssistantAgent] = None):
        super().__init__(agent)
        # 从配置中获取飞书参数
        feishu_config = LLMConfig.get_tool_config("feishu_channel")
        self.app_id = feishu_config.get("app_id", "")
        self.app_secret = feishu_config.get("app_secret", "")
        self.verification_token = feishu_config.get("verification_token", "")
        
        # 初始化飞书客户端 (用于发送消息)
        self.client = lark.Client.builder() \
            .app_id(self.app_id) \
            .app_secret(self.app_secret) \
            .log_level(lark.LogLevel.INFO) \
            .build()

    @property
    def channel_name(self) -> str:
        return "feishu"

    def _do_p2p_message_receive_v1(self, data: P2ImMessageReceiveV1) -> None:
        """
        处理接收到的消息 (v1 格式)
        """
        msg = data.event.message
        if msg.message_type == "text":
            chat_id = msg.chat_id
            content_data = json.loads(msg.content)
            user_text = content_data.get("text", "").strip()
            
            if user_text:
                logger.info(f"飞书收到消息: {user_text}")
                asyncio.create_task(self._process_and_reply(chat_id, user_text))

    async def handle_webhook(self, request_data: Dict[str, Any]) -> Any:
        """
        处理飞书 Webhook 回调 (保留 Webhook 模式支持)。
        """
        # 1. URL 验证
        if request_data.get("type") == "url_verification":
            return {"challenge": request_data.get("challenge")}

        # 2. 事件订阅 (此处仅做简单转发，建议生产环境使用官方 Dispatcher)
        event = request_data.get("event", {})
        message = event.get("message", {})
        
        if message.get("message_type") == "text":
            chat_id = message.get("chat_id")
            content_json = message.get("content", "{}")
            try:
                content_data = json.loads(content_json)
                user_text = content_data.get("text", "").strip()
            except json.JSONDecodeError:
                user_text = ""

            if user_text:
                asyncio.create_task(self._process_and_reply(chat_id, user_text))

        return {"code": 0}

    async def _process_and_reply(self, chat_id: str, text: str):
        """
        调用 Agent 处理并回复消息。
        """
        try:
            # 在后台线程运行同步的 agent.run
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None, 
                functools.partial(self.agent.run, {"query": text})
            )
            await self.send_message(chat_id, response_text)
        except Exception as e:
            logger.error(f"处理并回复飞书消息失败: {e}")
            await self.send_message(chat_id, f"哎呀，俺老孙刚才走神了（出错了）：{e}")

    async def send_message(self, chat_id: str, content: str) -> bool:
        """
        通过飞书发送消息。
        """
        request = CreateMessageRequest.builder() \
            .receive_id_type("chat_id") \
            .request_body(CreateMessageRequestBody.builder() \
                .receive_id(chat_id) \
                .msg_type("text") \
                .content(json.dumps({"text": content}, ensure_ascii=False)) \
                .build()) \
            .build()

        response: CreateMessageResponse = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.client.im.v1.message.create(request)
        )

        if not response.success():
            logger.error(f"发送飞书消息失败: {response.code}, {response.msg}, log_id: {response.get_settings().get('log_id')}")
            return False
        return True

    def start_websocket_listening(self):
        """
        启动 WebSocket 长连接监听。
        """
        logger.info("正在启动飞书 WebSocket 监听...")
        
        # 注册事件处理器
        event_handler = lark.EventDispatcherHandler.builder("", "") \
            .register_p2_im_message_receive_v1(self._do_p2p_message_receive_v1) \
            .build()

        # 创建长连接客户端
        ws_client = WSClient(
            self.app_id,
            self.app_secret,
            event_handler=event_handler,
            log_level=lark.LogLevel.INFO
        )
        
        # 启动监听 (此方法是阻塞的)
        ws_client.start()

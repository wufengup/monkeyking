import httpx
import json
import logging
import asyncio
import functools
import threading
from typing import Any, Dict, Optional
from src.channels.base_channel import BaseChannel
from src.utils.config import LLMConfig
from src.agents.assistant_agent import AssistantAgent

# 飞书 SDK 相关
import lark_oapi as lark
from lark_oapi.api.im.v1 import (
    P2ImMessageReceiveV1, 
    CreateMessageRequest, 
    CreateMessageRequestBody, 
    CreateMessageResponse, 
    Emoji, 
    CreateMessageReactionRequest, 
    CreateMessageReactionRequestBody, 
    CreateMessageReactionResponse,
    DeleteMessageReactionRequest,
    DeleteMessageReactionResponse
)
from src.agents.callback import AgentCallback
from lark_oapi.ws import Client as WSClient

logger = logging.getLogger(__name__)

class FeishuAgentCallback(AgentCallback):
    """
    飞书渠道专用的 Agent 回调，用于动态更新消息表情。
    """
    def __init__(self, channel: 'FeishuChannel', message_id: str):
        self.channel = channel
        self.message_id = message_id
        self.added_emojis = set() # 记录已添加的类型，避免重复

    def on_thought(self, thought: str):
        pass

    def on_tool_start(self, tool_name: str, tool_args: Dict[str, Any]):
        """根据调用的工具类型追加表情（不撤回旧的）"""
        emoji_type = "THINKING"
        if "search" in tool_name or "web" in tool_name:
            emoji_type = "Typing"
        elif "write" in tool_name or "create" in tool_name or "install" in tool_name:
            emoji_type = "Typing"
        elif "weather" in tool_name:
            emoji_type = "GeneralSun"
        
        if emoji_type not in self.added_emojis:
            self.channel._schedule_async(self.channel.send_reaction(self.message_id, emoji_type))
            self.added_emojis.add(emoji_type)

    def on_tool_end(self, tool_name: str, output: str):
        pass

    def on_error(self, error: Exception):
        # 出错时追加警告表情
        self.channel._schedule_async(self.channel.send_reaction(self.message_id, "ERROR"))

class FeishuChannel(BaseChannel):
    """
    飞书交互渠道，支持 Webhook 和 WebSocket 长连接模式。
    """
    def __init__(self, agent: Optional[AssistantAgent] = None):
        super().__init__(agent)
        # 支持动态获取 agent 的回调，解决单例隔离问题
        self.agent_provider = None
        
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

        # 核心：启动一个专门的后台线程来运行 asyncio 事件循环
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_background_loop, args=(self._loop,), daemon=True)
        self._loop_thread.start()

    def _run_background_loop(self, loop: asyncio.AbstractEventLoop):
        """后台线程：运行事件循环"""
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def _schedule_async(self, coro):
        """将协程调度到后台循环中执行（线程安全）"""
        return asyncio.run_coroutine_threadsafe(coro, self._loop)

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
            message_id = msg.message_id
            content_data = json.loads(msg.content)
            user_text = content_data.get("text", "").strip()
            
            if user_text:
                logger.info(f"飞书收到消息: {user_text}")
                # 1. 获取初始表情类型
                emoji_type = self._get_initial_emoji(user_text)
                # 2. 异步处理并获取 reaction_id
                self._schedule_async(self._handle_initial_reaction_and_process(chat_id, user_text, message_id, emoji_type))

    async def _handle_initial_reaction_and_process(self, chat_id: str, user_text: str, message_id: str, emoji_type: str):
        """处理初始表情并启动 Agent 逻辑"""
        await self.send_reaction(message_id, emoji_type)
        await self._process_and_reply(chat_id, user_text, message_id)

    def _get_initial_emoji(self, text: str) -> str:
        """根据关键词和时间获取初始表情"""
        import random
        from datetime import datetime
        
        # 1. 关键词驱动 (察言观色)
        keywords_map = {
            "你好": ["WAVE", "SMILE", "JOYFUL"],
            "哈喽": ["WAVE", "SMILE", "JOYFUL"],
            "下午好": ["WAVE", "SMILE", "JOYFUL"],
            "早上好": ["GeneralSun", "WAVE", "SMILE"],
            "晚安": ["GeneralMoon", "SLEEP"],
            "查": ["Typing", "StatusFlashOfInspiration", "GLANCED"],
            "搜": ["Typing", "StatusFlashOfInspiration", "GLANCED"],
            "写": ["Typing", "SMILE"],
            "帮我": ["StatusFlashOfInspiration", "JIAYI"],
            "为什么": ["WHAT", "THINKING"],
            "怎么": ["WHAT", "THINKING"],
            "天气": ["GeneralSun", "RAINBOW"]
        }
        
        for kw, emojis in keywords_map.items():
            if kw in text:
                return random.choice(emojis)
        
        # 2. 时间感知 (灵猴特色)
        hour = datetime.now().hour
        if 6 <= hour < 11:
            return "GeneralSun"
        elif 11 <= hour < 14:
            return "SMILE" # 中午用微笑，比 DONE 更礼貌
        elif 14 <= hour < 18:
            return "JOYFUL" # 下午用开心的表情
        elif 18 <= hour < 22:
            return "GeneralMoon"
        elif 22 <= hour or hour < 6:
            return "GeneralMoon"
            
        # 3. 默认随机多样性
        return random.choice(["THINKING", "Typing", "SMILE"])

    async def handle_webhook(self, request_data: Dict[str, Any]) -> Any:
        """
        处理飞书 Webhook 回调 (保留 Webhook 模式支持)。
        """
        # 1. URL 验证
        if request_data.get("type") == "url_verification":
            return {"challenge": request_data.get("challenge")}

        # 2. 事件订阅
        event = request_data.get("event", {})
        message = event.get("message", {})
        
        if message.get("message_type") == "text":
            chat_id = message.get("chat_id")
            message_id = message.get("message_id")
            content_json = message.get("content", "{}")
            try:
                content_data = json.loads(content_json)
                user_text = content_data.get("text", "").strip()
            except json.JSONDecodeError:
                user_text = ""

            if user_text:
                emoji_type = self._get_initial_emoji(user_text)
                self._schedule_async(self._handle_initial_reaction_and_process(chat_id, user_text, message_id, emoji_type))

        return {"code": 0}

    def get_agent_for_chat(self, chat_id: str) -> AssistantAgent:
        """获取当前会话对应的 Agent 实例"""
        if self.agent_provider:
            return self.agent_provider(chat_id)
        return self.agent

    async def _process_and_reply(self, chat_id: str, text: str, message_id: Optional[str] = None):
        """
        调用 Agent 处理并回复消息。
        """
        try:
            callback = None
            if message_id:
                callback = FeishuAgentCallback(self, message_id)

            # 获取当前 chat 对应的独立 Agent 实例
            current_agent = self.get_agent_for_chat(chat_id)

            # 每次请求前，检查内存中的 agent 是否因为其他渠道(比如控制台)或上次请求被切换了
            current_agent_name = current_agent.name
            
            # 兼容：如果当前是分身，而且用户提到了“变回大圣本尊”等字眼，在外部手动触发切换回本体
            # 这是一个快速通道，防止分身在没有 agent_creator 工具时无法切回
            if current_agent_name.lower() != "monkeyking" and text.strip() in ["变回大圣本尊", "变回大圣", "切换回大圣", "让大圣回来", "让MonkeyKing回来"]:
                current_agent.switch_to_agent("MonkeyKing")
                success = await self.send_message(chat_id, "✅ 已收回毫毛，变回大圣本尊！有什么我可以帮您的？")
                return

            # 在后台线程运行同步的 agent.run
            loop = asyncio.get_event_loop()
            response_text = await loop.run_in_executor(
                None, 
                functools.partial(current_agent.run, {"query": text}, False, callback)
            )
            
            # 检查执行后是否发生了身份切换
            if getattr(current_agent, "_agent_switched_in_turn", False) or current_agent.name != current_agent_name:
                # 分身切换成功，系统已经在 run 内部返回了切换成功的文案
                pass
            
            success = await self.send_message(chat_id, response_text)
            if not success:
                # 如果发送失败，记录到 Agent 的 Session 中，让大圣知道刚才的消息没发出去
                logger.error(f"发送消息到飞书失败，chat_id: {chat_id}")
                current_agent._append_to_session("System", f"[错误] 刚才给用户的回复发送失败了。请在下次对话中向用户致歉并重试。失败原因：飞书接口调用不成功。")
        except Exception as e:
            logger.error(f"处理并回复飞书消息失败: {e}")
            error_msg = f"哎呀，出错了：{e}"
            success = await self.send_message(chat_id, error_msg)
            if not success:
                logger.error(f"回复错误消息到飞书失败，chat_id: {chat_id}")
                # 尝试写入当前 agent session
                try:
                    self.get_agent_for_chat(chat_id)._append_to_session("System", f"[严重错误] 处理消息时报错且回复错误信息也失败了。错误：{e}")
                except:
                    pass

    async def send_reaction(self, message_id: str, reaction_type: str) -> bool:
        """
        给指定消息添加表情回复。
        """
        request = CreateMessageReactionRequest.builder() \
            .message_id(message_id) \
            .request_body(CreateMessageReactionRequestBody.builder() \
                .reaction_type(Emoji.builder() \
                    .emoji_type(reaction_type) \
                    .build()) \
                .build()) \
            .build()

        response: CreateMessageReactionResponse = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.client.im.v1.message_reaction.create(request)
        )

        if not response.success():
            logger.error(f"发送飞书表情失败: {response.code}, {response.msg}")
            # 同步给 Agent（默认使用主 Agent 记录日志）
            if self.agent:
                self.agent._append_to_session("System", f"[提示] 尝试在飞书消息上贴表情失败了（类型: {reaction_type}）。错误信息: {response.msg}")
            return False
        
        return True

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

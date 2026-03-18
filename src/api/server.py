import logging
from typing import Dict
from fastapi import FastAPI, Request, HTTPException
from src.channels.manager import ChannelManager
from src.agents.assistant_agent import AssistantAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(title="MonkeyKing Channel Server")

# 初始化渠道管理器
channel_manager = ChannelManager()

# --- 支持分身能力的 Session 管理器 ---
class AgentSessionManager:
    def __init__(self):
        # 暂时不考虑多用户问题，只维护一个全局共享的“当前会话 Agent”
        # 当某人要求切换分身时，这个全局实例就会切换
        self.global_agent = AssistantAgent()
        
    def get_agent(self, chat_id: str) -> AssistantAgent:
        # 无论哪个 chat_id，暂时都返回同一个全局 Agent，但保留了接口的扩展性
        return self.global_agent

session_manager = AgentSessionManager()

# 获取飞书渠道并注入动态的 agent 提供者
feishu_channel = channel_manager.get_channel("feishu")
if feishu_channel:
    feishu_channel.agent_provider = session_manager.get_agent
    feishu_channel.agent = session_manager.global_agent # 设为后备 fallback

@app.post("/webhook/feishu")
async def feishu_webhook(request: Request):
    """
    飞书 Webhook 回调接口。
    """
    try:
        data = await request.json()
        logger.info(f"收到飞书 Webhook 回调: {data}")
        feishu_channel = channel_manager.get_channel("feishu")
        if not feishu_channel:
            raise HTTPException(status_code=404, detail="Feishu channel not configured")
        
        return await feishu_channel.handle_webhook(data)
    except Exception as e:
        logger.error(f"处理飞书 Webhook 回调失败: {e}")
        return {"code": 1, "msg": str(e)}

@app.get("/health")
async def health_check():
    """
    健康检查接口。
    """
    return {"status": "ok"}

def run_websocket_server():
    """
    启动所有支持长连接的渠道监听。
    """
    feishu_channel = channel_manager.get_channel("feishu")
    if hasattr(feishu_channel, "start_websocket_listening"):
        feishu_channel.start_websocket_listening()
    else:
        logger.error("飞书渠道不支持 WebSocket 模式或未正确配置。")

# 如果需要启动服务，可以使用:
# uvicorn src.api.server:app --host 0.0.0.0 --port 8000

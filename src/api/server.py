import logging
from fastapi import FastAPI, Request, HTTPException
from src.channels.manager import ChannelManager
from src.agents.assistant_agent import AssistantAgent

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 初始化 FastAPI 应用
app = FastAPI(title="MonkeyKing Channel Server")

# 初始化 Agent 和渠道管理器
agent = AssistantAgent()
channel_manager = ChannelManager(agent)

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

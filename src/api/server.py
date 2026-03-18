import logging
import json
import asyncio
import functools
from pathlib import Path
from typing import Dict
from fastapi import FastAPI, Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from src.channels.manager import ChannelManager
from src.agents.assistant_agent import AssistantAgent
from src.utils.config import LLMConfig
from src.agents.callback import AgentCallback

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
        # 维护一个 {agent_name: AssistantAgent} 的缓存池
        # 实现不同分身对应不同的 Agent 实例
        self.agents_pool: Dict[str, AssistantAgent] = {}
        
        # 初始化默认的大圣本体
        self.global_agent = self._get_or_create_agent("MonkeyKing")

    def _get_or_create_agent(self, name: str) -> AssistantAgent:
        """根据名称获取或创建 Agent 实例"""
        if name not in self.agents_pool:
            # 创建新实例
            new_agent = AssistantAgent(name=name)
            self.agents_pool[name] = new_agent
        return self.agents_pool[name]

    def get_agent_by_name(self, name: str) -> AssistantAgent:
        return self._get_or_create_agent(name)

    def get_agent(self, chat_id: str) -> AssistantAgent:
        # 飞书等外部渠道暂时仍使用 global_agent (MonkeyKing) 作为入口
        # 未来可以根据 chat_id 映射到特定的分身
        return self.global_agent

session_manager = AgentSessionManager()

# --- 前端 Web UI 支持 ---
web_dir = Path(__file__).parent.parent / "web"
if web_dir.exists():
    app.mount("/static", StaticFiles(directory=str(web_dir)), name="static")

@app.get("/")
async def read_index():
    index_file = web_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "Web UI not found"}

@app.get("/api/agents")
async def get_agents():
    """获取所有可用的分身列表"""
    # 修复：LLMConfig 没有 get_base_dir 方法，应该是 get_agent_dir("MonkeyKing").parent 或者是 ~/.monkeyking
    base_dir = Path.home() / ".monkeyking"
    agents_dir = base_dir / "agents"
    agents = ["MonkeyKing"]
    if agents_dir.exists():
        for item in agents_dir.iterdir():
            if item.is_dir() and item.name.lower() != "monkeyking":
                agents.append(item.name)
    return {"current": session_manager.global_agent.name, "agents": agents}

@app.get("/api/agent/config")
async def get_agent_config(name: str = "MonkeyKing"):
    """获取指定 Agent 的配置和人格路径，默认 MonkeyKing"""
    agent = session_manager.get_agent_by_name(name)
    
    config_path = str(Path.home() / ".monkeyking" / "config.json")
    
    soul_path = "无"
    if hasattr(agent, 'soul_path') and agent.soul_path:
        soul_path = str(agent.soul_path)
            
    return {"config_path": config_path, "soul_path": soul_path}

class WebAgentCallback(AgentCallback):
    """通过 WebSocket 将 Agent 的思考过程推送到前端"""
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.loop = asyncio.get_event_loop()

    def on_thought(self, thought: str):
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_json({"type": "thought", "content": thought}), 
            self.loop
        )

    def on_tool_start(self, tool_name: str, tool_args: dict):
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_json({"type": "tool_start", "name": tool_name, "args": tool_args}), 
            self.loop
        )

    def on_tool_end(self, tool_name: str, output: str):
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_json({"type": "tool_end", "name": tool_name, "result": output}), 
            self.loop
        )

    def on_error(self, error: Exception):
        asyncio.run_coroutine_threadsafe(
            self.websocket.send_json({"type": "error", "content": str(error)}), 
            self.loop
        )

@app.websocket("/api/ws/chat/{agent_name}")
async def websocket_chat(websocket: WebSocket, agent_name: str = "MonkeyKing"):
    """WebSocket 聊天接口，支持指定 Agent 分身"""
    await websocket.accept()
    
    # 根据路径参数获取对应的 Agent 实例
    agent = session_manager.get_agent_by_name(agent_name)
    callback = WebAgentCallback(websocket)
    
    try:
        # 发送该 Agent 最近的历史记录作为欢迎消息
        history = []
        # 只取最近 10 条展示
        for msg in agent.current_session[-10:]:
            role = msg["role"]
            content = msg["content"]
            # 过滤掉系统和工具消息，只展示对话
            if role in ["User", agent.name, "MonkeyKing"] and not content.startswith("["):
                history.append({"role": role, "content": content})
        
        if history:
             await websocket.send_json({"type": "history", "messages": history})

        while True:
            data = await websocket.receive_json()
            query = data.get("query")
            if query:
                # 在后台线程运行 agent
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, 
                    functools.partial(agent.run, {"query": query}, False, callback)
                )
                await websocket.send_json({"type": "message", "content": response, "agent_name": agent.name})
    except WebSocketDisconnect:
        logger.info(f"Web客户端已断开连接 (Agent: {agent_name})")

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

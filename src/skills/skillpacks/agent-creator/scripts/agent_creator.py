import json
import httpx
import re
import asyncio
import threading
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig

class AgentCreatorInput(BaseModel):
    action: str = Field(description="要执行的操作：'create_agent' (创建分身Agent), 'update_agent_soul' (完善分身人格), 'list_agents' (列出所有分身)")
    name: Optional[str] = Field(default=None, description="分身名")
    soul_content: Optional[str] = Field(default=None, description="分身人格描述")

class AgentCreatorTool(BaseMonkeyKingTool):
    """
    分身炼制工坊（Agent Creator）：
    大圣的“毫毛分身”神通，用于炼制、完善和管理具备特定人格的分身 Agent。
    """
    @property
    def name(self) -> str:
        return "agent_creator"

    @property
    def description(self) -> str:
        return "炼制、完善和管理大圣的分身 Agent。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=AgentCreatorInput
        )

    def _run(self, action: str, name: Optional[str] = None, **kwargs) -> str:
        try:
            if action == "create_agent":
                return self._create_agent(name, kwargs.get("soul_content"))
            elif action == "update_agent_soul":
                return self._update_agent_soul(name, kwargs.get("soul_content"))
            elif action == "list_agents":
                return self._list_agents()
            elif action == "switch_agent":
                return self._switch_agent(name)

            else:
                return f"错误：未知操作 '{action}'."
        except Exception as e:
            return f"分身炼制过程中出了点岔子：{str(e)}"

    def _switch_agent(self, name: Optional[str] = None) -> str:
        """切换当前活跃的分身 Agent（仅在 Agent 交互模式下有效）。"""
        
        # 鉴权：检测运行环境，如果是 Server/Web 模式，禁止通过对话切换
        import sys
        # 简单的 heuristic：如果命令行参数包含 server 或 uvicorn，或者是 Web 模式
        is_server_mode = any(arg.endswith("server.py") or "uvicorn" in arg or "server" in arg for arg in sys.argv)
        
        if is_server_mode:
             return "错误：当前处于 Server/Web 模式，不支持通过对话切换分身。请使用 Web 界面左侧列表或更换 API 路由进行切换。"

        # 兼容性处理：将 "大圣"、"本体" 等别名映射回 "MonkeyKing"
        if name and name.strip() in ["大圣", "本体", "孙悟空", "MonkeyKing"]:
            name = "MonkeyKing"

        # 获取所有分身列表
        agents = self._get_all_agents()
        current_agent = self._agent_ref.name if hasattr(self, "_agent_ref") and self._agent_ref else "MonkeyKing"
        
        # 如果未指定名称，尝试自动切换
        if not name:
            if len(agents) == 2:
                # 只有 2 个分身，自动切换到另一个
                other_agent = next((a for a in agents if a != current_agent), None)
                if other_agent:
                    name = other_agent
                else:
                    return "错误：无法确定要切换到的分身。"
            elif len(agents) > 2:
                return f"当前有多个分身 ({', '.join(agents)})。请指定要切换到的分身名称，例如：'切换到{agents[1] if len(agents) > 1 else '某个分身'}'。"
            else:
                return "错误：当前没有可用的分身。请先使用 'create_agent' 炼制一个分身。"
        
        # 验证分身是否存在
        agent_dir = LLMConfig.get_agent_dir(name)
        if name.lower() != "monkeyking" and not agent_dir.exists():
            return f"错误：未找到名为 '{name}' 的分身。你可以先调用 'create_agent' 炼制它。"
        
        # 通过 _agent_ref 触发 AssistantAgent 的切换逻辑
        if hasattr(self, "_agent_ref") and self._agent_ref:
            try:
                self._agent_ref.switch_to_agent(name)
                # 注意：这个返回值可能不会直接显示给用户，因为 AssistantAgent.run 循环会检测到 _agent_switched_in_turn 并被中断
                if name.lower() == "monkeyking":
                    return "✅ 成功：大圣已收回毫毛，变回本尊。后续对话将记录在本体的记忆中。"
                return f"✅ 成功：大圣已变幻身形，切换到分身 '{name}'。后续对话将记录在 '{name}' 的记忆中。"
            except Exception as e:
                return f"切换失败：{str(e)}"
        
        return f"✅ 切换指令已下达，大圣即将切换到 '{name}' (提示：当前运行环境可能需要重启以完全生效)。"

    def _get_all_agents(self) -> List[str]:
        """获取所有分身 Agent 的名称列表（包括本体）"""
        agents = ["MonkeyKing"]
        if LLMConfig.AGENTS_DIR.exists():
            for d in LLMConfig.AGENTS_DIR.iterdir():
                if d.is_dir() and (d / "soul.md").exists():
                    agents.append(d.name)
        return agents

    def _create_agent(self, name: str, soul_content: str) -> str:
        """创建一个新的分身 Agent"""
        # 鉴权：只有 MonkeyKing 本尊才能创建分身
        current_agent = self._agent_ref.name if hasattr(self, "_agent_ref") and self._agent_ref else "MonkeyKing"
        if current_agent.lower() != "monkeyking":
            return f"错误：只有大圣本尊才能炼制分身，你当前是分身 '{current_agent}'，请先切换回本体。"

        if not name or not soul_content:
            return "错误：需要提供分身名称和人格描述（soul）。"
        
        agent_dir = LLMConfig.get_agent_dir(name)
        if agent_dir.exists():
            return f"错误：分身 '{name}' 已存在。请使用 'update_agent_soul' 完善人格。"
            
        try:
            agent_dir.mkdir(parents=True, exist_ok=True)
            (agent_dir / "memory").mkdir(exist_ok=True)
            (agent_dir / "session").mkdir(exist_ok=True)
            (agent_dir / "soul.md").write_text(soul_content, encoding="utf-8")
            return f"✅ 成功：分身 Agent '{name}' 已炼成！其人格已存入 {agent_dir / 'soul.md'}。主人可以切换到该分身与其对话了。"
        except Exception as e:
            return f"炼制分身失败：{str(e)}"

    def _update_agent_soul(self, name: str, soul_content: str) -> str:
        """完善分身人格"""
        if not name or not soul_content:
            return "错误：需要提供分身名称和新的人格描述。"
            
        agent_dir = LLMConfig.get_agent_dir(name)
        if not agent_dir.exists():
            return f"错误：未找到分身 '{name}'。"
            
        try:
            (agent_dir / "soul.md").write_text(soul_content, encoding="utf-8")
            return f"✅ 成功：分身 Agent '{name}' 的人格已完善。"
        except Exception as e:
            return f"完善人格失败：{str(e)}"

    def _list_agents(self) -> str:
        """列出所有分身 Agent"""
        agents = ["MonkeyKing (本体)"]
        if LLMConfig.AGENTS_DIR.exists():
            for d in LLMConfig.AGENTS_DIR.iterdir():
                if d.is_dir() and (d / "soul.md").exists():
                    agents.append(d.name)
        return "当前已有的分身 Agent 列表：\n" + "\n".join([f"- {a}" for a in agents])

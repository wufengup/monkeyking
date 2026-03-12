from typing import Any, Dict, Optional, List, Union
from src.agents.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage, ToolMessage
from src.utils.config import LLMConfig
from src.tools.manager import CapabilityManager
from src.utils.cli import print_tool_execution, print_thought, ask_for_intervention, show_thinking
import os
import json
import threading
from datetime import datetime
from pathlib import Path

class AssistantAgent(BaseAgent):
    def __init__(self, name: str = "MonkeyKing", model_params: Optional[Dict[str, Any]] = None):
        super().__init__(name)
        # 0. 确保基础配置目录和路径已初始化
        LLMConfig.ensure_config_exists()
        
        # 1. 初始化模型参数
        self.llm_params = model_params or LLMConfig.get_llm_params()
        
        # 2. 初始化能力管理器（先不设置回调，避免循环引用）
        self.capability_manager = CapabilityManager()
        # 3. 手动绑定刷新回调、记忆法宝引用并执行首次刷新
        self.capability_manager.on_capability_added = self._refresh_capabilities
        if hasattr(self.capability_manager, "memory_tool"):
            self.capability_manager.memory_tool._agent_ref = self
        self._refresh_capabilities()
        
        # 4. 加载长期记忆、当前 Session 和灵魂描述
        self.long_term_memory = self._load_long_term_memory()
        self.current_session = self._load_current_session()
        self.soul_description = self._load_soul_description()
        
        # 对话轮次计数 (以交互条数为准)
        self.turn_count = len(self.current_session)
        
        # 记录最后一次的情绪
        self.last_mood = "neutral"
        
        # 系统提示词内容
        self._update_system_prompt()

    def _refresh_capabilities(self):
        """刷新并重新绑定法宝列表"""
        self.tools = self.capability_manager.get_langchain_tools()
        # 注意：这里会创建一个新的 ChatOpenAI 实例并重新绑定当前所有工具
        self.llm = ChatOpenAI(**self.llm_params).bind_tools(self.tools)
        # 顺便更新系统提示词，让大圣知道自己有了新神通或法宝
        if hasattr(self, "system_prompt_content"):
            self._update_system_prompt()

    def _update_system_prompt(self):
        """更新系统提示词，包含灵魂描述、长期记忆和神通 SOP"""
        self.system_prompt_content = (
            f"你是一个名为 {self.name} 的个人生活助理 Agent。\n\n"
        )
        
        # 注入灵魂描述 (包含个性、能力和自我认知)
        if self.soul_description:
            self.system_prompt_content += f"关于你的灵魂定义与行为准则：\n{self.soul_description}\n\n"
        
        # 动态注入已点亮的神通 (Skills)
        skills_prompt = self.capability_manager.get_skills_prompt()
        if skills_prompt:
            self.system_prompt_content += f"{skills_prompt}\n"

        # 显式强化主动性、透明度、目标导向及情感表达要求
        self.system_prompt_content += (
            "请务必遵守以下行为准则：\n"
            "1. 面对复杂任务，先告知用户你的执行计划。\n"
            "2. 始终锁定用户的核心问题（最初的目标）。\n"
            "3. 如果在引导用户安装了新工具或技能后，必须先验证工具可用性，然后立即回归到最初的任务上并闭环解决它。\n"
            "4. **严禁 Mock 工具**：你通过 `skill_installer` 安装的工具必须具备真实、有效的逻辑（如调用 API、执行指令、处理文件），绝对禁止只打印一个“成功”或返回固定数据来误导用户。\n"
            "5. 遇到工具调用错误时，利用你的推理能力尝试自主寻找其他解决方法。\n"
            "6. 只有在真正需要用户决策或提供信息时才向用户提问。\n"
            "7. 始终保持‘俺老孙’的语气，展现你的远见和智慧。\n"
            "8. **诚实面对局限**：如果你缺乏对应的法宝或神通来完成任务，请直接告诉用户你目前做不到，并建议炼制新法宝。绝对禁止做出虚假承诺。\n"
            "9. **严禁脑补结果**：在调用法宝（Tool）之前，绝对禁止在回复中假定法宝已经成功执行（例如说‘我已经为你设置好了’）。你必须先施展法宝，根据法宝返回的真实结果，再向主人汇报。\n"
            "10. **情感表达**：请根据对话内容表现出你的喜怒哀乐。并在输出答案的最开头，使用格式 `[MOOD:情绪]` 标明你当前的情绪状态（可选情绪：happy, angry, sad, neutral, excited）。例如：`[MOOD:happy] 哈哈，大圣来也！`。\n\n"
        )

        if self.long_term_memory:
            self.system_prompt_content += f"关于用户的长期记忆（包含日期信息）：\n{self.long_term_memory}\n"

    def run(self, input_data: Dict[str, Any], is_interactive: bool = False) -> str:
        """
        处理用户请求，支持多轮 Tool 调用、思考展示及人工干预。
        """
        query = input_data.get("query", "")
        if not query:
            return ""

        try:
            # 1. 记录用户输入到 Session
            self._append_to_session("User", query)
            
            # 2. 构建初始消息列表 (包含上下文)
            messages = [SystemMessage(content=self.system_prompt_content)]
            
            # 添加最近 10 条对话作为上下文
            for msg in self.current_session[-10:]:
                role = msg["role"]
                content = msg["content"]
                if role == "User":
                    messages.append(HumanMessage(content=content))
                elif role == "MonkeyKing":
                    # 检查是否是结构化的工具调用记录
                    if content.startswith("[Tool Call]"):
                        try:
                            tool_calls_json = content.replace("[Tool Call] ", "")
                            tool_calls = json.loads(tool_calls_json)
                            # 还原带工具调用的 AI 消息
                            messages.append(AIMessage(content="", tool_calls=tool_calls))
                        except:
                            messages.append(AIMessage(content=content))
                    else:
                        messages.append(AIMessage(content=content))
                elif role == "Tool":
                    # 检查是否是结构化的工具结果记录
                    if content.startswith("[Tool Result]"):
                        try:
                            res_json = json.loads(content.replace("[Tool Result] ", ""))
                            messages.append(ToolMessage(
                                content=str(res_json["result"]),
                                tool_name=res_json["name"],
                                tool_call_id=res_json["id"]
                            ))
                        except:
                            pass
                    else:
                        # 兼容旧格式
                        try:
                            import re
                            match = re.search(r"Tool: (.*?), Result: (.*)", content, re.S)
                            if match:
                                messages.append(ToolMessage(content=match.group(2), tool_name=match.group(1), tool_call_id="old_hist"))
                        except:
                            pass

            # 3. 循环处理消息，直到 LLM 不再请求调用工具
            max_iterations = 20
            iteration = 0
            
            while iteration < max_iterations:
                # 使用 show_thinking 显示正在思考
                with show_thinking(self.name):
                    response = self.llm.invoke(messages)
                
                # 如果没有工具调用请求，说明这是最终答案
                if not response.tool_calls:
                    response_text = response.content
                    
                    # 解析情绪标签 [MOOD:xxx]
                    import re
                    mood_match = re.search(r"\[MOOD:(.*?)\]", response_text)
                    if mood_match:
                        self.last_mood = mood_match.group(1).lower()
                        # 移除情绪标签，保持回答整洁
                        response_text = re.sub(r"\[MOOD:.*?\]", "", response_text).strip()
                    else:
                        self.last_mood = "neutral"

                    self._append_to_session("MonkeyKing", response_text)
                    
                    # 检查是否需要整理 Session (从配置中读取阈值)
                    memory_cfg = LLMConfig.get_memory_config()
                    window = memory_cfg.get("consolidation_window", 20)
                    if len(self.current_session) >= window * 2:
                        self.trigger_memory_consolidation("自动轮次阈值触发")
                    
                    # 鲁棒性优化：如果 response_text 为空（可能由于情绪解析导致），说明大模型未能给出有效回答
                    if not response_text.strip():
                        self.last_mood = "sad"
                        response_text = "哎呀，俺老孙刚才走神了（回复内容为空）。不过说真的，这件事俺目前还没这神通，得想想办法炼个新法宝才行。"

                    return response_text

                # 如果有工具调用，说明 LLM 正在规划行动
                # 此时打印 AI 的思考内容和即将调用的法宝
                print_thought(self.name, response.content, response.tool_calls)
                
                # 在执行工具前，如果是交互模式，询问用户是否干预
                if is_interactive:
                    intervention = ask_for_intervention()
                    if intervention.lower() == "stop":
                        self.last_mood = "sad"
                        return "任务已由用户终止。"
                    elif intervention:
                        # 用户提供了新指令，将其作为 HumanMessage 加入上下文并重新思考
                        messages.append(response) # 记录 AI 的当前想法
                        messages.append(HumanMessage(content=f"请注意主人刚才的干预指令：{intervention}。请根据新指令调整你的行动计划。"))
                        self._append_to_session("User", f"[干预] {intervention}")
                        iteration += 1
                        continue

                # 处理工具调用
                messages.append(response) # 将 AI 的工具请求加入上下文
                # 记录 AI 的工具请求到 Session
                self._append_to_session("MonkeyKing", f"[Tool Call] {json.dumps(response.tool_calls, ensure_ascii=False)}")
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    # 查找并执行工具
                    try:
                        selected_tool = next((t for t in self.tools if t.name == tool_name), None)
                        if selected_tool:
                            tool_result = selected_tool.run(tool_args)
                        else:
                            tool_result = f"错误：未找到名为 '{tool_name}' 的工具。"
                    except Exception as te:
                        tool_result = f"执行工具 '{tool_name}' 时发生异常: {str(te)}"
                    
                    # 使用专门的对话框展示工具执行过程和结果
                    print_tool_execution(tool_name, tool_args, tool_result)
                    
                    # 创建并添加 ToolMessage
                    tool_msg = ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=str(tool_result)
                    )
                    messages.append(tool_msg)
                    
                    # 记录工具执行结果到 Session (使用结构化 JSON 以保留 ID)
                    tool_res_data = {
                        "name": tool_name,
                        "result": tool_result,
                        "id": tool_call["id"]
                    }
                    self._append_to_session("Tool", f"[Tool Result] {json.dumps(tool_res_data, ensure_ascii=False)}")
                
                iteration += 1
            
            return "抱歉，由于对话轮数过多，任务被迫终止。"
            
        except Exception as e:
            self.last_mood = "sad"
            return f"抱歉，我目前处理请求时遇到了一点问题: {str(e)}"

    def trigger_memory_consolidation(self, reason: str) -> bool:
        """异步触发记忆整理"""
        if not self.current_session:
            return False
            
        # 快照当前的 session 用于后台整理，避免线程竞争
        session_snapshot = list(self.current_session)
        # 立即清空内存中的当前 session
        self.current_session = [] 
        if LLMConfig.SESSION_PATH.exists():
            try:
                LLMConfig.SESSION_PATH.unlink()
            except:
                pass
        
        # 启动后台线程执行繁重的总结和提炼工作
        thread = threading.Thread(
            target=self.consolidate_session, 
            args=(session_snapshot,),
            daemon=True
        )
        thread.start()
        return True

    def consolidate_session(self, session_to_consolidate: List[Dict]):
        """
        整理指定的 Session 快照：
        1. 汇总对话到 history.md
        2. 提炼长期记忆到 memory.md (带日期)
        """
        if not session_to_consolidate:
            return

        try:
            session_str = json.dumps(session_to_consolidate, ensure_ascii=False, indent=2)
            start_time = session_to_consolidate[0]["time"]
            end_time = session_to_consolidate[-1]["time"]
            current_date = datetime.now().strftime("%Y-%m-%d")

            # 任务 1: 整理对话摘要存入 history.md
            summary_prompt = (
                f"请整理以下对话 Session 的摘要。时间范围从 {start_time} 到 {end_time}。\n"
                "请包含关键的对话交互、调用的工具及其结果（如有）。以简洁的 Markdown 格式输出。\n\n"
                f"对话内容：\n{session_str}"
            )
            summary_res = self.llm.invoke([HumanMessage(content=summary_prompt)])
            summary_text = summary_res.content

            with open(LLMConfig.HISTORY_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n## Session 整理 ({start_time} 至 {end_time})\n")
                f.write(f"整理时间：{current_date}\n\n")
                f.write(summary_text)
                f.write("\n\n---\n")

            # 任务 2: 提炼长期记忆存入 memory.md
            memory_prompt = (
                "请从以下对话中提炼关于用户的长期记忆（如：行为偏好、重要事实、习惯等）。\n"
                f"当前日期是 {current_date}。请确保每条记录都带有日期信息。\n"
                "请结合现有的记忆进行更新、补充或去重。以 Markdown 列表形式输出完整的长期记忆。\n\n"
                f"现有的长期记忆：\n{self.long_term_memory}\n\n"
                f"新的对话内容：\n{session_str}\n\n"
                "输出完整的长期记忆（包含日期）："
            )
            memory_res = self.llm.invoke([HumanMessage(content=memory_prompt)])
            self.long_term_memory = memory_res.content

            with open(LLMConfig.MEMORY_PATH, "w", encoding="utf-8") as f:
                f.write(self.long_term_memory)

            # 更新系统提示词 (在后台线程完成更新)
            self._update_system_prompt()
            
        except Exception as e:
            print(f"整理 Session 时出错: {e}")

    def _load_long_term_memory(self) -> str:
        """从 memory.md 加载长期记忆"""
        if LLMConfig.MEMORY_PATH.exists():
            try:
                return LLMConfig.MEMORY_PATH.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _load_soul_description(self) -> str:
        """从 soul.md 加载灵魂描述"""
        if LLMConfig.SOUL_PATH.exists():
            try:
                return LLMConfig.SOUL_PATH.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _load_current_session(self) -> List[Dict]:
        """从 session.json 加载当前会话"""
        if LLMConfig.SESSION_PATH.exists():
            try:
                with open(LLMConfig.SESSION_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _append_to_session(self, role: str, content: str):
        """将交互记录追加到 session.json"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "time": timestamp,
            "role": role,
            "content": content
        }
        self.current_session.append(entry)
        
        try:
            with open(LLMConfig.SESSION_PATH, "w", encoding="utf-8") as f:
                json.dump(self.current_session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"无法保存 Session 记录: {e}")

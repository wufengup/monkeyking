from typing import Any, Dict, Optional, List, Union
from src.agents.base_agent import BaseAgent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, BaseMessage, AIMessage, ToolMessage
from src.utils.config import LLMConfig
from src.tools.manager import CapabilityManager
from src.utils.cli import print_tool_execution, print_thought, ask_for_intervention, show_thinking
from src.agents.callback import AgentCallback
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
        
        # 0.1 初始化分身存储目录和路径
        self.agent_dir = LLMConfig.get_agent_dir(name)
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        (self.agent_dir / "memory").mkdir(exist_ok=True)
        (self.agent_dir / "session").mkdir(exist_ok=True)
        
        # 定义实例特定的路径
        self.soul_path = self.agent_dir / "soul.md"
        self.memory_path = self.agent_dir / "memory" / "memory.md"
        self.history_path = self.agent_dir / "memory" / "history.md"
        self.session_path = self.agent_dir / "session" / "session.json"
        
        # 1. 初始化锁，确保多线程下 Session 安全
        self._session_lock = threading.Lock()
        
        # 2. 初始化模型参数
        self.llm_params = model_params or LLMConfig.get_llm_params()
        
        # 2. 初始化能力管理器（先不设置回调，避免循环引用）
        self.capability_manager = CapabilityManager()
        # 3. 手动绑定刷新回调并执行首次刷新
        self.capability_manager.on_capability_added = self._refresh_capabilities
        self._refresh_capabilities()
        
        # 4. 加载长期记忆、当前 Session 和灵魂描述
        self.long_term_memory = self._load_long_term_memory()
        self.current_session = self._load_current_session()
        self.soul_description = self._load_soul_description()
        
        # 对话轮次计数 (以交互条数为准)
        self.turn_count = len(self.current_session)
        
        # 记录最后一次的情绪
        self.last_mood = "neutral"
        
        # 标志位：记录当前回合是否发生了分身切换
        self._agent_switched_in_turn = False
        
        # 系统提示词内容
        self._update_system_prompt()

    def switch_to_agent(self, name: str):
        """切换到另一个分身 Agent 身份"""
        # 1. 切换身份和路径
        self.name = name
        self.agent_dir = LLMConfig.get_agent_dir(name)
        self.agent_dir.mkdir(parents=True, exist_ok=True)
        (self.agent_dir / "memory").mkdir(exist_ok=True)
        (self.agent_dir / "session").mkdir(exist_ok=True)
        
        self.soul_path = self.agent_dir / "soul.md"
        self.memory_path = self.agent_dir / "memory" / "memory.md"
        self.history_path = self.agent_dir / "memory" / "history.md"
        self.session_path = self.agent_dir / "session" / "session.json"
        
        # 2. 重新加载新分身的配置和历史
        self.long_term_memory = self._load_long_term_memory()
        self.current_session = self._load_current_session()
        self.soul_description = self._load_soul_description()
        self.turn_count = len(self.current_session)
        
        # 3. 刷新法宝并更新系统提示词
        self._refresh_capabilities()
        
        # 4. 设置标志位，通知当前的 run 循环身份已改变
        self._agent_switched_in_turn = True

    def _refresh_capabilities(self):
        """刷新并重新绑定法宝列表"""
        self.tools = self.capability_manager.get_langchain_tools()
        
        # 遍历底层原始工具，为需要 Agent 引用的工具注入 self
        for tool in self.capability_manager.tools:
            if hasattr(tool, "_agent_ref") or getattr(tool, "name", "") in ["memory_manager", "agent_creator"]:
                tool._agent_ref = self

        # 注意：这里会创建一个新的 ChatOpenAI 实例并重新绑定当前所有工具
        self.llm = ChatOpenAI(**self.llm_params).bind_tools(self.tools)
        # 顺便更新系统提示词，让大圣知道自己有了新神通或法宝
        if hasattr(self, "system_prompt_content"):
            self._update_system_prompt()

    def _update_system_prompt(self, query: str = ""):
        """更新系统提示词，包含灵魂描述、长期记忆和神通 SOP"""
        # 根据当前身份决定称呼
        display_name = "大圣" if self.name.lower() == "monkeyking" else self.name
        
        self.system_prompt_content = (
            f"你是一个名为 {display_name} 的个人生活助理 Agent。\n\n"
        )
        
        # 注入灵魂描述 (包含个性、能力和自我认知)
        if self.soul_description:
            self.system_prompt_content += f"关于你的灵魂定义与行为准则：\n{self.soul_description}\n\n"
        
        # 动态注入已点亮的神通 (Skills)，支持按 query 激活
        skills_prompt = self.capability_manager.get_skills_prompt_for_query(query)
        if skills_prompt:
            self.system_prompt_content += f"{skills_prompt}\n"

        # 显式强化主动性、透明度、目标导向及情感表达要求
        self.system_prompt_content += (
            "请务必遵守以下行为准则：\n"
            "1. 面对复杂任务，先告知用户你的执行计划。\n"
            "2. 始终锁定用户的核心问题（最初的目标）。\n"
            "3. 如果在引导用户安装了新工具或技能后，必须先验证工具可用性，然后立即回归到最初的任务上并闭环解决它。\n"
            "4. **严禁 Mock 工具**：你创建或更新的任何能力（Tool/Skill）都必须具备真实、有效的逻辑（如调用 API、执行指令、处理文件），绝对禁止只打印一个“成功”或返回固定数据来误导用户。\n"
            "5. 遇到工具调用错误时，利用你的推理能力尝试自主寻找其他解决方法。\n"
            "6. 只有在真正需要用户决策或提供信息时才向用户提问。\n"
            f"7. 始终保持符合你当前身份（{display_name}）的语气，展现你的个性和智慧。\n"
            "8. **诚实面对局限**：如果你缺乏对应的法宝或神通来完成任务，请直接告诉用户你目前做不到，并建议炼制新法宝。绝对禁止做出虚假承诺。\n"
            "9. **严禁脑补结果**：在调用法宝（Tool）之前，绝对禁止在回复中假定法宝已经成功执行（例如说‘我已经为你设置好了’）。你必须先施展法宝，根据法宝返回的真实结果，再向主人汇报。\n"
            "10. **关注系统通知**：如果对话历史中出现了以 `[提示]` 或 `[错误]` 开头的系统通知（System 消息），说明你的分身在执行任务或操作界面时遇到了意外。你必须在回复中诚实地告知主人发生了什么，并视情况致歉。\n"
            f"11. **情感表达**：请根据对话内容表现出你的喜怒哀乐。并在输出答案的最开头，使用格式 `[MOOD:情绪]` 标明你当前的情绪状态（可选情绪：happy, angry, sad, neutral, excited）。例如：`[MOOD:happy] 哈哈，{display_name}来也！`。\n\n"
        )

        if self.long_term_memory:
            self.system_prompt_content += (
                f"\n=== 长期记忆 (Long-term Memory) ===\n"
                f"{display_name}，请务必特别关注【核心规则与偏好】部分，那是主人立下的禁令，你必须严格遵守！\n"
                f"【重要警告】无论长期记忆中记录了哪些其他分身（Agent）的人设或档案，那都是别人！你现在的唯一身份是：{display_name}！\n"
                f"{self.long_term_memory}\n"
            )

    def run(self, input_data: Dict[str, Any], is_interactive: bool = False, callback: Optional[AgentCallback] = None) -> str:
        """
        处理用户请求，支持多轮 Tool 调用、思考展示及人工干预。
        """
        query = input_data.get("query", "")
        if not query:
            return ""

        # 重置切换标志
        self._agent_switched_in_turn = False

        try:
            # 记录初始工具数量，用于检测是否由于技能激活而增加了新工具
            initial_tool_count = len(self.capability_manager.tools)

            # 1. 记录用户输入到 Session
            self._append_to_session("User", query)
            # 1.1 按当前 query 更新一次系统提示词（激活匹配的 skills）
            # 注意：此过程可能触发技能包的延迟加载，包括加载其 scripts 目录下的新法宝
            self._update_system_prompt(query=query)
            
            # 1.2 如果增加了新工具，需要重新绑定 LLM
            if len(self.capability_manager.tools) > initial_tool_count:
                self._refresh_capabilities()

            # 2. 构建初始消息列表 (包含上下文)
            messages = [SystemMessage(content=self.system_prompt_content)]
            
            # 添加全部对话作为上下文
            for msg in self.current_session:
                role = msg["role"]
                content = msg["content"]
                if role == "User":
                    messages.append(HumanMessage(content=content))
                elif role == "System":
                    messages.append(SystemMessage(content=f"系统通知：{content}"))
                elif role == self.name or role == "MonkeyKing":
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

                    self._append_to_session(self.name, response_text)
                    
                    # 检查是否需要整理 Session (从配置中读取阈值)
                    memory_cfg = LLMConfig.get_memory_config()
                    window = memory_cfg.get("consolidation_window", 40)
                    if len(self.current_session) >= window:
                        self.trigger_memory_consolidation("自动轮次阈值触发")
                    
                    # 鲁棒性优化：如果 response_text 为空（可能由于情绪解析导致），说明大模型未能给出有效回答
                    if not response_text.strip():
                        self.last_mood = "sad"
                        if self.name.lower() == "monkeyking":
                            response_text = "哎呀，俺老孙刚才走神了（回复内容为空）。不过说真的，这件事俺目前还没这神通，得想想办法炼个新法宝才行。"
                        else:
                            response_text = f"抱歉，{display_name}刚才走神了（回复内容为空）。请重新描述你的需求。"

                    return response_text

                # 如果有工具调用，说明 LLM 正在规划行动
                # 此时打印 AI 的思考内容和即将调用的法宝
                print_thought(self.name, response.content, response.tool_calls)
                if callback:
                    callback.on_thought(response.content)
                
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
                self._append_to_session(self.name, f"[Tool Call] {json.dumps(response.tool_calls, ensure_ascii=False)}")
                
                for tool_call in response.tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["args"]
                    
                    if callback:
                        callback.on_tool_start(tool_name, tool_args)
                    
                    # 查找并执行工具
                    try:
                        selected_tool = next((t for t in self.tools if t.name == tool_name), None)
                        if selected_tool:
                            tool_result = selected_tool.run(tool_args)
                        else:
                            tool_result = f"错误：未找到名为 '{tool_name}' 的工具。"
                    except Exception as te:
                        tool_result = f"执行工具 '{tool_name}' 时发生异常: {str(te)}"
                    
                    if callback:
                        callback.on_tool_end(tool_name, tool_result)
                    
                    # 使用专门的对话框展示工具执行过程和结果
                    print_tool_execution(tool_name, tool_args, tool_result)
                    
                    # 创建并添加 ToolMessage
                    tool_msg = ToolMessage(
                        tool_call_id=tool_call["id"],
                        content=str(tool_result)
                    )
                    messages.append(tool_msg)
                    
                    # 如果在执行工具（如 agent_creator）的过程中发生了分身切换
                    if getattr(self, "_agent_switched_in_turn", False):
                        # 我们不能把旧的 tool result 和后续的思考写入新的 session 中
                        # 直接中断循环，返回切换成功的消息
                        self.last_mood = "happy"
                        if self.name.lower() == "monkeyking":
                            switch_msg = "✅ 已收回毫毛，变回大圣本尊！有什么我可以帮您的？"
                        else:
                            switch_msg = f"✅ 已成功切换到分身 '{self.name}'！"
                        # 将这条成功消息记录到新分身的 session 中
                        self._append_to_session(self.name, switch_msg)
                        return switch_msg

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
            if callback:
                callback.on_error(e)
            self.last_mood = "sad"
            error_msg = f"抱歉，我目前处理请求时遇到了一点问题：{str(e)}"
            self._append_to_session(self.name, error_msg)
            return error_msg

    def trigger_memory_consolidation(self, reason: str) -> bool:
        """异步触发记忆整理"""
        if not self.current_session:
            return False
            
        # 按照用户要求：每次记忆整理，将session的一半整理到记忆中，剩下的一半仍然放到session中。
        # 这里解释为：保留最新的那一半（Context），将较旧的那一半（History）归档到长期记忆。
        mid_point = len(self.current_session) // 2
        
        # 切分 Session
        session_to_consolidate = self.current_session[:mid_point] # 较旧的一半 -> 归档
        remaining_session = self.current_session[mid_point:]      # 较新的一半 -> 保留
        
        # 快照当前的 session 和路径用于后台整理，避免由于分身切换导致路径错乱
        # 注意：这里只整理被切分出去的那一部分
        session_snapshot = list(session_to_consolidate)
        paths_snapshot = {
            "history": self.history_path,
            "memory": self.memory_path,
            "session": self.session_path
        }
        
        # 更新内存中的当前 session 为剩余部分
        self.current_session = list(remaining_session)
        
        # 立即将剩余的 session 写回磁盘，确保断电不丢失
        with self._session_lock:
            try:
                if self.session_path.parent.exists():
                    with open(self.session_path, "w", encoding="utf-8") as f:
                        json.dump(self.current_session, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"整理切分后保存 Session 失败: {e}")
        
        # 启动后台线程执行繁重的总结和提炼工作
        thread = threading.Thread(
            target=self.consolidate_session, 
            args=(session_snapshot, paths_snapshot),
            daemon=True
        )
        thread.start()
        return True

    def consolidate_session(self, session_to_consolidate: List[Dict], paths: Dict[str, Path] = None):
        """
        整理指定的 Session 快照：
        1. 汇总对话到 history.md
        2. 提炼长期记忆到 memory.md (带日期)
        """
        if not session_to_consolidate:
            return

        # 如果没有提供路径快照（兼容旧调用），则使用当前实例路径
        history_path = paths["history"] if paths else self.history_path
        memory_path = paths["memory"] if paths else self.memory_path

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

            with open(history_path, "a", encoding="utf-8") as f:
                f.write(f"\n## Session 整理 ({start_time} 至 {end_time})\n")
                f.write(f"整理时间：{current_date}\n\n")
                f.write(summary_text)
                f.write("\n\n---\n")

            # 任务 2: 提炼长期记忆存入 memory.md
            # 先加载目标记忆文件的现有内容（因为整理可能是在切换分身后进行的）
            existing_memory = ""
            if memory_path.exists():
                existing_memory = memory_path.read_text(encoding="utf-8")

            memory_prompt = (
                "你现在是大圣的‘记忆元神’。请从以下对话中提炼长期记忆，并严格按以下 Markdown 格式整合到现有记忆中：\n\n"
                "### 1. [核心规则与偏好]\n"
                "这里只记录用户明确要求的‘规则’、‘禁忌’或‘操作准则’（例如：‘以后整合前必须确认’、‘不要使用某种语气’）。\n\n"
                "### 2. [重要事实]\n"
                "记录关于用户、环境或项目的客观事实（如：用户所在地、主目录路径、正在进行的项目名）。\n\n"
                "### 3. [习惯与偏好]\n"
                "记录用户表现出的行为倾向（如：喜欢查天气、关注 AI 新闻）。\n\n"
                "### 4. [近期动态 (按日期)]\n"
                "简要记录每天发生的大事。请保留原有的日期记录，但要精简内容。\n\n"
                "--- 任务要求 ---\n"
                "1. 结合现有的记忆进行更新、补充或去重。\n"
                "2. 如果对话中有用户明确要求的‘以后要如何如何’，必须将其精准记录在‘核心规则与偏好’中。\n"
                f"3. 当前日期是 {current_date}。\n\n"
                f"现有的长期记忆：\n{existing_memory}\n\n"
                f"新的对话内容：\n{session_str}\n\n"
                "请输出整合后的完整长期记忆："
            )
            memory_res = self.llm.invoke([HumanMessage(content=memory_prompt)])
            new_long_term_memory = memory_res.content

            with open(memory_path, "w", encoding="utf-8") as f:
                f.write(new_long_term_memory)

            # 如果当前活跃的分身正是整理的对象，则更新内存中的记忆
            if memory_path == self.memory_path:
                self.long_term_memory = new_long_term_memory
                self._update_system_prompt()
            
        except Exception as e:
            print(f"整理 Session 时出错：{e}")

    def _load_long_term_memory(self) -> str:
        """从 memory.md 加载长期记忆"""
        if self.memory_path.exists():
            try:
                return self.memory_path.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _load_soul_description(self) -> str:
        """从 soul.md 加载灵魂描述"""
        if self.soul_path.exists():
            try:
                return self.soul_path.read_text(encoding="utf-8")
            except Exception:
                return ""
        return ""

    def _load_current_session(self) -> List[Dict]:
        """从 session.json 加载当前会话"""
        if self.session_path.exists():
            try:
                with open(self.session_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _append_to_session(self, role: str, content: str):
        """将交互记录追加到 session.json (线程安全)"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "time": timestamp,
            "role": role,
            "content": content
        }
        
        with self._session_lock:
            self.current_session.append(entry)
            try:
                # 确保父目录存在
                self.session_path.parent.mkdir(parents=True, exist_ok=True)
                with open(self.session_path, "w", encoding="utf-8") as f:
                    json.dump(self.current_session, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"无法保存 Session 记录到 {self.session_path}: {e}")

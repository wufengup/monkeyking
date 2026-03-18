# MonkeyKing 开发者 Wiki

MonkeyKing 是一个基于大语言模型（LLM）的智能 Agent 框架，旨在通过**神通 (Skills)** 和 **法宝 (Tools)** 的组合，赋予 AI 解决复杂任务的能力。它不仅支持标准的对话交互，还具备独特的**分身 (Agent Cloning)** 机制，允许在运行时动态切换不同的人格和记忆空间。

---

## 1. 核心概念 (Core Concepts)

### 1.1 Agent (大圣)
MonkeyKing 的核心是一个基于 LLM 的智能体。它负责理解用户意图，规划任务，调度工具，并维护对话上下文。
- **本体 (MonkeyKing)**: 默认的主体 Agent，拥有全局记忆。
- **分身 (Clones)**: 基于特定人格设定的独立 Agent 实例，拥有独立的记忆和会话历史。

### 1.2 Skill (神通)
Skill 是 MonkeyKing 的高层次能力单元，本质上是一套 **标准作业程序 (SOP)**。
- **作用**: 指导 Agent *如何* 完成特定类型的任务（如“写新闻简报”、“管理文件”）。
- **构成**:
  - `SKILL.md`: 定义技能名称、描述和详细的 SOP (Prompt)。
  - `scripts/`: (可选) 包含该技能专属的 Python 代码和 Tool 实现。
- **加载机制**: 支持 Claude 风格的延迟加载，仅在需要时加载完整 SOP 和脚本。

### 1.3 Tool (法宝)
Tool 是具体的执行单元，对应一个 Python 函数或类方法。
- **作用**: 执行实际的系统操作（如读写文件、搜索网页、执行命令）。
- **实现**: 继承自 `BaseMonkeyKingTool`，并转换为 LangChain 兼容格式。

### 1.4 Memory (记忆)
MonkeyKing 拥有两层记忆系统：
- **Session (短期记忆)**: 当前对话的上下文，存储在 `session/` 目录下的 JSON 文件中。
- **Consolidated Memory (长期记忆)**: 经过整理和压缩的关键信息，存储在 `memory/` 目录下。后台线程会定期将 Session 转化为 Long-term Memory。

---

## 2. 分身系统 (Agent Cloning System)

MonkeyKing 具备强大的**分身机制**，允许在单个进程内无缝切换不同的人格和上下文。

### 2.1 架构原理
- **热重载 (Hot-Swapping)**: 切换分身时，不需要重启进程。`AssistantAgent` 会动态更新自身的属性（Name, System Prompt, Memory Path, Session Path），实现“变身”。
- **状态隔离**:
  - **本体**: 数据存储在 `~/.monkeyking/` (或配置的根目录)。
  - **分身**: 数据存储在 `~/.monkeyking/agents/<agent_name>/`。
  - 每个分身拥有独立的 `soul.md` (人格定义), `session.json` (对话历史) 和 `memory.md` (长期记忆)。
- **防污染机制 (Break-Early)**: 切换指令执行后，当前 Agent 的思考循环会立即中断 (`_agent_switched_in_turn` 标志位)，防止旧 Agent 的思维惯性污染新 Agent 的 Session。

### 2.2 核心指令
分身功能由 `agent-creator` 技能包提供：
- **创建分身**: `create_agent(name="...", soul_content="...")`
  - 在 `agents/` 目录下创建新目录，并写入 `soul.md`。
- **切换分身**: `switch_agent(name="...")`
  - 触发热重载，切换到指定分身。
  - 如果只有两个分身（本体+1个），不指定名称会自动切换到另一个。
- **列出分身**: `list_agents()`
  - 显示所有可用的分身。

---

## 3. 目录结构说明 (Directory Structure)

```text
monkeyking/
├── .monkeyking/               # [用户数据] 默认存储位置
│   ├── config.json            # 用户配置 (API Key等)
│   ├── soul.md                # 本体人格定义
│   ├── session/               # 本体会话记录
│   ├── memory/                # 本体长期记忆
│   └── agents/                # [分身数据]
│       └── <AgentName>/       # 分身独立目录
│           ├── soul.md
│           ├── session/
│           └── memory/
├── src/
│   ├── agents/                # Agent 核心逻辑
│   │   └── assistant_agent.py # 主 Agent 实现 (含切换逻辑)
│   ├── skills/                # 技能系统
│   │   ├── base_skill.py      # Skill 基类
│   │   └── skillpacks/        # 内置技能包
│   │       ├── agent-creator/ # [核心] 分身管理技能
│   │       ├── deep-research/ # 深度搜索技能
│   │       └── ...
│   ├── tools/                 # 基础工具集
│   │   ├── base_tool.py       # Tool 基类
│   │   ├── manager.py         # 能力管理器 (加载 Skills/Tools)
│   │   └── ...
│   └── utils/                 # 通用工具
│       └── config.py          # 配置管理
├── main.py                    # 程序入口
└── README.md                  # 项目说明
```

---

## 4. 开发指南 (Developer Guide)

### 4.1 创建新 Skill (神通)
1. 在 `src/skills/skillpacks/` 下创建一个新目录，例如 `my-new-skill`。
2. 创建 `SKILL.md` 文件：
   ```markdown
   ---
   name: MyNewSkill
   description: 一个用于演示的新神通。
   ---
   
   # MyNewSkill SOP
   
   当用户询问关于 X 的问题时，请遵循以下步骤：
   1. 使用工具 Y 获取数据。
   2. 分析数据并回答。
   ```
3. (可选) 如果需要自定义 Python 逻辑，创建 `scripts/` 目录并在其中编写 Python 脚本。`CapabilityManager` 会自动加载其中的 Tool 类。

### 4.2 创建新 Tool (法宝)
1. 在 `src/tools/` 下创建 Python 文件，或在 Skill 的 `scripts/` 中创建。
2. 继承 `BaseMonkeyKingTool` 并实现必要方法：
   ```python
   from src.tools.base_tool import BaseMonkeyKingTool
   from langchain_core.tools import StructuredTool
   
   class MyTool(BaseMonkeyKingTool):
       @property
       def name(self): return "my_tool"
       
       @property
       def description(self): return "这是一个演示工具"
       
       def to_langchain_tool(self):
           return StructuredTool.from_function(
               func=self._run,
               name=self.name,
               description=self.description
           )
           
       def _run(self, param: str):
           return f"Executed with {param}"
   ```
3. 如果是在 `src/tools/` 下，需要在 `src/tools/manager.py` 中注册；如果是在 Skill 的 `scripts/` 下，会自动加载。

### 4.3 调试
- 使用 `python main.py --debug` 启动调试模式。
- 利用 `TRAE-debugger` 进行运行时断点调试。
- 查看 `logs/` (如果配置了日志) 或控制台输出。

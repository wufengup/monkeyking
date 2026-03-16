from typing import List, Dict, Any, Type
from src.tools.base_tool import BaseMonkeyKingTool
from src.tools.file_reader import FileReaderTool
from src.tools.directory_lister import DirectoryListerTool
from src.tools.directory_creator import DirectoryCreatorTool
from src.tools.file_writer import FileWriterTool
from src.tools.tool_config_manager import ToolConfigManagerTool
from src.tools.web_search import WebSearchTool
from src.tools.memory_consolidation import MemoryConsolidationTool
from src.tools.scheduling_tools import ScheduleTaskTool, ListTasksTool, ManageTaskTool
from src.utils.scheduler import SchedulerManager
from src.skills.base_skill import BaseMonkeyKingSkill
from src.skills.skill_pack import load_claude_skill_pack_from_dir
from src.utils.config import LLMConfig
from langchain_core.tools import BaseTool
import importlib
import sys
import os
from pathlib import Path

class CapabilityManager:
    """
    MonkeyKing 能力管理器：
    同时管理“法宝 (Tools)”和“神通 (Skills)”。
    """
    def __init__(self, on_capability_added=None):
        self.tools: List[BaseMonkeyKingTool] = []
        self.skills: List[BaseMonkeyKingSkill] = []
        self.on_capability_added = on_capability_added
        
        # 0. 初始化时空管理器
        self.scheduler = SchedulerManager(capability_manager=self)
        
        # 1. 注册内置法宝 (Tools)
        self._register_builtin_tools()
        
        # 2. 特殊法宝：法宝配置管理器
        config_manager = ToolConfigManagerTool()
        self.register_tool(config_manager)
        
        # 3. 自动加载外部法宝和神通
        self._load_installed_capabilities()
    
    def _register_builtin_tools(self):
        self.register_tool(FileReaderTool())
        self.register_tool(DirectoryListerTool())
        self.register_tool(DirectoryCreatorTool())
        self.register_tool(FileWriterTool())
        self.register_tool(WebSearchTool())
        
        # 定时任务法宝
        st = ScheduleTaskTool(); st._scheduler = self.scheduler
        lt = ListTasksTool(); lt._scheduler = self.scheduler
        mt = ManageTaskTool(); mt._scheduler = self.scheduler
        self.register_tool(st)
        self.register_tool(lt)
        self.register_tool(mt)
        
        # 特殊法宝：记忆整理器
        self.memory_tool = MemoryConsolidationTool()
        self.register_tool(self.memory_tool)

    def register_tool(self, tool: BaseMonkeyKingTool):
        """注册一个新法宝"""
        if any(t.name == tool.name for t in self.tools):
            return
        self.tools.append(tool)
        if self.on_capability_added:
            self.on_capability_added()

    def register_skill(self, skill: BaseMonkeyKingSkill):
        """注册一个新神通"""
        if any(s.name == skill.name for s in self.skills):
            return
        
        # 如果是 Claude 风格技能包，设置延迟加载脚本的回调
        if hasattr(skill, "_on_load_callback"):
            skill._on_load_callback = self._load_tools_from_skill_scripts
            
        self.skills.append(skill)
        if self.on_capability_added:
            self.on_capability_added()

    def get_langchain_tools(self) -> List[BaseTool]:
        """获取所有已注册法宝的 LangChain 兼容列表"""
        return [t.to_langchain_tool() for t in self.tools]

    def get_tool_names(self) -> List[str]:
        """获取所有已注册法宝的名称"""
        return [t.name for t in self.tools]

    def get_skills_prompt(self) -> str:
        """获取所有已注册神通的 SOP 描述，用于注入 System Prompt"""
        return self.get_skills_prompt_for_query("")

    def get_skills_prompt_for_query(self, query: str) -> str:
        """
        按 query 选择性注入技能：
        - 匹配的技能：加载完整上下文 (SOP, references, scripts)
        - 未匹配的技能：仅展示名称和描述 (按用户要求减少上下文)
        """
        if not self.skills:
            return ""

        matched: List[BaseMonkeyKingSkill] = []
        others: List[BaseMonkeyKingSkill] = []
        q = query or ""
        
        for skill in self.skills:
            matcher = getattr(skill, "matches_query", None)
            if callable(matcher) and matcher(q):
                matched.append(skill)
            else:
                others.append(skill)

        prompt = "\n=== 灵猴神通 (Skills) ===\n"
        
        # 1. 对于匹配的技能，加载完整上下文
        if matched:
            prompt += "\n[已激活的神通 - 包含详细 SOP]\n"
            for skill in matched:
                prompt += f"【{skill.name}】: {skill.description}\n"
                renderer = getattr(skill, "render_for_query", None)
                sop_content = renderer(q) if callable(renderer) else skill.sop
                prompt += f"SOP 指南：\n{sop_content}\n"
                if skill.required_tools:
                    prompt += f"依赖法宝: {', '.join(skill.required_tools)}\n"
                prompt += "---\n"

        # 2. 对于未匹配的技能，仅展示名称和描述，方便 LLM 发现
        if others:
            prompt += "\n[可选神通 - 仅展示概览]\n"
            for skill in others:
                prompt += f"- {skill.name}: {skill.description}\n"
        
        return prompt

    def _load_installed_capabilities(self):
        """扫描内置与用户目录能力并加载"""
        # 1. 加载内置法宝 (src/tools)
        self._load_from_dir(Path(__file__).parent, "src.tools")

        # 2. 加载代码目录中的内置 Skill Packs (src/skills/skillpacks)
        builtin_skillpacks_dir = Path(__file__).parent.parent / "skills" / "skillpacks"
        self._load_skills_from_dir(builtin_skillpacks_dir)
        
        # 3. 加载用户主目录下的法宝 (~/.monkeyking/tools)
        if LLMConfig.TOOLS_DIR.exists():
            self._load_from_dir(LLMConfig.TOOLS_DIR, "external_tools")

        # 4. 加载用户主目录下的神通 (~/.monkeyking/skills)
        if LLMConfig.SKILLS_DIR.exists():
            self._load_skills_from_dir(LLMConfig.SKILLS_DIR)

    def _load_tools_from_skill_scripts(self, skill_dir: Path):
        """从技能包的 scripts 目录加载法宝"""
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists() and scripts_dir.is_dir():
            # 将项目根目录和 scripts 目录加入 sys.path 以便导入
            project_root = str(Path(__file__).parent.parent.parent)
            if project_root not in sys.path:
                sys.path.append(project_root)
            if str(scripts_dir) not in sys.path:
                sys.path.append(str(scripts_dir))
            
            for file in scripts_dir.glob("*.py"):
                if file.name == "__init__.py": continue
                
                module_name = f"skill_script_{skill_dir.name}_{file.stem}"
                try:
                    spec = importlib.util.spec_from_file_location(module_name, file)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseMonkeyKingTool) and attr is not BaseMonkeyKingTool:
                            instance = attr()
                            if hasattr(instance, "_scheduler"):
                                instance._scheduler = self.scheduler
                            self.register_tool(instance)
                except Exception as e:
                    print(f"从技能脚本 {file} 加载法宝失败: {e}")

    def _load_from_dir(self, directory: Path, package_prefix: str):
        """通用加载逻辑：扫描目录并加载 BaseMonkeyKingTool"""
        # 如果加载外部目录，需要确保其在 sys.path 中
        is_external = not str(directory).startswith(str(Path(__file__).parent.parent.parent))
        if is_external and str(directory) not in sys.path:
            sys.path.append(str(directory))

        for file in directory.glob("*.py"):
            if file.name in ["__init__.py", "base_tool.py", "manager.py", 
                            "file_reader.py", "directory_lister.py", 
                            "directory_creator.py", "file_writer.py",
                            "skill_creator.py",
                            "web_search.py", "memory_consolidation.py",
                            "tool_config_manager.py", "scheduling_tools.py"]:
                continue
            
            # 外部模块直接用 stem，内部模块带前缀
            module_name = file.stem if is_external else f"{package_prefix}.{file.stem}"
            
            try:
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                module = importlib.import_module(module_name)
                
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseMonkeyKingTool) and attr is not BaseMonkeyKingTool:
                        instance = attr()
                        if hasattr(instance, "_scheduler"): # 自动注入 scheduler
                            instance._scheduler = self.scheduler
                        self.register_tool(instance)
            except Exception as e:
                print(f"加载法宝模块 {module_name} 失败: {e}")

    def _load_skills_from_dir(self, directory: Path):
        """扫描目录并加载 Skill（延迟加载）"""
        if not directory.exists():
            return

        if str(directory) not in sys.path:
            sys.path.append(str(directory))

        for skill_dir in directory.iterdir():
            if skill_dir.is_dir():
                # 1) 优先加载 Claude/OpenClaw 风格 SKILL.md 技能包 (元数据模式)
                claude_pack = load_claude_skill_pack_from_dir(skill_dir)
                if claude_pack:
                    self.register_skill(claude_pack)
                    continue

                # 2) 回退到旧版 Python Skill 动态加载
                # 寻找目录下的 .py 文件
                for file in skill_dir.glob("*.py"):
                    if file.name == "__init__.py": continue
                    
                    module_name = f"{skill_dir.name}.{file.stem}"
                    if str(skill_dir) not in sys.path:
                        sys.path.append(str(skill_dir))
                        
                    try:
                        # 动态导入
                        spec = importlib.util.spec_from_file_location(module_name, file)
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, BaseMonkeyKingSkill) and attr is not BaseMonkeyKingSkill:
                                self.register_skill(attr())
                    except Exception as e:
                        print(f"加载神通模块 {module_name} 失败: {e}")

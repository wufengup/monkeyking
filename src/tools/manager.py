from typing import List, Dict, Any, Type
from src.tools.base_tool import BaseMonkeyKingTool
from src.tools.file_reader import FileReaderTool
from src.tools.directory_lister import DirectoryListerTool
from src.tools.directory_creator import DirectoryCreatorTool
from src.tools.file_writer import FileWriterTool
from src.tools.skill_installer import SkillInstallerTool
from src.tools.tool_config_manager import ToolConfigManagerTool
from src.tools.web_search import WebSearchTool
from src.tools.baidu_search import BaiduSearchTool
from src.tools.memory_consolidation import MemoryConsolidationTool
from src.tools.scheduling_tools import ScheduleTaskTool, ListTasksTool, ManageTaskTool
from src.utils.scheduler import SchedulerManager
from src.skills.base_skill import BaseMonkeyKingSkill
from src.skills.skill_self_evolution import SkillSelfEvolution
from src.skills.weather_advisory_skill import WeatherAdvisorySkill
from src.skills.file_governance_skill import FileGovernanceSkill
from src.skills.deep_research_skill import DeepResearchSkill
from src.skills.memory_governance_skill import MemoryGovernanceSkill
from src.skills.scheduling_skill import SchedulingSkill
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
        
        # 2. 注册内置神通 (Skills)
        self._register_builtin_skills()
        
        # 特殊法宝：法宝配置管理器
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
        self.register_tool(BaiduSearchTool())
        
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
        
        # 特殊法宝：技能安装器
        installer = SkillInstallerTool()
        installer._tool_manager = self
        self.register_tool(installer)

    def _register_builtin_skills(self):
        self.register_skill(SkillSelfEvolution())
        self.register_skill(WeatherAdvisorySkill())
        self.register_skill(FileGovernanceSkill())
        self.register_skill(DeepResearchSkill())
        self.register_skill(MemoryGovernanceSkill())
        self.register_skill(SchedulingSkill())

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
        if not self.skills:
            return ""
        
        prompt = "\n=== 已点亮的神通 (Skills) ===\n"
        for skill in self.skills:
            prompt += f"【{skill.name}】: {skill.description}\n"
            prompt += f"SOP 指南：\n{skill.sop}\n"
            if skill.required_tools:
                prompt += f"依赖法宝: {', '.join(skill.required_tools)}\n"
            prompt += "---\n"
        return prompt

    def _load_installed_capabilities(self):
        """扫描内置和用户主目录下的 tools 和 skills 目录并加载"""
        # 1. 加载内置法宝 (src/tools)
        self._load_from_dir(Path(__file__).parent, "src.tools")
        
        # 2. 加载用户主目录下的法宝 (~/.monkeyking/tools)
        if LLMConfig.TOOLS_DIR.exists():
            self._load_from_dir(LLMConfig.TOOLS_DIR, "external_tools")

        # 3. 加载用户主目录下的神通 (~/.monkeyking/skills)
        if LLMConfig.SKILLS_DIR.exists():
            self._load_skills_from_dir(LLMConfig.SKILLS_DIR)

    def _load_from_dir(self, directory: Path, package_prefix: str):
        """通用加载逻辑：扫描目录并加载 BaseMonkeyKingTool"""
        # 如果加载外部目录，需要确保其在 sys.path 中
        is_external = not str(directory).startswith(str(Path(__file__).parent.parent.parent))
        if is_external and str(directory) not in sys.path:
            sys.path.append(str(directory))

        for file in directory.glob("*.py"):
            if file.name in ["__init__.py", "base_tool.py", "manager.py", 
                            "file_reader.py", "directory_lister.py", 
                            "directory_creator.py", "file_writer.py", "skill_installer.py",
                            "baidu_search.py", "web_search.py", "memory_consolidation.py",
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
        """扫描目录并加载 BaseMonkeyKingSkill (每个 skill 一个目录)"""
        if str(directory) not in sys.path:
            sys.path.append(str(directory))

        for skill_dir in directory.iterdir():
            if skill_dir.is_dir():
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

    def install_new_tool(self, file_name: str, code: str) -> str:
        """持久化新法宝到主目录并加载"""
        try:
            LLMConfig.TOOLS_DIR.mkdir(parents=True, exist_ok=True)
            file_path = LLMConfig.TOOLS_DIR / f"{file_name}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            self._load_installed_capabilities()
            return f"成功：法宝已炼成并保存至 {file_path}，当前已可施展。"
        except Exception as e:
            return f"炼制失败: {str(e)}"

    def install_new_skill(self, skill_name: str, file_name: str, code: str) -> str:
        """持久化新神通到主目录并加载 (每个 skill 独立目录)"""
        try:
            skill_path = LLMConfig.SKILLS_DIR / skill_name
            skill_path.mkdir(parents=True, exist_ok=True)
            file_path = skill_path / f"{file_name}.py"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(code)
            self._load_installed_capabilities()
            return f"成功：神通已点亮并保存至 {file_path}，大圣已心领神会。"
        except Exception as e:
            return f"领悟失败: {str(e)}"

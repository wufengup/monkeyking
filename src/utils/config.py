import os
import json
import shutil
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from pathlib import Path

# 加载 .env 文件作为备选的环境变量
load_dotenv()

class LLMConfig:
    """
    LLM 配置管理类
    1. 所有的配置文件都存放在用户主目录下的 .monkeyking 目录。
    2. 如果当前代码目录下存在 .monkeyking 目录，则在初始化时将其内容同步（覆盖）到主目录。
    3. 支持通过 monkeyking init 命令自动生成配置目录和文件。
    4. 支持在 config.json 中配置多个大模型，通过 default 参数选中。
    5. 支持通过命令行参数、配置文件和环境变量进行多层覆盖。
    """
    
    # 核心配置目录固定为用户主目录
    CONFIG_DIR = Path.home() / ".monkeyking"
    # 本地代码目录下的配置（用于同步）
    LOCAL_CONFIG_DIR = Path(".monkeyking")
    
    # 动态属性，由 ensure_config_exists 初始化
    CONFIG_PATH = CONFIG_DIR / "config.json"
    MEMORY_DIR = CONFIG_DIR / "memory"
    SESSION_DIR = CONFIG_DIR / "session"
    HISTORY_PATH = MEMORY_DIR / "history.md"
    MEMORY_PATH = MEMORY_DIR / "memory.md"
    SESSION_PATH = SESSION_DIR / "session.json"
    SOUL_PATH = CONFIG_DIR / "soul.md"
    TOOLS_DIR = CONFIG_DIR / "tools"
    SKILLS_DIR = CONFIG_DIR / "skills"
    AGENTS_DIR = CONFIG_DIR / "agents"
    
    # 初始化标记，避免重复执行同步逻辑
    _initialized = False
    
    # 默认配置模板
    DEFAULT_CONFIG = {
        "default": "gpt-4o-mini",
        "models": {
            "gpt-4o-mini": {
                "provider": "openai",
                "model_name": "gpt-4o-mini",
                "api_key": "",
                "base_url": None
            },
            "ark": {
                "provider": "volcengine",
                "model_name": "ep-xxxxxxxxxxxx",
                "api_key": "",
                "base_url": "https://ark.cn-beijing.volces.com/api/v3"
            }
        },
        "tools": {
            "weather_checker": {
                "gaode_api_key": "",
                "openweathermap_api_key": ""
            },
            "web_search": {
                "appbuilder_api_key": ""
            },
            "feishu_channel": {
                "app_id": "",
                "app_secret": "",
                "verification_token": ""
            }
        },
        "memory": {
            "consolidation_window": 50
        },
        "behavior": {
            "auto_approve_tools": False
        }
    }

    @classmethod
    def _update_paths(cls, new_dir: Path):
        """更新所有相关的路径属性"""
        cls.CONFIG_DIR = new_dir
        cls.CONFIG_PATH = cls.CONFIG_DIR / "config.json"
        cls.MEMORY_DIR = cls.CONFIG_DIR / "memory"
        cls.SESSION_DIR = cls.CONFIG_DIR / "session"
        cls.HISTORY_PATH = cls.MEMORY_DIR / "history.md"
        cls.MEMORY_PATH = cls.MEMORY_DIR / "memory.md"
        cls.SESSION_PATH = cls.SESSION_DIR / "session.json"
        cls.SOUL_PATH = cls.CONFIG_DIR / "soul.md"
        cls.TOOLS_DIR = cls.CONFIG_DIR / "tools"
        cls.SKILLS_DIR = cls.CONFIG_DIR / "skills"
        cls.AGENTS_DIR = cls.CONFIG_DIR / "agents"

    @classmethod
    def get_agent_dir(cls, agent_name: str) -> Path:
        """获取指定分身 Agent 的存储目录"""
        if agent_name.lower() == "monkeyking":
            return cls.CONFIG_DIR
        return cls.AGENTS_DIR / agent_name

    @classmethod
    def ensure_config_exists(cls, force: bool = False, sync: bool = False):
        """
        确保配置目录和文件存在。严格遵循只在主目录下操作的原则。
        :param force: 强制重新创建
        :param sync: 是否执行从本地目录同步到主目录的逻辑
        """
        if cls._initialized and not force:
            return "exists"

        created_or_synced = False
        
        # 1. 尝试初始化主目录及其子目录
        home_dir = Path.home() / ".monkeyking"
        try:
            home_dir.mkdir(parents=True, exist_ok=True)
            (home_dir / "memory").mkdir(parents=True, exist_ok=True)
            (home_dir / "session").mkdir(parents=True, exist_ok=True)
            (home_dir / "tools").mkdir(parents=True, exist_ok=True)
            (home_dir / "skills").mkdir(parents=True, exist_ok=True)
            (home_dir / "agents").mkdir(parents=True, exist_ok=True)
            cls._update_paths(home_dir)
            
            # 2. 同步逻辑：仅在 sync=True 时，如果本地存在配置目录，且与主目录不同，则同步过去
            # 遵循：如果有重复，以代码目录下的为准，但 config.json 需智能合并
            local_src = Path(".monkeyking")
            any_skipped = False
            if sync and local_src.exists() and local_src.resolve() != cls.CONFIG_DIR.resolve():
                for item in local_src.rglob("*"):
                    if item.is_file():
                        relative_path = item.relative_to(local_src)
                        target_file = cls.CONFIG_DIR / relative_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        
                        # 如果文件已存在且未指定 force，则跳过同步
                        if target_file.exists() and not force:
                            any_skipped = True
                            continue

                        # 对 config.json 执行智能合并
                        if relative_path.name == "config.json" and target_file.exists():
                            cls._merge_config_file(item, target_file)
                        else:
                            # 其他文件（如 soul.md）直接覆盖，符合“代码目录为准”
                            shutil.copy2(item, target_file)
                        created_or_synced = True

            # 3. 增量初始化：如果主目录下 config.json 已存在，则只补充缺失的 DEFAULT 节点
            if cls.CONFIG_PATH.exists():
                if not force:
                    cls._complement_config_with_defaults()
                    if any_skipped:
                        # 如果有文件被跳过，且没有新的创建/同步动作，我们希望返回 "exists"
                        pass
                else:
                    # 彻底重置
                    with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                        json.dump(cls.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
                    created_or_synced = True
            else:
                # 彻底不存在时，生成完整默认配置
                with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(cls.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
                created_or_synced = True
            
            cls._initialized = True
            
            if not created_or_synced and any_skipped:
                return "exists"
                    
        except (Exception, PermissionError) as e:
            # 如果主目录确实不可写，报错提醒，而不是静默回退到代码目录
            raise PermissionError(f"严重错误：无法在用户主目录下操作配置 ({e})。请检查权限或确保主目录可写。")

        return "created" if created_or_synced else "none"

    @classmethod
    def _complement_config_with_defaults(cls):
        """用默认配置补全当前配置文件中缺失的节点"""
        try:
            with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                current_cfg = json.load(f)
            
            modified = False
            # 递归补全逻辑
            def complement(source, target):
                nonlocal modified
                for k, v in source.items():
                    if k not in target:
                        target[k] = v
                        modified = True
                    elif isinstance(v, dict) and isinstance(target[k], dict):
                        complement(v, target[k])
            
            complement(cls.DEFAULT_CONFIG, current_cfg)
            
            if modified:
                with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(current_cfg, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"补全默认配置失败: {e}")

    @classmethod
    def _merge_config_file(cls, src_path: Path, dst_path: Path):
        """智能合并配置文件，保留 dst 中已有的非空工具配置"""
        try:
            with open(src_path, "r", encoding="utf-8") as f:
                src_cfg = json.load(f)
            with open(dst_path, "r", encoding="utf-8") as f:
                dst_cfg = json.load(f)
            
            # 基础合并：以 src 为准
            merged = src_cfg.copy()
            
            # 针对 tools 节点进行深度保护
            if "tools" in dst_cfg:
                if "tools" not in merged:
                    merged["tools"] = {}
                
                for tool_name, tool_params in dst_cfg["tools"].items():
                    if tool_name not in merged["tools"]:
                        merged["tools"][tool_name] = tool_params
                    else:
                        # 如果 src 中的 key 是空的，但 dst 中有值，保留 dst 的值 (即用户提供的 Key)
                        for k, v in tool_params.items():
                            if v and (k not in merged["tools"][tool_name] or not merged["tools"][tool_name][k]):
                                merged["tools"][tool_name][k] = v
            
            with open(dst_path, "w", encoding="utf-8") as f:
                json.dump(merged, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"合并配置文件失败: {e}")
            # 如果合并失败，退回到安全操作：不覆盖 dst

    @classmethod
    def load_config(cls) -> Dict[str, Any]:
        """加载 JSON 配置文件"""
        cls.ensure_config_exists() # 确保路径已正确初始化
        if cls.CONFIG_PATH.exists():
            try:
                with open(cls.CONFIG_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告: 无法读取 {cls.CONFIG_PATH}: {e}")
        return {}

    @classmethod
    def get_tool_config(cls, tool_name: str) -> Dict[str, Any]:
        """获取指定工具的配置"""
        config = cls.load_config()
        return config.get("tools", {}).get(tool_name, {})

    @classmethod
    def get_memory_config(cls) -> Dict[str, Any]:
        """获取记忆相关配置"""
        config = cls.load_config()
        return config.get("memory", cls.DEFAULT_CONFIG["memory"])

    @classmethod
    def get_behavior_config(cls) -> Dict[str, Any]:
        """获取行为相关配置"""
        config = cls.load_config()
        return config.get("behavior", cls.DEFAULT_CONFIG["behavior"])

    @classmethod
    def update_tool_config(cls, tool_name: str, new_config: Dict[str, Any]):
        """更新并持久化指定工具的配置"""
        config = cls.load_config()
        if "tools" not in config:
            config["tools"] = {}
        
        if tool_name not in config["tools"]:
            config["tools"][tool_name] = {}
            
        config["tools"][tool_name].update(new_config)
        
        try:
            with open(cls.CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"无法更新工具配置: {e}")

    @classmethod
    def get_llm_params(cls, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        根据优先级计算最终的 LLM 参数。
        """
        config = cls.load_config()
        overrides = overrides or {}
        
        models_config = config.get("models", cls.DEFAULT_CONFIG["models"])
        
        alias = (
            overrides.get("alias") or 
            os.getenv("LLM_ALIAS") or 
            config.get("default", cls.DEFAULT_CONFIG["default"])
        )
        
        base_model_config = models_config.get(alias, {})
        if not base_model_config and alias in cls.DEFAULT_CONFIG["models"]:
            base_model_config = cls.DEFAULT_CONFIG["models"][alias]

        provider = (
            overrides.get("provider") or 
            os.getenv("LLM_PROVIDER") or 
            base_model_config.get("provider", "openai")
        ).lower()

        params = {}
        
        def get_val(key, env_key, config_key):
            return overrides.get(key) or os.getenv(env_key) or base_model_config.get(config_key)

        if provider == "volcengine":
            params["model"] = get_val("model", "LLM_MODEL_NAME", "model_name") or "ep-xxxxxxxxxxxx"
            params["api_key"] = get_val("api_key", "VOLC_API_KEY", "api_key")
            params["base_url"] = get_val("base_url", "VOLC_BASE_URL", "base_url") or "https://ark.cn-beijing.volces.com/api/v3"
        else:
            params["model"] = get_val("model", "LLM_MODEL_NAME", "model_name") or "gpt-4o-mini"
            params["api_key"] = get_val("api_key", "OPENAI_API_KEY", "api_key")
            base_url = get_val("base_url", "OPENAI_BASE_URL", "base_url")
            if base_url:
                params["base_url"] = base_url

        return params

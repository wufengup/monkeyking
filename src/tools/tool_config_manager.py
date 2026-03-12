from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig

class ToolConfigManagerInput(BaseModel):
    tool_name: str = Field(description="法宝名称 (例如: weather_checker)")
    config_key: str = Field(description="配置项的名称 (例如: gaode_api_key)")
    config_value: str = Field(description="配置项的值")

class ToolConfigManagerTool(BaseMonkeyKingTool):
    """
    法宝配置管理工具：
    支持大圣在交互中动态更新 config.json 中的法宝配置。
    """
    
    @property
    def name(self) -> str:
        return "tool_config_manager"

    @property
    def description(self) -> str:
        return "更新法宝的配置信息（如 API Key）。当用户提供新的 Key 时使用此法宝进行持久化存储。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=ToolConfigManagerInput
        )

    def _run(self, tool_name: str, config_key: str, config_value: str) -> str:
        """执行配置更新逻辑"""
        try:
            # 更新配置
            LLMConfig.update_tool_config(tool_name, {config_key: config_value})
            return f"成功：已将法宝 '{tool_name}' 的配置项 '{config_key}' 更新并持久化到 config.json 中。"
        except Exception as e:
            return f"更新配置失败: {str(e)}"

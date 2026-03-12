from typing import Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig
import requests
import json

class WebSearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    count: int = Field(default=10, description="返回的搜索结果数量，默认为 10")

class WebSearchTool(BaseMonkeyKingTool):
    """
    内置网络搜索法宝：
    默认集成百度智能云千帆 AppBuilder，提供实时联网信息检索能力。
    """
    
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "通过百度搜索引擎查找全网实时信息（如新闻、百科、各行业实时资讯等）。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=WebSearchInput
        )

    def _run(self, query: str, count: int = 10) -> str:
        """执行联网搜索逻辑 (默认使用百度)"""
        # 1. 尝试从配置中获取 API Key
        # 优先使用 web_search 的配置，如果没有则回退到 baidu_search 的配置（兼容旧配置）
        config = LLMConfig.get_tool_config("web_search")
        api_key = config.get("appbuilder_api_key")
        
        if not api_key:
            # 兼容性检查：如果用户之前是在 baidu_search 下设置的
            old_config = LLMConfig.get_tool_config("baidu_search")
            api_key = old_config.get("appbuilder_api_key")

        if not api_key:
            return (
                "错误：缺少百度千帆 AppBuilder API Key。\n"
                "俺老孙的火眼金睛无法直达百度云端。请主人前往百度智能云获取 AppBuilder API Key，"
                "并告诉我要‘更新 web_search 的 appbuilder_api_key’。"
            )

        # 2. 调用百度搜索 API
        url = "https://qianfan.baidubce.com/v2/ai_search/web_search"
        headers = {
            "X-Appbuilder-Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "messages": [
                {
                    "content": query,
                    "role": "user"
                }
            ],
            "search_source": "baidu_search_v2",
            "resource_type_filter": [{"type": "web", "top_k": count}]
        }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 401:
                return "错误：百度 AppBuilder API Key 无效或已过期。请检查并更新你的 Key。"
            
            response.raise_for_status()
            data = response.json()
            
            # 3. 解析并格式化结果
            references = data.get("references", [])
            if not references:
                return f"大圣在百度云端翻了一圈，没有找到关于 '{query}' 的相关信息。"

            formatted_results = [f"### 关于 '{query}' 的搜索结果：\n"]
            for i, item in enumerate(references, 1):
                title = item.get("title", "无标题")
                snippet = item.get("content", "无摘要")
                link = item.get("url", "#")
                site = item.get("website", "未知来源")
                date = item.get("date", "未知日期")
                formatted_results.append(f"{i}. **{title}** ({site} | {date})\n   - 摘要: {snippet}\n   - 链接: {link}")

            return "\n".join(formatted_results)

        except requests.exceptions.Timeout:
            return "错误：百度搜索超时。请稍后再试。"
        except Exception as e:
            return f"法宝施展出错：{str(e)}"

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig
import requests
from typing import Optional

class WeatherCheckerInput(BaseModel):
    city: str = Field(description="需要查询天气的城市名称")
    gaode_api_key: Optional[str] = Field(None, description="高德地图API密钥（可选，默认从配置中读取）")

class WeatherCheckerTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "weather_checker"
    @property
    def description(self) -> str: return "查询指定城市的天气信息。如果配置中已存储API密钥，则无需手动输入。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=WeatherCheckerInput)
    def _run(self, city: str, gaode_api_key: Optional[str] = None) -> str:
        try:
            # 优先使用传入的 key，否则从配置中读取
            api_key = gaode_api_key or LLMConfig.get_tool_config("weather_checker").get("gaode_api_key")
            
            if not api_key:
                return "错误：未找到高德地图API密钥。请先在配置中设置，或在调用时提供。"

            # 调用高德地图天气API
            url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city}&key={api_key}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            if data.get("status") == "1" and data.get("lives"):
                live = data['lives'][0]
                return f"{city}天气：{live['weather']}，温度{live['temperature']}℃，风向{live['winddirection']}，风力{live['windpower']}级，湿度{live['humidity']}%"
            else:
                return f"获取{city}天气失败：{data.get('info', '未知错误')}"
        except Exception as e:
            return f"查询天气出错：{str(e)}"

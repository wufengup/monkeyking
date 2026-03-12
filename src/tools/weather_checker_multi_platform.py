from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig
import requests
from typing import Optional

class WeatherCheckerMultiPlatformInput(BaseModel):
    city: str = Field(description="需要查询天气的城市名称", required=True)
    platforms: list[str] = Field(default=["gaode"], description="要查询的天气平台列表，可选值：gaode, openweathermap", required=False)
    gaode_api_key: Optional[str] = Field(None, description="高德地图API密钥（可选）")
    openweathermap_api_key: Optional[str] = Field(None, description="OpenWeatherMap API密钥（可选）")

class WeatherCheckerMultiPlatformTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "weather_checker_multi_platform"
    @property
    def description(self) -> str: return "查询指定城市在多个平台的天气信息。如果配置中已存储密钥，则无需手动输入。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=WeatherCheckerMultiPlatformInput)
    def _run(self, city: str, platforms: list[str], gaode_api_key: Optional[str] = None, openweathermap_api_key: Optional[str] = None) -> dict:
        results = {}
        config = LLMConfig.get_tool_config("weather_checker")
        
        for platform in platforms:
            if platform == "gaode":
                key = gaode_api_key or config.get("gaode_api_key")
                if not key:
                    results[platform] = "错误：未找到高德地图API密钥"
                    continue
                try:
                    url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={key}&city={city}&extensions=base"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    if data.get("status") == "1" and data.get("lives"):
                        weather = data["lives"][0]
                        results[platform] = f"{weather['city']} {weather['weather']} {weather['temperature']}℃"
                    else:
                        results[platform] = f"查询失败：{data.get('info', '未知错误')}"
                except Exception as e:
                    results[platform] = f"查询失败：{str(e)}"
            elif platform == "openweathermap":
                key = openweathermap_api_key or config.get("openweathermap_api_key")
                if not key:
                    results[platform] = "错误：未找到OpenWeatherMap API密钥"
                    continue
                try:
                    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}&units=metric&lang=zh_cn"
                    response = requests.get(url)
                    response.raise_for_status()
                    data = response.json()
                    results[platform] = f"{data['name']} {data['weather'][0]['description']} {data['main']['temp']}℃"
                except Exception as e:
                    results[platform] = f"查询失败：{str(e)}"
        return results
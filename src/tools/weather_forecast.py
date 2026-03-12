from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig
import requests
from typing import Optional

class WeatherForecastInput(BaseModel):
    city: str = Field(description="需要查询天气的城市名称")
    gaode_api_key: Optional[str] = Field(None, description="高德地图API密钥（可选，默认从配置中读取）")
    days: int = Field(default=3, description="需要查询未来几天的天气，默认为3天")

class WeatherForecastTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "weather_forecast"
    @property
    def description(self) -> str: return "查询指定城市未来几天的天气信息。如果配置中已存储API密钥，则无需手动输入。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=WeatherForecastInput)
    def _run(self, city: str, gaode_api_key: Optional[str] = None, days: int =3) -> str:
        try:
            api_key = gaode_api_key or LLMConfig.get_tool_config("weather_checker").get("gaode_api_key")
            if not api_key:
                return "错误：未找到高德地图API密钥。"

            # 获取城市adcode
            geocode_url = f"https://restapi.amap.com/v3/geocode/geo?key={api_key}&address={city}"
            geocode_response = requests.get(geocode_url)
            geocode_data = geocode_response.json()
            if geocode_data['status'] != '1' or len(geocode_data['geocodes']) ==0:
                return f"无法获取城市{city}的编码信息"
            adcode = geocode_data['geocodes'][0]['adcode']
            # 获取天气预报
            forecast_url = f"https://restapi.amap.com/v3/weather/weatherInfo?key={api_key}&city={adcode}&extensions=all&output=json"
            forecast_response = requests.get(forecast_url)
            forecast_data = forecast_response.json()
            if forecast_data['status'] != '1':
                return "天气预报查询失败"
            forecasts = forecast_data['forecasts'][0]['casts']
            result = f"{city}未来{days}天天气：\n"
            for i in range(1, days+1):
                if i < len(forecasts):
                    cast = forecasts[i]
                    result += f"{cast['date']}：{cast['dayweather']}，{cast['daytemp']}℃~{cast['nighttemp']}℃\n"
                else:
                    break
            return result
        except Exception as e:
            return f"查询出错：{str(e)}"
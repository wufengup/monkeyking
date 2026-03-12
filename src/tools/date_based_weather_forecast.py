from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig
import requests
from typing import Optional

class DateBasedWeatherForecastInput(BaseModel):
    city: str = Field(description="需要查询天气的城市名称")
    date: str = Field(description="需要查询的日期，格式为YYYY-MM-DD")
    gaode_api_key: Optional[str] = Field(None, description="高德地图API密钥（可选，默认从配置中读取）")

class DateBasedWeatherForecastTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "date_based_weather_forecast"
    @property
    def description(self) -> str: return "根据指定日期查询城市的天气信息。如果配置中已存储API密钥，则无需手动输入。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=DateBasedWeatherForecastInput)
    def _run(self, city: str, date: str, gaode_api_key: Optional[str] = None) -> str:
        try:
            api_key = gaode_api_key or LLMConfig.get_tool_config("weather_checker").get("gaode_api_key")
            if not api_key:
                return "错误：未找到高德地图API密钥。"

            city_code_url = f"https://restapi.amap.com/v3/geocode/geo?address={city}&key={api_key}"
            city_response = requests.get(city_code_url)
            city_data = city_response.json()
            if city_data.get("status") != "1" or not city_data.get("geocodes"):
                return f"无法获取城市{city}的编码"
            city_code = city_data["geocodes"][0]["adcode"]
            weather_url = f"https://restapi.amap.com/v3/weather/weatherInfo?city={city_code}&date={date}&key={api_key}"
            weather_response = requests.get(weather_url)
            weather_data = weather_response.json()
            if weather_data.get("status") != "1" or not weather_data.get("forecasts"):
                return f"无法获取{city}在{date}的天气信息"
            forecast = weather_data["forecasts"][0]["casts"][0]
            return f"{date}天气：{forecast['dayweather']}，{forecast['nighttemp']}℃~{forecast['daytemp']}℃"
        except Exception as e:
            return f"查询出错：{str(e)}"

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
    date: Optional[str] = Field(
        default=None,
        description="可选，指定日期查询，格式 YYYY-MM-DD。若提供该值，将优先按日期返回。"
    )

class WeatherForecastTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "weather_forecast"
    @property
    def description(self) -> str: return "查询指定城市的天气预报，支持按未来天数（days）或按具体日期（date）查询。"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=WeatherForecastInput)
    def _run(self, city: str, gaode_api_key: Optional[str] = None, days: int = 3, date: Optional[str] = None) -> str:
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
            # 若指定 date，优先按日期查询
            if date:
                target = next((c for c in forecasts if c.get("date") == date), None)
                if not target:
                    available = ", ".join(c.get("date", "") for c in forecasts if c.get("date"))
                    return f"未找到 {city} 在 {date} 的预报。可用日期：{available}"
                return (
                    f"{city} {date} 天气：{target['dayweather']}，"
                    f"{target['nighttemp']}℃~{target['daytemp']}℃，"
                    f"风向{target.get('daywind', '-')}/{target.get('nightwind', '-')}"
                )

            # 默认按天数返回；含当天（索引 0）起算更直观
            days = max(1, min(days, len(forecasts)))
            result = f"{city}未来{days}天天气：\n"
            for cast in forecasts[:days]:
                result += f"{cast['date']}：{cast['dayweather']}，{cast['daytemp']}℃~{cast['nighttemp']}℃\n"
            return result.strip()
        except Exception as e:
            return f"查询出错：{str(e)}"

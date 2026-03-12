from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool

class GoldenCudgelAnimatorInput(BaseModel):
    duration: int = Field(description="动画时长（秒），默认5秒", default=5)
    speed: float = Field(description="动画速度倍率，默认1.0", default=1.0)

class GoldenCudgelAnimatorTool(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "golden_cudgel_animator"
    @property
    def description(self) -> str: return "生成金箍棒动画的HTML内容"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=GoldenCudgelAnimatorInput)
    def _run(self, duration: int =5, speed: float=1.0) -> str:
        adjusted_duration = duration / speed
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>金箍棒动画</title>
    <style>
        body {{ display: flex; justify-content: center; align-items: center; height: 100vh; margin:0; background: #f0f0f0; }}
        #cudgel {{ width:20px; height:200px; background:gold; border-radius:10px; position:relative; animation: grow {adjusted_duration}s ease-in-out infinite alternate; }}
        @keyframes grow {{
            0% {{ height:200px; width:20px; transform: rotate(0deg); }}
            50% {{ height:400px; width:40px; transform: rotate(180deg); }}
            100% {{ height:200px; width:20px; transform: rotate(360deg); }}
        }}
    </style>
</head>
<body>
    <div id="cudgel"></div>
</body>
</html>
"""
        return html_content

from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
import base64
from pathlib import Path

class CustomGoldenCudgelAnimatorInput(BaseModel):
    file_path: str = Field(description="用户提供的图片路径，必须是用户目录下的绝对路径或相对路径")
    duration: int = Field(default=5, description="动画时长（秒），默认5秒")
    speed: float = Field(default=1.0, description="动画速度倍率，默认1.0")

class CustomGoldenCudgelAnimator(BaseMonkeyKingTool):
    @property
    def name(self) -> str: return "custom_golden_cudgel_animator"
    @property
    def description(self) -> str: return "生成包含用户提供图片的金箍棒动画HTML内容"
    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(func=self._run, name=self.name, description=self.description, args_schema=CustomGoldenCudgelAnimatorInput)
    def _run(self, file_path: str, duration: int = 5, speed: float = 1.0) -> str:
        # 读取图片文件并转换为base64
        try:
            with open(file_path, "rb") as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode("utf-8")
        except Exception as e:
            return f"读取图片失败：{str(e)}"
        
        # 生成动画HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <title>酷炫金箍棒动画</title>
    <style>
        body {{ display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #000; }}
        #monkey {{ position: absolute; width: 150px; z-index: 2; transition: transform {duration}s linear; }}
        #cudgel {{ position: absolute; width: 50px; height: 600px; background: linear-gradient(45deg, #ffd700, #ffA500); border-radius: 25px; z-index: 1; animation: spin {duration/speed}s linear infinite; }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
    <img id="monkey" src="data:image/jpeg;base64,{img_base64}" alt="悟空">
    <div id="cudgel"></div>
    <script>
        const monkey = document.getElementById('monkey');
        const cudgel = document.getElementById('cudgel');
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;
        const radius = 200;
        let angle = 0;
        
        function animate() {{
            angle += 0.05 * {speed};
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);
            monkey.style.left = `${{x - 75}}px`;
            monkey.style.top = `${{y - 75}}px`;
            monkey.style.transform = `rotate(${{angle * 180 / Math.PI}}deg)`;
            requestAnimationFrame(animate);
        }}
        animate();
    </script>
</body>
</html>"""
        return html_content

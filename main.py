import typer
from typing import Optional
from dotenv import load_dotenv
from src.agents.assistant_agent import AssistantAgent
from src.utils.cli import (
    print_logo, 
    print_agent_message, 
    print_user_prompt, 
    print_system_message,
    print_error,
    show_thinking
)
from prompt_toolkit import PromptSession
from prompt_toolkit.formatted_text import ANSI
from rich.console import Console

# 加载环境变量
load_dotenv()

console = Console()

app = typer.Typer(help="MonkeyKing: 您的个人生活助理 Agent 命令行工具")

@app.command(name="init")
def init_config(
    force: bool = typer.Option(False, "--force", "-f", help="强制重新初始化配置文件")
):
    """
    初始化 MonkeyKing 配置目录和文件。
    在用户主目录下创建 .monkeyking/config.json。
    """
    from src.utils.config import LLMConfig
    status = LLMConfig.ensure_config_exists(force=force, sync=True)
    
    if status == "created":
        print_system_message(f"成功初始化配置！配置文件已创建在: {LLMConfig.CONFIG_PATH}")
        print_system_message("请编辑该文件并填入您的 API Key。")
    elif status == "exists":
        print_error(f"配置文件已存在: {LLMConfig.CONFIG_PATH}。使用 --force 强制覆盖。")
    else:
        print_system_message(f"配置文件已存在: {LLMConfig.CONFIG_PATH}")

@app.command(name="agent")
def start_agent(
    name: str = typer.Option("MonkeyKing", "--name", "-n", help="Agent 的名称"),
    alias: Optional[str] = typer.Option(None, "--alias", "-a", help="使用 config.json 中指定的模型别名"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="模型供应商 (openai, volcengine)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="模型名称或 Endpoint ID"),
    api_key: Optional[str] = typer.Option(None, "--api-key", "-k", help="API 密钥"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="API 基础 URL"),
    interactive: bool = typer.Option(True, "--interactive/--no-interactive", help="是否开启对话交互模式"),
    auto_approve: Optional[bool] = typer.Option(None, "--auto-approve", "-y", help="是否自动批准法宝调用（无需人工干预）")
):
    """
    启动 MonkeyKing 助理 Agent。
    """
    # 1. 检查配置文件是否存在
    from src.utils.config import LLMConfig
    if not LLMConfig.CONFIG_PATH.exists():
        print_error("未找到配置文件！")
        print_system_message("请先运行 `monkeyking init` 进行初始化。")
        raise typer.Exit(code=1)

    # 2. 合并参数并获取最终配置
    overrides = {}
    if alias: overrides["alias"] = alias
    if provider: overrides["provider"] = provider
    if model: overrides["model"] = model
    if api_key: overrides["api_key"] = api_key
    if base_url: overrides["base_url"] = base_url
    
    llm_params = LLMConfig.get_llm_params(overrides=overrides)
    
    # 2.1 确定 auto_approve 最终值：优先级 命令行参数 > 配置文件 > 默认 False
    behavior_cfg = LLMConfig.get_behavior_config()
    final_auto_approve = auto_approve if auto_approve is not None else behavior_cfg.get("auto_approve_tools", False)

    # 3. 准备提示信息
    print_logo()
    display_name = "大圣" if name.lower() == "monkeyking" else name
    print_system_message(f"--- {display_name} 正在启动... ---")
    
    # 4. 初始化 AssistantAgent
    try:
        agent = AssistantAgent(name=name, model_params=llm_params)
        print_system_message(f"--- {display_name} 准备就绪 ---")
    except Exception as e:
        print_error(f"Agent 初始化失败: {str(e)}")
        raise typer.Exit(code=1)
    
    if interactive:
        session = PromptSession()
        # 预渲染 prompt 为 ANSI 字符串以适配 prompt_toolkit
        # [bold green]用户[/bold green] > 
        prompt_ansi = ANSI("\x1b[1;32m用户\x1b[0m > ")
        
        try:
            while True:
                # 使用 prompt_toolkit 提供更好的输入体验 (支持回退、快捷键等)
                user_input = session.prompt(prompt_ansi)
                
                # 如果输入为空或仅包含空白字符，则直接跳过，不进行回答
                if not user_input.strip():
                    continue
                
                if user_input.lower() in ["exit", "quit", "退出"]:
                    display_name = "大圣" if agent.name.lower() == "monkeyking" else agent.name
                    print_agent_message(display_name, "再见！祝你今天过得愉快。", mood="happy")
                    break
                
                # Agent 处理，支持动态思考状态显示及人工干预
                # 如果 auto_approve 为 True，则 is_interactive 为 False
                response = agent.run({"query": user_input}, is_interactive=not final_auto_approve)
                
                # 获取情绪并打印消息
                mood = getattr(agent, "last_mood", "neutral")
                # 使用 agent.name 而非启动参数 name，以支持动态切换后的显示
                display_name = "大圣" if agent.name.lower() == "monkeyking" else agent.name
                print_agent_message(display_name, response, mood=mood)
                
        except (KeyboardInterrupt, typer.Abort):
            display_name = "大圣" if agent.name.lower() == "monkeyking" else agent.name
            print_agent_message(display_name, "程序被中断。再见！", mood="sad")
    else:
        display_name = "大圣" if agent.name.lower() == "monkeyking" else agent.name
        print_agent_message(display_name, "非交互模式暂未实现具体逻辑。")

@app.command()
def version():
    """
    显示 MonkeyKing 的版本信息。
    """
    typer.echo("MonkeyKing Version: 0.1.0")

@app.command(name="server")
def start_server(
    mode: str = typer.Option("websocket", "--mode", "-m", help="启动模式: websocket (免公网IP) 或 webhook (需公网IP)"),
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="监听主机地址（仅 webhook 模式有效）"),
    port: int = typer.Option(8000, "--port", "-p", help="监听端口号（仅 webhook 模式有效）")
):
    """
    启动 MonkeyKing 多渠道交互服务端。
    支持长连接 (WebSocket) 和 Webhook 两种模式。
    """
    from src.utils.cli import print_logo, print_system_message
    from src.api.server import run_websocket_server
    import uvicorn
    
    print_logo()
    
    if mode == "websocket":
        print_system_message("--- MonkeyKing 长连接监听已开启 (免公网IP模式) ---")
        run_websocket_server()
    else:
        print_system_message(f"--- MonkeyKing Webhook 服务端正在启动 ({host}:{port}) ---")
        uvicorn.run("src.api.server:app", host=host, port=port, reload=False)

if __name__ == "__main__":
    app()

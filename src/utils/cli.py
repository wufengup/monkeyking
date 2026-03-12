from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()

MONKEYKING_LOGO = """
  __  __             _              _  ___             
 |  \/  | ___  _ __ | | _____ _   _| |/ (_)_ __   __ _ 
 | |\/| |/ _ \| '_ \| |/ / _ \ | | | ' /| | '_ \ / _` |
 | |  | | (_) | | | |   <  __/ |_| | . \| | | | | (_| |
 |_|  |_|\___/|_| |_|_|\_\___|\__, |_|\_\_|_| |_|\__, |
                              |___/              |___/ 
"""

def print_logo():
    logo_text = Text(MONKEYKING_LOGO, style="bold yellow")
    panel = Panel(
        logo_text,
        title="[bold blue]MonkeyKing Assistant[/bold blue]",
        subtitle="[italic green]Your Intelligent Life Agent[/italic green]",
        border_style="magenta",
        expand=False
    )
    console.print(panel)

def print_agent_message(name: str, message: str, mood: str = "neutral"):
    """打印 Agent 消息，支持根据情绪调整样式"""
    mood_styles = {
        "happy": {"color": "bold green", "emoji": "🐒✨"},
        "angry": {"color": "bold red", "emoji": "🔥💢"},
        "sad": {"color": "bold blue", "emoji": "💧🐒"},
        "neutral": {"color": "cyan", "emoji": "🐒"},
        "excited": {"color": "bold magenta", "emoji": "🕺🐵"}
    }
    
    style = mood_styles.get(mood, mood_styles["neutral"])
    color = style["color"]
    emoji = style["emoji"]
    
    console.print(f"[bold magenta]{name}[/bold magenta] {emoji}: [{color}]{message}[/{color}]")

def print_user_prompt() -> str:
    return "[bold green]用户[/bold green] > "

def print_system_message(message: str):
    console.print(f"[italic gray]{message}[/italic gray]")

def print_error(message: str):
    console.print(f"[bold red]错误: {message}[/bold red]")

def show_thinking(name: str):
    """显示动态的思考状态"""
    return console.status(f"[italic cyan]{name} 正在思考中...[/italic cyan]", spinner="dots")

def print_tool_execution(tool_name: str, args: dict, result: str):
    """在一个对话框中展示工具的调用和返回结果"""
    import json
    
    content = Text()
    content.append("🛠️  正在动用法宝: ", style="bold yellow")
    content.append(f"{tool_name}\n", style="bold green")
    
    # 格式化参数 JSON
    try:
        formatted_args = json.dumps(args, ensure_ascii=False, indent=2)
        content.append("📥 输入参数: ", style="bold blue")
        content.append(f"{formatted_args}\n", style="white")
    except:
        content.append("📥 输入参数: ", style="bold blue")
        content.append(f"{args}\n", style="white")
        
    content.append("-" * 30 + "\n", style="gray")
    content.append("📤 执行结果: ", style="bold magenta")
    
    # 处理结果展示（截断过长的内容）
    str_result = str(result)
    is_error = "错误" in str_result or "失败" in str_result
    
    if len(str_result) > 1000:
        display_result = str_result[:1000] + "\n... (内容过长，已截断显示)"
    else:
        display_result = str_result

    if is_error:
        content.append(display_result, style="bold red")
        title = "[bold red]❌ 法宝执行失败[/bold red]"
        border_style = "red"
    else:
        content.append(display_result, style="green")
        title = "[bold green]✅ 法宝执行成功[/bold green]"
        border_style = "yellow"

    panel = Panel(
        content,
        title=title,
        border_style=border_style,
        padding=(1, 2),
        expand=False
    )
    console.print(panel)

def print_thought(name: str, thought: str, tool_calls: list = None):
    """打印 Agent 的思考内容和计划"""
    content = Text()
    if thought and thought.strip():
        content.append(thought + "\n", style="italic cyan")
    
    if tool_calls:
        content.append("\n[俺老孙准备动用法宝]:\n", style="bold yellow")
        for tc in tool_calls:
            t_name = tc.get("name", "未知工具")
            t_args = tc.get("args", {})
            content.append(f" 🛠️  {t_name}", style="bold green")
            content.append(f" (参数: {t_args})\n", style="white")

    if not content:
        return

    panel = Panel(
        content,
        title=f"[bold magenta]{name} 的思考与计划[/bold magenta]",
        border_style="cyan",
        padding=(1, 2)
    )
    console.print(panel)

def ask_for_intervention() -> str:
    """询问用户是否需要干预"""
    console.print("\n[bold yellow]💡 此时你可以直接回车让大圣按计划行事，或者输入新吩咐进行干预（输入 'stop' 喊停）：[/bold yellow]")
    intervention = input("吩咐 > ").strip()
    return intervention

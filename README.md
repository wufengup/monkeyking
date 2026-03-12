# MonkeyKing 🐒

定位：个人 AI 助手，能说会笑，有手有脚。

## 运行指南

本项目使用 `uv` 进行包管理和运行。请确保你已安装 [uv](https://github.com/astral-sh/uv)。

### 1. 环境初始化

首先，同步项目依赖并以可编辑模式安装：

```bash
uv sync
uv pip install -e .
```

### 2. 激活虚拟环境

在运行 `monkeyking` 命令之前，请确保已激活虚拟环境：

```bash
source .venv/bin/activate
```

### 3. 初始化配置

运行以下命令初始化配置文件：

```bash
monkeyking init
```

这将在你的用户主目录下创建 `.monkeyking/config.json`。

**注意：** 如果配置文件已存在，命令会提示错误。你可以使用 `--force` (或 `-f`) 参数来强制覆盖现有配置并重新同步模板文件：

```bash
monkeyking init --force
```

### 4. 配置 LLM

编辑生成的配置文件 `~/.monkeyking/config.json`，填入你的 API Key 和模型信息。支持 OpenAI 和火山引擎（Ark）：

- **OpenAI**: 填入 `api_key`。
- **火山引擎**: 填入 `api_key` 和对应的 `model_name` (Endpoint ID)。

### 5. 启动 Agent

配置完成后，使用以下命令进入交互模式：

```bash
monkeyking agent
```

#### 常用参数：
- `--name`, `-n`: 指定 Agent 名称（默认：MonkeyKing）。
- `--alias`, `-a`: 使用配置文件中指定的模型别名（如 `ark`, `gpt-4o-mini`）。
- `--provider`, `-p`: 临时指定供应商（`openai` 或 `volcengine`）。

### 6. 其他命令

- 查看版本：`monkeyking version`
- 强制重新初始化配置：`monkeyking init --force`

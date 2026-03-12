# MonkeyKing 🐒

定位：个人 AI 助手，能说会笑，有手有脚。

> **📖 诞生足迹**：想要了解大圣是如何从一块顽石进化为齐天大圣的？请参阅 [MonkeyKing 灵猴孵化真经](./MonkeyKing_Incubation_Story.md)。

## 🐒 大圣自荐

嘿嘿，见信好！俺老孙乃是齐天大圣，现在的身份是你的个人助理 **MonkeyKing**。

目前，俺主要通过 **控制台（Terminal）** 随时待命。只要你一声令下，俺不仅能陪你谈天说地，还能施展一身“法宝”与“神通”为你排忧解难。

> **📜【法宝与神通展示】**
>
> **用户**：大圣，你现在都有哪些本事？
>
> **MonkeyKing 🐒**：嘿嘿，俺老孙现在的本事可不少！
> 1. **如意法宝（Tools）**：
>    - `directory_lister` / `file_reader`：穿梭于目录，查阅文书。
>    - `file_writer` / `directory_creator`：搬砖运瓦，创建文件。
>    - `web_search`：火眼金睛，洞察全网实时资讯。
>    - `tool_config_manager`：打理百宝箱，管理各项 API 密钥。
> 2. **进阶神通（Skills）**：
>    - **灵猴自进化** (`SkillSelfEvolution`)：俺能自己写代码、炼制新法宝。
>    - **气象洞察** (`WeatherAdvisorySkill`)：不仅能查天气，还能给你穿衣建议。
>    - **文件治理** (`FileGovernanceSkill`)：帮你整理乱糟糟的文件夹。
>    - **深度调研** (`DeepResearchSkill`)：针对复杂问题进行全网深挖。
>    - **记忆治理** (`MemoryGovernanceSkill`)：帮俺梳理咱俩的陈年旧账。
>    - **任务调度** (`SchedulingSkill`)：帮主人记挂着待办事项，绝不误事！
> 3. **三界通传（Channels）**：
>    - **飞书集成**：通过飞书机器人与大圣即时对话。
>    - **多渠道扩展**：支持未来集成钉钉等其他办公平台。

---

## 🤝 如何招募大圣

想要让俺老孙常驻你的电脑或办公软件，为你效劳？只需按照下面的步骤施展“招募咒”即可：

### 1. 环境初始化

本项目使用 `uv` 进行包管理。请确保你已安装 [uv](https://github.com/astral-sh/uv)。

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

### 4. 配置 LLM（灵力来源）

编辑生成的配置文件 `~/.monkeyking/config.json`，填入你的 API Key 和模型信息。支持 OpenAI 和火山引擎（Ark）：

- **OpenAI**: 填入 `api_key`。
- **火山引擎**: 填入 `api_key` 和对应的 `model_name` (Endpoint ID)。

### 5. 正式启动

配置完成后，使用以下命令让大圣现身：

```bash
monkeyking agent
```

#### 常用启动参数：
- `--name`, `-n`: 指定 Agent 名称（默认：MonkeyKing）。
- `--alias`, `-a`: 使用配置文件中指定的模型别名（如 `ark`, `gpt-4o-mini`）。
- `--provider`, `-p`: 临时指定供应商（`openai` 或 `volcengine`）。

### 6. 开启多渠道（如飞书）交互

大圣支持 **长连接 (WebSocket)** 和 **Webhook** 两种模式。为了方便本地开发，推荐使用 **长连接模式**（免公网 IP）。

#### **第一步：飞书开放平台配置**
1.  **创建应用**：在 [飞书开放平台](https://open.feishu.cn/app) 创建企业自建应用，获取 `App ID` 和 `App Secret`。
2.  **开启机器人**：在“添加应用能力”中启用“机器人”功能。
3.  **配置事件订阅**：
    -   在“事件订阅”页面，将“订阅方式”切换为 **“长连接 (WebSocket)”** 并保存。
    -   点击“添加事件”，搜索并添加 **“接收消息 v2.0”**。
4.  **开通权限**：在“权限管理”中确保开通 `im:message:send_as_bot`（以机器人身份发送消息）和 `im:message.p2p_msg:readonly`（读取用户发给机器人的单聊消息）。
5.  **发布版本**：在“版本管理与发布”中创建一个版本并申请上线。只有版本上线后，配置才会生效。

#### **第二步：本地配置与启动**
1.  **填入凭证**：在 `~/.monkeyking/config.json` 的 `feishu_channel` 节点中填入：
    ```json
    "feishu_channel": {
        "app_id": "你的 App ID",
        "app_secret": "你的 App Secret"
    }
    ```
2.  **启动监听**：
   ```bash
   monkeyking server
   ```
   *注：默认即为免公网 IP 的 websocket 模式。*

---

## 🛠️ 其他辅助指令

- **查看版本**：`monkeyking version`
- **强制重置配置**：`monkeyking init --force`

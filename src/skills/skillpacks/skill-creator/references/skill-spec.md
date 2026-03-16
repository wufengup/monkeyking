# Claude 神通 (Skill) 规范指南

一个“神通包”（Skill Pack）是一个包含指令和可选捆绑资源的目录结构。

## 目录结构
- `神通名称/` (skill-name/)
    - `SKILL.md` (必填)
        - 必须包含 YAML 格式的元数据（frontmatter），其中 `name` 和 `description` 是必填项。
        - 包含 Markdown 格式的执行指南（SOP）。
    - 捆绑资源 (选填)
        - `scripts/`: 存放确定性任务的可执行代码。在大圣系统中，该目录下任何继承自 `BaseMonkeyKingTool` 的 Python 类都会被自动加载为“法宝”。
        - `references/`: 存放根据需要加载到上下文中的参考文档。在 `SKILL.md` 中可以使用 `[链接文本](references/doc.md)` 进行引用。
        - `assets/`: 存放输出中使用的文件（模板、图标、字体等）。

## 最佳实践
1. **聚焦 SOP**: `SKILL.md` 应定义高层执行逻辑，即“怎么做”。
2. **脚本驱动行动**: 如果任务涉及复杂逻辑或外部 API，应在 `scripts/` 中实现为 Python 法宝。
3. **资料解耦**: 将长篇背景资料放入 `references/`，保持 `SKILL.md` 简洁明了。
4. **自包含**: 一个神通应当尽可能包含其运行所需的所有指令和资源。

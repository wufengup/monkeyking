---
name: skill-creator
description: 根据对话、GitHub 仓库或网页链接，炼制/更新符合 Claude 规范的神通 (Skill Pack)。
---

# Skill Creator (灵猴进化)

大圣通过感悟万物，将其沉淀为可复用的神通。本神通遵循 [Claude Skill 规范](references/skill-spec.md)，确保每一项新神通都结构严谨、法力无边。

## 适用场景
- 当前法宝集中没有可直接完成任务的能力。
- 用户明确要求“记住这个处理流程”、“去 GitHub 安装这个项目”或“从这个链接学习技能”。
- 需要将复杂的对话上下文沉淀为可复用的能力。
- 需要对已有的神通进行优化、修复或结构化重组。

## 执行流程

### 1. 对话沉淀为神通 (Context to Skill)
- **场景**：与用户完成了一项复杂任务，用户希望“以后都这么办”。
- **步骤**：
    1. 总结刚才的成功处理流程（SOP）。
    2. 确定技能名称（name）和描述（description）。
    3. 调用 `skill_creator`，设置 `action='create_skill'`，将 SOP 写入 `content`。
    4. 系统会自动创建符合规范的目录结构（含 `scripts/`, `references/`, `assets/`）。

### 2. GitHub 搬运安装 (GitHub Install)
- **场景**：用户提供了 GitHub 链接或要求从某仓库安装技能。
- **步骤**：
    1. 识别仓库地址（如 `HKUDS/nanobot`）和目录路径。
    2. 调用 `skill_creator`，设置 `action='install_from_github'`。
    3. 安装完成后，读取新神通的 `SKILL.md` 了解其法力。

### 3. 链接提取学习 (Link Extraction)
- **场景**：用户给了一个教程链接或技术文档。
- **步骤**：
    1. 调用 `skill_creator`，设置 `action='install_from_url'` 抓取网页内容。
    2. 根据抓取到的原始内容，分析、总结并提炼出核心 SOP。
    3. 再次调用 `skill_creator` 的 `create_skill` 动作，将其炼制成正式神通。

### 4. 神通包优化 (Skill Pack Evolution)
- **场景**：需要对已有的 Skill Pack 进行优化或重构。
- **步骤**：
    1. **评估现状**：读取目标技能的 `SKILL.md` 及资源。
    2. **对标规范**：参照 [Skill Spec](references/skill-spec.md) 进行重构建议。
    3. **覆盖更新**：使用 `skill_creator` 的 `create_skill` 动作更新内容。

## 所用法宝
- 核心法宝：`skill_creator` (位于本神通的 `scripts/` 目录下)
- 辅助法宝：`file_reader`, `directory_lister`

## 约束条件
- **规范第一**：必须包含 YAML frontmatter，且必须包含 `name` 和 `description`。
- **存储边界**：严禁修改 `src/` 下的内置代码，所有炼制产物必须存放在 `~/.monkeyking/skills/` 目录下。
- **闭环验证**：神通炼成后，必须立即尝试调用并反馈结果给主人。

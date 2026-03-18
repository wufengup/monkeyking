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
    4. **脚本法宝注入 (可选)**：如果该神通需要特定的自动化逻辑（如 API 调用、复杂计算），请编写 Python 脚本并再次调用 `skill_creator`，设置 `action='add_script_to_skill'`，将其存入该神通的 `scripts/` 目录下。
    5. 系统会自动创建符合规范的目录结构（含 `scripts/`, `references/`, `assets/`）。

### 2. GitHub 搬运安装 (GitHub Install)
- **场景**：用户提供了 GitHub 链接或要求从某仓库安装技能。
- **步骤**：
    1. 识别仓库地址（如 `HKUDS/nanobot`）和目录路径。
    2. 调用 `skill_creator`，设置 `action='install_from_github'`。
    3. 安装完成后，读取新神通的 `SKILL.md` 了解其法力。

### 3. 链接提取学习 (Link Extraction)
- **场景**：用户给了一个教程链接、技术文档或 ClawHub 链接。
- **步骤**：
    1. **浏览页面**：调用 `skill_creator`，设置 `action='install_from_url'` 抓取页面内容。
    2. **提取标识 (ClawHub)**：
        - 如果是 ClawHub 页面，从内容中寻找 `clawhub install <slug>` 命令或相关标识。
        - 提取出 `<slug>` 后，再次调用 `skill_creator`，设置 `action='install_from_clawhub'` 完成安装。
    3. **总结感悟 (普通链接)**：
        - 如果是普通网页，分析原始内容，总结出核心 SOP。
        - 再次调用 `skill_creator` 的 `create_skill` 动作，将其炼制成正式神通。

### 4. 神通包优化 (Skill Pack Evolution)
- **场景**：需要对已有的 Skill Pack 进行优化或重构。
- **步骤**：
    1. **评估现状**：读取目标技能的 `SKILL.md` 及资源。
    2. **对标规范**：参照 [Skill Spec](references/skill-spec.md) 进行重构建议。
    3. **覆盖更新**：使用 `skill_creator` 的 `create_skill` 动作更新内容。

### 5. 神通整合 (Skill Consolidation)
- **场景**：大圣发现多个神通功能重叠、有重复部分，或需要将零散的神通整合为更强大的体系。
- **步骤**：
    1. **定期自检**：大圣应定期检查已有的扩展神通列表，评估是否存在功能重叠。
    2. **提议整合**：向用户展示重叠部分，并提议整合方案（包含新名称、新描述、整合后的 SOP）。
    3. **执行合并**：在用户确认后，调用 `skill_creator`，设置 `action='merge_skills'`。
    4. **资源搬运**：系统会自动将源技能的 `scripts/`, `references/` 等资源搬运至新技能包中。
    5. **清理旧账**：合并完成后，系统会自动卸载旧的扩展神通。

### 7. 神通卸载 (Skill Uninstallation)
- **场景**：用户明确要求“删除这个技能”、“卸载这个神通”或“清理这个扩展”。
- **步骤**：
    1. **确认名称**：明确要卸载的神通名称。
    2. **执行卸载**：调用 `skill_creator`，设置 `action='uninstall_skill'`。
    3. **约束说明**：大圣只能卸载主目录 `~/.monkeyking/skills/` 下的扩展神通，不能动摇 `src/` 下的内置根基。

## 所用法宝
- 核心法宝：`skill_creator` (位于本神通的 `scripts/` 目录下)
- 辅助法宝：`file_reader`, `directory_lister`

## 约束条件
- **规范第一**：必须包含 YAML frontmatter，且必须包含 `name` 和 `description`。
- **神通带法宝**：大圣不再直接炼制全局独立的法宝（Tool），而是先感悟出神通（Skill），若该神通需要特殊逻辑，则将其炼制成脚本（Script）存放在该神通的 `scripts/` 目录下。
- **存储边界**：严禁修改 `src/` 下的内置代码，所有炼制产物必须存放在 `~/.monkeyking/skills/` 目录下。
- **闭环验证**：神通及配套脚本炼成后，必须立即尝试调用并反馈结果给主人。

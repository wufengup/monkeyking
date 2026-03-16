import json
import httpx
import re
import asyncio
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig

class SkillCreatorInput(BaseModel):
    action: str = Field(description="要执行的操作：'create_skill' (沉淀上下文为技能), 'install_from_github' (从GitHub安装), 'install_from_url' (从链接提取安装)")
    name: str = Field(description="神通名称（kebab-case 命名，如：'news-brief'）")
    description: Optional[str] = Field(default=None, description="神通的简短描述")
    content: Optional[str] = Field(default=None, description="神通的核心内容（SOP 流程说明）")
    github_repo: Optional[str] = Field(default=None, description="GitHub 仓库地址（如 'HKUDS/nanobot'）")
    github_path: Optional[str] = Field(default=None, description="仓库内的目录路径")
    url: Optional[str] = Field(default=None, description="来源链接地址")

class SkillCreatorTool(BaseMonkeyKingTool):
    """
    灵猴悟性车间（Skill Creator）：
    大圣的“感悟法门”，用于通过对话沉淀、GitHub 搬运或链接提取来炼制新的神通 (Skill)。
    大圣进化现在只通过创建 Skill (SOP) 实现，不再单独生成 Tool。
    """
    @property
    def name(self) -> str:
        return "skill_creator"

    @property
    def description(self) -> str:
        return "通过对话沉淀、GitHub 仓库安装或网页链接提取来创建/更新大圣的神通 (Skill)。"

    def to_langchain_tool(self) -> BaseTool:
        return StructuredTool.from_function(
            func=self._run,
            name=self.name,
            description=self.description,
            args_schema=SkillCreatorInput
        )

    def _run(self, action: str, name: str, **kwargs) -> str:
        try:
            if action == "create_skill":
                return self._create_skill(name, kwargs.get("description"), kwargs.get("content"))
            elif action == "install_from_github":
                return self._install_from_github(name, kwargs.get("github_repo"), kwargs.get("github_path"))
            elif action == "install_from_url":
                return self._install_from_url(name, kwargs.get("url"))
            else:
                return f"错误：未知操作 '{action}'。"
        except Exception as e:
            return f"感悟过程中出了点岔子：{str(e)}"

    def _create_skill(self, name: str, description: str, content: str) -> str:
        """创建符合 Claude 规范的 Skill Pack"""
        if not description or not content:
            return "错误：感悟新神通需要提供 description 和 content（SOP）。"
        
        skill_dir = LLMConfig.SKILLS_DIR / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "references").mkdir(exist_ok=True)
        (skill_dir / "scripts").mkdir(exist_ok=True)
        (skill_dir / "assets").mkdir(exist_ok=True)

        # 构造 SKILL.md，符合 Claude 规范（YAML frontmatter）
        skill_md_content = f"""---
name: {name}
description: {description}
---

{content}
"""
        with open(skill_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(skill_md_content)
        
        return f"✅ 成功：神通 '{name}' 已悟出并存入 {skill_dir}。该神通包含 SKILL.md 以及预留的 scripts/references/assets 目录。"

    def _install_from_github(self, name: str, repo: str, path: str) -> str:
        """从 GitHub 仓库安装 Skill"""
        if not repo:
            return "错误：必须提供 github_repo (如 'owner/repo')。"
        
        api_url = f"https://api.github.com/repos/{repo}/contents/{path or ''}"
        
        try:
            with httpx.Client(follow_redirects=True) as client:
                resp = client.get(api_url)
                if resp.status_code != 200:
                    return f"错误：无法访问 GitHub 仓库 ({resp.status_code})。请检查仓库地址和路径。"
                
                items = resp.json()
                if not isinstance(items, list):
                    return "错误：指定的路径不是一个目录或无法解析。"

                # 寻找 SKILL.md
                is_skill_pack = any(item['name'] == "SKILL.md" for item in items)
                
                if is_skill_pack:
                    target_dir = LLMConfig.SKILLS_DIR / name
                    target_dir.mkdir(parents=True, exist_ok=True)
                    self._download_recursive(client, items, target_dir)
                    return f"✅ 成功：已从 GitHub 安装神通包 '{name}' 到 {target_dir}。"
                
                return "未在指定路径找到符合 Claude 规范的 SKILL.md 文件。"
        except Exception as e:
            return f"从 GitHub 安装失败：{str(e)}"

    def _download_recursive(self, client, items, target_dir: Path):
        """递归下载目录内容"""
        for item in items:
            if item['type'] == 'file':
                f_resp = client.get(item['download_url'])
                with open(target_dir / item['name'], "w", encoding="utf-8") as f:
                    f.write(f_resp.text)
            elif item['type'] == 'dir':
                new_target = target_dir / item['name']
                new_target.mkdir(exist_ok=True)
                dir_resp = client.get(item['url'])
                self._download_recursive(client, dir_resp.json(), new_target)

    def _install_from_url(self, name: str, url: str) -> str:
        """从链接提取并感悟能力"""
        if not url:
            return "错误：必须提供 url。"
        
        try:
            with httpx.Client(follow_redirects=True) as client:
                resp = client.get(url)
                if resp.status_code != 200:
                    return f"错误：无法访问链接 ({resp.status_code})。"
                
                content = resp.text[:10000] # 抓取前 10000 字符
                return f"已抓取链接内容。请大圣根据以下内容总结并调用 'create_skill' 感悟神通：\n\n--- CONTENT START ---\n{content}\n--- CONTENT END ---"
        except Exception as e:
            return f"从链接提取失败：{str(e)}"

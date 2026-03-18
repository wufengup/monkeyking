import json
import httpx
import re
import asyncio
import threading
import shutil
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool, StructuredTool
from src.tools.base_tool import BaseMonkeyKingTool
from src.utils.config import LLMConfig

class SkillCreatorInput(BaseModel):
    action: str = Field(description="要执行的操作：'create_skill' (创建技能), 'add_script_to_skill' (为已有技能添加脚本法宝), 'merge_skills' (整合多个技能为一个), 'install_from_github' (GitHub安装), 'install_from_url' (链接安装), 'install_from_clawhub' (ClawHub安装), 'uninstall_skill' (卸载技能)")
    name: str = Field(description="名称（如技能名）")
    description: Optional[str] = Field(default=None, description="描述信息")
    content: Optional[str] = Field(default=None, description="核心内容（SOP、脚本代码）")
    script_name: Optional[str] = Field(default=None, description="脚本文件名（用于 add_script_to_skill）")
    source_skills: Optional[List[str]] = Field(default=None, description="要被整合/合并的源技能名称列表（用于 merge_skills 动作）")
    github_repo: Optional[str] = Field(default=None, description="GitHub 仓库")
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
            elif action == "add_script_to_skill":
                return self._add_script_to_skill(name, kwargs.get("script_name"), kwargs.get("content"))
            elif action == "merge_skills":
                return self._merge_skills(name, kwargs.get("source_skills"), kwargs.get("description"), kwargs.get("content"))
            elif action == "install_from_github":
                return self._install_from_github(name, kwargs.get("github_repo"), kwargs.get("github_path"))
            elif action == "install_from_url":
                return self._install_from_url(name, kwargs.get("url", ""))
            elif action == "install_from_clawhub":
                return self._install_from_clawhub(name)
            elif action == "uninstall_skill":
                return self._uninstall_skill(name)
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

    def _add_script_to_skill(self, skill_name: str, script_name: str, content: str) -> str:
        """为已有技能添加脚本法宝"""
        if not skill_name or not script_name or not content:
            return "错误：需要提供技能名称、脚本名称以及脚本代码内容。"
        
        # 查找技能目录（优先主目录，其次内置目录以便更新）
        skill_dir = LLMConfig.SKILLS_DIR / skill_name
        if not skill_dir.exists():
            # 尝试内置目录
            builtin_dir = Path(__file__).parent.parent.parent / skill_name
            if builtin_dir.exists():
                skill_dir = builtin_dir
            else:
                return f"错误：未找到名为 '{skill_name}' 的神通。"

        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        
        script_file = scripts_dir / (script_name if script_name.endswith(".py") else f"{script_name}.py")
        
        try:
            with open(script_file, "w", encoding="utf-8") as f:
                f.write(content)
            return f"✅ 成功：已为神通 '{skill_name}' 炼制并存入脚本法宝 '{script_file.name}'。"
        except Exception as e:
            return f"脚本炼制失败：{str(e)}"

    def _merge_skills(self, target_name: str, source_skills: List[str], description: str, content: str) -> str:
        """整合/合并多个已有技能为一个更强大的新技能"""
        if not target_name or not source_skills or not description or not content:
            return "错误：整合神通需要提供目标名称、源技能列表、新描述及整合后的 SOP (content)。"
        
        # 1. 创建目标技能目录
        target_dir = LLMConfig.SKILLS_DIR / target_name
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "references").mkdir(exist_ok=True)
        (target_dir / "scripts").mkdir(exist_ok=True)
        (target_dir / "assets").mkdir(exist_ok=True)

        # 2. 收集源技能的资源并搬运
        merged_resources = []
        for src_name in source_skills:
            src_dir = LLMConfig.SKILLS_DIR / src_name
            if not src_dir.exists():
                # 尝试内置目录 (只读搬运，不删除)
                src_dir = Path(__file__).parent.parent.parent / src_name
                if not src_dir.exists():
                    continue

            # 搬运 scripts, references, assets
            for sub_dir in ["scripts", "references", "assets"]:
                src_sub = src_dir / sub_dir
                if src_sub.exists():
                    for item in src_sub.iterdir():
                        if item.is_file():
                            shutil.copy2(item, target_dir / sub_dir / item.name)
            
            merged_resources.append(src_name)

        # 3. 写入新的 SKILL.md
        skill_md_content = f"""---
name: {target_name}
description: {description}
---

{content}

> 本神通由以下神通整合而成：{', '.join(merged_resources)}
"""
        with open(target_dir / "SKILL.md", "w", encoding="utf-8") as f:
            f.write(skill_md_content)

        # 4. 卸载旧的扩展技能 (仅限主目录下的)
        uninstalled = []
        for src_name in source_skills:
            if src_name == target_name: continue # 如果是原地更新，不删除
            
            src_dir = (LLMConfig.SKILLS_DIR / src_name).resolve()
            if src_dir.exists() and str(src_dir).startswith(str(LLMConfig.SKILLS_DIR.resolve())):
                try:
                    shutil.rmtree(src_dir)
                    uninstalled.append(src_name)
                except:
                    pass

        status_msg = f"✅ 成功：已将 {', '.join(merged_resources)} 整合为新神通 '{target_name}'。"
        if uninstalled:
            status_msg += f"\n已清理旧的扩展技能：{', '.join(uninstalled)}。"
        
        return status_msg

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
                
                content = resp.text[:15000] # 抓取前 15000 字符，增加一点余地
                
                # 如果是 ClawHub 链接，增加专门的提示
                if "clawhub.ai" in url:
                    return f"已抓取 ClawHub 页面内容。请大圣从以下内容中寻找技能标识 (Slug，通常在 'clawhub install' 命令或标题附近)，找到后请调用 'install_from_clawhub' 动作进行安装：\n\n--- CONTENT START ---\n{content}\n--- CONTENT END ---"
                
                return f"已抓取链接内容。请大圣根据以下内容总结并调用 'create_skill' 感悟神通：\n\n--- CONTENT START ---\n{content}\n--- CONTENT END ---"
        except Exception as e:
            return f"从链接提取失败：{str(e)}"

    def _uninstall_skill(self, name: str) -> str:
        """从主目录卸载扩展技能"""
        if not name:
            return "错误：必须提供要卸载的神通名称。"
        
        # 确保只在主目录下的技能目录中操作
        target_dir = (LLMConfig.SKILLS_DIR / name).resolve()
        skills_base = LLMConfig.SKILLS_DIR.resolve()

        if not target_dir.exists():
            return f"错误：未找到神通 '{name}'，请确认名称是否正确（仅支持卸载主目录下的扩展技能）。"
        
        # 安全检查：确保 target_dir 是 skills_base 的子目录
        if not str(target_dir).startswith(str(skills_base)):
            return f"错误：拒绝访问。'{name}' 不在可卸载的扩展技能目录中。"

        try:
            shutil.rmtree(target_dir)
            return f"✅ 成功：神通 '{name}' 已从主目录卸载。"
        except Exception as e:
            return f"卸载神通时失败：{str(e)}"

    def _install_from_clawhub(self, slug: str) -> str:
        """从 ClawHub 安装 Skill"""
        if not slug:
            return "错误：必须提供 ClawHub 的 slug (如 'weather')。"
        
        skills_dir = LLMConfig.SKILLS_DIR
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        target_dir = skills_dir / slug
        if target_dir.exists():
            try:
                # 先尝试清理旧目录，防止 clawhub install 冲突
                shutil.rmtree(target_dir)
            except Exception as e:
                return f"安装前清理旧目录失败：{str(e)}"

        # 使用 clawhub cli 安装
        try:
            cmd = [
                "clawhub", "install", slug,
                "--workdir", str(skills_dir),
                "--dir", ".",
                "--no-input",
                "--force" # 增加强制覆盖参数
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return f"✅ 成功：已从 ClawHub 安装神通 '{slug}' 到 {skills_dir / slug}。\n输出：{result.stdout}"
        except subprocess.CalledProcessError as e:
            return f"从 ClawHub 安装失败：{e.stderr or e.stdout or str(e)}"
        except Exception as e:
            return f"安装过程中出现未知错误：{str(e)}"

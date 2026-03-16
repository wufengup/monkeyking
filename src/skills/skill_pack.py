import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.skills.base_skill import BaseMonkeyKingSkill


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def _split_frontmatter(raw_text: str) -> Tuple[Dict[str, Any], str]:
    """
    解析 SKILL.md 的 YAML frontmatter（原生风格最小子集）：
    - 仅解析扁平的 key: value
    - 主要使用 name / description
    """
    if not raw_text.startswith("---\n"):
        return {}, raw_text

    end = raw_text.find("\n---\n", 4)
    if end == -1:
        return {}, raw_text

    frontmatter_text = raw_text[4:end]
    body = raw_text[end + 5 :]

    data: Dict[str, Any] = {}
    for line in frontmatter_text.splitlines():
        if not line.strip():
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        data[key] = value.strip('"').strip("'")

    return data, body


def _extract_reference_paths(body: str) -> List[str]:
    """
    提取 markdown 链接中的相对路径作为 references（只收本地文件）。
    """
    refs: List[str] = []
    for match in re.findall(r"\[[^\]]+\]\(([^)]+)\)", body):
        target = match.strip()
        if target.startswith("http://") or target.startswith("https://") or target.startswith("#"):
            continue
        refs.append(target)
    # 去重保序
    seen = set()
    ordered: List[str] = []
    for ref in refs:
        if ref not in seen:
            seen.add(ref)
            ordered.append(ref)
    return ordered


def _tokenize(text: str) -> List[str]:
    """
    轻量分词：
    - 英文/数字按连续词切分
    - 中文连续片段额外展开为 2~3 字 ngram，提升“政策变化/最新消息”类匹配召回
    """
    raw_chunks = re.findall(r"[A-Za-z0-9_\-]+|[\u4e00-\u9fff]+", text.lower())
    tokens: List[str] = []
    for chunk in raw_chunks:
        if re.fullmatch(r"[\u4e00-\u9fff]+", chunk):
            if len(chunk) >= 2:
                tokens.append(chunk)
            for n in (2, 3):
                if len(chunk) < n:
                    continue
                for i in range(0, len(chunk) - n + 1):
                    tokens.append(chunk[i : i + n])
        else:
            if len(chunk) >= 2:
                tokens.append(chunk)

    # 去重保序
    seen = set()
    out: List[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            out.append(token)
    return out


class ClaudeStyleSkillPack(BaseMonkeyKingSkill):
    """
    Claude/OpenClaw 风格技能包：
    - 目录内以 SKILL.md 为主入口
    - frontmatter 提供 name/description (启动时加载)
    - body/references/scripts 仅在需要时延迟加载
    """

    skill_pack_type = "claude"

    def __init__(self, pack_dir: Path, metadata: Dict[str, Any]):
        self._pack_dir = pack_dir
        self._metadata = metadata
        self._body: Optional[str] = None
        self._refs: Optional[List[Path]] = None
        self._hint_terms: Optional[List[str]] = None
        self._loaded = False
        self._on_load_callback = None

    def _ensure_loaded(self):
        """延迟加载正文、参考资料和脚本"""
        if self._loaded:
            return
        
        skill_md = self._pack_dir / "SKILL.md"
        raw = _safe_read_text(skill_md)
        _, body = _split_frontmatter(raw)
        self._body = body.strip()
        self._refs = [Path(self._pack_dir / p).resolve() for p in _extract_reference_paths(self._body)]
        
        # 通知管理器加载脚本 (scripts 目录)
        if self._on_load_callback:
            self._on_load_callback(self._pack_dir)
            
        self._loaded = True

    def _get_hint_terms(self) -> List[str]:
        if self._hint_terms is None:
            # 基础匹配词项：仅使用名称和描述，避免启动时加载大文件
            self._hint_terms = _tokenize(f"{self.name} {self.description}")
        return self._hint_terms

    @property
    def name(self) -> str:
        return str(self._metadata.get("name", self._pack_dir.name))

    @property
    def description(self) -> str:
        return str(self._metadata.get("description", "Claude style skill pack"))

    @property
    def sop(self) -> str:
        self._ensure_loaded()
        return self._body

    def matches_query(self, query: str) -> bool:
        if not query.strip():
            return True
        q_tokens = set(_tokenize(query))
        if not q_tokens:
            return False
        # 基于名称和描述进行初步匹配
        overlap = sum(1 for t in self._get_hint_terms() if t in q_tokens)
        return overlap > 0

    def _select_reference_context(self, query: str, budget_chars: int = 2400) -> str:
        self._ensure_loaded()
        if not query.strip() or not self._refs:
            return ""

        q_tokens = set(_tokenize(query))
        candidates: List[Tuple[int, Path, str]] = []
        for ref in self._refs:
            content = _safe_read_text(ref)
            if not content:
                continue
            head = content[:800]
            text_for_score = f"{ref.name} {head}"
            score = sum(1 for t in q_tokens if t in text_for_score.lower())
            candidates.append((score, ref, content))

        candidates.sort(key=lambda x: x[0], reverse=True)
        picked: List[str] = []
        used = 0
        for score, ref, content in candidates:
            if score <= 0:
                continue
            chunk = content[:1200]
            block = f"\n[Reference: {ref}]\n{chunk}\n"
            if used + len(block) > budget_chars:
                break
            picked.append(block)
            used += len(block)

        return "".join(picked)

    def render_for_query(self, query: str) -> str:
        self._ensure_loaded()
        prompt = self._body
        ref_ctx = self._select_reference_context(query=query)
        if ref_ctx:
            prompt += "\n\n参考资料（按需加载）：\n" + ref_ctx
        return prompt


def load_claude_skill_pack_from_dir(pack_dir: Path) -> Optional[ClaudeStyleSkillPack]:
    """
    从目录中仅加载元数据（延迟加载正文）：
    - 入口文件：SKILL.md
    - 仅解析 frontmatter 的 name/description
    """
    skill_md = pack_dir / "SKILL.md"
    if not skill_md.exists():
        return None

    raw = _safe_read_text(skill_md)
    if not raw.strip():
        return None

    # 仅解析元数据
    metadata, _ = _split_frontmatter(raw)
    if not metadata.get("name"):
        metadata["name"] = pack_dir.name
    if not metadata.get("description"):
        metadata["description"] = "Claude style skill pack"

    return ClaudeStyleSkillPack(pack_dir=pack_dir, metadata=metadata)

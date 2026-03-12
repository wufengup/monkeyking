from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class DeepResearchSkill(BaseMonkeyKingSkill):
    """
    大圣的神通：深度搜索与调研。
    指导大圣如何利用联网搜索能力进行多维度的信息整合。
    """
    
    @property
    def name(self) -> str:
        return "DeepResearchSkill"

    @property
    def description(self) -> str:
        return "针对复杂问题进行深度联网调研、多源信息对比并产出洞察报告的能力。"

    @property
    def sop(self) -> str:
        return """
施展【深度搜索】神通的步骤：
1. **关键词拆解**：
    - 不要只搜索一个宽泛的词。将用户的问题拆解为多个核心关键词。
    - 如果首轮搜索结果不理想，尝试更换同义词或专业术语再次搜索。
2. **多源验证**：
    - 不要只相信第一个搜索结果。
    - 针对国内实时资讯，百度搜索（通过 web_search 法宝）通常能提供最丰富、最准确的内容。
    - 交叉验证多个站点的信息，确保事实的准确性。
3. **结构化输出**：
    - 将搜索到的零散信息整理为：现状、原因分析、大圣建议（结合教员远见）。
    - 必须注明重要信息的来源（网站名称）。
4. **长效记忆**：
    - 如果搜索到的信息对主人有长期价值（如：主人关心的行业趋势、技术选型），应主动建议将其存入长期记忆（Memory）。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["web_search", "baidu_search"]

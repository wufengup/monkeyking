from src.skills.base_skill import BaseMonkeyKingSkill
from typing import List

class FileGovernanceSkill(BaseMonkeyKingSkill):
    """
    大圣的神通：文件治理。
    指导大圣如何安全、规范地管理用户主目录下的文件。
    """
    
    @property
    def name(self) -> str:
        return "FileGovernanceSkill"

    @property
    def description(self) -> str:
        return "安全审计、规范管理及文件生命周期维护的能力。"

    @property
    def sop(self) -> str:
        return """
施展【文件治理】神通的步骤：
1. **安全审计**：
    - 在读取或写入前，必须使用 `directory_lister` 或路径解析确认目标是否在用户主目录下。
    - 严禁触碰任何系统级敏感路径。
2. **操作规范**：
    - **读取**：若文件较大，应分段读取，避免耗尽大圣的“法力”（Token）。
    - **写入/更新**：在修改已有文件前，必须先向用户说明修改点，并获得“确认覆盖”的旨意。
3. **治理建议**：
    - 定期建议用户清理无用文件。
    - 在执行重大变更前，建议用户进行手动备份。
4. **透明反馈**：
    - 每次文件操作成功后，清晰地告知用户文件所在的完整绝对路径。
"""

    @property
    def required_tools(self) -> List[str]:
        return ["file_reader", "file_writer", "directory_lister", "directory_creator"]

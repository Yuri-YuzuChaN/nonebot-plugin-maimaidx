import json

from ...resources import group_alias_file
from ..tool import writefile
from .models.alias import AliasesPush


class GroupAlias:
    push: AliasesPush

    def __init__(self) -> None:
        """别名推送类"""
        if not group_alias_file.exists():
            self.push = AliasesPush()
        else:
            self.push = AliasesPush.model_validate(
                json.load(open(group_alias_file, "r", encoding="utf-8"))
            )

    async def on(self, gid: int) -> str:
        """开启推送"""
        if gid not in self.push.enable:
            self.push.enable.append(gid)
        if gid in self.push.disable:
            self.push.disable.remove(gid)
        await writefile(group_alias_file, self.push.model_dump())
        return "群别名推送功能已开启"

    async def off(self, gid: int) -> str:
        """关闭推送"""
        if gid not in self.push.disable:
            self.push.disable.append(gid)
        if gid in self.push.enable:
            self.push.enable.remove(gid)
        await writefile(group_alias_file, self.push.model_dump())
        return "群别名推送功能已关闭"

    async def alias_global_change(self, switch: bool, group_list: list[int]):
        """修改全局开关"""
        if switch:
            self.push.disable.clear()
            self.push.enable.clear()
            self.push.enable.extend(group_list)
        else:
            self.push.enable.clear()
            self.push.disable.clear()
            self.push.disable.extend(group_list)
        await writefile(group_alias_file, self.push.model_dump())


alias = GroupAlias()

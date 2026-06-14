import json
import time
import traceback

import httpx
from pydantic import BaseModel, Field

from ...config import log
from ...resources import arcades_file
from ..tool import writefile

ARCADE_API_URL = "http://wc.wahlap.net/maidx/rest/location"


class Arcade(BaseModel):
    name: str
    location: str
    province: str = ""
    mall: str = ""
    num: int
    id: str
    alias: list[str] = Field(default_factory=list)
    group: list[int] = Field(default_factory=list)
    person: int = 0
    by: str = ""
    time: str = ""


class ArcadeList(list[Arcade]):
    async def save_arcade(self) -> bool:
        return await writefile(arcades_file, [arcade.model_dump() for arcade in self])

    def search_name(self, name: str) -> list[Arcade]:
        """模糊查询机厅。"""
        return [
            arcade
            for arcade in self
            if name in arcade.name or name in arcade.location or name in arcade.alias
        ]

    def search_fullname(self, name: str) -> list[Arcade]:
        return [arcade for arcade in self if name == arcade.name]

    def search_id(self, arcade_id: str) -> list[Arcade]:
        return [arcade for arcade in self if arcade_id == arcade.id]

    def add_arcade(self, arcade: dict) -> None:
        self.append(Arcade(**arcade))

    def del_arcade(self, arcade_name: str) -> bool:
        for arcade in self:
            if arcade_name == arcade.name:
                self.remove(arcade)
                return True
        return False

    def group_in_arcade(self, group_id: int, arcade_name: str) -> bool:
        for arcade in self:
            if arcade_name == arcade.name and group_id in arcade.group:
                return True
        return False

    def group_subscribe_arcade(self, group_id: int) -> list[Arcade]:
        return [arcade for arcade in self if group_id in arcade.group]

    @classmethod
    def arcade_to_msg(cls, arcade_list: list[Arcade]) -> list[str]:
        result = []
        for arcade in arcade_list:
            msg = f"{arcade.name}\n    - 当前 {arcade.person} 人\n"
            if arcade.num > 1:
                msg += f"    - 平均 {arcade.person / arcade.num:.2f} 人\n"
            if arcade.by:
                msg += f"    - 由 {arcade.by} 更新于 {arcade.time}"
            result.append(msg.strip())
        return result


class ArcadeData:
    total: ArcadeList | None = None

    def __init__(self) -> None:
        self.arcades: list[dict] = []
        self.id_list: list[int] = []

    def _load_local_arcades(self) -> None:
        if not arcades_file.exists():
            arcades_file.write_text("[]", encoding="utf-8")
        self.arcades = json.loads(arcades_file.read_text(encoding="utf-8"))

    def get_by_id(self, arcade_id: str) -> dict | None:
        for arcade in self.arcades:
            if str(arcade.get("id")) == arcade_id:
                return arcade
        return None

    async def get_arcades(self) -> None:
        self._load_local_arcades()
        self.total = await download_arcade_info()
        self.id_list = [int(arcade.id) for arcade in self.total]

    async def ensure_loaded(self) -> ArcadeList:
        if self.total is None:
            await self.get_arcades()
        if self.total is None:
            raise RuntimeError("机厅数据初始化失败")
        return self.total


arcade = ArcadeData()


async def download_arcade_info(save: bool = True) -> ArcadeList:
    try:
        data = None
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(ARCADE_API_URL)
                resp.raise_for_status()
                data = resp.json()
        except Exception:
            log.error("获取机厅信息失败，将使用本地缓存")

        arcade_list = ArcadeList()
        if data is not None:
            local_ids = set()
            for remote_arcade in data:
                arcade_id = str(remote_arcade["id"])
                local_ids.add(arcade_id)
                arcade_dict = arcade.get_by_id(arcade_id)
                if arcade_dict is None:
                    arcade_dict = {
                        "name": remote_arcade["arcadeName"],
                        "location": remote_arcade["address"],
                        "province": remote_arcade["province"],
                        "mall": remote_arcade["mall"],
                        "num": remote_arcade["machineCount"],
                        "id": arcade_id,
                        "alias": [],
                        "group": [],
                        "person": 0,
                        "by": "",
                        "time": "",
                    }
                else:
                    arcade_dict.update(
                        {
                            "name": remote_arcade["arcadeName"],
                            "location": remote_arcade["address"],
                            "province": remote_arcade["province"],
                            "mall": remote_arcade["mall"],
                            "num": remote_arcade["machineCount"],
                            "id": arcade_id,
                        }
                    )
                arcade_list.append(Arcade(**arcade_dict))

            for local_arcade in arcade.arcades:
                local_id = str(local_arcade.get("id"))
                if local_id not in local_ids and int(local_id) >= 10000:
                    arcade_list.append(Arcade(**{**local_arcade, "id": local_id}))
        else:
            for local_arcade in arcade.arcades:
                arcade_list.append(
                    Arcade(**{**local_arcade, "id": str(local_arcade.get("id"))})
                )

        if save:
            await arcade_list.save_arcade()
        return arcade_list
    except Exception:
        log.error(f"获取机厅信息失败：{traceback.format_exc()}")
        return ArcadeList()


async def update_arcade_machine_count(arcade_name: str, num: str) -> str:
    arcade_list = await arcade.ensure_loaded()
    if arcade_name.isdigit():
        matched = arcade_list.search_id(arcade_name)
    else:
        matched = arcade_list.search_fullname(arcade_name)
    if not matched:
        return f"未找到机厅：{arcade_name}"

    matched[0].num = int(num)
    await arcade_list.save_arcade()
    return f"已修改机厅 [{matched[0].name}] 机台数量为 [{num}]"


async def update_arcade_alias(arcade_name: str, alias_name: str, add: bool) -> str:
    arcade_list = await arcade.ensure_loaded()
    if arcade_name.isdigit():
        matched = arcade_list.search_id(arcade_name)
    else:
        matched = arcade_list.search_fullname(arcade_name)
    if not matched:
        return f"未找到机厅：{arcade_name}"

    selected = matched[0]
    changed = False
    if add:
        if alias_name in selected.alias:
            msg = f"机厅：{selected.name}\n已拥有别名：{alias_name}\n请勿重复添加"
        else:
            selected.alias.append(alias_name)
            changed = True
            msg = f"机厅：{selected.name}\n已添加别名：{alias_name}"
    else:
        if alias_name not in selected.alias:
            msg = f"机厅：{selected.name}\n未拥有别名：{alias_name}"
        else:
            selected.alias.remove(alias_name)
            changed = True
            msg = f"机厅：{selected.name}\n已删除别名：{alias_name}"

    if changed:
        await arcade_list.save_arcade()
    return msg


async def subscribe_arcade(group_id: int, arcade_name: str, sub: bool) -> str:
    arcade_list = await arcade.ensure_loaded()
    if arcade_name.isdigit():
        matched = arcade_list.search_id(arcade_name)
    else:
        matched = arcade_list.search_fullname(arcade_name)
    if not matched:
        return f"未找到机厅：{arcade_name}"

    selected = matched[0]
    changed = False
    if sub:
        if arcade_list.group_in_arcade(group_id, selected.name):
            msg = f"该群已订阅机厅：{selected.name}"
        else:
            selected.group.append(group_id)
            changed = True
            msg = f"群：{group_id} 已添加订阅机厅：{selected.name}"
    else:
        if not arcade_list.group_in_arcade(group_id, selected.name):
            msg = f"该群未订阅机厅：{selected.name}，无需取消订阅"
        else:
            selected.group.remove(group_id)
            changed = True
            msg = f"群：{group_id} 已取消订阅机厅：{selected.name}"

    if changed:
        await arcade_list.save_arcade()
    return msg


async def update_arcade_person(
    arcade_list: list[Arcade], user_name: str, action: str, person: int
) -> str:
    if len(arcade_list) > 1:
        return "找到多个机厅，请使用ID变更人数\n" + "\n".join(
            [f"{arcade.id}：{arcade.name}" for arcade in arcade_list]
        )
    if not arcade_list:
        return "没有找到指定机厅"

    selected = arcade_list[0]
    original_person = selected.person
    if action in ["+", "＋", "增加", "添加", "加"]:
        if person > 30:
            return "请勿一次增加过多人数"
        selected.person += person
    elif action in ["-", "－", "减少", "降低", "减"]:
        if person > 30 or person > selected.person:
            return "请勿一次减少过多人数"
        selected.person -= person
    elif action in ["=", "＝", "设置", "设定"]:
        if abs(selected.person - person) > 30:
            return "请勿一次变更过多人数"
        selected.person = person

    if selected.person == original_person:
        return f"人数没有变化\n机厅：{selected.name}\n当前人数：{selected.person}"

    selected.by = user_name
    selected.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    total = await arcade.ensure_loaded()
    await total.save_arcade()
    return f"机厅：{selected.name}\n当前人数：{selected.person}\n变更时间：{selected.time}"


async def reset_arcade_people() -> None:
    arcade.total = await download_arcade_info(False)
    total = await arcade.ensure_loaded()
    for selected in total:
        selected.person = 0
        selected.by = "自动清零"
        selected.time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    await total.save_arcade()
    log.info("maimaiDX排卡数据更新完毕")

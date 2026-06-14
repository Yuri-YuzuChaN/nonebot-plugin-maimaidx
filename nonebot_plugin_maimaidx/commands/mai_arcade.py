import re
from re import Match

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_OWNER,
    GroupMessageEvent,
    Message,
    MessageSegment,
)
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER

from ..config import log
from ..core.image.tools import text_to_bytes_io
from ..core.service.arcade import (
    arcade,
    download_arcade_info,
    reset_arcade_people,
    subscribe_arcade,
    update_arcade_alias,
    update_arcade_machine_count,
    update_arcade_person,
)

sv_help = """排卡指令如下：
添加机厅 <店名> <地址> <机台数量> 添加机厅信息
删除机厅 <店名> 删除机厅信息
修改机厅 <店名/ID> 数量 <数量> 修改机厅信息
添加/删除机厅别名 <店名/ID> <别名>
订阅机厅 <店名/ID> 订阅机厅，简化后续指令
查看订阅 查看群组订阅机厅的信息
取消订阅机厅 <店名/ID> 取消群组机厅订阅
查找机厅,查询机厅,机厅查找,机厅查询 <关键词> 查询对应机厅信息
<店名/别名>人数设置,设定,=,增加,加,+,减少,减,-<人数> 操作排卡人数
<店名/别名>有多少人,有几人,有几卡,几人,几卡 查看排卡人数
机厅几人 查看已订阅机厅排卡人数"""

manage_permission = SUPERUSER | GROUP_OWNER | GROUP_ADMIN

arcade_help = on_command("帮助maimaiDX排卡", aliases={"帮助maimaidx排卡"})
add_arcade = on_command("添加机厅", aliases={"新增机厅"}, permission=manage_permission)
del_arcade = on_command("删除机厅", aliases={"移除机厅"}, permission=manage_permission)
arcade_alias = on_command(
    "添加机厅别名", aliases={"删除机厅别名"}, permission=manage_permission
)
edit_arcade = on_command("修改机厅", aliases={"编辑机厅"}, permission=manage_permission)
watch_arcade = on_command("查看订阅", aliases={"查看订阅机厅"})
search_arcade = on_command(
    "查找机厅", aliases={"查询机厅", "机厅查找", "机厅查询", "搜索机厅", "机厅搜索"}
)
check_all_num = on_command("机厅几人", aliases={"jtj", "机厅几"})
check_num = on_command(
    "有多少人", aliases={"有几人", "有几卡", "多少人", "多少卡", "几人", "jr", "几卡"}
)
subscribe_matcher = on_regex(r"^(订阅机厅|取消订阅机厅|取消订阅)\s(.+)")
arcade_person_matcher = on_regex(
    r"^(.+)?\s?(设置|设定|＝|=|增加|添加|加|＋|\+|减少|降低|减|－|-)\s?([0-9]+|＋|\+|－|-)(人|卡)?$"
)
arcade_query_matcher = on_regex(r"^(.+)(有多少人|有几人|有几卡|多少人|多少卡|几人|几卡)$")


@arcade_help.handle()
async def _():
    await arcade_help.finish(
        MessageSegment.image(text_to_bytes_io(sv_help)), reply_message=True
    )


@add_arcade.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) == 1 and args[0] in ["帮助", "help", "指令帮助"]:
        await add_arcade.finish(
            "添加机厅指令格式：添加机厅 <店名> <位置> <机台数量> <别称1> <别称2> ...",
            reply_message=True,
        )
    if len(args) < 3 or not args[2].isdigit():
        await add_arcade.finish(
            "格式错误：添加机厅 <店名> <地址> <机台数量> [别称1] [别称2] ...",
            reply_message=True,
        )

    total = await arcade.ensure_loaded()
    if total.search_fullname(args[0]):
        await add_arcade.finish(f"机厅：{args[0]} 已存在，无法添加机厅", reply_message=True)

    next_id = max([10000, *arcade.id_list]) + 1
    total.add_arcade(
        {
            "name": args[0],
            "location": args[1],
            "province": "",
            "mall": "",
            "num": int(args[2]),
            "id": str(next_id),
            "alias": args[3:],
            "group": [],
            "person": 0,
            "by": "",
            "time": "",
        }
    )
    arcade.id_list.append(next_id)
    await total.save_arcade()
    await add_arcade.finish(f"机厅：{args[0]} 添加成功", reply_message=True)


@del_arcade.handle()
async def _(message: Message = CommandArg()):
    name = message.extract_plain_text().strip()
    if not name:
        await del_arcade.finish("格式错误：删除机厅 <店名>，店名需全名", reply_message=True)

    total = await arcade.ensure_loaded()
    if not total.del_arcade(name):
        await del_arcade.finish(f"未找到机厅：{name}", reply_message=True)

    await total.save_arcade()
    await del_arcade.finish(f"机厅：{name} 删除成功", reply_message=True)


@arcade_alias.handle()
async def _(event: GroupMessageEvent, message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    add = event.message.extract_plain_text().startswith("添加")
    if len(args) != 2:
        await arcade_alias.finish("格式错误：添加/删除机厅别名 <店名/ID> <别名>", reply_message=True)

    total = await arcade.ensure_loaded()
    if not args[0].isdigit() and len(matched := total.search_fullname(args[0])) > 1:
        await arcade_alias.finish(
            "找到多个相同店名的机厅，请使用店铺ID更改机厅别名\n"
            + "\n".join([f"{item.id}：{item.name}" for item in matched]),
            reply_message=True,
        )

    msg = await update_arcade_alias(args[0], args[1], add)
    await arcade_alias.finish(msg, reply_message=True)


@edit_arcade.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) != 3 or args[1] != "数量" or not args[2].isdigit():
        await edit_arcade.finish("格式错误：修改机厅 <店名/ID> 数量 <数量>", reply_message=True)

    msg = await update_arcade_machine_count(args[0], args[2])
    await edit_arcade.finish(msg, reply_message=True)


@watch_arcade.handle()
async def _(event: GroupMessageEvent):
    total = await arcade.ensure_loaded()
    subscribed = total.group_subscribe_arcade(event.group_id)
    if not subscribed:
        await watch_arcade.finish("该群未订阅任何机厅", reply_message=True)

    result = [f"群{event.group_id}订阅机厅信息如下："]
    for item in subscribed:
        alias = "\n  ".join(item.alias)
        result.append(
            f"店名：{item.name}\n    - 地址：{item.location}\n"
            f"    - 数量：{item.num}\n    - 别名：{alias}"
        )
    await watch_arcade.finish("\n".join(result), reply_message=True)


@search_arcade.handle()
async def _(message: Message = CommandArg()):
    name = message.extract_plain_text().strip()
    if not name:
        await search_arcade.finish("格式错误：查找机厅 <关键词>", reply_message=True)

    total = await arcade.ensure_loaded()
    arcade_list = total.search_name(name)
    if not arcade_list:
        await search_arcade.finish("没有这样的机厅哦", reply_message=True)

    result = ["为您找到以下机厅：\n"]
    for item in arcade_list:
        result.append(
            f"店名：{item.name}\n    - 地址：{item.location}\n"
            f"    - ID：{item.id}\n    - 数量：{item.num}"
        )
    if len(arcade_list) < 5:
        msg = "\n==========\n".join(result)
    else:
        msg = MessageSegment.image(text_to_bytes_io("\n".join(result)))
    await search_arcade.finish(msg, reply_message=True)


@subscribe_matcher.handle()
async def _(event: GroupMessageEvent, match: Match[str] = RegexMatched()):
    action = match.group(1)
    name = match.group(2)
    sub = action == "订阅机厅"

    total = await arcade.ensure_loaded()
    if not name.isdigit() and len(matched := total.search_fullname(name)) > 1:
        await subscribe_matcher.finish(
            "找到多个相同店名的机厅，请使用店铺ID订阅\n"
            + "\n".join([f"{item.id}：{item.name}" for item in matched]),
            reply_message=True,
        )

    msg = await subscribe_arcade(event.group_id, name, sub)
    await subscribe_matcher.finish(msg, reply_message=True)


@arcade_person_matcher.handle()
async def _(event: GroupMessageEvent, match: Match[str] = RegexMatched()):
    msg = None
    try:
        total = await arcade.ensure_loaded()
        arcade_name = match.group(1)
        action = match.group(2)
        amount = match.group(3)
        person = 1 if amount in ["＋", "+", "－", "-"] else int(amount)
        nickname = event.sender.card or event.sender.nickname or str(event.user_id)
        subscribed = total.group_subscribe_arcade(event.group_id)
        if not subscribed:
            return

        if not arcade_name:
            return
        if "人数" in arcade_name or "卡" in arcade_name:
            arcade_name = arcade_name[:-2]
        matched = [
            item
            for item in subscribed
            if arcade_name == item.name or arcade_name in item.alias
        ]
        if not matched:
            return

        msg = await update_arcade_person(matched, nickname, action, person)
    except Exception as e:
        log.exception(f"更新机厅人数失败：{e}")
        msg = "发生了一个错误"

    if msg:
        await arcade_person_matcher.finish(msg, reply_message=True)


@check_all_num.handle()
async def _(event: GroupMessageEvent):
    total = await arcade.ensure_loaded()
    subscribed = total.group_subscribe_arcade(event.group_id)
    if not subscribed:
        await check_all_num.finish("该群未订阅任何机厅", reply_message=True)

    await check_all_num.finish("\n".join(total.arcade_to_msg(subscribed)))


@check_num.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, message: Message = CommandArg()):
    await _query_arcade_num(matcher, event, message.extract_plain_text().strip())


@arcade_query_matcher.handle()
async def _(matcher: Matcher, event: GroupMessageEvent, match: Match[str] = RegexMatched()):
    await _query_arcade_num(matcher, event, match.group(1).strip())


async def _query_arcade_num(
    matcher: Matcher, event: GroupMessageEvent, name: str
) -> None:
    total = await arcade.ensure_loaded()
    subscribed = total.group_subscribe_arcade(event.group_id)
    if name:
        arcade_list = _search_subscribed_arcades(subscribed, name)
        if not arcade_list:
            await matcher.finish("已订阅的机厅中未找到匹配项", reply_message=True)
        await matcher.finish("\n".join(total.arcade_to_msg(arcade_list)))

    if subscribed:
        await matcher.finish("\n".join(total.arcade_to_msg(subscribed)))
    await matcher.finish(
        "该群未订阅任何机厅，请使用 订阅机厅 <名称> 指令订阅机厅", reply_message=True
    )


def _search_subscribed_arcades(subscribed: list, name: str) -> list:
    return [
        item
        for item in subscribed
        if name in item.name or any(name in alias for alias in item.alias)
    ]


async def update_arcade_daily() -> None:
    await reset_arcade_people()


async def refresh_arcade_data() -> None:
    arcade.total = await download_arcade_info()

import re
import traceback
from re import Match
from textwrap import dedent

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    GroupMessageEvent,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER

from ..config import log
from ..constants import SONGS_PER_PAGE
from ..core.clients.yuzuchan.client import YuzuChaNAPI
from ..core.clients.yuzuchan.models import Alias
from ..core.image.tools import text_to_bytes_io
from ..core.service import alias, mai, update_local_alias

update_alias = on_command("更新别名库", permission=SUPERUSER)
alias_local_apply = on_command("添加本地别名", aliases={"添加本地别称"})
alias_apply = on_command(
    "添加别名", aliases={"申请别名", "增加别名", "增添别名", "添加别称"}
)
alias_agree = on_command("同意别名", aliases={"同意别称"})
alias_status = on_command("当前投票", aliases={"当前别名投票", "当前别称投票"})
alias_switch = on_regex(
    r"^([开启关闭]+)别名推送$", permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN
)
alias_global_switch = on_regex(r"^全局([开启关闭]+)别名推送$", permission=SUPERUSER)
alias_song = on_regex(r"^(id)?\s?(.+)\s?有什么别[名称]$", re.IGNORECASE)


@update_alias.handle()
async def _(event: PrivateMessageEvent):
    try:
        await mai.get_music_alias()
        log.info("手动更新别名库成功")
        await update_alias.send("手动更新别名库成功")
    except Exception:
        log.error("手动更新别名库失败")
        await update_alias.send("手动更新别名库失败")


@alias_local_apply.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) != 2:
        await alias_local_apply.finish("参数错误", reply_message=True)
    song_id, alias_name = args
    if song_id.isdigit():
        song_id = int(song_id)
    else:
        await alias_local_apply.finish("请输入正确的ID", reply_message=True)
    if not mai.total_list.by_id(song_id):
        await alias_local_apply.finish(
            f"未找到ID「{song_id}」的曲目", reply_message=True
        )
    api = YuzuChaNAPI()
    server_exist = await api.get_aliases(song_id=song_id)
    if isinstance(server_exist, Alias) and alias_name.lower() in server_exist.alias:
        await alias_local_apply.finish(
            f"该曲目的别名「{alias_name}」已存在别名服务器", reply_message=True
        )

    local_exist = mai.total_alias_list.by_id(song_id)
    if local_exist and alias_name.lower() in local_exist[0].alias:
        await alias_local_apply.finish("本地别名库已存在该别名", reply_message=True)

    issave = await update_local_alias(song_id, alias_name)
    if not issave:
        msg = "添加本地别名失败"
    else:
        msg = f"已成功为ID「{song_id}」添加别名「{alias_name}」到本地别名库"
    await alias_local_apply.send(msg, reply_message=True)


@alias_apply.handle()
async def _(event: GroupMessageEvent, message: Message = CommandArg()):
    try:
        args = message.extract_plain_text().strip().split()
        if len(args) < 2:
            await alias_apply.finish("参数错误", reply_message=True)
        song_id = args[0]
        if not song_id.isdigit():
            await alias_apply.finish("请输入正确的ID", reply_message=True)
        alias_name = " ".join(args[1:])
        if not mai.total_list.by_id(int(song_id)):
            await alias_apply.finish(f"未找到ID「{song_id}」的曲目", reply_message=True)

        api = YuzuChaNAPI()
        isexist = await api.get_aliases(song_id=song_id)
        if isinstance(isexist, Alias) and alias_name.lower() in isexist.alias:
            await alias_apply.finish(
                f"该曲目的别名「{alias_name}」已存在别名服务器", reply_message=True
            )

        result = await api.post_alias(
            song_id, alias_name, event.user_id, event.group_id
        )
        msg = result.message
    except Exception as e:
        log.error(traceback.format_exc())
        msg = str(e)
    await alias_apply.finish(msg, reply_message=True)


@alias_agree.handle()
async def _(event: GroupMessageEvent, message: Message = CommandArg()):
    try:
        tag = message.extract_plain_text().strip().upper()
        api = YuzuChaNAPI()
        status = await api.post_agree_user(tag, event.user_id)
        await alias_agree.finish(status.message, reply_message=True)
    except ValueError as e:
        await alias_agree.finish(str(e), reply_message=True)


@alias_status.handle()
async def _(message: Message = CommandArg()):
    try:
        args = message.extract_plain_text().strip()
        api = YuzuChaNAPI()
        status = await api.get_status()
        if not status:
            await alias_status.finish("未查询到正在进行的别名投票", reply_message=True)

        page = max(min(int(args), len(status) // SONGS_PER_PAGE + 1), 1) if args else 1
        result = []
        for num, _s in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                apply_alias = _s.apply_alias
                if len(_s.apply_alias) > 15:
                    apply_alias = _s.apply_alias[:15] + "..."
                result.append(
                    dedent(f"""\
                        - {_s.tag}：
                        - ID：{_s.song_id}
                        - 别名：{apply_alias}
                        - 票数：{_s.agree_votes}/{_s.votes}
                    """)
                )
        result.append(f"第「{page}」页，共「{len(status) // SONGS_PER_PAGE + 1}」页")
        msg = MessageSegment.image(text_to_bytes_io("\n".join(result)))
    except Exception as e:
        log.error(traceback.format_exc())
        msg = str(e)
    await alias_status.finish(msg, reply_message=True)


@alias_song.handle()
async def _(match: Match[str] = RegexMatched()):
    findid = bool(match.group(1))
    name = match.group(2)
    aliases = None
    if findid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(int(name))
        if not alias_id:
            await alias_song.finish(
                "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                reply_message=True,
            )
        else:
            aliases = alias_id
    else:
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(int(name))
                if not alias_id:
                    await alias_song.finish(
                        "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                        reply_message=True,
                    )
                else:
                    aliases = alias_id
            else:
                await alias_song.finish(
                    "未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名",
                    reply_message=True,
                )
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = "\n".join(songs.alias)
            msg.append(f"ID：{songs.song_id}\n{alias_list}")
        await alias_song.finish(
            f"找到{len(aliases)}个相同别名的曲目：\n" + "\n======\n".join(msg),
            reply_message=True,
        )

    if len(aliases[0].alias) == 1:
        await alias_song.finish("该曲目没有别名", reply_message=True)

    msg = f"该曲目有以下别名：\nID：{aliases[0].song_id}\n"
    msg += "\n".join(aliases[0].alias)
    await alias_song.send(msg, reply_message=True)


@alias_switch.handle()
async def _(event: GroupMessageEvent, match: Match[str] = RegexMatched()):
    if match.group(1) == "开启":
        msg = await alias.on(event.group_id)
    elif match.group(1) == "关闭":
        msg = await alias.off(event.group_id)
    else:
        raise ValueError("matcher type error")

    await alias_switch.finish(msg, reply_message=True)


@alias_global_switch.handle()
async def _(bot: Bot, match: Match[str] = RegexMatched()):
    group = await bot.get_group_list()
    group_id = [g["group_id"] for g in group]
    if match.group(1) == "开启":
        await alias.alias_global_change(True, group_id)
        await alias_global_switch.finish("已全局开启maimai别名推送")
    elif match.group(1) == "关闭":
        await alias.alias_global_change(False, group_id)
        await alias_global_switch.finish("已全局关闭maimai别名推送")
    else:
        await alias_global_switch.finish()

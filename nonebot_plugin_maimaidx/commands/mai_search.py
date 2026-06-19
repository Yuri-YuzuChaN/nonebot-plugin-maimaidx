import re
from re import Match

from nonebot import on_regex
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.params import Depends, RegexMatched

from ..core.clients.yuzuchan.client import YuzuChaNAPI
from ..core.clients.yuzuchan.models import AliasStatus, Songs, StatusEnum
from ..core.database.qq import User
from ..core.handler import draw_chart_info, draw_song_list
from ..core.merge.alias import yuzu_alias_to_alias
from ..core.merge.models import Song
from ..core.service import mai
from .depend import GetUserAndAuthOrNone, process_regex

search = on_regex(r"^(定数|bpm|曲师|谱师)?查歌\s?(.+)", re.IGNORECASE)
search_alias_song = on_regex(r"(.+)是(?:什么|啥)歌[？?]?([0-9]+)?$", re.IGNORECASE)
query_chart = on_regex(r"^id\s?([0-9]+)$", re.IGNORECASE)


@search.handle()
async def _(
    result: tuple[list[Song], int] = Depends(process_regex),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    songs, page = result
    if not songs:
        await search.finish(
            "没有找到这样的乐曲。\n※ 如果是别名请使用「XXX是什么歌」指令进行查询哦。",
            reply_message=True,
        )

    if len(songs) == 1:
        image = await draw_chart_info(songs[0], user)
    elif len(songs) <= 5:
        r = ""
        for song in songs:
            r += f"{f'「{song.song_id}」':<7} {song.song_name}\n"
        image = MessageSegment.text(r)
    else:
        image = draw_song_list(songs, page)
    await search.send(image, reply_message=True)


@search_alias_song.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    name = match.group(1).strip()
    page = match.group(2) or 1
    error_msg = (
        f"未找到别名为「{name}」的歌曲\n"
        "※ 可以使用「添加别名」指令给该乐曲添加别名\n"
        "※ 如果是歌名的一部分，请使用「查歌」指令查询哦。"
    )
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        api = YuzuChaNAPI()
        try:
            obj = await api.get_songs(name)
            if isinstance(obj, Songs):
                if obj.type == StatusEnum.ONGOING and isinstance(
                    obj.data[0], AliasStatus
                ):
                    msg = f"未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n"
                    for _s in obj.data:
                        msg += f"- {_s.tag}\n    ID {_s.song_id}: {_s.name}\n"
                    msg += "※ 可以使用指令「同意别名 XXXXX」进行投票"
                    await search_alias_song.finish(msg.strip(), reply_message=True)
                else:
                    alias_data = yuzu_alias_to_alias(obj.data)
        except Exception:
            pass

    if alias_data:
        if len(alias_data) != 1:
            msg = f"找到{len(alias_data)}个相同别名的曲目：\n"
            for song in alias_data:
                msg += f"{song.song_id}：{song.song_name}\n"
            msg += "※ 请使用「id xxxxx」查询指定曲目"
            await search_alias_song.finish(msg.strip(), reply_message=True)
        else:
            song = mai.total_list.by_id(alias_data[0].song_id)
            if song:
                msg = "您要找的是不是：" + await draw_chart_info(song, user)
            else:
                msg = error_msg
            await search_alias_song.finish(msg, reply_message=True)

    # id
    if name.isdigit() and (song := mai.total_list.by_id(int(name))):
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user), reply_message=True
        )
    if search_id := re.search(r"^id([0-9]+)$", name, re.IGNORECASE):
        song = mai.total_list.by_id(int(search_id.group(1)))
        if not song:
            await search_alias_song.finish(
                f"未找到ID「{search_id.group(1)}」的乐曲", reply_message=True
            )
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user), reply_message=True
        )

    # 标题
    result = mai.total_list.filter(title=name)
    if len(result) == 0:
        msg = error_msg
    elif len(result) == 1:
        msg = "您要找的是不是：" + await draw_chart_info(result[0], user)
    elif len(result) <= 5:
        msg_ = (
            f"未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n"
        )
        for song in sorted(result, key=lambda x: int(x.song_id)):
            msg_ += f"{f'「{song.song_id}」':<7} {song.song_name}\n"
        msg_ += "※ 请使用「id xxxxx」查询指定曲目"
        msg = msg_
    else:
        msg = (
            f"未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n"
        )
        msg += draw_song_list(result, int(page))
    await search_alias_song.finish(msg, reply_message=True)


@query_chart.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    song_id = match.group(1)
    if not song_id.isdigit():
        await query_chart.finish("请输入正确的曲目ID", reply_message=True)

    song = mai.total_list.by_id(int(song_id))
    if not song:
        msg = f"未找到ID「{song_id}」的乐曲"
    else:
        msg = await draw_chart_info(song, user)
    await query_chart.finish(msg, reply_message=True)

import re
from textwrap import dedent

from nonebot import on_command, on_endswith, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.params import CommandArg, Depends, RegexMatched

from ..constants import DIFFS, SONGS_PER_PAGE
from ..core.clients.yuzuchan.client import YuzuChaNAPI
from ..core.clients.yuzuchan.models import AliasStatus
from ..core.database.qq import User
from ..core.image.tools import text_to_bytes_io
from ..core.search import draw_chart_info
from ..core.service import mai
from .extra import get_optional_user, get_user_db

search_music = on_command("查歌", aliases={"search"})
search_base = on_command("定数查歌", aliases={"search base"})
search_bpm = on_command("bpm查歌", aliases={"search bpm"})
search_artist = on_command("曲师查歌", aliases={"search artist"})
search_designer = on_command("谱师查歌", aliases={"search charter"})
search_alias_song = on_endswith(("是什么歌", "是啥歌"))
query_chart = on_regex(r"^id\s?([0-9]+)$", re.IGNORECASE)


def song_level(ds1: float, ds2: float) -> list[tuple[str, str, float, str]]:
    """
    查询定数范围内的乐曲

    Params:
        `ds1`: 定数下限
        `ds2`: 定数上限
    Return:
        `result`: 查询结果
    """
    result: list[tuple[str, str, float, str]] = []
    music_data = mai.total_list.filter(level_value=(ds1, ds2))
    for music in sorted(music_data, key=lambda x: int(x.song_id)):
        if int(music.song_id) >= 100000:
            continue
        for d in music.difficulties:
            result.append(
                (music.song_id, music.song_name, d.level_value, DIFFS[d.level_index])
            )
    return result


@search_music.handle()
async def _(
    message: Message = CommandArg(), user: User | None = Depends(get_optional_user)
):
    name = message.extract_plain_text().strip()
    page = 1
    if not name:
        await search_music.finish("请输入关键词")
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_music.finish(
            "没有找到这样的乐曲。\n※ 如果是别名请使用「别名查歌」指令进行查询哦。"
        )
    if len(result) == 1:
        await search_music.finish(await draw_chart_info(result[0], user))

    search_result = ""
    result.sort(key=lambda i: int(i.song_id))
    for i, music in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f"{f'「{music.song_id}」':<7} {music.song_name}\n"
    search_result += (
        f"第「{page}」页，"
        f"共「{len(result) // SONGS_PER_PAGE + 1}」页。"
        "请使用「id xxxxx」查询指定曲目。"
    )
    await search_music.send(MessageSegment.image(text_to_bytes_io(search_result)))


@search_base.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) > 4 or len(args) == 0:
        await search_base.finish(
            dedent("""
                命令格式：
                定数查歌 「定数」「页数」
                定数查歌 「定数下限」「定数上限」「页数」
            """)
        )
    page = 1
    if len(args) == 1:
        ds1, ds2 = args[0], args[0]
    elif len(args) == 2:
        if "." in args[1]:
            ds1, ds2 = args
        else:
            ds1, ds2 = args[0], args[0]
            page = args[1]
    else:
        ds1, ds2, page = args
    page = int(page)
    result = song_level(float(ds1), float(ds2))
    if not result:
        await search_base.finish("没有找到这样的乐曲。")

    search_result = ""
    for i, _result in enumerate(result):
        id, title, ds, diff = _result
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += (
                f"{f'「{id}」':<7}{f'「{diff}」':<11}{f'「{ds}」'} {title}\n"
            )
    search_result += (
        f"第「{page}」页，"
        f"共「{len(result) // SONGS_PER_PAGE + 1}」页。"
        "请使用「id xxxxx」查询指定曲目。"
    )
    await search_base.send(MessageSegment.image(text_to_bytes_io(search_result)))


@search_bpm.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        result = mai.total_list.filter(bpm=int(args[0]))
    elif len(args) == 2:
        if (bpm := int(args[0])) > int(args[1]):
            page = int(args[1])
            result = mai.total_list.filter(bpm=bpm)
        else:
            result = mai.total_list.filter(bpm=(bpm, int(args[1])))
    elif len(args) == 3:
        result = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
        page = int(args[2])
    else:
        await search_bpm.finish(
            "命令格式：\nbpm查歌 「bpm」\nbpm查歌 「bpm下限」「bpm上限」「页数」",
        )
    if not result:
        await search_bpm.finish("没有找到这样的乐曲。")

    search_result = ""
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    result.sort(key=lambda x: int(x.bpm))

    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += (
                f"{f'「{m.song_id}」':<7}{f'「BPM {m.bpm}」':<9} {m.song_name} \n"
            )
    search_result += (
        f"第「{page}」页，"
        f"共「{len(result) // SONGS_PER_PAGE + 1}」页。"
        "请使用「id xxxxx」查询指定曲目。"
    )
    await search_bpm.send(MessageSegment.image(text_to_bytes_io(search_result)))


@search_artist.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish("命令格式：\n曲师查歌「曲师名称」「页数」")
    else:
        await search_artist.finish("命令格式：\n曲师查歌「曲师名称」「页数」")

    result = mai.total_list.filter(artist_search=name)
    if not result:
        await search_artist.finish("没有找到这样的乐曲。")

    search_result = ""
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += (
                f"{f'「{m.song_id}」':<7}{f'「{m.artist}」'} - {m.song_name}\n"
            )
    search_result += (
        f"第「{page}」页，"
        f"共「{len(result) // SONGS_PER_PAGE + 1}」页。"
        "请使用「id xxxxx」查询指定曲目。"
    )
    await search_artist.send(MessageSegment.image(text_to_bytes_io(search_result)))


@search_designer.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_designer.finish("命令格式：\n谱师查歌「谱师名称」「页数」")
    else:
        await search_designer.finish("命令格式：\n谱师查歌「谱师名称」「页数」")

    result = mai.total_list.filter(charter_search=name)
    if not result:
        await search_designer.finish("没有找到这样的乐曲。")

    search_result = ""
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip(
                [DIFFS[d] for d in m.difficulties],
                [d.note_designer for d in m.difficulties],
            )
            diff_parts = [f"{f'「{d}」':<9}{f'「{c}」'}" for d, c in diff_charter]
            diff_str = " ".join(diff_parts)
            line = f"{f'「{m.song_id}」':<7}{diff_str} {m.song_name}\n"
            search_result += line
    search_result += (
        f"第「{page}」页，"
        f"共「{len(result) // SONGS_PER_PAGE + 1}」页。"
        "请使用「id xxxxx」查询指定曲目。"
    )
    await search_designer.send(MessageSegment.image(text_to_bytes_io(search_result)))


@search_alias_song.handle()
async def _(message: Message = CommandArg(), user: User = Depends(get_user_db)):
    name = message.extract_plain_text().strip().lower()
    error_msg = f"未找到别名为「{name}」的歌曲"
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    api = YuzuChaNAPI()
    if not alias_data:
        obj = await api.get_songs(name)
        if obj:
            if isinstance(obj[0], AliasStatus):
                await search_alias_song.finish(error_msg)
            else:
                alias_data = obj
    if alias_data:
        if len(alias_data) != 1:
            msg = f"找到{len(alias_data)}个相同别名的曲目：\n"
            for songs in alias_data:
                msg += f"{songs.song_id}：{songs.alias[0]}\n"
            msg += "※ 请使用「id xxxxx」查询指定曲目"
            await search_alias_song.finish(msg.strip())
        else:
            song = mai.total_list.by_id(str(alias_data[0].song_id))
            if song:
                msg = "您要找的是不是：" + await draw_chart_info(song, user)
            else:
                msg = error_msg
            await search_alias_song.finish(msg)

    # id
    if name.isdigit() and (song := mai.total_list.by_id(name)):
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user)
        )
    if search_id := re.search(r"^id([0-9]*)$", name, re.IGNORECASE):
        song = mai.total_list.by_id(search_id.group(1))
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(song, user)
        )

    # 标题
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_alias_song.finish(error_msg)
    elif len(result) == 1:
        await search_alias_song.finish(
            "您要找的是不是：" + await draw_chart_info(result[0], user)
        )
    elif len(result) < 50:
        msg = f"未找到别名为「{name}」的歌曲，但找到{len(result)}个相似标题的曲目：\n"
        for music in sorted(result, key=lambda x: int(x.song_id)):
            msg += f"{f'「{music.song_id}」':<7} {music.song_name}\n"
        msg += "※ 请使用「id xxxxx」查询指定曲目"
        await search_alias_song.finish(msg.strip())
    else:
        await search_alias_song.finish(f"结果过多「{len(result)}」条，请缩小查询范围。")


@query_chart.handle()
async def _(match=RegexMatched(), user: User | None = Depends(get_optional_user)):
    _id = match.group(1)
    if not _id.isdigit():
        await query_chart.finish("请输入正确的曲目ID")

    song = mai.total_list.by_id(int(_id))
    if not song:
        msg = f"未找到ID「{_id}」的乐曲"
    else:
        msg = await draw_chart_info(song, user)
    await query_chart.finish(msg)

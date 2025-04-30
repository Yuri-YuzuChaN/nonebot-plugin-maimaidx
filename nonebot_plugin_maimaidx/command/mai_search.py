import re
from typing import List, Tuple

from nonebot import on_command, on_endswith, on_regex
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
)
from nonebot.params import CommandArg, Endswith, RegexMatched

from ..config import SONGS_PER_PAGE, diffs
from ..libraries.image import text_to_bytes_io
from ..libraries.maimaidx_error import AliasesNotFoundError
from ..libraries.maimaidx_model import AliasStatus
from ..libraries.maimaidx_music import guess, mai, maiApi
from ..libraries.maimaidx_music_info import draw_music_info

search_music        = on_command('查歌', aliases={'search'})
search_base         = on_command('定数查歌', aliases={'search base'})
search_bpm          = on_command('bpm查歌', aliases={'search bpm'})
search_artist       = on_command('曲师查歌', aliases={'search artist'})
search_charter      = on_command('谱师查歌', aliases={'search charter'})
search_alias_song   = on_endswith(('是什么歌', '是啥歌'))
query_chart         = on_regex(r'^id\s?([0-9]+)$', re.IGNORECASE)


def song_level(ds1: float, ds2: float) -> List[Tuple[str, str, float, str]]:
    """
    查询定数范围内的乐曲
    
    Params:
        `ds1`: 定数下限
        `ds2`: 定数上限
    Return:
        `result`: 查询结果
    """
    result: List[Tuple[str, str, float, str]] = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    for music in sorted(music_data, key=lambda x: int(x.id)):
        if int(music.id) >= 100000:
            continue
        for i in music.diff:
            result.append((music.id, music.title, music.ds[i], diffs[i]))
    return result


@search_music.handle()
async def _(event: GroupMessageEvent, message: Message = CommandArg()):
    name = message.extract_plain_text().strip()
    page = 1
    if not name:
        await search_music.finish('请输入关键词', reply_message=True)
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_music.finish('没有找到这样的乐曲。\n※ 如果是别名请使用「xxx是什么歌」指令进行查询哦。', reply_message=True)
    if len(result) == 1:
        await search_music.finish(await draw_music_info(result.random(), event.user_id))
    
    search_result = ''
    result.sort(key=lambda i: int(i.id))
    for i, music in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{music.id}」":<7} {music.title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_music.finish(MessageSegment.image(text_to_bytes_io(search_result)), reply_message=True)


@search_base.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) > 3 or len(args) == 0:
        await search_base.finish('命令格式：\n定数查歌 「定数」「页数」\n定数查歌 「定数下限」「定数上限」「页数」')
    page = 1
    if len(args) == 1:
        ds1, ds2 = args[0], args[0]
    elif len(args) == 2:
        if '.' in args[1]:
            ds1, ds2 = args
        else:
            ds1, ds2 = args[0], args[0]
            page = args[1]
    else:
        ds1, ds2, page = args
    page = int(page)
    result = song_level(float(ds1), float(ds2))
    if not result:
        await search_base.finish('没有找到这样的乐曲。', reply_message=True)
    
    search_result = ''
    for i, _result in enumerate(result):
        id, title, ds, diff = _result
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{id}」":<7}{f"「{diff}」":<11}{f"「{ds}」"} {title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_base.finish(MessageSegment.image(text_to_bytes_io(search_result)), reply_message=True)


@search_bpm.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_bpm.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
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
        await search_bpm.finish('命令格式：\nbpm查歌 「bpm」\nbpm查歌 「bpm下限」「bpm上限」「页数」', reply_message=True)
    if not result:
        await search_bpm.finish('没有找到这样的乐曲。', reply_message=True)
    
    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    result.sort(key=lambda x: int(x.basic_info.bpm))
    
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「BPM {m.basic_info.bpm}」":<9} {m.title} \n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_bpm.finish(MessageSegment.image(text_to_bytes_io(search_result)), reply_message=True)


@search_artist.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_artist.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish('命令格式：\n曲师查歌「曲师名称」「页数」', reply_message=True)
    else:
        await search_artist.finish('命令格式：\n曲师查歌「曲师名称」「页数」', reply_message=True)

    result = mai.total_list.filter(artist_search=name)
    if not result:
        await search_artist.finish('没有找到这样的乐曲。', reply_message=True)

    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            search_result += f'{f"「{m.id}」":<7}{f"「{m.basic_info.artist}」"} - {m.title}\n'
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_artist.finish(MessageSegment.image(text_to_bytes_io(search_result)), reply_message=True)


@search_charter.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_bpm.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
    args = message.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name = args[0]
    elif len(args) == 2:
        name = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_charter.finish('命令格式：\n谱师查歌「谱师名称」「页数」', reply_message=True)
    else:
        await search_charter.finish('命令格式：\n谱师查歌「谱师名称」「页数」', reply_message=True)
    
    result = mai.total_list.filter(charter_search=name)
    if not result:
        await search_charter.finish('没有找到这样的乐曲。', reply_message=True)
    
    search_result = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            search_result += f'''{f"「{m.id}」":<7}{" ".join([f"{f'「{d}」':<9}{f'「{c}」'}" for d, c in diff_charter])} {m.title}\n'''
    search_result += f'第「{page}」页，共「{len(result) // SONGS_PER_PAGE + 1}」页。请使用「id xxxxx」查询指定曲目。'
    await search_charter.finish(MessageSegment.image(text_to_bytes_io(search_result)), reply_message=True)


@search_alias_song.handle()
async def _(event: MessageEvent, end: str = Endswith()):
    name = event.get_plaintext().lower()[0:-len(end)].strip()
    error_msg = f'未找到别名为「{name}」的歌曲\n※ 可以使用「添加别名」指令给该乐曲添加别名\n※ 如果是歌名的一部分，请使用「查歌」指令查询哦。'
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        try:
            obj = await maiApi.get_songs(name)
            if obj:
                if type(obj[0]) == AliasStatus:
                    msg = f'未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n'
                    for _s in obj:
                        msg += f'- {_s.Tag}\n    ID {_s.SongID}: {name}\n'
                    msg += f'※ 可以使用指令「同意别名 {_s.Tag}」进行投票'
                    await search_alias_song.finish(msg.strip(), reply_message=True)
                else:
                    alias_data = obj
        except AliasesNotFoundError:
            pass
    if alias_data:
        if len(alias_data) != 1:
            msg = f'找到{len(alias_data)}个相同别名的曲目：\n'
            for songs in alias_data:
                msg += f'{songs.SongID}：{songs.Name}\n'
            msg += '※ 请使用「id xxxxx」查询指定曲目'
            await search_alias_song.finish(msg.strip(), reply_message=True)
        else:
            music = mai.total_list.by_id(str(alias_data[0].SongID))
            if music:
                msg = '您要找的是不是：' + await draw_music_info(music, event.user_id)
            else:
                msg = error_msg
            await search_alias_song.finish(msg, reply_message=True)
    
    # id
    if name.isdigit() and (music := mai.total_list.by_id(name)):
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(music, event.user_id), reply_message=True)
    if search_id := re.search(r'^id([0-9]*)$', name, re.IGNORECASE):
        music = mai.total_list.by_id(search_id.group(1))
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(music, event.user_id), reply_message=True)
    
    # 标题
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_alias_song.finish(error_msg, reply_message=True)
    elif len(result) == 1:
        msg = await draw_music_info(result.random(), event.user_id)
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(result.random(), event.user_id), reply_message=True)
    elif len(result) < 50:
        msg = f'未找到别名为「{name}」的歌曲，但找到「{len(result)}」个相似标题的曲目：\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            msg += f'{f"「{music.id}」":<7} {music.title}\n'
        msg += '请使用「id xxxxx」查询指定曲目。'
        await search_alias_song.finish(msg.strip(), reply_message=True)
    else:
        await search_alias_song.finish(f'结果过多「{len(result)}」条，请缩小查询范围。', reply_message=True)


@query_chart.handle()
async def _(event: MessageEvent, match = RegexMatched()):
    id = match.group(1)
    music = mai.total_list.by_id(id)
    if not music:
        msg = f'未找到ID「{id}」的乐曲'
    else:
        msg = await draw_music_info(music, event.user_id)
    await query_chart.finish(msg)
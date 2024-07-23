import re

from nonebot import on_command, on_endswith, on_regex
from nonebot.adapters.onebot.v11 import GroupMessageEvent, Message, MessageEvent
from nonebot.params import CommandArg, Endswith, RegexMatched

from ..libraries.image import to_bytes_io
from ..libraries.maimaidx_music import guess
from ..libraries.maimaidx_music_info import *
from ..libraries.maimaidx_update_plate import *

search_music        = on_command('查歌', aliases={'search'}, priority=5)
search_base         = on_command('定数查歌', aliases={'search base'}, priority=5)
search_bpm          = on_command('bpm查歌', aliases={'search bpm'}, priority=5)
search_artist       = on_command('曲师查歌', aliases={'search artist'}, priority=5)
search_charter      = on_command('谱师查歌', aliases={'search charter'}, priority=5)
search_alias_song   = on_endswith(('是什么歌', '是啥歌'), priority=5)
query_chart         = on_regex(r'^id\s?([0-9]+)$', re.IGNORECASE, priority=5)


def song_level(ds1: float, ds2: float, stats1: str = None, stats2: str = None) -> list:
    result = []
    music_data = mai.total_list.filter(ds=(ds1, ds2))
    if stats1:
        if stats2:
            stats1 = stats1 + ' ' + stats2
            stats1 = stats1.title()
        for music in sorted(music_data, key=lambda x: int(x.id)):
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    else:
        for music in sorted(music_data, key=lambda x: int(x.id)):
            for i in music.diff:
                result.append((music.id, music.title, music.ds[i], diffs[i], music.level[i]))
    return result


@search_music.handle()
async def _(args: Message = CommandArg()):
    name = args.extract_plain_text().strip()
    if not name:
        return
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_music.finish('没有找到这样的乐曲。\n※ 如果是别名请使用「xxx是什么歌」指令来查询哦。', reply_message=True)
    elif len(result) == 1:
        msg = await draw_music_info(result.random())
        await search_music.finish(msg, reply_message=True)
    elif len(result) < 50:
        search_result = ''
        for music in sorted(result, key=lambda i: int(i.id)):
            search_result += f'{music.id}. {music.title}\n'
        await search_music.finish(search_result.strip() + '\n※ 请使用「id xxxxx」查询指定曲目', reply_message=True)
    else:
        await search_music.finish(f'结果过多（{len(result)} 条），请缩小查询范围。', reply_message=True)


@search_base.handle()
async def _(args: Message = CommandArg()):
    args = args.extract_plain_text().strip().split()
    page = 1
    if len(args) > 4 or len(args) == 0:
        await search_base.finish('命令格式为\n定数查歌 <定数>\n定数查歌 <定数下限> <定数上限>', reply_message=True)
    if len(args) == 1:
        result = song_level(float(args[0]), float(args[0]))
    elif len(args) == 2:
        try:
            result = song_level(float(args[0]), float(args[1]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]))
    elif len(args) == 3:
        try:
            result = song_level(float(args[0]), float(args[1]), str(args[2]))
        except:
            result = song_level(float(args[0]), float(args[0]), str(args[1]), str(args[2]))
    else:
        result = song_level(float(args[0]), float(args[1]), str(args[2]), str(args[3]))
    if not result:
        await search_base.finish('没有找到这样的乐曲。', reply_message=True)
    msg = ''
    page = max(min(page, len(result) // SONGS_PER_PAGE + 1), 1)
    for i, r in enumerate(result):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'{r[0]}. {r[1]} {r[3]} {r[4]}({r[2]})\n'
    msg += f'第{page}页，共{len(result) // SONGS_PER_PAGE + 1}页'
    await search_base.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)


@search_bpm.handle()
async def _(event: MessageEvent, args: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_bpm.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
    args = args.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        music_data = mai.total_list.filter(bpm=int(args[0]))
    elif len(args) == 2:
        if (bpm := int(args[0])) > int(args[1]):
            page = int(args[1])
            music_data = mai.total_list.filter(bpm=bpm)
        else:
            music_data = mai.total_list.filter(bpm=(bpm, int(args[1])))
    elif len(args) == 3:
        music_data = mai.total_list.filter(bpm=(int(args[0]), int(args[1])))
        page = int(args[2])
    else:
        await search_bpm.finish('命令格式为：\nbpm查歌 <bpm>\nbpm查歌 <bpm下限> <bpm上限> (<页数>)', reply_message=True)
    if not music_data:
        await search_bpm.finish('没有找到这样的乐曲。', reply_message=True)
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(sorted(music_data, key=lambda i: int(i.basic_info.bpm))):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} bpm {m.basic_info.bpm}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_bpm.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)


@search_artist.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_artist.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
    args = arg.extract_plain_text().strip().split()
    page = 1
    name = ''
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)', reply_message=True)
    else:
        await search_artist.finish('命令格式为：\n曲师查歌 <曲师名称> (<页数>)', reply_message=True)
    if not name:
        return
    music_data = mai.total_list.filter(artist_search=name)
    if not music_data:
        await search_artist.finish('没有找到这样的乐曲。', reply_message=True)
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            msg += f'No.{i + 1} {m.id}. {m.title} {m.basic_info.artist}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_artist.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)


@search_charter.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    if isinstance(event, GroupMessageEvent) and str(event.group_id) in guess.Group:
        await search_bpm.finish('本群正在猜歌，不要作弊哦~', reply_message=True)
    args = arg.extract_plain_text().strip().split()
    page = 1
    if len(args) == 1:
        name: str = args[0]
    elif len(args) == 2:
        name: str = args[0]
        if args[1].isdigit():
            page = int(args[1])
        else:
            await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)', reply_message=True)
    else:
        name = ''
        await search_charter.finish('命令格式为：\n谱师查歌 <谱师名称> (<页数>)', reply_message=True)
    if not name:
        return
    music_data = mai.total_list.filter(charter_search=name)
    if not music_data:
        await search_charter.finish('没有找到这样的乐曲。', reply_message=True)
    msg = ''
    page = max(min(page, len(music_data) // SONGS_PER_PAGE + 1), 1)
    for i, m in enumerate(music_data):
        if (page - 1) * SONGS_PER_PAGE <= i < page * SONGS_PER_PAGE:
            diff_charter = zip([diffs[d] for d in m.diff], [m.charts[d].charter for d in m.diff])
            msg += f'No.{i + 1} {m.id}. {m.title} {" ".join([f"{d}/{c}" for d, c in diff_charter])}\n'
    msg += f'第{page}页，共{len(music_data) // SONGS_PER_PAGE + 1}页'
    await search_charter.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)


@search_alias_song.handle()
async def _(event: MessageEvent, end: str = Endswith()):
    name = event.get_plaintext().lower()[0:-len(end)].strip()  # before 3.9
    # 别名
    alias_data = mai.total_alias_list.by_alias(name)
    if not alias_data:
        obj = await maiApi.get_songs(name)
        if obj:
            if 'status' in obj and obj['status']:
                msg = f'未找到别名为「{name}」的歌曲，但找到与此相同别名的投票：\n'
                for _s in obj['status']:
                    msg += f'- {_s["Tag"]}\n    ID {_s["SongID"]}: {name}\n'
                msg += f'※ 可以使用指令「同意别名 {_s["Tag"]}」进行投票'
                await search_alias_song.finish(msg.strip(), reply_message=True)
            else:
                alias_data = [Alias(**_a) for _a in obj]
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
                msg = '您要找的是不是：' + (await draw_music_info(music, event.user_id))
            else:
                msg = f'未找到别名为「{name}」的歌曲\n※ 可以使用「添加别名」指令给该乐曲添加别名\n※ 如果是歌名的一部分，请使用「查歌」指令查询哦。'
            await search_alias_song.finish(msg, reply_message=True)
    # id
    if name.isdigit() and (music := mai.total_list.by_id(name)):
        await search_alias_song.finish('您要找的是不是：' + (await draw_music_info(music, event.user_id)), reply_message=True)
    if search_id := re.search(r'^id([0-9]*)$', name, re.IGNORECASE):
        music = music = mai.total_list.by_id(search_id.group(1))
        await search_alias_song.finish('您要找的是不是：' + (await draw_music_info(music, event.user_id)), reply_message=True)
    # 标题
    result = mai.total_list.filter(title_search=name)
    if len(result) == 0:
        await search_alias_song.finish(f'未找到别名为「{name}」的歌曲\n※ 可以使用「添加别名」指令给该乐曲添加别名\n※ 如果是歌名的一部分，请使用「查歌」指令查询哦。', reply_message=True)
    elif len(result) == 1:
        msg = await draw_music_info(result.random(), event.user_id)
        await search_alias_song.finish('您要找的是不是：' + await draw_music_info(result.random(), event.user_id), reply_message=True)
    elif len(result) < 50:
        msg = f'未找到别名为「{name}」的歌曲，但找到{len(result)}个相似标题的曲目：\n'
        for music in sorted(result, key=lambda x: int(x.id)):
            msg += f'{music.id}. {music.title}\n'
        msg += '※ 请使用「id xxxxx」查询指定曲目'
        await search_alias_song.finish(msg.strip(), reply_message=True)
    else:
        await search_alias_song.finish(f'结果过多（{len(result)} 条），请缩小查询范围。', reply_message=True)


@query_chart.handle()
async def _(event: MessageEvent, match = RegexMatched()):
    id = match.group(1)
    music = mai.total_list.by_id(id)
    if not music:
        msg = f'未找到ID为「{id}」的乐曲'
    else:
        msg = await draw_music_info(music, event.user_id)
    await query_chart.send(msg)

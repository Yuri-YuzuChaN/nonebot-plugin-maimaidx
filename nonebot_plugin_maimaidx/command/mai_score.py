import re
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

from ..libraries.image import to_bytes_io
from ..libraries.maimaidx_music_info import *
from ..libraries.maimaidx_player_score import *
from ..libraries.maimaidx_update_plate import *

best50  = on_command('b50', aliases={'B50'}, priority=5)
minfo   = on_command('minfo', aliases={'minfo', 'Minfo', 'MINFO', 'info', 'Info', 'INFO'}, priority=5)
ginfo   = on_command('ginfo', aliases={'ginfo', 'Ginfo', 'GINFO'}, priority=5)
score   = on_command('分数线', priority=5)


def get_at_qq(message: Message) -> Optional[int]:
    for item in message:
        if isinstance(item, MessageSegment) and item.type == 'at' and item.data['qq'] != 'all':
            return int(item.data['qq'])


@best50.handle()
async def _(event: MessageEvent, matcher: Matcher, arg: Message = CommandArg()):
    qqid = get_at_qq(arg) or event.user_id
    username = arg.extract_plain_text().split()
    if _q := get_at_qq(arg):
        qqid = _q
    await matcher.finish(await generate(qqid, username), reply_message=True)


@minfo.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    qqid = get_at_qq(arg) or event.user_id
    args = arg.extract_plain_text().strip()
    if not args:
        await minfo.finish('请输入曲目id或曲名', reply_message=True)

    if mai.total_list.by_id(args):
        songs = args
    elif by_t := mai.total_list.by_title(args):
        songs = by_t.id
    else:
        aliases = mai.total_alias_list.by_alias(args)
        if not aliases:
            await minfo.finish('未找到曲目', reply_message=True)
        elif len(aliases) != 1:
            msg = '找到相同别名的曲目，请使用以下ID查询：\n'
            for songs in aliases:
                msg += f'{songs.SongID}：{songs.Name}\n'
            await minfo.finish(msg.strip(), reply_message=True)
        else:
            songs = str(aliases[0].SongID)
    pic = await music_play_data(qqid, songs)
    await minfo.finish(pic, reply_message=True)


@ginfo.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if not args:
        await ginfo.finish('请输入曲目id或曲名', reply_message=True)
    if args[0] not in '绿黄红紫白':
        level_index = 3
    else:
        level_index = '绿黄红紫白'.index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish('请输入曲目id或曲名', reply_message=True)
    if mai.total_list.by_id(args):
        id = args
    elif by_t := mai.total_list.by_title(args):
        id = by_t.id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            await ginfo.finish('未找到曲目', reply_message=True)
        elif len(alias) != 1:
            msg = '找到相同别名的曲目，请使用以下ID查询：\n'
            for songs in alias:
                msg += f'{songs.SongID}：{songs.Name}\n'
            await ginfo.finish(msg.strip(), reply_message=True)
        else:
            id = str(alias[0].SongID)
    music = mai.total_list.by_id(id)
    if not music.stats:
        await ginfo.finish('该乐曲还没有统计信息', reply_message=True)
    if len(music.ds) == 4 and level_index == 4:
        await ginfo.finish('该乐曲没有这个等级', reply_message=True)
    if not music.stats[level_index]:
        await ginfo.finish('该等级没有统计信息', reply_message=True)
    stats = music.stats[level_index]
    data = await music_global_data(music, level_index) + dedent(f'''\
        游玩次数：{round(stats.cnt)}
        拟合难度：{stats.fit_diff:.2f}
        平均达成率：{stats.avg:.2f}%
        平均 DX 分数：{stats.avg_dx:.1f}
        谱面成绩标准差：{stats.std_dev:.2f}
        ''')
    await ginfo.finish(data, reply_message=True)


@score.handle()
async def _(arg: Message = CommandArg()):
    _args = arg.extract_plain_text().strip()
    args = _args.split()
    if args and args[0] == '帮助':
        msg = dedent('''\
            此功能为查找某首歌分数线设计。
            命令格式：分数线 <难度+歌曲id> <分数线>
            例如：分数线 紫799 100
            命令将返回分数线允许的 TAP GREAT 容错以及 BREAK 50落等价的 TAP GREAT 数。
            以下为 TAP GREAT 的对应表：
            GREAT/GOOD/MISS
            TAP\t1/2.5/5
            HOLD\t2/5/10
            SLIDE\t3/7.5/15
            TOUCH\t1/2.5/5
            BREAK\t5/12.5/25(外加200落)''')
        await score.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)
    else:
        try:
            result = re.search(r'([绿黄红紫白])\s?([0-9]+)', _args)
            level_labels = ['绿', '黄', '红', '紫', '白']
            level_labels2 = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:MASTER']
            level_index = level_labels.index(result.group(1))
            chart_id = result.group(2)
            line = float(args[-1])
            music = mai.total_list.by_id(chart_id)
            chart = music.charts[level_index]
            tap = int(chart.notes.tap)
            slide = int(chart.notes.slide)
            hold = int(chart.notes.hold)
            touch = int(chart.notes.touch) if len(chart.notes) == 5 else 0
            brk = int(chart.notes.brk)
            total_score = tap * 500 + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            msg = dedent(f'''\
                {music.title} {level_labels2[level_index]}
                分数线 {line}% 允许的最多 TAP GREAT 数量为 {(total_score * reduce / 10000):.2f}(每个-{10000 / total_score:.4f}%),
                BREAK 50落(一共{brk}个)等价于 {(break_50_reduce / 100):.3f} 个 TAP GREAT(-{break_50_reduce / total_score * 100:.4f}%)''')
            await score.finish(MessageSegment.image(to_bytes_io(msg)), reply_message=True)
        except (AttributeError, ValueError) as e:
            log.exception(e)
            await score.finish('格式错误，输入“分数线 帮助”以查看帮助信息', reply_message=True)

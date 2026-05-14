import re
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends

from ..config import log
from ..core.database.qq import User
from ..core.image.tools import text_to_bytes_io
from ..core.search import draw_best50, draw_play_data, draw_song_galobal_data
from ..core.service import mai
from .depend import GetUserAndAuth

best50 = on_command("b50", aliases={"B50"})
info = on_command("info", aliases={"minfo", "Minfo", "MINFO", "info", "Info", "INFO"})
ginfo = on_command("ginfo", aliases={"ginfo", "Ginfo", "GINFO"})
score = on_command("分数线")


@best50.handle()
async def _(
    matcher: Matcher,
    message: Message = CommandArg(),
    user: User = Depends(GetUserAndAuth),
):
    username = message.extract_plain_text().strip()
    result = await draw_best50(user, username=username)
    await matcher.send(result, reply_message=True)


@info.handle()
async def _(
    matcher: Matcher,
    message: Message = CommandArg(),
    user: User = Depends(GetUserAndAuth),
):
    data = message.extract_plain_text().strip()
    if not data:
        await matcher.finish("请输入曲目id或曲名", reply_message=True)

    if data.isdigit() and mai.total_list.by_id(int(data)):
        song_id = data
    elif by_t := mai.total_list.by_name(data):
        song_id = by_t.song_id
    else:
        aliases = mai.total_alias_list.by_alias(data)
        if not aliases:
            await matcher.finish("未找到曲目", reply_message=True)
        elif len(aliases) != 1:
            msg = "找到相同别名的曲目，请使用以下ID查询：\n"
            for alias in aliases:
                msg += f"{alias.song_id}：{alias.alias[0]}\n"
            await matcher.finish(msg.strip(), reply_message=True)
        else:
            song_id = aliases[0].song_id
    song = mai.total_list.by_id(int(song_id))

    result = await draw_play_data(user, song)
    await matcher.send(result, reply_message=True)


@ginfo.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip()
    if not args:
        await ginfo.finish("请输入曲目id或曲名", reply_message=True)

    if args[0] not in "绿黄红紫白":
        level_index = 3
    else:
        level_index = "绿黄红紫白".index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish("请输入曲目id或曲名", reply_message=True)
    if mai.total_list.by_id(args):
        id = args
    elif by_t := mai.total_list.by_name(args):
        id = by_t.song_id
    else:
        alias = mai.total_alias_list.by_alias(args)
        if not alias:
            await ginfo.finish("未找到曲目", reply_message=True)
        elif len(alias) != 1:
            msg = "找到相同别名的曲目，请使用以下ID查询：\n"
            for songs in alias:
                msg += f"{songs.song_id}：{songs.alias[0]}\n"
            await ginfo.finish(msg.strip(), reply_message=True)
        else:
            id = str(alias[0].song_id)

    song = mai.total_list.by_id(id)
    stats = song.difficulties[level_index].stats

    if len(song.difficulties) == 4 and level_index == 4:
        await ginfo.finish("该乐曲没有这个等级", reply_message=True)
    if not song.difficulties[level_index]:
        await ginfo.finish("该等级没有统计信息", reply_message=True)

    data = await draw_song_galobal_data(song, level_index) + dedent(f"""\
        游玩次数：{round(stats.cnt)}
        拟合难度：{stats.fit_diff:.2f}
        平均达成率：{stats.avg:.2f}%
        平均 DX 分数：{stats.avg_dx:.1f}
        谱面成绩标准差：{stats.std_dev:.2f}""")
    await ginfo.send(data, reply_message=True)


@score.handle()
async def _(message: Message = CommandArg()):
    _args = message.extract_plain_text().strip()
    args = _args.split()
    if args and args[0] == "帮助":
        msg = dedent("""\
            此功能为查找某首歌分数线设计。
            命令格式：分数线「难度+歌曲id」「分数线」
            例如：分数线 紫799 100
            命令将返回分数线允许的「TAP」「GREAT」容错，
            以及「BREAK」50落等价的「TAP」「GREAT」数。
            以下为「TAP」「GREAT」的对应表：
                    GREAT / GOOD / MISS
            TAP         1 / 2.5  / 5
            HOLD        2 / 5    / 10
            SLIDE       3 / 7.5  / 15
            TOUCH       1 / 2.5  / 5
            BREAK       5 / 12.5 / 25 (外加200落)
        """).strip()
        await score.finish(
            MessageSegment.image(text_to_bytes_io(msg)), reply_message=True
        )
    else:
        try:
            result = re.search(r"([绿黄红紫白])\s?([0-9]+)", _args)
            level_labels = ["绿", "黄", "红", "紫", "白"]
            level_labels2 = ["Basic", "Advanced", "Expert", "Master", "Re:MASTER"]
            level_index = level_labels.index(result.group(1))
            chart_id = int(result.group(2))
            line = float(args[-1])
            song = mai.total_list.by_id(chart_id)
            chart = song.difficulties[level_index]
            tap = int(chart.notes.tap)
            slide = int(chart.notes.slide)
            hold = int(chart.notes.hold)
            touch = int(chart.notes.touch) if len(chart.notes) == 5 else 0
            brk = int(chart.notes.brk)
            total_score = (
                tap * 500 + slide * 1500 + hold * 1000 + touch * 500 + brk * 2500
            )
            break_bonus = 0.01 / brk
            break_50_reduce = total_score * break_bonus / 4
            reduce = 101 - line
            if reduce <= 0 or reduce >= 101:
                raise ValueError
            msg = (
                f"{song.song_name}「{level_labels2[level_index]}」\n"
                f"分数线「{line}%」\n允许的最多「TAP」「GREAT」数量为\n"
                f"「{(total_score * reduce / 10000):.2f}」(每个-{10000 / total_score:.4f}%),\n"
                f"「BREAK」50落(一共「{brk}」个)\n"
                f"等价于「{(break_50_reduce / 100):.3f}」个「TAP」"
                f"「GREAT」(-{break_50_reduce / total_score * 100:.4f}%)"
            )
            await score.finish(msg, reply_message=True)
        except (AttributeError, ValueError) as e:
            log.exception(e)
            await score.finish(
                "格式错误，输入“分数线 帮助”以查看帮助信息", reply_message=True
            )

import re
from textwrap import dedent

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.matcher import Matcher
from nonebot.params import CommandArg, Depends

from ..config import log
from ..core.database.qq import User
from ..core.handler import draw_best50, draw_play_data, draw_song_global_data
from ..core.image.tools import text_to_bytes_io
from ..core.merge.models import Song
from ..core.service import mai
from .depend import GetUserAndAuth

best50 = on_command("b50", aliases={"B50"})
ap50 = on_command("ap50", aliases={"AP50"})
info = on_command("info", aliases={"minfo", "Minfo", "MINFO", "info", "Info", "INFO"})
ginfo = on_command("ginfo", aliases={"ginfo", "Ginfo", "GINFO"})
score = on_command("分数线")


@best50.handle()
@ap50.handle()
async def _(
    matcher: Matcher,
    message: Message = CommandArg(),
    user: User = Depends(GetUserAndAuth),
):
    username = message.extract_plain_text().strip()
    result = await draw_best50(
        user, username=username, all_perfect=isinstance(matcher, ap50)
    )
    await matcher.send(result, reply_message=True)


async def search_song(matcher: Matcher, data: str) -> Song | None:
    if data.isdigit() and (by_id := mai.total_list.by_id(int(data))):
        song = by_id
    elif by_t := mai.total_list.by_name(data):
        song = by_t
    elif alias := mai.total_alias_list.by_alias(data):
        if not alias:
            await matcher.finish("未找到曲目", reply_message=True)
        elif len(alias) != 1:
            msg = "找到相同别名的曲目，请使用以下ID查询：\n"
            for songs in alias:
                msg += f"{songs.song_id}：{songs.alias[0]}\n"
            await matcher.finish(msg.strip(), reply_message=True)
        else:
            song = mai.total_list.by_id(alias[0].song_id)
    else:
        by_t = mai.total_list.filter(title=data)
        if (tn := len(by_t)) == 1:
            song = by_t[0]
        elif tn <= 5 and tn > 1:
            msg = f"未找到别名为「{data}」的歌曲，但找到「{tn}」个相似标题的曲目：\n"
            for s in sorted(by_t, key=lambda x: int(x.song_id)):
                msg += f"{f'「{s.song_id}」':<7} {s.song_name}\n"
            msg += "※ 请使用「info xxxxx」查询指定曲目"
            await matcher.finish(msg, reply_message=True)
        elif tn > 5:
            await matcher.finish("查询相似的曲目过多，请缩小范围。", reply_message=True)
        else:
            song = None

    return song


@info.handle()
async def _(
    message: Message = CommandArg(),
    user: User = Depends(GetUserAndAuth),
):
    args = message.extract_plain_text().strip().lower()
    if not args:
        await info.finish("请输入曲目id或曲名", reply_message=True)

    song = await search_song(info, args)

    if song is None:
        await info.finish("未找到曲目", reply_message=True)

    result = await draw_play_data(user, song)
    await info.send(result, reply_message=True)


@ginfo.handle()
async def _(message: Message = CommandArg()):
    args = message.extract_plain_text().strip().lower()
    if not args:
        await ginfo.finish("请输入曲目id或曲名", reply_message=True)

    if args[0] not in "绿黄红紫白":
        level_index = 3
    else:
        level_index = "绿黄红紫白".index(args[0])
        args = args[1:].strip()
        if not args:
            await ginfo.finish("请输入曲目id或曲名", reply_message=True)

    song = await search_song(ginfo, args)
    if song is None:
        await ginfo.finish("未找到曲目", reply_message=True)

    if level_index >= len(song.difficulties):
        await ginfo.finish("该乐曲没有这个等级", reply_message=True)
    stats = song.difficulties[level_index].stats
    if stats is None:
        await ginfo.finish("该等级没有统计信息", reply_message=True)

    data = await draw_song_global_data(song, level_index) + dedent(f"""\
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
            if song is None or level_index >= len(song.difficulties):
                raise ValueError
            chart = song.difficulties[level_index]
            tap = int(chart.notes.tap)
            slide = int(chart.notes.slide)
            hold = int(chart.notes.hold)
            touch = int(chart.notes.touch)
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

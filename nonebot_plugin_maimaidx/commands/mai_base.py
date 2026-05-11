import random
import re
from re import Match
from textwrap import dedent

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import (
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.matcher import Matcher
from nonebot.params import Arg, CommandArg, Depends, RegexMatched
from nonebot.permission import SUPERUSER
from PIL import Image

from ..config import lxnsconfig, maiconfig
from ..constants import FORTUNE, LEVEL_LIST
from ..core.clients.divingfish.client import DivingFishAPI
from ..core.database.qq import User, update_user
from ..core.image.tools import image_to_base64, song_chart
from ..core.merge.models import ServiceName, Theme
from ..core.search import (
    bind_lxns,
    draw_chart_info,
    draw_rating_ranking,
    draw_rise_score_list,
    get_mai_what,
)
from ..core.service import mai
from ..core.tool import qqhash
from ..resources import Root
from .depend import GetOrCreateUser, GetUserAndAuth, GetUserAndAuthOrNone

CODE_PATTERN = re.compile(r"^[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}$")
AUTHORIZE_URL = (
    "https://maimai.lxns.net/oauth/authorize"
    "?response_type=code"
    f"&client_id={lxnsconfig.lx_client_id}"
    f"&redirect_uri={lxnsconfig.redirect_uri}"
    "&scope=read_player+read_user_profile+write_player"
)
AUTHORIZE_MSG = dedent(f"""
    请点击以下链接进行授权
    允许「{maiconfig.bot_name} BOT」访问您的落雪查分器数据
    =======================
    {AUTHORIZE_URL}
    =======================
    点击授权后您应收到该格式的
    授权码：「XXXX-XXXX-XXXX」
    请复制该授权码，并粘贴到该窗口完成授权
    =======================
    请注意！！您必须在落雪查分器的
    「账号设置 -> 常规设置」中的
    「隐私设置」开启允许读取成绩，否
    则BOT将无法查询您的成绩
""").strip()
LXNS_ERROR = "BOT管理员尚未配置落雪查分器相关信息"


update_data = on_command("更新maimai数据", permission=SUPERUSER)
help = on_command("帮助maimaiDX", aliases={"帮助maimaidx"})
maimaidxrepo = on_command("项目地址maimaiDX", aliases={"项目地址maimaidx"})
bind = on_command("lxbind", aliases={"绑定落雪", "绑定lx"})
source = on_command("数据源")
theme = on_command("主题")
portune = on_command("今日舞萌")
mai_what = on_regex(r".*mai.*什么(.+)?")
random_song = on_regex(r"^[随来给]个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?).*")
rise_score = on_regex(r"^我要在?([0-9]+\+?)?[上加\+]([0-9]+)?分\s?(.+)?")
rating_ranking = on_command("查看排名")
my_rating_ranking = on_command("我的排名")


@update_data.handle()
async def _(event: PrivateMessageEvent):
    await mai.get_music()
    await mai.get_music_alias()
    await mai.get_plate_json()
    await update_data.finish("maimai数据更新完成")


@help.handle()
async def _():
    await help.finish(
        MessageSegment.image(image_to_base64(Image.open(Root / "maimaidxhelp.png"))),
        reply_message=True,
    )


@maimaidxrepo.handle()
async def _():
    await maimaidxrepo.finish(
        (
            "项目地址：https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx"
            "\n求star，求宣传~"
        ),
        reply_message=True,
    )


@bind.handle()
async def _(matcher: Matcher, message: Message = CommandArg()):
    if lxnsconfig.lxns_dev_token is None and (
        lxnsconfig.lx_client_id is None or lxnsconfig.redirect_uri is None
    ):
        await bind.finish(LXNS_ERROR + "，无法进行绑定授权。", reply_message=True)
    if message:
        matcher.set_arg("code", message)


@bind.got("code", prompt=AUTHORIZE_MSG)
async def _(message: Message = Arg("code"), user: User = Depends(GetOrCreateUser)):
    code = message.extract_plain_text().strip()
    if not CODE_PATTERN.fullmatch(code):
        await bind.reject("授权码格式错误，请重新发送。", reply_message=True)
    result = await bind_lxns(user, code)
    await bind.send(result, reply_message=True)


@source.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetOrCreateUser)):
    args = message.extract_plain_text().strip()
    source_ = ServiceName.get_by_index(args)
    if source_ is None:
        await source.finish(
            f"未找到该数据源：\n{ServiceName.get_help()}", reply_message=True
        )
    if (
        source_ == ServiceName.LXNS
        and lxnsconfig.lxns_dev_token is None
        and (lxnsconfig.lx_client_id is None or lxnsconfig.redirect_uri is None)
    ):
        await update_user(user.qqid, service=ServiceName.DIVINGFISH)
        await source.finish(
            LXNS_ERROR + "。为防止无法查询成绩，已强制将数据源切换为水鱼查分器。",
            reply_message=True,
        )

    await update_user(user.qqid, service=source_)
    await source.send(f"主题已切换为：「{source_.value}」", reply_message=True)


@theme.handle()
async def _(message: Message = CommandArg(), user: User = Depends(GetOrCreateUser)):
    args = message.extract_plain_text().strip()
    theme_ = Theme.get_by_index(args)
    if theme_ is None:
        await theme.finish(f"未找到该主题：\n{Theme.get_help()}", reply_message=True)

    await update_user(user.qqid, theme=theme_)
    await theme.send(f"主题已切换为：「{theme_.value}」", reply_message=True)


@portune.handle()
async def _(user: User = Depends(GetOrCreateUser)):
    h = qqhash(user.qqid)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f"\n今日人品值：{rp}\n"
    for i in range(11):
        if wm_value[i] == 3:
            msg += f"宜 {FORTUNE[i]}\n"
        elif wm_value[i] == 0:
            msg += f"忌 {FORTUNE[i]}\n"
    song = mai.total_list.root[h % len(mai.total_list.root)]
    ds = "/".join([str(d.level_value) for d in song.difficulties])
    msg += (
        f"{maiconfig.bot_name} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
        f"ID.{song.song_id} - {song.song_name}"
        f"{MessageSegment.image(song_chart(song.song_id))}"
        f"{ds}"
    )
    await portune.send(msg, reply_message=True)


@mai_what.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    song = mai.total_list.random()
    if (point := match.group(1)) and (
        "推分" in point or "上分" in point or "加分" in point
    ):
        _song = await get_mai_what(user)
        if _song is not None:
            song = _song
    await mai_what.finish(await draw_chart_info(song, user))


@random_song.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    if not match:
        await random_song.finish("参数错误，请重新发送随机谱面")
    diff = match.group(1)
    if diff == "dx":
        type_ = ["DX"]
    elif diff == "sd" or diff == "标准":
        type_ = ["SD"]
    else:
        type_ = ["SD", "DX"]
    level = match.group(3)
    if match.group(2) == "":
        songs = mai.total_list.filter(level=level, type=type_)
    else:
        songs = mai.total_list.filter(level=level, type=type_)
    if len(songs) == 0:
        result = "没有这样的乐曲哦。"
    else:
        result = await draw_chart_info(random.choice(songs), user)
    await random_song.send(result, reply_message=True)


@rise_score.handle()
async def _(match: Match[str] = RegexMatched(), user: User = Depends(GetUserAndAuth)):
    if not match:
        rating = None
        score = None
    else:
        rating = match.group(1)
        score = match.group(2)
    if score is not None:
        score = int(score)

    if rating and rating not in LEVEL_LIST:
        await rise_score.finish("无此等级", reply_message=True)

    data = await draw_rise_score_list(user, None, rating, score)
    await rise_score.send(data, reply_message=True)


@rating_ranking.handle()
async def _(message: Message = CommandArg()):
    name = ""
    page = 1
    args = message.extract_plain_text().strip()
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()
    pic = await draw_rating_ranking(name, page)
    await rating_ranking.send(pic, reply_message=True)


@my_rating_ranking.handle()
async def _(user: User = Depends(GetOrCreateUser)):
    api = DivingFishAPI(qqid=user.qqid)
    info = await api.query_user_b50()
    rank_data = await api.rating_ranking()
    for num, rank in enumerate(rank_data):
        if rank.username == info.username:
            result = f"您的Rating为「{rank.ra}」，排名第「{num + 1}」名"
            await my_rating_ranking.finish(result, reply_message=True)

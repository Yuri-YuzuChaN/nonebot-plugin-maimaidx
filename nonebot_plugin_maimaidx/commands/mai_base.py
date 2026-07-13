import random
import re
from re import Match
from textwrap import dedent

from httpx import HTTPError as HTTPXError
from nonebot import on_command, on_message, on_regex
from nonebot.adapters.onebot.v11 import (
    GroupMessageEvent,
    Message,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg, Depends, RegexMatched
from nonebot.permission import SUPERUSER
from nonebot.rule import Rule, is_type
from PIL import Image
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from ..config import log, lxnsconfig, maiconfig
from ..constants import FORTUNE, LEVEL_LIST
from ..core.clients.exceptions import HTTPError, UnknownError
from ..core.clients.divingfish.client import DivingFishAPI
from ..core.database.qq import User, update_user
from ..core.handler import (
    bind_lxns,
    draw_chart_info,
    draw_rating_ranking,
    draw_rise_score_list,
    get_mai_what,
)
from ..core.image.tools import image_to_base64, song_chart
from ..core.merge.models import ServiceName, Theme
from ..core.service import mai
from ..core.tool import qqhash
from ..lxns_oauth import (
    PendingBindingStore,
    build_authorize_url,
    extract_authorization_code,
    is_binding_channel_allowed,
)
from ..resources import Root
from .depend import GetOrCreateUser, GetUserAndAuth, GetUserAndAuthOrNone

AUTHORIZE_URL = build_authorize_url(
    lxnsconfig.lx_client_id or "", lxnsconfig.redirect_uri or ""
)
AUTHORIZE_MSG = dedent(f"""
    请完成落雪账号绑定：

    1. 打开以下链接并允许「{maiconfig.bot_name} BOT」访问您的落雪查分器数据
    =======================
    {AUTHORIZE_URL}
    =======================
    2. 授权完成后，复制页面显示的授权码
    3. 回到 QQ，直接发送授权码或完整回调链接

    本次绑定有效期为 10 分钟，授权码只能使用一次；
    超时或失效后请重新发送「lxbind」获取授权链接
    =======================
    请注意！！您必须在落雪查分器的
    「账号设置 -> 常规设置」中的
    「隐私设置」开启允许读取成绩，否
    则BOT将无法查询您的成绩
""").strip()
LXNS_ERROR = "BOT管理员尚未配置落雪查分器相关信息"
GROUP_BIND_GUIDE = (
    "BOT 管理员已将落雪绑定设置为仅私聊。"
    "\n请添加 Bot 为好友后，在私聊中发送「lxbind」开始绑定。"
    "\n部分 OneBot 实现无法接收陌生人的私聊消息；若没有响应，请先确认好友关系。"
)
INVALID_CODE_MSG = (
    "未识别到有效的落雪授权码。"
    "\n请发送授权页面显示的完整授权码，或直接粘贴完整回调链接。"
)
OAUTH_FAILED_MSG = (
    "落雪绑定失败：授权码可能已使用、已过期，或授权未成功。"
    "\n当前绑定会话仍有效，您可以发送新的授权码；"
    "如需重新授权，请再次发送「lxbind」。"
)
BINDING_TEMPORARY_FAILED_MSG = (
    "落雪绑定暂时失败：网络、响应数据或本地数据库出现异常。"
    "\n当前绑定会话仍有效，您可以稍后重新发送授权码；"
    "如果授权码已经使用，请再次发送「lxbind」重新授权。"
)
pending_bindings = PendingBindingStore()


async def is_pending_authorization_code(
    event: GroupMessageEvent | PrivateMessageEvent,
) -> bool:
    if not is_binding_channel_allowed(
        private_only=lxnsconfig.lxns_bind_private_only,
        is_private=isinstance(event, PrivateMessageEvent),
    ):
        return False
    return pending_bindings.is_active(event.self_id, event.user_id) and bool(
        extract_authorization_code(event.get_plaintext())
    )


async def complete_lxns_binding(user: User, code: str) -> tuple[str, bool]:
    try:
        result = await bind_lxns(user, code)
    except HTTPError as error:
        log.warning(f"落雪 OAuth 绑定失败：{type(error).__name__}")
        return OAUTH_FAILED_MSG, False
    except (HTTPXError, UnknownError, ValidationError, SQLAlchemyError) as error:
        log.warning(f"落雪 OAuth 绑定暂时失败：{type(error).__name__}")
        return BINDING_TEMPORARY_FAILED_MSG, False
    return result, result == "授权完成。"


update_data = on_command("更新maimai数据", permission=SUPERUSER)
help = on_command("帮助maimaiDX", aliases={"帮助maimaidx"})
maimaidxrepo = on_command("项目地址maimaiDX", aliases={"项目地址maimaidx"})
bind = on_command("lxbind", aliases={"绑定落雪", "绑定lx"}, block=True)
bind_code = on_message(
    rule=is_type(GroupMessageEvent, PrivateMessageEvent)
    & Rule(is_pending_authorization_code),
    priority=0,
    block=True,
)
source = on_command("数据源")
theme = on_command("主题")
portune = on_command("今日舞萌")
mai_what = on_regex(r".*mai.*什么(.+)?")
random_song = on_regex(
    r"^[随来给]个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?).*", re.IGNORECASE
)
rise_score = on_regex(r"^我要在?([0-9]+\+?)?[上加\+]([0-9]+)?分\s?(.+)?")
rating_ranking = on_command("查看排名")
my_rating_ranking = on_command("我的排名")


@update_data.handle()
async def _(event: PrivateMessageEvent):
    await mai.update()
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
async def _(
    event: GroupMessageEvent | PrivateMessageEvent,
    message: Message = CommandArg(),
    user: User = Depends(GetOrCreateUser),
):
    is_private = isinstance(event, PrivateMessageEvent)
    if not is_binding_channel_allowed(
        private_only=lxnsconfig.lxns_bind_private_only,
        is_private=is_private,
    ):
        await bind.finish(GROUP_BIND_GUIDE, reply_message=True)

    if not all(
        (
            lxnsconfig.lx_client_id,
            lxnsconfig.lx_client_secret,
            lxnsconfig.redirect_uri,
        )
    ):
        await bind.finish(LXNS_ERROR + "，无法进行绑定授权。", reply_message=True)

    text = message.extract_plain_text().strip()
    if not text:
        pending_bindings.start(event.self_id, event.user_id)
        channel_guide = (
            "请在当前私聊发送授权码或完整回调链接。"
            if is_private
            else (
                "建议在 Bot 私聊中发送授权码或完整回调链接；"
                "若 Bot 无法接收陌生人私聊，也可在当前群聊发送。"
            )
        )
        await bind.finish(
            f"{AUTHORIZE_MSG}\n\n{channel_guide}", reply_message=True
        )

    code = extract_authorization_code(text)
    if code is None:
        await bind.finish(INVALID_CODE_MSG, reply_message=True)

    result, succeeded = await complete_lxns_binding(user, code)
    if succeeded:
        pending_bindings.discard(event.self_id, event.user_id)
    else:
        pending_bindings.start(event.self_id, event.user_id)
    await bind.finish(result, reply_message=True)


@bind_code.handle()
async def _(
    event: GroupMessageEvent | PrivateMessageEvent,
    user: User = Depends(GetOrCreateUser),
):
    code = extract_authorization_code(event.get_plaintext())
    if code is None or not pending_bindings.is_active(
        event.self_id, event.user_id
    ):
        return
    result, succeeded = await complete_lxns_binding(user, code)
    if succeeded:
        pending_bindings.consume(event.self_id, event.user_id)
    await bind_code.finish(result, reply_message=True)


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
    await source.send(f"数据源已切换为：「{source_.value}」", reply_message=True)


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
    fortune_hash = qqhash(user.qqid)
    daily_random = random.Random(fortune_hash)
    rp = fortune_hash % 100
    h = fortune_hash
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f"今日人品值：{rp}\n"
    for i in range(11):
        if wm_value[i] == 3:
            msg += f"宜 {FORTUNE[i]}\n"
        elif wm_value[i] == 0:
            msg += f"忌 {FORTUNE[i]}\n"
    song = daily_random.choice(mai.total_list.root)
    ds = "/".join([str(d.level_value) for d in song.difficulties])
    result = (
        MessageSegment.text(
            msg
            + f"{maiconfig.bot_name} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲："
            + f"ID.{song.song_id} - {song.song_name}"
        )
        + MessageSegment.image(image_to_base64(Image.open(song_chart(song.song_id))))
        + MessageSegment.text(ds)
    )
    await portune.send(result, reply_message=True)


@mai_what.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    song = mai.total_list.random()
    if (
        (point := match.group(1))
        and ("推分" in point or "上分" in point or "加分" in point)
        and user
    ):
        _song = await get_mai_what(user)
        if _song is not None:
            song = _song
    await mai_what.finish(await draw_chart_info(song, user), reply_message=True)


@random_song.handle()
async def _(
    match: Match[str] = RegexMatched(),
    user: User | None = Depends(GetUserAndAuthOrNone),
):
    if not match:
        await random_song.finish("参数错误，请重新发送随机谱面", reply_message=True)
    diff = (match.group(1) or "").lower()
    if diff == "dx":
        type_ = ["DX"]
    elif diff == "sd" or diff == "标准":
        type_ = ["SD"]
    else:
        type_ = ["SD", "DX"]
    level = match.group(3)
    color = match.group(2)
    songs = mai.total_list.filter(level=level, type=type_)
    if color:
        ci = "绿黄红紫白".index(color)
        songs = [
            s
            for s in songs
            if len(s.difficulties) > ci and s.difficulties[ci].level == level
        ]
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

    data = await draw_rise_score_list(user, rating, score)
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
    await my_rating_ranking.finish(
        "未在查分器排行榜中找到您的记录。", reply_message=True
    )

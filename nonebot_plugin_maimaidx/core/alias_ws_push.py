import asyncio
import json
from textwrap import dedent

import httpx
from httpx_ws import WebSocketDisconnect, aconnect_ws
from nonebot import get_bot
from nonebot.adapters.onebot.v11 import (
    Bot,
    MessageSegment,
)

from ..config import log, maiconfig
from ..constants import UUID, VOTE_URL
from ..core.clients.yuzuchan.models import PushAliasStatus
from ..core.search import draw_chart_info
from ..core.service import alias, mai


async def push_alias(push: PushAliasStatus):
    bot: Bot = get_bot()
    song_id = push.Status.SongID
    alias_name = push.Status.ApplyAlias
    song = mai.total_list.by_id(song_id)

    if push.Type == "Approved":
        message = (
            MessageSegment.at(push.Status.ApplyUID)
            + "\n"
            + dedent(f"""\
            您申请的别名已通过审核
            =================
            {push.Status.Tag}：
            ID：{song_id}
            标题：{push.Status.Name}
            别名：{alias_name}
            =================
            请使用指令「同意别名 {push.Status.Tag}」进行投票
        """).strip()
            + await draw_chart_info(song)
        )
        await bot.send_group_msg(group_id=push.Status.GroupID, message=message)
        return
    if push.Type == "Reject":
        message = (
            MessageSegment.at(push.Status.ApplyUID)
            + "\n"
            + dedent(f"""\
            您申请的别名被拒绝
            =================
            ID：{song_id}
            标题：{push.Status.Name}
            别名：{alias_name}
        """).strip()
            + await draw_chart_info(song)
        )
        await bot.send_group_msg(group_id=push.Status.GroupID, message=message)
        return

    if not maiconfig.maimaidx_alias_push:
        await mai.get_music_alias()
        return
    group_list = await bot.get_group_list()
    group_ids: list[int] = list({g["group_id"] for g in group_list})
    message = ""
    if push.Type == "Apply":
        message = dedent(f"""\
            检测到新的别名申请
            =================
            {push.Status.Tag}：
            ID：{song_id}
            标题：{song.song_name}
            别名：{alias_name}
            浏览{VOTE_URL}查看详情
        """).strip() + await draw_chart_info(song)
    if push.Type == "End":
        message = dedent(f"""\
            检测到新增别名
            =================
            ID：{song_id}
            标题：{song.song_name}
            别名：{alias_name}
        """).strip() + await draw_chart_info(song)

    for gid in group_ids:
        if gid in alias.push.disable:
            continue
        try:
            await bot.send_group_msg(group_id=gid, message=message)
            await asyncio.sleep(5)
        except Exception:
            continue


async def ws_alias_server():
    log.info("正在连接别名推送服务器")
    if maiconfig.maimaidx_alias_proxy:
        wsapi = "www.yuzuchan.site/api/maimaidx"
    else:
        wsapi = "www.yuzuchan.moe/api/maimaidx"
    while True:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(60)) as session:
                async with aconnect_ws(f"wss://{wsapi}/ws/{UUID}", session) as ws:
                    log.success("别名推送服务器连接成功")
                    while True:
                        data = await ws.receive_text()
                        if data == "Hello":
                            log.info("别名推送服务器正常运行")
                        try:
                            newdata = json.loads(data)
                            status = PushAliasStatus.model_validate(newdata)
                            await push_alias(status)
                        except Exception:
                            continue
        except (WebSocketDisconnect, httpx.LocalProtocolError) as e:
            log.warning(f"连接断开或异常: {e}，将在 60 秒后重连")
            await asyncio.sleep(60)
            continue
        except Exception as e:
            log.error(f"别名推送服务器连接失败: {e}，将在 60 秒后重试")
            await asyncio.sleep(60)
            continue

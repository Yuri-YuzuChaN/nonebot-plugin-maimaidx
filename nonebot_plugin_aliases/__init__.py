import asyncio
import json
from textwrap import dedent

import httpx
from httpx_ws import WebSocketDisconnect, aconnect_ws
from loguru import logger as log
from nonebot import get_bot, get_driver, get_plugin_config, on_command
from nonebot.adapters.onebot.v11 import Bot, Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER
from pydantic import BaseModel

from ..nonebot_plugin_maimaidx.libraries.maimaidx_error import UnknownError
from ..nonebot_plugin_maimaidx.libraries.maimaidx_model import (
    AliasStatus,
    APIResult,
    PushAliasStatus,
)
from ..nonebot_plugin_maimaidx.libraries.maimaidx_music_info import draw_music_info, mai

headers = {
    'SakuraToken': 'loli5261'
}


class Config(BaseModel):
    
    supergroup: int


config = get_plugin_config(Config)


driver = get_driver()


@driver.on_startup
async def _():
    asyncio.ensure_future(ws_alias_server())



approved = on_command('通过别名', permission=SUPERUSER)
disagree = on_command('拒绝别名', permission=SUPERUSER)


@approved.handle()
@disagree.handle()
async def _(matcher: Matcher, message: Message = CommandArg()):
    args = message.extract_plain_text().strip().upper()
    if len(args) != 5:
        await approved.finish('标签错误', reply_message=True)
    
    if type(matcher) == approved:
        endpoint = 'approveapply'
        m = '通过'
    else:
        endpoint = 'rejectapply'
        m = '拒绝'
    
    async with httpx.AsyncClient(headers=headers) as session:
        res = await session.post(f'https://www.yuzuchan.moe/api/maimaidx/{endpoint}', json={'Tag': args})
        if res.status_code == 200:
            data = APIResult.model_validate(res.json())
        else:
            raise UnknownError
        if data.code == 3004:
            await approved.finish(data.content, reply_message=True)
        if data.code == 0:
            status = AliasStatus.model_validate(data.content)
        else:
            raise UnknownError
    
    await approved.send(f'已{m}「{status.Tag}」的别名申请')


async def push_alias(push: PushAliasStatus):
    bot: Bot = get_bot()
    
    pic = await draw_music_info(mai.total_list.by_id(push.Status.SongID))
    msg = dedent(f'''
        接收到新的别名申请：
        标签：「{push.Status.Tag}」
        别名：「{push.Status.ApplyAlias}」
    ''').strip() + pic
    
    await bot.send_group_msg(group_id=config.supergroup, message=msg)


async def ws_alias_server():
    """
    连接别名服务器
    """
    while True:
        try:
            async with httpx.AsyncClient(headers=headers) as session:
                async with aconnect_ws('wss://www.yuzuchan.moe/api/maimaidx/ws/super', session) as ws:
                    while True:
                        try:
                            log.success('别名审核推送服务器连接成功')
                            data = await ws.receive_text()
                            if data == 'Hello':
                                log.info('别名审核推送服务器正常运行')
                            try:
                                newdata = json.loads(data)
                                status = PushAliasStatus.model_validate(newdata)
                                await asyncio.create_task(push_alias(status))
                            except:
                                continue
                        except WebSocketDisconnect:
                            log.warning('别名推送服务器已断开连接，将在1分钟后重新尝试连接')
                            await asyncio.sleep(60)
                            log.info('正在尝试重新连接别名推送服务器')
                        except httpx.LocalProtocolError:
                            log.error('别名推送服务器连接失败，将在1分钟后重试')
                            await asyncio.sleep(60)
                            log.info('正在尝试重新连接别名推送服务器')
        except:
            log.error('别名推送服务器连接失败，将在1分钟后重试')
            await asyncio.sleep(60)
            log.info('正在尝试重新连接别名推送服务器')
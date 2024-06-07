import asyncio
import re
import traceback
from textwrap import dedent

from loguru import logger as log
from nonebot import get_bot, on_command, on_endswith, on_regex
from nonebot.adapters.onebot.v11 import (
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER
from PIL import Image

from ..config import *
from ..libraries.image import image_to_base64, text_to_image
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import *
from ..libraries.maimaidx_model import Alias
from ..libraries.maimaidx_music import alias, mai, update_local_alias

update_alias        = on_command('更新别名库', priority=5, permission=SUPERUSER)
alias_local_apply   = on_command('添加本地别名', aliases={'添加本地别称'}, priority=5)
alias_apply         = on_command('添加别名', aliases={'增加别名', '增添别名', '添加别称'}, priority=5)
alias_agree         = on_command('同意别名', aliases={'同意别称'}, priority=5)
alias_status        = on_command('当前投票', aliases={'当前别名投票', '当前别称投票'}, priority=5)
alias_switch        = on_endswith(('别名推送', '别称推送'), priority=5, permission=SUPERUSER)
alias_global_switch = on_regex(r'^全局([开启关闭]+)别名推送$', priority=5, permission=SUPERUSER)
alias_song          = on_regex(r'^(id)?\s?(.+)\s?有什么别[名称]$', re.IGNORECASE, priority=5)


@update_alias.handle()
async def _(event: PrivateMessageEvent):
    try:
        await mai.get_music_alias()
        log.info('手动更新别名库成功')
        await update_alias.send('手动更新别名库成功')
    except:
        log.error('手动更新别名库失败')
        await update_alias.send('手动更新别名库失败')


@alias_local_apply.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip().split()
    if len(args) != 2:
        await alias_local_apply.finish('参数错误', reply_message=True)
    _id, alias_name = args
    if not mai.total_list.by_id(_id):
        await alias_local_apply.finish(f'未找到ID为「{_id}」的曲目', reply_message=True)
    server_exist = await maiApi.get_songs_alias(_id)
    if alias_name in server_exist['Alias']:
        await alias_local_apply.finish(f'该曲目的别名「{alias_name}」已存在别名服务器，不能重复添加别名，如果bot未生效，请联系BOT管理员使用指令「更新别名库」')
    local_exist = mai.total_alias_list.by_id(_id)
    if local_exist and alias_name.lower() in local_exist[0].Alias:
        await alias_local_apply.finish(f'本地别名库已存在该别名', reply_message=True)
    issave = await update_local_alias(_id, alias_name)
    if not issave:
        msg = '添加本地别名失败'
    else:
        msg = f'已成功为ID「{_id}」添加别名「{alias_name}」到本地别名库'
    await alias_local_apply.send(msg, reply_message=True)
    
    
@alias_apply.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    try:
        args = arg.extract_plain_text().strip().split()
        if len(args) != 2:
            await alias_apply.finish('参数错误', reply_message=True)
        _id, alias_name = args
        if not mai.total_list.by_id(_id):
            await alias_apply.finish(f'未找到ID为 [{_id}] 的曲目', reply_message=True)
        isexist = await maiApi.get_songs_alias(_id)
        if alias_name in isexist['Alias']:
            await alias_apply.finish(f'该曲目的别名「{alias_name}」已存在，不能重复添加别名，如果bot未生效，请联系BOT管理员使用指令 「更新别名库」', reply_message=True)
        status = await maiApi.post_alias(_id, alias_name, event.user_id)
        if isinstance(status, str):
            await alias_apply.finish(status)
        msg = dedent(f'''\
            您已提交以下别名申请
            ID：{_id}
            别名：{alias_name}
            现在可用使用唯一标签「{status['Tag']}」来进行投票，例如：同意别名 {status['Tag']}
            浏览{vote_url}查看详情
            ''') + MessageSegment.image(image_to_base64(Image.open(await maiApi.download_music_pictrue(_id))))
    except ServerError as e:
        log.error(e)
        msg = str(e)
    except ValueError as e:
        log.error(traceback.format_exc())
        msg = str(e)
    await alias_apply.send(msg, reply_message=True)


@alias_agree.handle()
async def _(event: MessageEvent, arg: Message = CommandArg()):
    try:
        tag = arg.extract_plain_text().strip().upper()
        status = await maiApi.post_agree_user(tag, event.user_id)
        await alias_agree.finish(status, reply_message=True)
    except ValueError as e:
        await alias_agree.send(str(e), reply_message=True)


@alias_status.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    try:
        args = arg.extract_plain_text().strip()
        status = await maiApi.get_alias_status()
        if not status:
            await alias_status.finish('未查询到正在进行的别名投票', reply_message=True)
        page = max(min(int(args), len(status) // SONGS_PER_PAGE + 1), 1) if args else 1
        result = []
        for num, _s in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                result.append(dedent(f'''{_s['Tag']}：
                - ID：{_s['SongID']}
                - 别名：{_s['ApplyAlias']}
                - 票数：{_s['AgreeVotes']}/{_s['Votes']}'''))
        result.append(f'第{page}页，共{len(status) // SONGS_PER_PAGE + 1}页')
        msg = MessageSegment.image(image_to_base64(text_to_image('\n'.join(result))))
    except ServerError as e:
        log.error(str(e))
        msg = str(e)
    except ValueError as e:
        msg = str(e)
    await alias_status.send(msg, reply_message=True)


@alias_song.handle()
async def _(match = RegexMatched()):
    findid = bool(match.group(1))
    name = match.group(2)
    aliases: List[Alias] = []
    if findid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(name)
        if not alias_id:
            await alias_song.finish('未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', reply_message=True)
        else:
            aliases = alias_id
    else:            
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(name)
                if not alias_id:
                    await alias_song.finish('未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', reply_message=True)
                else:
                    aliases = alias_id
            else:
                await alias_song.finish('未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', reply_message=True)
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = '\n'.join(songs.Alias)
            msg.append(f'ID：{songs.SongID}\n{alias_list}')
        await alias_song.finish(f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg), reply_message=True)

    if len(aliases[0].Alias) == 1:
        await alias_song.finish('该曲目没有别名', reply_message=True)

    msg = f'该曲目有以下别名：\nID：{aliases[0].SongID}\n'
    msg += '\n'.join(aliases[0].Alias)
    await alias_song.finish(msg, reply_message=True)


@alias_switch.handle()
async def _(event: GroupMessageEvent, arg: Message = CommandArg()):
    gid = str(event.group_id)
    args = arg.extract_plain_text().strip()
    if args == '开启':
        msg = await alias.on(gid)
    elif args == '关闭':
        msg = await alias.off(gid)
    else:
        raise ValueError('matcher type error')

    await alias_switch.finish(msg, reply_message=True)


@alias_global_switch.handle()
async def _(event: PrivateMessageEvent, match = RegexMatched()):
    if match.group(1) == '开启':
        alias.alias_global_change(True)
        await alias_global_switch.send('已全局开启maimai别名推送')
    elif match.group(1) == '关闭':
        alias.alias_global_change(False)
        await alias_global_switch.send('已全局关闭maimai别名推送')
    else:
        return


async def alias_apply_status():
    bot: Bot = get_bot()
    try:
        if (status := await maiApi.get_alias_status()) and alias.config['global']:
            msg = ['检测到新的别名申请']
            for _s in status:
                if _s['IsNew'] and (usernum := _s['AgreeVotes']) < (votes := _s['Votes']):
                    song_id = str(_s['SongID'])
                    alias_name = _s['ApplyAlias']
                    music = mai.total_list.by_id(song_id)
                    msg.append(f'{_s["Tag"]}：\nID：{song_id}\n标题：{music.title}\n别名：{alias_name}\n票数：{usernum}/{votes}')
            if len(msg) != 1:
                for group in await bot.get_group_list():
                    gid = group['group_id']
                    if gid in alias.config['disable'] or gid not in alias.config['enable']:
                        continue
                    try:
                        await bot.send_group_msg(group_id=gid, message='\n======\n'.join(msg))
                        await asyncio.sleep(5)
                    except:
                        continue
        await asyncio.sleep(5)
        if end := await maiApi.get_alias_end():
            if alias.config['global']:
                msg2 = ['以下是已成功添加别名的曲目']
                for _e in end:
                    song_id = str(_e['SongID'])
                    alias_name = _e['ApplyAlias']
                    music = mai.total_list.by_id(song_id)
                    msg2.append(f'ID：{song_id}\n标题：{music.title}\n别名：{alias_name}')
                if len(msg2) != 1:
                    for group in await bot.get_group_list():
                        gid = group['group_id']
                        if gid in alias.config['disable'] or gid not in alias.config['enable']:
                            continue
                        try:
                            await bot.send_group_msg(group_id=gid, message='\n======\n'.join(msg2))
                            await asyncio.sleep(5)
                        except:
                            continue
            await mai.get_music_alias()
    except ServerError as e:
        log.error(str(e))
    except ValueError as e:
        log.error(str(e))
import asyncio
import re
import traceback
from textwrap import dedent

from nonebot import get_bot, on_command, on_regex
from nonebot.adapters.onebot.v11 import (
    GROUP_ADMIN,
    GROUP_OWNER,
    Bot,
    GroupMessageEvent,
    Message,
    MessageEvent,
    MessageSegment,
    PrivateMessageEvent,
)
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER

from ..config import *
from ..libraries.image import text_to_bytes_io
from ..libraries.maimaidx_api_data import maiApi
from ..libraries.maimaidx_error import AliasesNotFoundError, ServerError
from ..libraries.maimaidx_music import alias, mai, update_local_alias
from ..libraries.maimaidx_music_info import draw_music_info

update_alias        = on_command('更新别名库', permission=SUPERUSER)
alias_local_apply   = on_command('添加本地别名', aliases={'添加本地别称'})
alias_apply         = on_command('添加别名', aliases={'增加别名', '增添别名', '添加别称'})
alias_agree         = on_command('同意别名', aliases={'同意别称'})
alias_status        = on_command('当前投票', aliases={'当前别名投票', '当前别称投票'})
alias_switch        = on_regex(
    r'^([开启关闭]+)别名推送$',
    permission=SUPERUSER | GROUP_OWNER | GROUP_ADMIN
)
alias_global_switch = on_regex(r'^全局([开启关闭]+)别名推送$', permission=SUPERUSER)
alias_song          = on_regex(r'^(id)?\s?(.+)\s?有什么别[名称]$', re.IGNORECASE)


@update_alias.handle()
async def _(event: PrivateMessageEvent):
    try:
        await mai.get_music_alias()
        log.info('手动更新别名库成功')
        await update_alias.finish('手动更新别名库成功')
    except:
        log.error('手动更新别名库失败')
        await update_alias.finish('手动更新别名库失败')


@alias_local_apply.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    args = message.extract_plain_text().strip().split()
    if len(args) != 2:
        await alias_local_apply.finish('参数错误', reply_message=True)
    song_id, alias_name = args
    if not mai.total_list.by_id(song_id):
        await alias_local_apply.finish(f'未找到ID「{song_id}」的曲目', reply_message=True)
    try:
        server_exist = await maiApi.get_songs_alias(song_id)
        if alias_name.lower() in server_exist.Alias:
            await alias_apply.send(
                f'该曲目的别名「{alias_name}」已存在别名服务器，不能重复添加别名，正在进行更新别名库', 
                reply_message=True
            )
            await mai.get_music_alias()
            await alias_apply.finish('别名库更新完成', reply_message=True)
    except AliasesNotFoundError:
        pass

    local_exist = mai.total_alias_list.by_id(song_id)
    if local_exist and alias_name.lower() in local_exist[0].Alias:
        await alias_local_apply.finish(f'本地别名库已存在该别名', reply_message=True)
    
    issave = await update_local_alias(song_id, alias_name)
    if not issave:
        msg = '添加本地别名失败'
    else:
        msg = f'已成功为ID「{song_id}」添加别名「{alias_name}」到本地别名库'
    await alias_local_apply.send(msg, reply_message=True)
    
    
@alias_apply.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    try:
        args = message.extract_plain_text().strip().split()
        if len(args) != 2:
            await alias_apply.finish('参数错误', reply_message=True)
        song_id, alias_name = args
        if not (music := mai.total_list.by_id(song_id)):
            await alias_apply.finish(f'未找到ID「{song_id}」的曲目', reply_message=True)
        try:
            isexist = await maiApi.get_songs_alias(song_id)
            if alias_name.lower() in isexist.Alias:
                await alias_apply.send(
                    f'该曲目的别名「{alias_name}」已存在别名服务器，不能重复添加别名，正在进行更新别名库', 
                    reply_message=True
                )
                await mai.get_music_alias()
                await alias_apply.finish('别名库更新完成', reply_message=True)
        except AliasesNotFoundError:
            pass

        status = await maiApi.post_alias(song_id, alias_name, event.user_id)
        msg = MessageSegment.text(dedent(f'''\
            您已提交以下别名申请
            ID：{song_id}
            别名：{alias_name}
            现在可用使用唯一标签「{status.Tag}」来进行投票，例如：同意别名 {status.Tag}
            浏览{vote_url}查看详情
        ''')) + await draw_music_info(music)
    except (ServerError, ValueError) as e:
        log.error(traceback.format_exc())
        msg = str(e)
    await alias_apply.finish(msg, reply_message=True)


@alias_agree.handle()
async def _(event: MessageEvent, message: Message = CommandArg()):
    try:
        tag = message.extract_plain_text().strip().upper()
        status = await maiApi.post_agree_user(tag, event.user_id)
        await alias_agree.finish(status, reply_message=True)
    except ValueError as e:
        await alias_agree.finish(str(e), reply_message=True)


@alias_status.handle()
async def _(message: Message = CommandArg()):
    try:
        args = message.extract_plain_text().strip()
        status = await maiApi.get_alias_status()
        if not status:
            await alias_status.finish('未查询到正在进行的别名投票', reply_message=True)
        
        page = max(min(int(args), len(status) // SONGS_PER_PAGE + 1), 1) if args else 1
        result = []
        for num, _s in enumerate(status):
            if (page - 1) * SONGS_PER_PAGE <= num < page * SONGS_PER_PAGE:
                apply_alias = _s.ApplyAlias
                if len(_s.ApplyAlias) > 15:
                    apply_alias = _s.ApplyAlias[:15] + '...'
                r = f'{_s.Tag}：\n- ID：{_s.SongID}\n- 别名：{apply_alias}\n- 票数：{_s.AgreeVotes}/{_s.Votes}'
                result.append(r)
        result.append(f'第「{page}」页，共「{len(status) // SONGS_PER_PAGE + 1}」页')
        msg = MessageSegment.image(text_to_bytes_io('\n'.join(result)))
    except (ServerError, ValueError) as e:
        log.error(traceback.format_exc())
        msg = str(e)
    await alias_status.finish(msg, reply_message=True)


@alias_song.handle()
async def _(match = RegexMatched()):
    findid = bool(match.group(1))
    name = match.group(2)
    aliases = None
    if findid and name.isdigit():
        alias_id = mai.total_alias_list.by_id(name)
        if not alias_id:
            await alias_song.finish(
                '未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', 
                reply_message=True
            )
        else:
            aliases = alias_id
    else:            
        aliases = mai.total_alias_list.by_alias(name)
        if not aliases:
            if name.isdigit():
                alias_id = mai.total_alias_list.by_id(name)
                if not alias_id:
                    await alias_song.finish(
                        '未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', 
                        reply_message=True
                    )
                else:
                    aliases = alias_id
            else:
                await alias_song.finish(
                    '未找到此歌曲\n可以使用「添加别名」指令给该乐曲添加别名', 
                    reply_message=True
                )
    if len(aliases) != 1:
        msg = []
        for songs in aliases:
            alias_list = '\n'.join(songs.Alias)
            msg.append(f'ID：{songs.SongID}\n{alias_list}')
        await alias_song.finish(
            f'找到{len(aliases)}个相同别名的曲目：\n' + '\n======\n'.join(msg), 
            reply_message=True
        )

    if len(aliases[0].Alias) == 1:
        await alias_song.finish('该曲目没有别名', reply_message=True)

    msg = f'该曲目有以下别名：\nID：{aliases[0].SongID}\n'
    msg += '\n'.join(aliases[0].Alias)
    await alias_song.finish(msg, reply_message=True)


@alias_switch.handle()
async def _(event: GroupMessageEvent, match = RegexMatched()):
    if match.group(1) == '开启':
        msg = await alias.on(event.group_id)
    elif match.group(1) == '关闭':
        msg = await alias.off(event.group_id)
    else:
        raise ValueError('matcher type error')

    await alias_switch.finish(msg, reply_message=True)


@alias_global_switch.handle()
async def _(match = RegexMatched()):
    if match.group(1) == '开启':
        await alias.alias_global_change(True)
        await alias_global_switch.finish('已全局开启maimai别名推送')
    elif match.group(1) == '关闭':
        await alias.alias_global_change(False)
        await alias_global_switch.finish('已全局关闭maimai别名推送')
    else:
        await alias_global_switch.finish()


async def alias_apply_status():
    bot: Bot = get_bot()
    try:
        group_list = await bot.get_group_list()
        status = await maiApi.get_alias_status()
        if not alias.push.global_switch:
            await mai.get_music_alias()
            return
        if status:
            msg = ['检测到新的别名申请']
            msg2 = ['以下是已成功添加别名的曲目']
            for _s in status:
                if _s.IsNew and (usernum := _s.AgreeVotes) < (votes := _s.Votes):
                    song_id = str(_s.SongID)
                    alias_name = _s.ApplyAlias
                    music = mai.total_list.by_id(song_id)
                    msg.append(f'{_s.Tag}：\nID：{song_id}\n标题：{music.title}\n别名：{alias_name}\n票数：{usernum}/{votes}')
                elif _s.IsEnd:
                    song_id = str(_s.SongID)
                    alias_name = _s.ApplyAlias
                    music = mai.total_list.by_id(song_id)
                    msg2.append(f'ID：{song_id}\n标题：{music.title}\n别名：{alias_name}')

            if len(msg) != 1 and len(msg2) != 1:
                for group in group_list:
                    gid: int = group['group_id']
                    if gid in alias.push.disable:
                        continue
                    try:
                        if len(msg) != 1: 
                            await bot.send_group_msg(
                                group_id=gid, 
                                message='\n======\n'.join(msg) + f'\n浏览{vote_url}查看详情'
                            )
                            await asyncio.sleep(5)
                        if len(msg2) != 1:
                            await bot.send_group_msg(
                                group_id=gid, 
                                message='\n======\n'.join(msg2)
                            )
                            await asyncio.sleep(5)
                    except: 
                        continue
        await mai.get_music_alias()
    except (ServerError, ValueError) as e:
        log.error(str(e))
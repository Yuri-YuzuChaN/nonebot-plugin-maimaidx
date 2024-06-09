import random

from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Message, MessageEvent, PrivateMessageEvent
from nonebot.params import CommandArg, RegexMatched
from nonebot.permission import SUPERUSER

from ..libraries.maimaidx_music_info import *
from ..libraries.maimaidx_player_score import *
from ..libraries.maimaidx_update_plate import *
from ..libraries.tool import hash

maimaidxhelp    = on_command('帮助maimaiDX', aliases={'帮助maimaidx'}, priority=5)
maimaidxrepo    = on_command('项目地址maimaiDX', aliases={'项目地址maimaidx'}, priority=5)
update_data     = on_command('更新maimai数据', permission=SUPERUSER, priority=5)
mai_today       = on_command('今日mai', aliases={'今日舞萌', '今日运势'}, priority=5)
mai_what        = on_regex(r'.*mai.*什么(.+)?', priority=5)
random_song     = on_regex(r'^[随来给]个((?:dx|sd|标准))?([绿黄红紫白]?)([0-9]+\+?)$', priority=5)
rating_ranking  = on_command('查看排名', aliases={'查看排行'}, priority=5)


@maimaidxhelp.handle()
async def _():
    await maimaidxhelp.finish(MessageSegment.image(image_to_base64(Image.open(Root / 'maimaidxhelp.png'))), reply_message=True)


@maimaidxrepo.handle()
async def _():
    await maimaidxrepo.finish('项目地址：https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx\n求star，求宣传~', reply_message=True)


@update_data.handle()
async def _(event: PrivateMessageEvent):
    await mai.get_music()
    await mai.get_music_alias()
    await update_data.send('maimai数据更新完成')


@mai_today.handle()
async def _(event: MessageEvent):
    wm_list = ['拼机', '推分', '越级', '下埋', '夜勤', '练底力', '练手法', '打旧框', '干饭', '抓绝赞', '收歌']
    uid = event.user_id
    h = hash(uid)
    rp = h % 100
    wm_value = []
    for i in range(11):
        wm_value.append(h & 3)
        h >>= 2
    msg = f'\n今日人品值：{rp}\n'
    for i in range(11):
        if wm_value[i] == 3:
            msg += f'宜 {wm_list[i]}\n'
        elif wm_value[i] == 0:
            msg += f'忌 {wm_list[i]}\n'
    music = mai.total_list[h % len(mai.total_list)]
    ds = '/'.join([str(_) for _ in music.ds])
    msg += f'{maiconfig.botName} Bot提醒您：打机时不要大力拍打或滑动哦\n今日推荐歌曲：\n'
    msg += f'ID.{music.id} - {music.title}'
    msg += MessageSegment.image(image_to_base64(Image.open(await maiApi.download_music_pictrue(music.id))))
    msg += ds
    await mai_today.finish(msg, reply_message=True)


@mai_what.handle()
async def _(event: MessageEvent, match = RegexMatched()):
    music = mai.total_list.random()
    user = None
    if (point := match.group(1)) and ('推分' in point or '上分' in point or '加分' in point):
        try:
            obj = await maiApi.query_user('player', qqid=event.user_id)
            user = UserInfo(**obj)
            r = random.randint(0, 1)
            _ra = 0
            ignore = []
            if r == 0:
                if sd := user.charts.sd:
                    ignore = [m.song_id for m in sd if m.achievements < 100.5]
                    _ra = sd[-1].ra
            else:
                if dx := user.charts.dx:
                    ignore = [m.song_id for m in dx if m.achievements < 100.5]
                    _ra = dx[-1].ra
            if _ra != 0:
                ds = round(_ra / 22.4, 1)
                musiclist = mai.total_list.filter(ds=(ds, ds + 1))
                for _m in musiclist:
                    if int(_m.id) in ignore:
                        musiclist.remove(_m)
                music = musiclist.random()
        except UserNotFoundError:
            pass
        except UserDisabledQueryError:
            pass
    await mai_what.finish(await draw_music_info(music, event.user_id, user))


@random_song.handle()
async def _(match = RegexMatched()):
    try:
        diff = match.group(1)
        if diff == 'dx':
            tp = ['DX']
        elif diff == 'sd' or diff == '标准':
            tp = ['SD']
        else:
            tp = ['SD', 'DX']
        level = match.group(3)
        if match.group(2) == '':
            music_data = mai.total_list.filter(level=level, type=tp)
        else:
            music_data = mai.total_list.filter(level=level, diff=['绿黄红紫白'.index(match[1])], type=tp)
        if len(music_data) == 0:
            msg = '没有这样的乐曲哦。'
        else:
            msg = await draw_music_info(music_data.random())
    except:
        msg = '随机命令错误，请检查语法'
    await random_song.finish(msg, reply_message=True)


@rating_ranking.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    page = 1
    name = ''
    if args.isdigit():
        page = int(args)
    else:
        name = args.lower()

    data = await rating_ranking_data(name, page)
    await rating_ranking.finish(data, reply_message=True)


async def data_update_daily():
    await mai.get_music()
    mai.guess()
    log.info('maimaiDX数据更新完毕')

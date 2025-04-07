import copy

from .image import rounded_corners
from .maimaidx_best_50 import *
from .maimaidx_music import Music, mai


def newbestscore(song_id: str, lv: int, value: int, bestlist: List[ChartInfo]) -> int:
    for v in bestlist:
        if song_id == str(v.song_id) and lv == v.level_index:
            if value >= v.ra:
                return value - v.ra
            else:
                return 0
    return value - bestlist[-1].ra


async def draw_music_info(music: Music, qqid: Optional[int] = None, user: Optional[UserInfo] = None) -> MessageSegment:
    """
    查看谱面
    
    Params:
        `music`: 曲目模型
        `qqid`: QQID
        `user`: 用户模型
    Returns:
        `MessageSegment`
    """
    calc = True
    isfull = True
    bestlist: List[ChartInfo] = []
    try:
        if qqid:
            if user is None:
                player = await maiApi.query_user_b50(qqid=qqid)
            else:
                player = user
            if music.basic_info.version in list(plate_to_version.values())[-2]:
                bestlist = player.charts.dx
                isfull = bool(len(bestlist) == 15)
            else:
                bestlist = player.charts.sd
                isfull = bool(len(bestlist) == 35)
        else:
            calc = False
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError):
        calc = False
    except Exception:
        calc = False

    im = Image.open(maimaidir / 'song_bg.png').convert('RGBA')
    dr = ImageDraw.Draw(im)
    mr = DrawText(dr, SIYUAN)
    tb = DrawText(dr, TBFONT)

    default_color = (124, 130, 255, 255)

    im.alpha_composite(Image.open(maimaidir / 'logo.png').resize((249, 120)), (65, 25))
    if music.basic_info.is_new:
        im.alpha_composite(Image.open(maimaidir / 'UI_CMN_TabTitle_NewSong.png').resize((249, 120)), (940, 100))
    songbg = Image.open(music_picture(music.id)).resize((280, 280))
    im.alpha_composite(rounded_corners(songbg, 17, (True, False, False, True)), (110, 180))
    im.alpha_composite(Image.open(maimaidir / f'{music.basic_info.version}.png').resize((182, 90)), (800, 370))
    im.alpha_composite(Image.open(maimaidir / f'{music.type}.png').resize((80, 30)), (410, 375))

    title = music.title
    if coloumWidth(title) > 40:
        title = changeColumnWidth(title, 39) + '...'
    mr.draw(405, 220, 28, title, default_color, 'lm')
    artist = music.basic_info.artist
    if coloumWidth(artist) > 50:
        artist = changeColumnWidth(artist, 49) + '...'
    mr.draw(407, 265, 20, artist, default_color, 'lm')
    tb.draw(460, 330, 30, music.basic_info.bpm, default_color, 'lm')
    tb.draw(405, 435, 28, f'ID {music.id}', default_color, 'lm')
    mr.draw(665, 435, 24, music.basic_info.genre, default_color, 'mm')

    for num, _ in enumerate(music.level):
        if num == 4:
            color = (255, 255, 255, 255)
        else:
            color = (255, 255, 255, 255)
        tb.draw(181, 610 + 73 * num, 30, f'{music.level[num]}({music.ds[num]})', color, 'mm')
        tb.draw(
            315, 600 + 73 * num, 30, 
            f'{round(music.stats[num].fit_diff, 2):.2f}' if music.stats and music.stats[num] else '-', 
            default_color, 'mm'
        )
        notes = list(music.charts[num].notes)
        tb.draw(437, 600 + 73 * num, 30, sum(notes), default_color, 'mm')
        if len(notes) == 4:
            notes.insert(3, '-')
        for n, c in enumerate(notes):
            tb.draw(556 + 119 * n, 600 + 73 * num, 30, c, default_color, 'mm')
        if num > 1:
            charter = music.charts[num].charter
            if coloumWidth(charter) > 19:
                charter = changeColumnWidth(charter, 18) + '...'
            mr.draw(372, 1030 + 47 * (num - 2), 18, charter, default_color, 'mm')
            ra = sorted([computeRa(music.ds[num], r) for r in achievementList[-6:]], reverse=True)
            for _n, value in enumerate(ra):
                size = 25
                if not calc:
                    rating = value
                elif not isfull:
                    size = 20
                    rating = f'{value}(+{value})'
                elif value > bestlist[-1].ra:
                    new = newbestscore(music.id, num, value, bestlist)
                    if new == 0:
                        rating = value
                    else:
                        size = 20
                        rating = f'{value}(+{new})'
                else:
                    rating = value
                tb.draw(536 + 101 * _n, 1030 + 47 * (num - 2), size, rating, default_color, 'mm')
    mr.draw(600, 1212, 22, f'Designed by Yuri-YuzuChaN & BlueDeer233. Generated by {maiconfig.botName} BOT', default_color, 'mm')
    return MessageSegment.image(image_to_base64(im))


async def draw_music_play_data(qqid: int, music_id: str) -> Union[str, MessageSegment]:
    """
    谱面游玩
    
    Params:
        `qqid`: QQID
        `music_id`: 曲目ID
    Returns:
        `Union[str, MessageSegment]`
    """
    try:
        diff: List[Union[None, PlayInfoDev, PlayInfoDefault]]
        if maiconfig.maimaidxtoken:
            data = await maiApi.query_user_post_dev(qqid=qqid, music_id=music_id)
            if not data:
                raise MusicNotPlayError

            music = mai.total_list.by_id(music_id)
            diff = [None for _ in music.ds]
            for _d in data:
                diff[_d.level_index] = _d
            dev = True
        else:
            version = list(set(_v for _v in plate_to_version.values()))
            data = await maiApi.query_user_plate(qqid=qqid, version=version)

            music = mai.total_list.by_id(music_id)
            _temp = [None for _ in music.ds]
            diff = copy.deepcopy(_temp)

            for _d in data:
                if _d.song_id == int(music_id):
                    diff[_d.level_index] = _d
            if diff == _temp:
                raise MusicNotPlayError
            dev = False

        im = Image.open(maimaidir / 'info_bg.png').convert('RGBA')
    
        dr = ImageDraw.Draw(im)
        tb = DrawText(dr, TBFONT)
        mr = DrawText(dr, SIYUAN)

        im.alpha_composite(Image.open(maimaidir / 'logo.png').resize((249, 120)), (0, 34))
        cover = Image.open(music_picture(music_id))
        im.alpha_composite(cover.resize((300, 300)), (100, 260))
        im.alpha_composite(Image.open(maimaidir / f'info-{category[music.basic_info.genre]}.png'), (100, 260))
        im.alpha_composite(Image.open(maimaidir / f'{music.basic_info.version}.png').resize((183, 90)), (295, 205))
        im.alpha_composite(Image.open(maimaidir / f'{music.type}.png').resize((55, 20)), (350, 560))
        
        color = (124, 129, 255, 255)
        artist = music.basic_info.artist
        if coloumWidth(artist) > 58:
            artist = changeColumnWidth(artist, 57) + '...'
        mr.draw(255, 595, 12, artist, color, 'mm')
        title = music.title
        if coloumWidth(title) > 38:
            title = changeColumnWidth(title, 37) + '...'
        mr.draw(255, 622, 18, title, color, 'mm')
        tb.draw(160, 720, 22, music.id, color, 'mm')
        tb.draw(380, 720, 22, music.basic_info.bpm, color, 'mm')

        y = 100
        for num, info in enumerate(diff):
            im.alpha_composite(Image.open(maimaidir / f'd-{num}.png'), (650, 235 + y * num))
            if info:
                im.alpha_composite(Image.open(maimaidir / 'ra-dx.png'), (850, 272 + y * num))
                if dev:
                    dxscore = info.dxScore
                    _dxscore = sum(music.charts[num].notes) * 3
                    dxnum = dxScore(dxscore / _dxscore * 100)
                    rating, rate = info.ra, score_Rank_l[info.rate]
                    if dxnum != 0:
                        im.alpha_composite(
                            Image.open(maimaidir / f'UI_GAM_Gauge_DXScoreIcon_0{dxnum}.png').resize((32, 19)), 
                            (851, 296 + y * num)
                        )
                    tb.draw(916, 304 + y * num, 13, f'{dxscore}/{_dxscore}', color, 'mm')
                else:
                    rating, rate = computeRa(music.ds[num], info.achievements, israte=True)
                
                im.alpha_composite(Image.open(maimaidir / 'fcfs.png'), (965, 265 + y * num))
                if info.fc:
                    im.alpha_composite(
                        Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[info.fc]}.png').resize((65, 65)), 
                        (960, 261 + y * num)
                    )
                if info.fs:
                    im.alpha_composite(
                        Image.open(maimaidir / f'UI_CHR_PlayBonus_{fsl[info.fs]}.png').resize((65, 65)), 
                        (1025, 261 + y * num)
                    )
                im.alpha_composite(Image.open(maimaidir / 'ra.png'), (1350, 405 + y * num))
                im.alpha_composite(
                    Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((100, 45)), 
                    (737, 272 + y * num)
                )

                tb.draw(510, 292 + y * num, 42, f'{info.achievements:.4f}%', color, 'lm')
                tb.draw(685, 248 + y * num, 25, music.ds[num], anchor='mm')
                tb.draw(915, 283 + y * num, 18, rating, color, 'mm')
            else:
                tb.draw(685, 248 + y * num, 25, music.ds[num], anchor='mm')
                mr.draw(800, 302 + y * num, 30, '未游玩', color, 'mm')
        if len(diff) == 4:
            mr.draw(800, 302 + y * 4, 30, '没有该难度', color, 'mm')

        mr.draw(600, 827, 22, f'Designed by Yuri-YuzuChaN & BlueDeer233. Generated by {maiconfig.botName} Bot', color, 'mm')
        msg = MessageSegment.image(image_to_base64(im))
        
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError, MusicNotPlayError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


def calc_achievements_fc(scorelist: Union[List[float], List[str]], lvlist_num: int, isfc: bool = False) -> int:
    r = -1
    obj = range(4) if isfc else achievementList[-6:]
    for __f in obj:
        if len(list(filter(lambda x: x >= __f, scorelist))) == lvlist_num:
            r += 1
        else:
            break
    return r


def draw_rating(rating: str, path: Path) -> MessageSegment:
    """
    绘制指定定数表文字
    
    Params:
        `rating`: 定数
        `path`: 路径
    Returns:
        `MessageSegment`
    """
    im = Image.open(path)
    dr = ImageDraw.Draw(im)
    sy = DrawText(dr, SIYUAN)
    sy.draw(700, 100, 65, f'Level.{rating}   定数表', (124, 129, 255, 255), 'mm', 5, (255, 255, 255, 255))
    return MessageSegment.image(image_to_base64(im))


async def draw_rating_table(qqid: int, rating: str, isfc: bool = False) -> Union[MessageSegment, str]:
    """
    绘制定数表
    
    Params:
        `qqid`: QQID
        `rating`: 定数
        `isfc`: 是否查询fc成绩
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        version = list(set(_v for _v in plate_to_version.values()))
        obj = await maiApi.query_user_plate(qqid=qqid, version=version)
        
        statistics = {
            'clear': 0,
            'sync':  0,
            's':     0,
            'sp':    0,
            'ss':    0,
            'ssp':   0,
            'sss':   0,
            'sssp':  0,
            'fc':    0,
            'fcp':   0,
            'ap':    0,
            'app':   0,
            'fs':    0,
            'fsp':   0,
            'fsd':   0,
            'fsdp':  0,
        }
        fromid = {}
        
        sp = score_Rank[-6:]
        for _d in obj:
            if _d.level != rating:
                continue
            if (id := str(_d.song_id)) not in fromid:
                fromid[id] = {}
            fromid[id][str(_d.level_index)] = {
                'achievements': _d.achievements,
                'fc': _d.fc,
                'level': _d.level
            }
            rate = computeRa(_d.ds, _d.achievements, onlyrate=True).lower()
            if _d.achievements >= 80:
                statistics['clear'] += 1
            if rate in sp:
                r_index = sp.index(rate)
                for _r in range(r_index + 1):
                    statistics[sp[_r]] += 1
            if _d.fc:
                fc_index = combo_rank.index(_d.fc)
                for _f in range(fc_index + 1):
                    statistics[combo_rank[_f]] += 1
            if _d.fs:
                if _d.fs != 'sync':
                    fs_index = sync_rank.index(_d.fs)
                    for _s in range(fs_index + 1):
                        statistics[sync_rank[_s]] += 1
                else:
                    statistics[_d.fs] += 1

        achievements_fc_list: List[Union[float, List[float]]] = []
        lvlist = mai.total_level_data[rating]
        lvnum = sum([len(v) for v in lvlist.values()])
        
        rating_bg = Image.open(maimaidir / 'rating_bg.png')
        unfinished_bg = Image.open(maimaidir / 'unfinished_bg.png')
        complete_bg = Image.open(maimaidir / 'complete_bg.png')
        
        bg = ratingdir / f'{rating}.png'
        
        im = Image.open(bg).convert('RGBA')
        dr = ImageDraw.Draw(im)
        sy = DrawText(dr, SIYUAN)
        tb = DrawText(dr, TBFONT)
        
        im.alpha_composite(rating_bg, (600, 25))
        sy.draw(305, 60, 65, f'Level.{rating}', (124, 129, 255, 255), 'mm', 5, (255, 255, 255, 255))
        sy.draw(305, 130, 65, '定数表', (124, 129, 255, 255), 'mm', 5, (255, 255, 255, 255))
        tb.draw(700, 130, 45, lvnum, (124, 129, 255, 255), 'mm', 5, (255, 255, 255, 255))
        
        y = 22
        for n, v in enumerate(statistics):
            if n % 8 == 0:
                x = 824
                y += 56
            else:
                x += 64
            tb.draw(x, y, 20, statistics[v], (124, 129, 255, 255), 'mm', 2, (255, 255, 255, 255))
        
        y = 118
        for ra in lvlist:
            x = 158
            y += 20
            for num, music in enumerate(lvlist[ra]):
                if num % 14 == 0:
                    x = 158
                    y += 85
                else:
                    x += 85
                if music.id in fromid and music.lv in fromid[music.id]:
                    if not isfc:
                        score = fromid[music.id][music.lv]['achievements']
                        achievements_fc_list.append(score)
                        rate = computeRa(music.ds, score, onlyrate=True)
                        rank = Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((78, 35))
                        if score >= 100:
                            im.alpha_composite(complete_bg, (x + 2, y - 18))
                        else:
                            im.alpha_composite(unfinished_bg, (x + 2, y - 18))
                        im.alpha_composite(rank, (x, y - 5))
                        continue
                    if _fc := fromid[music.id][music.lv]['fc']:
                        achievements_fc_list.append(combo_rank.index(_fc))
                        fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[_fc]}.png').resize((50, 50))
                        im.alpha_composite(complete_bg, (x + 2, y - 18))
                        im.alpha_composite(fc, (x + 15, y - 12))

        if len(achievements_fc_list) == lvnum:
            r = calc_achievements_fc(achievements_fc_list, lvnum, isfc)
            if r != -1:
                pic = fcl[combo_rank[r]] if isfc else score_Rank_l[score_Rank[-6:][r]]
                im.alpha_composite(Image.open(maimaidir / f'UI_MSS_Allclear_Icon_{pic}.png'), (40, 40))
        
        msg = MessageSegment.image(image_to_base64(im))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg


async def draw_plate_table(qqid: int, version: str, plan: str) -> Union[MessageSegment, str]:
    """
    绘制完成表
    
    Params:
        `qqid`: QQID
        `version`: 版本
        `plan`: 计划
    Returns:
        `Union[MessageSegment, str]`
    """
    try:
        if version in platecn:
            version = platecn[version]
        if version == '真':
            ver = [plate_to_version['真']] + [plate_to_version['初']]
            _ver = version
        elif version in ['熊', '华', '華']:
            ver = [plate_to_version['熊']]
            _ver = '熊&华'
        elif version in ['爽', '煌']:
            ver = [plate_to_version['爽']]
            _ver = '爽&煌'
        elif version in ['宙', '星']:
            ver = [plate_to_version['宙']]
            _ver = '宙&星'
        elif version in ['祭', '祝']:
            ver = [plate_to_version['祭']]
            _ver = '祭&祝'
        elif version in ['双', '宴']:
            ver = [plate_to_version['双']]
            _ver = '双&宴'
        else:
            ver = [plate_to_version[version]]
            _ver = version
  
        music_id_list = mai.total_plate_id_list[_ver]
        music = mai.total_list.by_id_list(music_id_list)
        plate_total_num = len(music_id_list)
        playerdata: List[PlayInfoDefault] = []
        
        obj = await maiApi.query_user_plate(qqid=qqid, version=ver)
        for _d in obj:
            if _d.song_id not in music_id_list:
                continue
            _music = mai.total_list.by_id(_d.song_id)
            _d.table_level = _music.level
            _d.ds = _music.ds[_d.level_index]
            playerdata.append(_d)

        ra: Dict[str, Dict[str, List[Optional[PlayInfoDefault]]]] = {}
        """
        {
            "14+": {
                "365": [None, None, None, PlayInfoDefault, None],
                ...
            },
            "14": {
                ...
            }
        }
        """
        music.sort(key=lambda x: x.ds[3], reverse=True)
        number = 4 if version not in ['霸', '舞'] else 5
        for _m in music:
            if _m.level[3] not in ra:
                ra[_m.level[3]] = {}
            ra[_m.level[3]][_m.id] = [None for _ in range(number)]
        for _d in playerdata:
            if number == 4 and _d.level_index == 4:
                continue
            ra[_d.table_level[3]][str(_d.song_id)][_d.level_index] = _d
        
        finished_bg = [Image.open(maimaidir / f't-{_}.png') for _ in range(4)]
        unfinished_bg = Image.open(maimaidir / 'unfinished_bg_2.png')
        complete_bg = Image.open(maimaidir / 'complete_bg_2.png')

        im = Image.open(platedir / f'{version}.png')
        draw = ImageDraw.Draw(im)
        tr = DrawText(draw, TBFONT)
        mr = DrawText(draw, SIYUAN)
        
        im.alpha_composite(Image.open(maimaidir / 'plate_num.png'), (185, 20))
        im.alpha_composite(
            Image.open(platedir / f'{version}{"極" if plan == "极" else plan}.png').resize((1000, 161)), 
            (200, 35)
        )
        lv: List[set[int]] = [set() for _ in range(number)]
        y = 245
        # if plan == '者':
        #     for level in ra:
        #         x = 200
        #         y += 15
        #         for num, _id in enumerate(ra[level]):
        #             if num % 10 == 0:
        #                 x = 200
        #                 y += 115
        #             else:
        #                 x += 115
        #             f: List[int] = []
        #             for num, play in enumerate(ra[level][_id]):
        #                 if play.achievements or not play.achievements >= 80: continue
        #                 fc = Image.open(maimaidir / f'UI_MSS_MBase_Icon_{fcl[play.fc]}.png')
        #                 im.alpha_composite(fc, (x, y))
        #                 f.append(n)
        #             for n in f:
        #                 im.alpha_composite(finished_bg[n], (x + 5 + 25 * n, y + 67))
        if plan == '极' or plan == '極':
            for level in ra:
                x = 200
                y += 15
                for num, _id in enumerate(ra[level]):
                    if num % 10 == 0:
                        x = 200
                        y += 115
                    else:
                        x += 115
                    f: List[int] = []
                    for n, play in enumerate(ra[level][_id]):
                        if play is None or not play.fc: continue
                        if n == 3:
                            im.alpha_composite(complete_bg, (x, y))
                            fc = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[play.fc]}.png').resize((75, 75))
                            im.alpha_composite(fc, (x + 13, y + 3))
                        lv[n].add(play.song_id)
                        f.append(n)
                    for n in f:
                        im.alpha_composite(finished_bg[n], (x + 5 + 25 * n, y + 67))
        if plan == '将':
            for level in ra:
                x = 200
                y += 15
                for num, _id in enumerate(ra[level]):
                    if num % 10 == 0:
                        x = 200
                        y += 115
                    else:
                        x += 115
                    f: List[int] = []
                    for n, play in enumerate(ra[level][_id]):
                        if play is None or play.achievements < 100: continue
                        if n == 3:
                            im.alpha_composite(complete_bg if play.achievements >= 100 else unfinished_bg, (x, y))
                            rate = computeRa(play.ds, play.achievements, onlyrate=True)
                            rank = Image.open(maimaidir / f'UI_TTR_Rank_{rate}.png').resize((102, 46))
                            im.alpha_composite(rank, (x - 1, y + 15))
                        lv[n].add(play.song_id)
                        f.append(n)
                    for n in f:
                        im.alpha_composite(finished_bg[n], (x + 5 + 25 * n, y + 67))
        if plan == '神':
            _fc = ['ap', 'app']
            for level in ra:
                x = 200
                y += 15
                for num, _id in enumerate(ra[level]):
                    if num % 10 == 0:
                        x = 200
                        y += 115
                    else:
                        x += 115
                    f: List[int] = []
                    for n, play in enumerate(ra[level][_id]):
                        if play is None or play.fc not in _fc: continue
                        if n == 3:
                            im.alpha_composite(complete_bg, (x, y))
                            ap = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fcl[play.fc]}.png').resize((75, 75))
                            im.alpha_composite(ap, (x + 13, y + 3))
                        lv[n].add(play.song_id)
                        f.append(n)
                    for n in f:
                        im.alpha_composite(finished_bg[n], (x + 5 + 25 * n, y + 67))
        if plan == '舞舞':
            fs = ['fsd', 'fdx', 'fsdp', 'fdxp']
            for level in ra:
                x = 200
                y += 15
                for num, _id in enumerate(ra[level]):
                    if num % 10 == 0:
                        x = 200
                        y += 115
                    else:
                        x += 115
                    f: List[int] = []
                    for n, play in enumerate(ra[level][_id]):
                        if play is None or play.fs not in fs:
                            continue
                        if n == 3:
                            im.alpha_composite(complete_bg, (x, y))
                            fsd = Image.open(maimaidir / f'UI_CHR_PlayBonus_{fsl[play.fs]}.png').resize((75, 75))
                            im.alpha_composite(fsd, (x + 13, y + 3))
                        lv[n].add(play.song_id)
                        f.append(n)
                    for n in f:
                        im.alpha_composite(finished_bg[n], (x + 5 + 25 * n, y + 67))
        
        color = ScoreBaseImage.id_color.copy()
        color.insert(0, (124, 129, 255, 255))
        for num in range(len(lv) + 1):
            if num == 0:
                v = set.intersection(*lv)
                _v = f'{len(v)}/{plate_total_num}'
            else:
                _v = len(lv[num - 1])
            if _v == plate_total_num:
                mr.draw(390 + 200 * num, 270, 35, '完成', color[num], 'rm', 4, (255, 255, 255, 255))
            else:
                tr.draw(390 + 200 * num, 270, 40, _v, color[num], 'rm', 4, (255, 255, 255, 255))
        
        msg = MessageSegment.image(image_to_base64(im))
    except (UserNotFoundError, UserNotExistsError, UserDisabledQueryError) as e:
        msg = str(e)
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'未知错误：{type(e)}\n请联系Bot管理员'
    return msg
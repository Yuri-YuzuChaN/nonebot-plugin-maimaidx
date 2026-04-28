from PIL import Image, ImageDraw

from ...constants import COMBO_MAP, RANK_MAP, SYNC_MAP
from ...resources import FOTNEWRODIN, SIYUAN, TBFONT, pic_dir
from ..merge.models.score import PlayedResult
from ..merge.models.theme import Theme
from ..service import mai
from ..utils.calc import calc_ds, dx_score
from .tools import DrawText, song_chart


def get_char_width(o: int) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), 
        (1154, 1), (1161, 0), (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), 
        (8426, 0), (9000, 1), (9002, 2), (11021, 1), (12350, 2), (12351, 1), (12438, 2), 
        (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1), (64106, 2), (65039, 1), 
        (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2), (120831, 1), 
        (262141, 2), (1114109, 1)
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloum_width(s: str) -> int:
    res = 0
    for ch in s:
        res += get_char_width(ord(ch))
    return res


def change_column_width(s: str, len: int) -> str:
    res = 0
    slist = []
    for ch in s:
        res += get_char_width(ord(ch))
        if res <= len:
            slist.append(ch)
    return "".join(slist)


class ScoreBaseImage:
    
    theme = Theme.CIRCLE
    
    _default_text_color = (124, 129, 255, 255)
    _diff_text_color = [
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (255, 255, 255, 255), 
        (138, 0, 226, 255)
    ]
    _id_text_color = [
        (129, 217, 85, 255), 
        (245, 189, 21, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (138, 0, 226, 255)
    ]
    _bg_color = [
        (111, 212, 61, 255), 
        (248, 183, 9, 255), 
        (255, 129, 141, 255), 
        (159, 81, 220, 255), 
        (219, 170, 255, 255)
    ]
    
    # 预存图片
    _id_diff_im = [Image.new("RGBA", (55, 10), color) for color in _bg_color]
    _dx_star_bg = [
        Image.open(pic_dir / f"UI_GAM_Gauge_DXScoreIcon_0{num}.png") for num in range(1, 6)
    ]
    _diff_bg = [
        Image.open(pic_dir / "b50_score_basic.png"), 
        Image.open(pic_dir / "b50_score_advanced.png"), 
        Image.open(pic_dir / "b50_score_expert.png"), 
        Image.open(pic_dir / "b50_score_master.png"), 
        Image.open(pic_dir / "b50_score_remaster.png")
    ]
    _rise_bg = [
        Image.open(pic_dir / "rise_score_basic.png"),
        Image.open(pic_dir / "rise_score_advanced.png"),
        Image.open(pic_dir / "rise_score_expert.png"),
        Image.open(pic_dir / "rise_score_master.png"),
        Image.open(pic_dir / "rise_score_remaster.png")
    ]
    _separator_bg       = Image.open(pic_dir / "separator.png")
    _chart_white_bg     = Image.open(pic_dir / "chart_white_bg.png")
    _cloud_bg           = Image.open(pic_dir / "rainbow.png").convert("RGBA")
    _rainbow_bottom_bg  = Image.open(pic_dir / "rainbow_bottom.png").convert("RGBA")
    _aurora_bg          = Image.open(pic_dir / "aurora.png").convert("RGBA")
    _shines_bg          = Image.open(pic_dir / "bg_shines.png").convert("RGBA")
    _pattern_bg         = Image.open(pic_dir / "pattern.png").convert("RGBA")

    def __init__(self, image: Image.Image = None, theme: Theme = Theme.CIRCLE) -> None:
        self._im = image
        self.theme = theme
        dr = ImageDraw.Draw(self._im)
        self._sy = DrawText(dr, SIYUAN)
        self._tb = DrawText(dr, TBFONT)
        self._fot = DrawText(dr, FOTNEWRODIN)
        
        self._title_bg           = Image.open(pic_dir / theme.value / "title.png")
        self._title_lengthen_bg  = Image.open(pic_dir / theme.value / "title_lengthen.png")
    
    def whiledraw(
        self, 
        data: list[PlayedResult], 
        dx: bool = False, 
        list_y: int = 0
    ):
        gap = 114
        dx_step = 276
        start_x = 16
        
        if list_y == 0:
            initial_y = 1085 if dx else 235
        else:
            initial_y = list_y
        for num, info in enumerate(data):
            row, col = divmod(num, 5)
            x = start_x + col * dx_step
            y = initial_y + row * gap

            cover = Image.open(song_chart(info.song_id)).resize((75, 75))
            version = Image.open(pic_dir / f"{info.type.upper()}.png").resize((37, 14))
            if info.rate.islower():
                rate = Image.open(
                    pic_dir / self.theme.value / f"UI_TTR_Rank_{RANK_MAP[info.rate]}.png"
                ).resize((63, 28))
            else:
                rate = Image.open(
                    pic_dir / self.theme.value / f"UI_TTR_Rank_{info.rate}.png"
                ).resize((63, 28))

            self._im.alpha_composite(self._diff_bg[info.level_index], (x, y))
            self._im.alpha_composite(cover, (x + 12, y + 12))
            self._im.alpha_composite(version, (x + 51, y + 91))
            self._im.alpha_composite(rate, (x + 92, y + 78))
            if info.fc:
                fc = Image.open(
                    pic_dir / f"UI_MSS_MBase_Icon_{COMBO_MAP[info.fc]}.png"
                ).resize((34, 34))
                self._im.alpha_composite(fc, (x + 154, y + 77))
            if info.fs:
                fs = Image.open(
                    pic_dir / f"UI_MSS_MBase_Icon_{SYNC_MAP[info.fs]}.png"
                ).resize((34, 34))
                self._im.alpha_composite(fs, (x + 185, y + 77))
            
            song = mai.total_list.by_id(info.song_id)
            dxscore = song.difficulties[info.level_index].dx_score
            if (dx_star := dx_score(info.dx_score / dxscore * 100)) != 0:
                self._im.alpha_composite(
                    self._dx_star_bg[dx_star - 1].resize((47, 26)), 
                    (x + 217, y + 80)
                )

            self._tb.draw(
                x + 26, y + 98, 13, info.song_id, 
                self._id_text_color[info.level_index], anchor="mm"
            )
            
            title = info.song_name
            if coloum_width(title) > 18:
                title = change_column_width(title, 17) + "..."
            self._sy.draw(
                x + 93, y + 14, 14, title, 
                self._diff_text_color[info.level_index], anchor="lm"
            )
            self._tb.draw(
                x + 93, y + 38, 30, f"{info.achievements:.4f}%", 
                self._diff_text_color[info.level_index], anchor="lm"
            )
            self._tb.draw(
                x + 219, y + 65, 15, f"{info.dx_score}/{dxscore}", 
                self._diff_text_color[info.level_index], anchor="mm"
            )
            
            ds = calc_ds(info.rating, info.achievements)
            self._tb.draw(
                x + 93, y + 65, 15, f"{ds} -> {info.rating}", 
                self._diff_text_color[info.level_index], anchor="lm"
            )
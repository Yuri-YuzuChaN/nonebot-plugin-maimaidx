from collections import defaultdict

from PIL import Image, ImageDraw
from pydantic import BaseModel

from ...constants import (
    ACHIEVEMENT_LIST,
    COMBO_MAP,
    COMBO_SP,
    LEVEL_LIST,
    RANK_MAP,
    RANK_SP,
    STATISTICS_KEYS,
    SYNC_D_SP,
    SYNC_MAP,
)
from ...resources import (
    FOTNEWRODIN,
    TBFONT,
    pic_dir,
    plate_table_dir,
    plate_version_dir,
    rating_table_dir,
)
from ..merge.models import PlayedResult, RatingTableResult, ServiceName, Song, Theme
from ..service import mai
from ..utils.calc import compute_rating
from .assets import AssetsImage
from .tools import DrawText, image_to_base64, tricolor_gradient_prism_plus

PlayedResultMap = defaultdict[int, dict[int, RatingTableResult]]
PlateResultMap = dict[str, dict[int, list[PlayedResult | None]]]


class PlateSongProgress(BaseModel):
    song_id: int
    results: list[PlayedResult | None]
    qualified_slots: list[int]
    completed: bool


class PlateProgressData(BaseModel):
    total_count: int
    remaster_count: int
    levels: dict[str, list[PlateSongProgress]]
    display_levels: list[str]
    slot_counts: list[int]
    completed_count: int


class RatingGridConfig:
    start_x = 140
    """作图 `x` 轴起点"""
    start_y = 450
    """作图 `y` 轴起点"""
    gap = 85
    """间距"""
    row_count = 14
    """`x` 轴数量"""
    stats_first_line_x = 534
    """统计数据第一行 `x` 轴起点"""
    stats_first_line_y = 238
    """统计数据第一行 `y` 轴起点"""
    stats_second_line_x = 292
    """统计数据第二行 `x` 轴起点"""
    stats_second_line_y = 323
    """统计数据第二行 `y` 轴起点"""


class PlateGridConfig:
    start_x = 180
    """作图 `x` 轴起点"""
    start_y = 490
    """作图 `y` 轴起点"""
    gap = 96
    """`x` 和 `y` 轴间距"""
    row_count = 12
    """数量"""


class DrawRatingTable(AssetsImage):
    def __init__(
        self,
        rating: str,
        *,
        service: ServiceName | None = None,
        play_result: list[PlayedResult] | None = None,
        plan: bool = False,
        level_text: bool = False,
    ):
        """
        Params:
            `rating`: 定数
            `service`: 数据源
            `play_result`: 游玩数据列表
            `plan`: 可选，是否指定目标
            `level_text`: 可选，是否只画定数标题，例如：`Level.13+`
        """
        super().__init__()
        self.rating = rating
        self.service = service
        self.result = play_result
        self.plan = plan
        self.level_text = level_text

        self._rank_cache: dict[str, Image.Image] = {}
        self._fc_cache: dict[str, Image.Image] = {}

    def _get_rank_icon(self, rate: str) -> Image.Image:
        """按需加载并缓存图标"""
        if rate not in self._rank_cache:
            path = pic_dir / Theme.PRISM_PLUS.value / f"UI_TTR_Rank_{rate}.png"
            if path.exists():
                self._rank_cache[rate] = self._open_image(path)
        return self._rank_cache.get(rate)

    def _get_fc_icon(self, fc: str) -> Image.Image:
        if fc not in self._fc_cache:
            path = pic_dir / f"UI_MSS_MBase_Icon_{COMBO_MAP[fc]}.png"
            if path.exists():
                self._fc_cache[fc] = self._open_image(path).resize((50, 50))
        return self._fc_cache.get(fc)

    def _calc_achievements_fc(
        self, score_list: list[float] | list[str], lvlist_num: int
    ) -> int:
        r = -1
        thresholds = range(4) if self.plan else ACHIEVEMENT_LIST[-6:]
        for _t in thresholds:
            count = sum(1 for s in score_list if s >= _t)
            if count == lvlist_num:
                r += 1
            else:
                break
        return r

    def _process_rating_table_data(self) -> tuple[dict[str, int], PlayedResultMap]:
        """
        处理定数表数据
        """
        statistics = {k: 0 for k in STATISTICS_KEYS}
        played_map: PlayedResultMap = defaultdict(dict)
        rank_sp = RANK_SP[-6:]

        for _d in self.result:
            if _d.level != self.rating:
                continue
            played_map[_d.song_id][_d.level_index] = RatingTableResult(
                achievements=_d.achievements, level=_d.level, fc=_d.fc
            )
            rate = compute_rating(
                _d.level_value, _d.achievements, onlyrate=True
            ).lower()
            if _d.achievements >= 80:
                statistics["clear"] += 1

            if rate in rank_sp:
                for r in rank_sp[: rank_sp.index(rate) + 1]:
                    statistics[r] += 1

            if _d.fc and _d.fc.value in COMBO_SP:
                for f in COMBO_SP[: COMBO_SP.index(_d.fc.value) + 1]:
                    statistics[f] += 1

            if _d.fs:
                if _d.fs.value == "sync":
                    statistics["sync"] += 1
                elif _d.fs.value in SYNC_D_SP:
                    for s in SYNC_D_SP[: SYNC_D_SP.index(_d.fs.value) + 1]:
                        statistics[s] += 1

        return statistics, played_map

    def draw(self) -> str:
        """
        绘制定数表

        Returns:
            `base64 str`
        """
        im = Image.open(rating_table_dir / f"{self.rating}.png").convert("RGBA")
        dr = ImageDraw.Draw(im)
        tb = DrawText(dr, TBFONT)
        fot = DrawText(dr, FOTNEWRODIN)

        font_color = (114, 188, 254, 255)

        if self.level_text:
            fot.draw(495, 220, 70, "Level.", font_color, "ld", 8, (255, 255, 255, 255))
            fot.draw(
                750, 220, 100, self.rating, font_color, "ld", 8, (255, 255, 255, 255)
            )
            return image_to_base64(im)

        fot.draw(495, 160, 70, "Level.", font_color, "ld", 8, (255, 255, 255, 255))
        fot.draw(750, 160, 100, self.rating, font_color, "ld", 8, (255, 255, 255, 255))

        statistics, played_map = self._process_rating_table_data()

        lv_data = mai.total_level_data.get(self.rating)
        total_songs_count = sum(len(v) for v in lv_data.values())
        achievements_or_fc_list: list[float | int] = []

        im.alpha_composite(self._table_complete_bg, (251, 190))

        tb.draw(
            394,
            RatingGridConfig.stats_first_line_y,
            30,
            f"{statistics['clear']}/{total_songs_count}",
            self._default_text_color,
            "mm",
            5,
            (255, 255, 255, 255),
        )

        for n, key in enumerate(STATISTICS_KEYS[1:]):
            if n < 6:
                col = n % 6
                x = RatingGridConfig.stats_first_line_x + col * 102
                y = RatingGridConfig.stats_first_line_y
            else:
                col = (n - 6) % 9
                x = RatingGridConfig.stats_second_line_x + col * 102
                y = RatingGridConfig.stats_second_line_y
            tb.draw(
                x,
                y,
                30,
                statistics[key],
                self._default_text_color,
                "mm",
                2,
                (255, 255, 255, 255),
            )

        current_y = RatingGridConfig.start_y
        for ra, songs in lv_data.items():
            for num, song in enumerate(lv_data[ra]):
                row, col = divmod(num, RatingGridConfig.row_count)
                x = RatingGridConfig.start_x + col * RatingGridConfig.gap
                y = current_y + row * RatingGridConfig.gap

                _record = played_map.get(song.song_id)
                if _record is None:
                    continue

                record = _record.get(song.difficulties.level_index)
                if record is None:
                    continue

                if not self.plan:
                    achievements_or_fc_list.append(record.achievements)
                    bg = (
                        self._rating_complete_bg
                        if record.achievements >= 100
                        else self._rating_unfinished_bg
                    )
                    im.alpha_composite(bg, (x + 1, y + 1))

                    rate = compute_rating(
                        song.difficulties.level_value,
                        record.achievements,
                        onlyrate=True,
                    )
                    im.alpha_composite(
                        self._get_rank_icon(rate).resize((78, 35)), (x, y + 20)
                    )
                    continue

                if record.fc:
                    achievements_or_fc_list.append(COMBO_SP.index(record.fc))
                    im.alpha_composite(self._rating_complete_bg, (x + 1, y + 1))
                    im.alpha_composite(self._get_fc_icon(record.fc), (x + 15, y + 13))

            group_rows = (len(songs) - 1) // RatingGridConfig.row_count + 1
            current_y += group_rows * RatingGridConfig.gap + 30

        if len(achievements_or_fc_list) == total_songs_count:
            r = self._calc_achievements_fc(achievements_or_fc_list, total_songs_count)
            if r != -1:
                pic = COMBO_MAP[COMBO_SP[r]] if self.plan else RANK_MAP[RANK_SP[-6:][r]]
                im.alpha_composite(
                    Image.open(pic_dir / f"UI_MSS_Allclear_Icon_{pic}.png"), (40, 40)
                )

        final_im = im.resize(
            (int(im.size[0] * 0.8), int(im.size[1] * 0.8)), Image.Resampling.LANCZOS
        )
        return image_to_base64(final_im)


class PlateTable(AssetsImage):
    PLAN_CRITERIA: dict[str, dict[str, str | list[str] | int]] = {
        "者": {"attr": "achievements", "values": 80, "prefix": "RANK"},
        "极": {"attr": "fc", "values": COMBO_SP, "prefix": "UI_CHR_PlayBonus_"},
        "極": {"attr": "fc", "values": COMBO_SP, "prefix": "UI_CHR_PlayBonus_"},
        "将": {"attr": "achievements", "values": 100, "prefix": "RANK"},
        "神": {"attr": "fc", "values": ["ap", "app"], "prefix": "UI_CHR_PlayBonus_"},
        "舞舞": {
            "attr": "fs",
            "values": ["fsd", "fsdp", "fsdpx", "fsdp+"],
            "prefix": "UI_CHR_PlayBonus_",
        },
    }

    def __init__(
        self,
        service: ServiceName,
        play_result: list[PlayedResult],
        *,
        plan: str | None = None,
        version: str | None = None,
        version_name: str | None = None,
        page: int | None = None,
    ):
        """
        绘制完成表

        Params:
            `service`: 数据源
            `play_result`: 游玩数据列表
            `plan`: 计划
            `version`: 游戏版本
            `version_name`: 版本名称
            `page`: 页数
        """
        super().__init__()
        self.service = service
        self.result = play_result
        self.plan = plan
        self.version = version
        self.version_name = version_name
        self.page = page
        self.is_wu = version in ["舞", "霸"]

        if self.is_wu:
            self.plate_name = f"{version}-{page}"
            self.slot_num = 5
        else:
            self.plate_name = version
            self.slot_num = 4

    def _get_level_dict(self) -> dict[str, list[Song]]:
        return {lv: [] for lv in reversed(LEVEL_LIST)}

    def _is_qualified(self, play: PlayedResult | None, plan: str) -> bool:
        """判定单个谱面是否符合牌子要求"""
        if not play:
            return False
        cfg = self.PLAN_CRITERIA.get(plan)
        if not cfg:
            return False

        val = getattr(play, cfg["attr"])
        if plan == "将":
            return val >= 100
        if plan == "者":
            return val >= 80
        return val in cfg["values"]

    def _process_plate_table_data(self) -> tuple[int, PlateResultMap]:
        """
        处理牌子表数据
        """
        plate_id_list = mai.total_plate_id_list[self.version_name]
        song_list = mai.total_list.by_id_list(plate_id_list)

        song_id_to_level = {
            song.song_id: song.difficulties[3].level for song in song_list
        }

        played_map: PlateResultMap = defaultdict(
            lambda: defaultdict(lambda: [None] * 4)
        )

        song_list.sort(key=lambda x: x.difficulties[3].level_value, reverse=True)
        for song in song_list:
            played_map[song.difficulties[3].level][song.song_id]

        for _d in self.result:
            if _d.song_id not in song_id_to_level:
                continue
            if self.slot_num == 4 and _d.level_index == 4:
                continue
            target_level = song_id_to_level[_d.song_id]
            played_map[target_level][_d.song_id][_d.level_index] = _d

        return len(plate_id_list), played_map

    def _process_plate_table_wu_data(self) -> tuple[int, int, PlateResultMap]:
        """
        处理牌子 `舞` 和 `霸者` 的数据
        """
        wu_id_list = mai.total_plate_id_list["舞"]
        wu_re_id_set = set(mai.total_plate_id_list["舞ReMASTER"])
        wu_song_list = mai.total_list.by_id_list(wu_id_list)

        all_level_dict = self._get_level_dict()

        def get_display_level_value(song: Song) -> str:
            if song.song_id in wu_re_id_set and len(song.difficulties) > 4:
                return song.difficulties[4].level_value
            return song.difficulties[3].level_value

        wu_song_list.sort(key=get_display_level_value, reverse=True)

        def get_display_level(song: Song) -> str:
            if song.song_id in wu_re_id_set and len(song.difficulties) > 4:
                return song.difficulties[4].level
            return song.difficulties[3].level

        song_id_to_level = {
            song.song_id: get_display_level(song) for song in wu_song_list
        }

        for song in wu_song_list:
            lv = get_display_level(song)
            if lv in all_level_dict:
                all_level_dict[lv].append(song)

        played_map: PlateResultMap = defaultdict(lambda: defaultdict(list))
        for lv in all_level_dict.keys():
            songs_in_lv = all_level_dict[lv]
            if not songs_in_lv:
                continue

            for song in songs_in_lv:
                sid = song.song_id
                slot_size = 5 if sid in wu_re_id_set else 4
                played_map[lv][sid] = [None] * slot_size

        for _d in self.result:
            if _d.song_id not in song_id_to_level:
                continue
            target_level = song_id_to_level[_d.song_id]

            if _d.song_id in played_map[target_level]:
                current_slots = played_map[target_level][_d.song_id]
                if _d.level_index < len(current_slots):
                    current_slots[_d.level_index] = _d

        return len(wu_id_list), len(wu_re_id_set), played_map

    def process(self) -> PlateProgressData:
        """
        处理所有牌子数据
        """
        plate_wu_total_count = 0
        if self.is_wu:
            plate_total_count, plate_wu_total_count, played_map = (
                self._process_plate_table_wu_data()
            )

            keys = list(played_map.keys())
            idx = keys.index("13") if "13" in keys else len(keys)
            if self.page == 1:
                display_levels = keys[:idx]
            else:
                display_levels = keys[idx:]
        else:
            plate_total_count, played_map = self._process_plate_table_data()
            display_levels = list(played_map.keys())

        slot_songs = [set() for _ in range(self.slot_num)]
        finished_songs: set[int] = set()
        levels: dict[str, list[PlateSongProgress]] = {}
        for level, songs_dict in played_map.items():
            level_progress: list[PlateSongProgress] = []
            for song_id, results in songs_dict.items():
                qualified_slots = [
                    idx
                    for idx, play in enumerate(results)
                    if self._is_qualified(play, self.plan)
                ]
                for slot in qualified_slots:
                    slot_songs[slot].add(song_id)

                has_any_play = any(play is not None for play in results)
                completed = has_any_play and all(
                    play is None or idx in qualified_slots
                    for idx, play in enumerate(results)
                )
                if completed:
                    finished_songs.add(song_id)

                level_progress.append(
                    PlateSongProgress(
                        song_id=song_id,
                        results=results,
                        qualified_slots=qualified_slots,
                        completed=completed,
                    )
                )
            levels[level] = level_progress

        return PlateProgressData(
            total_count=plate_total_count,
            remaster_count=plate_wu_total_count,
            levels=levels,
            display_levels=display_levels,
            slot_counts=[len(songs) for songs in slot_songs],
            completed_count=len(finished_songs),
        )

    def _plate_background(self) -> Image.Image:
        plan = "極" if self.plan == "极" else self.plan
        return Image.open(plate_version_dir / f"{self.version}{plan}.png").convert(
            "RGBA"
        )


class DrawPlateTable(PlateTable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_wu:
            self.progress_bg = self._plate_progress_wu_bg
            self.progress_small = self._plate_progress_small_wu
            self.progress_width = 176
            self.stats_start_x = 292
            self.stats_gap_x = 204
        else:
            self.progress_bg = self._plate_progress_bg
            self.progress_small = self._plate_progress_small
            self.progress_width = 230
            self.stats_start_x = 320
            self.stats_gap_x = 253

    def _get_plate_icon(self, play: PlayedResult, plan: str) -> Image.Image:
        """获取完成表中已达成谱面的图标。"""
        if plan == "将":
            rate = compute_rating(play.level_value, play.achievements, onlyrate=True)
            return self._open_image(
                pic_dir / Theme.PRISM_PLUS.value / f"UI_TTR_Rank_{rate}.png"
            ).resize((80, 36))

        cfg = self.PLAN_CRITERIA.get(plan)
        val = getattr(play, cfg["attr"])

        icon_name = COMBO_MAP.get(val) or SYNC_MAP.get(val) or val
        path = pic_dir / f"{cfg['prefix']}{icon_name}.png"
        return self._open_image(path).resize((60, 60))

    def draw(self) -> str:
        """绘制逐曲完成表。"""
        data = self.process()
        im = Image.open(plate_table_dir / f"{self.plate_name}.png")
        draw = ImageDraw.Draw(im)
        fot = DrawText(draw, FOTNEWRODIN)

        im.alpha_composite(self.progress_bg, (175, 20))
        im.alpha_composite(self._plate_background().resize((1000, 161)), (200, 45))

        current_y = PlateGridConfig.start_y
        for level, songs in data.levels.items():
            is_current_page = level in data.display_levels
            rows = (len(songs) - 1) // PlateGridConfig.row_count + 1
            for idx, song in enumerate(songs):
                row, col = divmod(idx, PlateGridConfig.row_count)
                x = PlateGridConfig.start_x + col * PlateGridConfig.gap
                y = current_y + row * PlateGridConfig.gap

                if not is_current_page:
                    continue

                index = len(song.results) - 1
                if index in song.qualified_slots:
                    play = song.results[index]
                    im.alpha_composite(self._plate_complete_bg, (x + 1, y + 1))
                    icon = self._get_plate_icon(play, self.plan)
                    dest = (x, y + 22) if self.plan == "将" else (x + 10, y + 12)
                    im.alpha_composite(icon, dest)

                for s_idx in song.qualified_slots:
                    if self.is_wu and len(song.results) == 5:
                        im.alpha_composite(
                            self._plate_finished_bg[s_idx].resize((14, 14)),
                            (x + 1 + 16 * s_idx, y + 64),
                        )
                    else:
                        im.alpha_composite(
                            self._plate_finished_bg[s_idx], (x + 4 + 19 * s_idx, y + 63)
                        )

            if is_current_page:
                current_y += rows * PlateGridConfig.gap + 30

        complete_sum = data.completed_count
        if complete_sum == data.total_count:
            text = "COMPLETED!!!"
        else:
            text = f"{complete_sum}/{data.total_count}"

        progress = complete_sum / data.total_count
        if progress != 0:
            bar = self._plate_progress_big.crop((0, 0, int(993 * progress), 92))
            im.alpha_composite(bar, (204, 219))

        fot.draw(
            700,
            240,
            30,
            text,
            self._default_text_color,
            "mm",
            3,
            (255, 255, 255, 255),
        )
        fot.draw(
            1190,
            240,
            30,
            f"{round(progress * 100, 2)}%",
            self._default_text_color,
            "rm",
            3,
            (255, 255, 255, 255),
        )

        stats_start_y = 300

        for _l, complete_sum_group in enumerate(data.slot_counts):
            x = self.stats_start_x + _l * self.stats_gap_x

            if self.is_wu:
                _progress_text_x = 89
                _progress_x = 88
            else:
                _progress_text_x = 115
                _progress_x = 115

            plate_count = data.total_count if _l != 4 else data.remaster_count

            progress_group = complete_sum_group / plate_count
            if progress_group != 0:
                bar_group_rounded = self.progress_small.crop(
                    (0, 0, int(self.progress_width * progress_group), 46)
                )
                im.alpha_composite(bar_group_rounded, (x - _progress_x, 326))

            if complete_sum_group == plate_count:
                fot.draw(
                    x,
                    stats_start_y,
                    24,
                    "COMPLETED!!!",
                    self._id_text_color[_l],
                    "mm",
                    4,
                    (255, 255, 255, 255),
                )

            fot.draw(
                x,
                stats_start_y,
                40,
                complete_sum_group,
                self._id_text_color[_l],
                "mm",
                4,
                (255, 255, 255, 255),
            )
            fot.draw(
                x + _progress_text_x,
                stats_start_y + 20,
                14,
                f"/{plate_count}",
                self._id_text_color[_l],
                "rd",
                3,
                (255, 255, 255, 255),
            )
            fot.draw(
                x + _progress_text_x,
                343,
                20,
                f"{round(progress_group * 100, 2)}%",
                self._default_text_color,
                "rm",
                2,
                (255, 255, 255, 255),
            )

        return image_to_base64(im)


class DrawPlateProgress(PlateTable):
    """绘制按等级聚合的牌子进度图。"""

    def _draw_bar(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        fill: tuple[int, int, int, int],
    ) -> None:
        draw.rounded_rectangle(box, radius=15, fill=(255, 255, 255, 180))
        if progress:
            left, top, right, bottom = box
            width = max(30, int((right - left) * progress))
            draw.rounded_rectangle(
                (left, top, left + width, bottom), radius=15, fill=fill
            )

    def draw(self) -> str:
        data = self.process()
        height = max(650, 440 + len(data.levels) * 58)
        im = tricolor_gradient_prism_plus(1400, height)
        draw = ImageDraw.Draw(im)
        fot = DrawText(draw, FOTNEWRODIN)
        tb = DrawText(draw, TBFONT)

        im.alpha_composite(self._plate_background().resize((1000, 161)), (200, 35))

        total_progress = data.completed_count / data.total_count
        fot.draw(175, 222, 30, "TOTAL PROGRESS", self._default_text_color, "lm")
        fot.draw(
            1225,
            222,
            30,
            f"{data.completed_count}/{data.total_count}  {total_progress:.2%}",
            self._default_text_color,
            "rm",
        )
        self._draw_bar(
            draw, (175, 252, 1225, 286), total_progress, (100, 193, 255, 255)
        )

        slot_width = 232 if self.slot_num == 4 else 180
        slot_gap = 18
        start_x = (
            1400 - (slot_width * self.slot_num + slot_gap * (self.slot_num - 1))
        ) // 2
        for index, count in enumerate(data.slot_counts):
            total = data.remaster_count if index == 4 else data.total_count
            progress = count / total if total else 0
            x = start_x + index * (slot_width + slot_gap)
            tb.draw(
                x,
                315,
                22,
                f"{count}/{total}",
                self._id_text_color[index],
                "lt",
            )
            self._draw_bar(
                draw,
                (x, 349, x + slot_width, 373),
                progress,
                self._id_text_color[index],
            )

        start_y = 422
        for index, (level, songs) in enumerate(data.levels.items()):
            complete_count = sum(song.completed for song in songs)
            progress = complete_count / len(songs)
            y = start_y + index * 58
            tb.draw(175, y + 16, 26, level, self._default_text_color, "lm")
            self._draw_bar(draw, (275, y, 1050, y + 32), progress, (100, 193, 255, 255))
            tb.draw(
                1225,
                y + 16,
                22,
                f"{complete_count}/{len(songs)}  {progress:.2%}",
                self._default_text_color,
                "rm",
            )

        return image_to_base64(im)

from ..clients.divingfish.models.score import ChartInfo, UserInfo
from ..clients.lxns.models.player import Player
from ..clients.lxns.models.score import Best50 as b50
from ..clients.lxns.models.score import Score
from ..utils.calc import calc_ds
from .models.best50 import Best50
from .models.player import Player
from .models.score import PlayedResult


def lxns_play_list(score: list[Score]) -> list[PlayedResult]:
    return [
        PlayedResult(
            song_id=v.id if v.type == "SD" else v.id + 10000,
            song_name=v.song_name,
            level=v.level,
            level_index=v.level_index,
            type=v.type,
            rating=v.dx_rating,
            achievements=v.achievements,
            fc=v.fc,
            fs=v.fs,
            rate=v.rate,
            dx_score=v.dx_score,
            level_value=calc_ds(v.dx_rating, v.achievements)
        ) for v in score
    ]


def lxns_to_best50(best50: b50) -> Best50:
    sd_play_list = lxns_play_list(best50.standard)
    dx_play_list = lxns_play_list(best50.dx)
    return Best50(
        sd_total=best50.standard_total,
        dx_total=best50.dx_total,
        sd=sd_play_list,
        dx=dx_play_list
    )



def df_to_player(userinfo: UserInfo) -> Player:
    return Player(
        name=userinfo.nickname,
        rating=userinfo.rating,
        course_rank=userinfo.additional_rating,
        name_plate=userinfo.plate
    )


def df_total_play_list(chart: list[ChartInfo]) -> tuple[int, list[PlayedResult]]:
    total = 0
    play_list = []
    for v in chart:
        total += v.ra
        play_list.append(
            PlayedResult(
                song_id=v.song_id,
                song_name=v.title,
                level=v.level,
                level_value=v.ds,
                level_index=v.level_index,
                type=v.type,
                rating=v.ra,
                achievements=v.achievements,
                fc=v.fc,
                fs=v.fs,
                rate=v.rate,
                dx_score=v.dxScore,
                level_label=v.level_label
            )
        )
    
    return total, play_list


def df_to_best50(userinfo: UserInfo) -> Best50:
    sd_total, sd_play_list = df_total_play_list(userinfo.charts.sd)
    dx_total, dx_play_list = df_total_play_list(userinfo.charts.dx)
    return Best50(
        sd_total=sd_total,
        dx_total=dx_total,
        sd=sd_play_list,
        dx=dx_play_list
    )
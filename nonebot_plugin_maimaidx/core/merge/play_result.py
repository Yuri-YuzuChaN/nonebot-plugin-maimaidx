from typing import overload

from ..clients.divingfish.models.score import PlayInfoDefault, PlayInfoDev
from ..clients.lxns.models.enum import SongType
from ..clients.lxns.models.score import Score
from ..utils.calc import calc_ds
from .models.score import NotPlayedResult, PlayedResult
from .models.song import Song


def df_format_result(
    v: PlayInfoDefault | PlayInfoDev, 
    level_value: float = 0
) -> PlayedResult:
    return PlayedResult(
        song_id=v.song_id, 
        song_name=v.title, 
        level=v.level, 
        level_index=v.level_index, 
        level_value=level_value,
        type=v.type, 
        rating=v.ra, 
        achievements=v.achievements, 
        fc=v.fc, 
        fs=v.fs, 
        rate=v.rate, 
        dx_score=v.dxScore
    )


@overload
def df_to_playresult(data: list[Score]) -> list[PlayedResult]: ...
@overload
def df_to_playresult(
    data: list[Score], *, song: Song | None = None
) -> list[PlayedResult | NotPlayedResult]: ...
def df_to_playresult(
    data: list[PlayInfoDefault] | list[PlayInfoDev],
    *, 
    song: Song | None = None
) -> list[PlayedResult | NotPlayedResult]:
    if song:
        r = [
            NotPlayedResult(
                level_value=v.level_value,
                song_id=song.song_id,
                level_index=v.level_index
            ) for v in song.difficulties
        ]
    else:
        r = []
    
    for v in data:
        if song:
            r[v.level_index] = df_format_result(v, r[v.level_index].level_value)
        else:
            r.append(df_format_result(v))
            
    return r


def lxns_format_result(v: Score) -> PlayedResult:
    return PlayedResult(
        song_id=v.id if v.type == SongType.STANDARD else v.id + 10000,
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
    )


@overload
def lxns_to_playresult(data: list[Score]) -> list[PlayedResult]: ...
@overload
def lxns_to_playresult(
    data: list[Score], *, song: Song | None = None
) -> list[PlayedResult | NotPlayedResult]: ...
def lxns_to_playresult(
    data: list[Score], 
    *, 
    song: Song | None = None
) -> list[PlayedResult | NotPlayedResult]:
    if song:
        r = [
            NotPlayedResult(
                level_value=v.level_value,
                song_id=song.song_id,
                level_index=v.level_index
            )
            for v in song.difficulties
        ]
    else:
        r = []
    for v in data:
        result = lxns_format_result(v)
        if song:
            r[v.level_index] = result
        else:
            r.append(result)
    return r
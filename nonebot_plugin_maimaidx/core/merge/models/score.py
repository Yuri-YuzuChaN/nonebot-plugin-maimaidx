from pydantic import BaseModel, field_validator

from ...clients.lxns.models.enum import FCType, FSType, LevelIndex, RateType


class BaseResult(BaseModel):
    
    level_value: float
    """谱面定数"""


class NotPlayedResult(BaseResult):
    
    song_id: int
    level_index: LevelIndex

class Result(BaseResult):
    
    song_id: int
    song_name: str
    level_index: LevelIndex
    type: str
    
    rating: int
    achievements: float
    rate: RateType | None = None
    
    @field_validator("rate", mode="before")
    @classmethod
    def rate_to_none(cls, v: str):
        if v == "":
            return None
        return v


class PlayedResult(Result):
    
    level: str
    
    fc: FCType | None = None
    fs: FSType | None = None
    dx_score: int
    
    dx_star: int | None = None
    """dx星数"""
    upload_time: str | None = None
    """上传时间。仅 `lxns`"""
    level_label: str | None = None
    """难度。仅 `diving-fish`"""
    
    @field_validator("fc", "fs", mode="before")
    @classmethod
    def to_none(cls, v: str):
        if v == "":
            return None
        return v


class RiseResult(Result):
    
    old_rating: int = 0
    old_achievements: float = 0
    old_rate: str = "D"


class RatingTableResult(BaseModel):
    
    achievements: float
    level: str
    fc: FCType | None = None
    
    @field_validator("fc", mode="before")
    @classmethod
    def to_none(cls, v: str):
        if v == "":
            return None
        return v
from pydantic import BaseModel


class Alias(BaseModel):
    song_id: int
    alias: list[str]


class AliasesPush(BaseModel):
    enable: list[int] = []
    disable: list[int] = []

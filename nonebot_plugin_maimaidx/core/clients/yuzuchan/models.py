from pydantic import BaseModel


class APIResult(BaseModel):
    code: int = 0
    content: dict | list | str


class Alias(BaseModel):
    SongID: int
    Name: str
    Alias: list[str]


class StatusBase(BaseModel):
    SongID: int
    ApplyUID: int
    ApplyAlias: str


class Approved(StatusBase):
    Tag: str
    Name: str
    GroupID: int | None = None
    WSUUID: str | None = None


class AliasStatus(StatusBase):
    Tag: str
    Name: str
    Time: str
    AgreeVotes: int | None = 0
    Votes: int


class Reviewed(StatusBase):
    Tag: str
    Name: str


class PushAliasStatus(BaseModel):
    Type: str
    Status: AliasStatus | Approved | Reviewed

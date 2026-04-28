from pydantic import BaseModel


class Alias(BaseModel):
    
    song_id: int
    alias: list[str]
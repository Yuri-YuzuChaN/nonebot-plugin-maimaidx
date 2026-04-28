from enum import Enum


class Category(str, Enum):
    
    DEFAULT = "default"
    COMPLETED = "completed"
    UNFINISHED = "unfinished"
    NOTPLAYED = "notplayed"
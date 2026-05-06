from enum import Enum


class ServiceName(str, Enum):
    LXNS = "Lxns-Network"
    DIVINGFISH = "Diving-Fish"

    @classmethod
    def get_by_index(cls, index_str: str) -> "ServiceName | None":
        mapping = {str(i): item for i, item in enumerate(cls)}
        return mapping.get(index_str)

    @classmethod
    def get_help(cls) -> str:
        return "\n".join([f"{i}: {item.value}" for i, item in enumerate(cls)])


class Category(str, Enum):
    DEFAULT = "default"
    COMPLETED = "completed"
    UNFINISHED = "unfinished"
    NOTPLAYED = "notplayed"


class Theme(str, Enum):
    CIRCLE = "circle"
    PRISM_PLUS = "prism_plus"

    @classmethod
    def get_by_index(cls, index_str: str) -> "Theme | None":
        mapping = {str(i): item for i, item in enumerate(cls)}
        return mapping.get(index_str)

    @classmethod
    def get_help(cls) -> str:
        return "\n".join([f"{i}: {item.value}" for i, item in enumerate(cls)])

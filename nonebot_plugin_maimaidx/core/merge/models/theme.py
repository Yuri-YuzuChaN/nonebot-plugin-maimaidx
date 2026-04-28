from enum import Enum


class Theme(str, Enum):
    
    CIRCLE = "circle"
    PRISM_PLUS = "prism_plus"
    
    @classmethod
    def get_by_index(cls, index_str: str) -> "Theme | None":
        mapping = {str(i): item for i, item in enumerate(cls)}
        return mapping.get(index_str)

    @classmethod
    def get_help(cls) -> str:
        return " | ".join([f"{i}: {item.value}" for i, item in enumerate(cls)])
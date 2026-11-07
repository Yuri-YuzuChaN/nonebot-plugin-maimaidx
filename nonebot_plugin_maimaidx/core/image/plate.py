from pathlib import Path

# API responses and static asset packs can use different character variants.
_PLATE_TRANSLATION = str.maketrans(
    {
        "鏡": "镜",
        "雙": "双",
        "晓": "暁",
        "曉": "暁",
        "樱": "櫻",
        "堇": "菫",
        "辉": "輝",
        "华": "華",
        "极": "極",
        "將": "将",
    }
)


def resolve_plate_path(name: str, directory: Path, default: Path) -> Path:
    """Prefer the exact asset, then its known spelling, then the default plate."""
    if not name or any(char in name for char in ("/", "\\", "\0")):
        return default

    for spelling in dict.fromkeys((name, name.translate(_PLATE_TRANSLATION))):
        path = directory / f"{spelling}.png"
        if path.is_file():
            return path

    return default

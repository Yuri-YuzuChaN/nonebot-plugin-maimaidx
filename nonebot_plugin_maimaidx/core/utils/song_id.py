
def get_charts_id(id: int) -> int:
    """获取谱面id"""
    if 10000 <= id < 100000:
        id -= 10000
    return id


def get_score_id(id: int) -> int:
    """获取成绩曲目id"""
    if 1000 <= id < 10000:
        id += 10000
    if 11000 <= id < 100000:
        id -= 10000
    return id
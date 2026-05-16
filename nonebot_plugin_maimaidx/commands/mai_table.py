import re

from nonebot import on_fullmatch, on_regex
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from nonebot.params import Depends, RegexMatched
from nonebot.permission import SUPERUSER

from ..constants import COMBO_PLUS, LEVEL_LIST, PLATE_CN, RANK_PLUS, SYNC_PLUS
from ..core.database.qq import User
from ..core.handler import (
    draw_level_progress,
    draw_level_score_list,
    draw_plate_progress,
    draw_plate_table,
    draw_rating_table,
    draw_rating_table_text,
)
from ..core.image.update_table import UpdateTable
from ..core.merge.models import Category
from .depend import GetUserAndAuth

RATING_PATTERN = r"^([0-9]+\+?)(ap|app|fc|fcp|fs|fsp|fdx|fdxp)?\s?完成表$"
TABLE_PATTERN = (
    r"^([真超檄橙暁晓桃櫻樱紫菫堇白雪輝辉舞霸熊華华爽煌星宙祭祝双宴镜彩])"
    r"([極极将舞神者]舞?){}\s?([12])?"
)
RISE_SCORE_PATTERN = r"^我要在?([0-9]+\+?)?[上加\+]([0-9]+)?分\s?(.+)?"
LEVEL_PATTERN = (
    r"([0-9]+\+?)\s?([abcdsfxp\+]+)\s?([\u4e00-\u9fa5]+)?\s?进度\s?([0-9]+)?\s?(.+)?"
)
LEVEL_LIST_PATTERN = r"([0-9]+\.?[0-9]?\+?)\s?分数列表\s?([0-9]+)?\s?(.+)?"
CATEGORY_ALIAS = {
    "已完成": Category.COMPLETED,
    "未完成": Category.UNFINISHED,
    "未开始": Category.NOTPLAYED,
    "未游玩": Category.NOTPLAYED,
}


update_table = on_fullmatch("更新定数表", permission=SUPERUSER)
update_plate = on_fullmatch("更新完成表", permission=SUPERUSER)
rating_table = on_regex(r"([0-9]+\+?)定数表")
rating_table_pfm = on_regex(RATING_PATTERN, re.IGNORECASE)
plate_table_pfm = on_regex(TABLE_PATTERN.format("完成表"))
plate_progress = on_regex(TABLE_PATTERN.format("进度"))
level_progress = on_regex(LEVEL_PATTERN, re.IGNORECASE)
level_score_list = on_regex(LEVEL_LIST_PATTERN)


@update_table.handle()
async def _(event: PrivateMessageEvent):
    await update_table.send("正在更新定数表...")
    update = UpdateTable()
    await update.update_rating_table()
    await update.update_level_15_rating_table()
    await update_table.finish("定数表更新完成")


@update_plate.handle()
async def _(event: PrivateMessageEvent):
    await update_plate.send("正在更新完成表...")
    update = UpdateTable()
    await update.update_plate_table()
    await update.update_wu_plate_table()
    await update_plate.finish("完成表更新完成")


@rating_table.handle()
async def _(match=RegexMatched()):
    rating = match.group(1).strip()
    if rating in LEVEL_LIST[:6]:
        result = "只支持查询lv7-15的定数表"
    elif rating in LEVEL_LIST[6:]:
        result = draw_rating_table_text(rating)
    else:
        result = "无法识别的定数"
    await rating_table.send(result, reply_message=True)


@rating_table_pfm.handle()
async def _(match=RegexMatched(), user: User = Depends(GetUserAndAuth)):
    ra = match.group(1)
    plan = match.group(2)
    if ra in LEVEL_LIST[:6]:
        await rating_table_pfm.finish("只支持查询lv7-15的完成表", reply_message=True)
    elif ra in LEVEL_LIST[6:]:
        pic = await draw_rating_table(
            user, ra, True if plan and plan.lower() in COMBO_PLUS else False
        )
        await rating_table_pfm.finish(pic, reply_message=True)
    else:
        await rating_table_pfm.finish("无法识别的定数", reply_message=True)


@plate_table_pfm.handle()
async def _(match=RegexMatched(), user: User = Depends(GetUserAndAuth)):
    ver = match.group(1)
    plan = match.group(2)
    page = match.group(3) or 1
    if ver in PLATE_CN:
        ver = PLATE_CN[ver]
    if f"{ver}{plan}" == "真将":
        await plate_table_pfm.finish("真系没有真将哦", reply_message=True)
    pic = await draw_plate_table(user, ver, plan, page)
    await plate_table_pfm.finish(pic, reply_message=True)


@plate_progress.handle()
async def _(match=RegexMatched(), user: User = Depends(GetUserAndAuth)):
    username = None
    if not match:
        await plate_progress.finish("输入错误，请重新确定牌子", reply_message=True)
    ver = match.group(1)
    plan = match.group(2)
    if f"{ver}{plan}" == "真将":
        await plate_progress.finish("真系没有真将哦", reply_message=True)

    data = await draw_plate_progress(user, username, ver, plan)
    await plate_progress.send(data, reply_message=True)


@level_progress.handle()
async def _(match=RegexMatched(), user: User = Depends(GetUserAndAuth)):
    if not match:
        await level_progress.finish("输入错误，请重新输入难度等级", reply_message=True)
    level = match.group(1)
    plan = match.group(2)
    category_ = match.group(3)
    page = match.group(4) or 1

    if level not in LEVEL_LIST:
        await level_progress.finish("无此等级", reply_message=True)
    if plan.lower() not in RANK_PLUS + COMBO_PLUS + SYNC_PLUS:
        await level_progress.finish("无此评价等级", reply_message=True)
    if LEVEL_LIST.index(level) < 11 or (
        plan.lower() in RANK_PLUS and RANK_PLUS.index(plan.lower()) < 8
    ):
        await level_progress.finish("兄啊，有点志向好不好", reply_message=True)
    if category_:
        target_category = CATEGORY_ALIAS.get(category_)
        if target_category:
            category = target_category
        else:
            await level_progress.finish(
                f"无法指定查询「{category_}」", reply_message=True
            )
    else:
        category = Category.DEFAULT

    data = await draw_level_progress(user, level, plan, category, int(page))
    await level_progress.send(data, reply_message=True)


@level_score_list.handle()
async def _(match=RegexMatched(), user: User = Depends(GetUserAndAuth)):
    if not match:
        await level_score_list.finish(
            "输入错误，请重新输入指定等级", reply_message=True
        )
    rating = match.group(1)
    page = match.group(2) or 1
    try:
        if "." in rating:
            rating = round(float(rating), 1)
        elif rating not in LEVEL_LIST:
            await level_score_list.finish("无此等级", reply_message=True)
    except ValueError:
        if rating not in LEVEL_LIST:
            await level_score_list.finish("无此等级", reply_message=True)

    result = await draw_level_score_list(user, rating, int(page))
    await level_score_list.send(result, reply_message=True)

import asyncio
from pathlib import Path

import nonebot
from nonebot.plugin import PluginMetadata, require

from .commands import *  # noqa: F403
from .commands.mai_alias import ws_alias_server
from .config import BaseConfig, dfconfig, driver, log, maiconfig
from .constants import ALL_VERSION_KEY, PLATE_CN
from .core.clients.divingfish.client import DivingFishAPI
from .core.database.qq import create_database
from .core.merge.guess import guess
from .core.service import mai
from .resources import plate_table_dir, rating_table_dir

scheduler = require("nonebot_plugin_apscheduler")

from nonebot_plugin_apscheduler import scheduler  # noqa: E402, F811

__plugin_meta__ = PluginMetadata(
    name="nonebot-plugin-maimaidx",
    description="移植自 mai-bot 开源项目，基于 nonebot2 的街机音游 舞萌DX 的查询插件",
    usage="请使用 帮助maimaiDX 指令查看使用方法",
    type="application",
    config=BaseConfig,
    homepage="https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx",
    supported_adapters={"~onebot.v11"},
)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath("plugins").resolve())
)


@driver.on_startup
async def get_music():
    """
    bot启动时开始获取所有数据
    """
    await create_database()
    if dfconfig.divingfish_prober_proxy:
        log.info("使用代理服务器访问「水鱼」查分器")
        DivingFishAPI.set_proxy()
    if maiconfig.maimaidx_alias_proxy:
        log.info("使用代理服务器访问「柚子」别名服务器")

    if maiconfig.maimaidx_alias_push:
        log.opt(colors=True).info("别名推送为「<g>开启</g>」状态")
        asyncio.ensure_future(ws_alias_server())  # noqa: F405
    else:
        log.opt(colors=True).info("别名推送为「<r>关闭</r>」状态")

    log.info("正在获取maimai曲目数据")
    await mai.get_music()
    log.info("正在获取maimai曲目别名数据")
    await mai.get_music_alias()
    log.info("正在获取maimai牌子数据")
    await mai.get_plate_json()
    guess.guess()
    log.success("maimai数据获取完成")

    if maiconfig.save_in_memory:
        # ScoreBaseImage._load_image()
        log.success("已将图片保存在内存中")

    if not list(rating_table_dir.iterdir()):
        log.opt(colors=True).warning(
            "<y>注意！注意！</y>检测到定数表文件夹为空！"
            "可能导致「定数表」「完成表」指令无法使用，"
            "请及时私聊BOT使用指令「更新定数表」进行生成。"
        )
    plate_list = [name for name in ALL_VERSION_KEY[1:]]
    plate_table_dir_list = [f.name.split(".")[0] for f in plate_table_dir.iterdir()]
    cn_list = [name for name in list(PLATE_CN.keys())]
    not_in = set(plate_list) - set(plate_table_dir_list) - set(cn_list)
    if not_in:
        anyname = "，".join(not_in)
        log.opt(colors=True).warning(
            f"<y>注意！注意！</y>未检测到牌子文件夹中的牌子：<y>{anyname}</y>，"
            "可能导致这些牌子的「完成表」指令无法使用，"
            "请及时私聊BOT使用指令「更新完成表」进行生成。"
        )


scheduler.add_job(mai.update, "cron", hour=4)

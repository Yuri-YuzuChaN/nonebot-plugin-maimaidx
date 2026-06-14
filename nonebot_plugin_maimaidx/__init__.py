import asyncio
from pathlib import Path

import nonebot
from nonebot.plugin import PluginMetadata, require

from . import commands as commands
from .config import BaseConfig, dfconfig, driver, log, lxnsconfig, maiconfig
from .core.alias_ws_push import ws_alias_server
from .core.clients.divingfish.client import DivingFishAPI
from .core.database.qq import create_database
from .core.image import AssetsImage
from .core.service import guess, mai
from .core.service.arcade import arcade
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
        asyncio.ensure_future(ws_alias_server())
    else:
        log.opt(colors=True).info("别名推送为「<r>关闭</r>」状态")

    log.info("正在获取maimai曲目数据")
    await mai.get_music()
    log.info("正在获取maimai曲目别名数据")
    await mai.get_music_alias()
    log.info("正在获取maimai牌子数据")
    await mai.get_plate_json()
    log.info("正在获取maimai机厅数据")
    await arcade.get_arcades()
    log.success("maimai机厅数据获取完成")
    guess.guess()
    log.success("猜歌数据初始化完成")
    log.success("maimai数据获取完成")

    if dfconfig.divingfish_token is None:
        log.opt(colors=True).warning(
            "<r>未配置水鱼查分器开发者Token，查分模块只能使用「b50」指令</r>"
        )
    if lxnsconfig.lxns_dev_token is None:
        log.opt(colors=True).warning(
            "<r>未配置落雪查分器开发者Token，无法使用落雪数据源</r>"
        )

    if maiconfig.save_in_memory:
        AssetsImage._load_image()
        log.success("已将图片保存在内存中")

    if not list(rating_table_dir.iterdir()):
        log.opt(colors=True).warning(
            "<y>注意！注意！</y>检测到定数表文件夹为空！"
            "可能导致「定数表」「完成表」指令无法使用，"
            "请及时私聊BOT使用指令「更新定数表」进行生成。"
        )

    if not list(plate_table_dir.iterdir()):
        log.opt(colors=True).warning(
            "<y>注意！注意！</y>检测到牌子文件夹为空！"
            "可能导致「完成表」指令无法使用，"
            "请及时私聊BOT使用指令「更新完成表」进行生成。"
        )


scheduler.add_job(mai.update, "cron", hour=4)
scheduler.add_job(
    commands.mai_arcade.update_arcade_daily,
    "cron",
    hour=4,
    minute=0,
    id="maimaidx_arcade_daily_update",
    replace_existing=True,
)

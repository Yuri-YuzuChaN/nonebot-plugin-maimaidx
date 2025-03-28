import nonebot
from nonebot.plugin import PluginMetadata, require

from .command import *

scheduler = require('nonebot_plugin_apscheduler')

from nonebot_plugin_apscheduler import scheduler

__plugin_meta__ = PluginMetadata(
    name='nonebot-plugin-maimaidx',
    description='移植自 mai-bot 开源项目，基于 nonebot2 的街机音游 舞萌DX 的查询插件',
    usage='请使用 帮助maimaiDX 指令查看使用方法',
    type='application',
    config=Config,
    homepage='https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx',
    supported_adapters={'~onebot.v11'}
)

sub_plugins = nonebot.load_plugins(
    str(Path(__file__).parent.joinpath('plugins').resolve())
)


@driver.on_startup
async def get_music():
    """
    bot启动时开始获取所有数据
    """
    if maiconfig.maimaidxproberproxy:
        log.info('正在使用代理服务器访问查分器')
    if maiconfig.maimaidxaliasproxy:
        log.info('正在使用代理服务器访问别名服务器')
    maiApi.load_token_proxy()
    log.info('正在获取maimai所有曲目信息')
    await mai.get_music()
    log.info('正在获取maimai牌子数据')
    await mai.get_plate_json()
    log.info('正在获取maimai所有曲目别名信息')
    await mai.get_music_alias()
    log.success('maimai数据获取完成')


scheduler.add_job(alias_apply_status, 'interval', minutes=5)
scheduler.add_job(data_update_daily, 'cron', hour=4)

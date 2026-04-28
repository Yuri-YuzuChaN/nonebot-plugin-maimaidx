from ...config import log, lxnsconfig
from ..merge import merge_alias_data, merge_music_data
from ..merge.alias_list import AliasList
from ..merge.models.song import SimpleSong
from ..merge.music_list import MusicList
from .diving_fish import get_music_list
from .lxns import get_music_aliases, get_music_data
from .yuzuchan import get_music_alias_list, get_plate_data


class MaiMusic:

    total_list: MusicList
    """曲目数据"""
    total_alias_list: AliasList
    """别名数据"""
    total_plate_id_list: dict[str, list[int]]
    """牌子ID列表数据"""
    total_level_data: dict[str, dict[str, list[SimpleSong]]]
    """等级列表数据"""

    def __init__(self) -> None:
        """封装所有曲目信息以及猜歌数据，便于更新"""

    async def get_music(self) -> None:
        """获取所有曲目数据"""
        df_music_data, df_stats_data = await get_music_list()
        log.success("成功获取「水鱼」查分器曲目数据")
        if lxnsconfig.lxns_dev_token:
            lxns_data = await get_music_data()
            log.success("成功获取「落雪」查分器曲目数据")
        else:
            lxns_data = None
            log.warning("未配置落雪开发者Token，跳过获取「落雪」曲目数据源")
        
        log.info("正在合并曲目数据")
        self.total_list = await merge_music_data(
            diving_fish_list=df_music_data, 
            lxns_list=lxns_data, 
            stats_map=df_stats_data
        )
        log.success("曲目数据合并完成")
        
        self.total_level_data = self.total_list.by_level_list()

    async def get_music_alias(self) -> None:
        """获取所有曲目别名"""
        yuzu_data = await get_music_alias_list()
        log.success("成功获取「柚子」别名数据")
        if lxnsconfig.lxns_dev_token:
            lxns_data = await get_music_aliases()
            log.success("成功获取「落雪」别名数据")
        else:
            lxns_data = None
            log.warning("未配置落雪开发者Token，跳过获取「落雪」别名数据源")
            
        log.info("正在合并别名数据")
        self.total_alias_list = await merge_alias_data(yuzu_data, lxns_data)
        log.success("别名数据合并完成")
        
    async def get_plate_json(self) -> None:
        """获取所有牌子数据"""
        self.total_plate_id_list = await get_plate_data()
        log.success("成功获取牌子数据")
    
    async def update(self) -> None:
        """更新数据"""
        await self.get_music()
        await self.get_music_alias()
        await self.get_plate_json()
        log.success("maimaiDX数据更新完毕")
    

mai = MaiMusic()
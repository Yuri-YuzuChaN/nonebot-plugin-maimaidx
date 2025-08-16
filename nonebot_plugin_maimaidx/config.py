import uuid
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger as log
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel

driver = get_driver()


class Config(BaseModel):
    
    maimaidxtoken: Optional[str] = None
    maimaidxpath: str
    maimaidxproberproxy: bool = False
    maimaidxaliasproxy: bool = False
    maimaidxaliaspush: bool = True
    saveinmem: Optional[bool] = True
    botName: str = list(driver.config.nickname)[0] if driver.config.nickname else 'maimai'


maiconfig = get_plugin_config(Config)


vote_url: str = 'https://www.yuzuchan.moe/vote'

# ws
UUID = uuid.uuid1()


# echartsjs
SNAPSHOT_JS = (
    "echarts.getInstanceByDom(document.querySelector('div[_echarts_instance_]'))."
    "getDataURL({type: 'PNG', pixelRatio: 2, excludeComponents: ['toolbox']})"
)


# 文件路径
Root: Path = Path(__file__).parent
if maiconfig.maimaidxpath:
    static: Path = Path(maiconfig.maimaidxpath)
else:
    raise ValueError(
        '`nonebot-plugin-maimaidx` 插件未检测到静态文件夹 `static`，'
        '请根据 README 配置页说明进行下载静态文件'
    )
alias_file: Path = static / 'music_alias.json'                  # 别名暂存文件
local_alias_file: Path = static / 'local_music_alias.json'      # 本地别名文件
music_file: Path = static / 'music_data.json'                   # 曲目暂存文件
chart_file: Path = static / 'music_chart.json'                  # 谱面数据暂存文件
guess_file: Path = static / 'group_guess_switch.json'           # 猜歌开关群文件
group_alias_file: Path = static / 'group_alias_switch.json'     # 别名推送开关群文件
pie_html_file: Path = static / 'temp_pie.html'                  # 饼图html文件


# 静态资源路径
maimaidir: Path = static / 'mai' / 'pic'
coverdir: Path = static / 'mai' / 'cover'
ratingdir: Path = static / 'mai' / 'rating'
platedir: Path = static / 'mai' / 'plate'


# 字体路径
SIYUAN: Path =  static / 'ResourceHanRoundedCN-Bold.ttf'
SHANGGUMONO: Path = static / 'ShangguMonoSC-Regular.otf'
TBFONT: Path = static / 'Torus SemiBold.otf'


# 常用变量
SONGS_PER_PAGE: int = 25
scoreRank: List[str] = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 's+', 'ss', 'ss+', 'sss', 'sss+']
score_Rank: List[str] = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'sp', 'ss', 'ssp', 'sss', 'sssp']
score_Rank_l: Dict[str, str] = {
    'd': 'D', 
    'c': 'C', 
    'b': 'B', 
    'bb': 'BB', 
    'bbb': 'BBB', 
    'a': 'A', 
    'aa': 'AA', 
    'aaa': 'AAA', 
    's': 'S', 
    'sp': 'Sp', 
    'ss': 'SS', 
    'ssp': 'SSp', 
    'sss': 'SSS', 
    'sssp': 'SSSp'
}
comboRank: List[str] = ['fc', 'fc+', 'ap', 'ap+']
combo_rank: List[str] = ['fc', 'fcp', 'ap', 'app']
syncRank: List[str] = ['fs', 'fs+', 'fdx', 'fdx+']
sync_rank: List[str] = ['fs', 'fsp', 'fsd', 'fsdp']
sync_rank_p: List[str] = ['fs', 'fsp', 'fdx', 'fdxp']
diffs: List[str] = ['Basic', 'Advanced', 'Expert', 'Master', 'Re:Master']
levelList: List[str] = [
    '1', 
    '2', 
    '3', 
    '4', 
    '5', 
    '6', 
    '7', 
    '7+', 
    '8', 
    '8+', 
    '9', 
    '9+', 
    '10', 
    '10+', 
    '11', 
    '11+', 
    '12', 
    '12+', 
    '13', 
    '13+', 
    '14', 
    '14+', 
    '15'
]
achievementList: List[float] = [50.0, 60.0, 70.0, 75.0, 80.0, 90.0, 94.0, 97.0, 98.0, 99.0, 99.5, 100.0, 100.5]
BaseRaSpp: List[float] = [7.0, 8.0, 9.6, 11.2, 12.0, 13.6, 15.2, 16.8, 20.0, 20.3, 20.8, 21.1, 21.6, 22.4]
fcl: Dict[str, str] = {'fc': 'FC', 'fcp': 'FCp', 'ap': 'AP', 'app': 'APp'}
fsl: Dict[str, str] = {'fs': 'FS', 'fsp': 'FSp', 'fsd': 'FSD', 'fdx': 'FSD', 'fsdp': 'FSDp', 'fdxp': 'FSDp', 'sync': 'Sync'}
plate_to_sd_version: Dict[str, str] = {
    '初': 'maimai',
    '真': 'maimai PLUS',
    '超': 'maimai GreeN',
    '檄': 'maimai GreeN PLUS',
    '橙': 'maimai ORANGE',
    '暁': 'maimai ORANGE PLUS',
    '晓': 'maimai ORANGE PLUS',
    '桃': 'maimai PiNK',
    '櫻': 'maimai PiNK PLUS',
    '樱': 'maimai PiNK PLUS',
    '紫': 'maimai MURASAKi',
    '菫': 'maimai MURASAKi PLUS',
    '堇': 'maimai MURASAKi PLUS',
    '白': 'maimai MiLK',
    '雪': 'MiLK PLUS',
    '輝': 'maimai FiNALE',
    '辉': 'maimai FiNALE'
}
plate_to_dx_version: Dict[str, str] = {
    **plate_to_sd_version,
    '熊': 'maimai でらっくす',
    '華': 'maimai でらっくす PLUS',
    '华': 'maimai でらっくす PLUS',
    '爽': 'maimai でらっくす Splash',
    '煌': 'maimai でらっくす Splash PLUS',
    '宙': 'maimai でらっくす UNiVERSE',
    '星': 'maimai でらっくす UNiVERSE PLUS',
    '祭': 'maimai でらっくす FESTiVAL',
    '祝': 'maimai でらっくす FESTiVAL PLUS',
    '双': 'maimai でらっくす BUDDiES',
    '宴': 'maimai でらっくす BUDDiES PLUS',
    '镜': 'maimai でらっくす PRiSM'
}
version_map = {
    '真': ([plate_to_dx_version['真'], plate_to_dx_version['初']], '真'),
    '超': ([plate_to_sd_version['超']], '超'),
    '檄': ([plate_to_sd_version['檄']], '檄'),
    '橙': ([plate_to_sd_version['橙']], '橙'),
    '暁': ([plate_to_sd_version['暁']], '暁'),
    '桃': ([plate_to_sd_version['桃']], '桃'),
    '櫻': ([plate_to_sd_version['櫻']], '櫻'),
    '紫': ([plate_to_sd_version['紫']], '紫'),
    '菫': ([plate_to_sd_version['菫']], '菫'),
    '白': ([plate_to_sd_version['白']], '白'),
    '雪': ([plate_to_sd_version['雪']], '雪'),
    '輝': ([plate_to_sd_version['輝']], '輝'),
    '霸': (list(set(plate_to_sd_version.values())), '舞'),
    '舞': (list(set(plate_to_sd_version.values())), '舞'),
    '熊': ([plate_to_dx_version['熊']], '熊&华'),
    '华': ([plate_to_dx_version['熊']], '熊&华'),
    '華': ([plate_to_dx_version['熊']], '熊&华'),
    '爽': ([plate_to_dx_version['爽']], '爽&煌'),
    '煌': ([plate_to_dx_version['爽']], '爽&煌'),
    '宙': ([plate_to_dx_version['宙']], '宙&星'),
    '星': ([plate_to_dx_version['宙']], '宙&星'),
    '祭': ([plate_to_dx_version['祭']], '祭&祝'),
    '祝': ([plate_to_dx_version['祭']], '祭&祝'),
    '双': ([plate_to_dx_version['双']], '双&宴'),
    '宴': ([plate_to_dx_version['双']], '双&宴'),
    '镜': ([plate_to_dx_version['镜']], '镜')
}
platecn = {
    '晓': '暁',
    '樱': '櫻',
    '堇': '菫',
    '辉': '輝',
    '华': '華'
}
category: Dict[str, str] = {
    '流行&动漫': 'anime',
    '舞萌': 'maimai',
    'niconico & VOCALOID': 'niconico',
    '东方Project': 'touhou',
    '其他游戏': 'game',
    '音击&中二节奏': 'ongeki',
    'POPSアニメ': 'anime',
    'maimai': 'maimai',
    'niconicoボーカロイド': 'niconico',
    '東方Project': 'touhou',
    'ゲームバラエティ': 'game',
    'オンゲキCHUNITHM': 'ongeki',
    '宴会場': '宴会场'
}
from pathlib import Path

from .config import maiconfig

Root = Path(__file__).parent

if maiconfig.maimaidx_path:
    static = Path(maiconfig.maimaidx_path)
else:
    raise ValueError(
        "`nonebot-plugin-maimaidx` 插件未检测到静态文件夹 `static`，"
        "请根据 README 配置页说明进行下载静态文件"
    )


# 静态资源路径
font_dir            = static / "font"
data_dir            = static / "data"
pic_dir             = static / "mai" / "pic"
cover_dir           = static / "mai" / "cover"
plate_dir           = static / "mai" / "plate"
plate_version_dir   = static / "mai" / "plate_version"
plate_table_dir     = static / "mai" / "plate_table"
rating_table_dir    = static / "mai" / "rating_table"


# 路径文件
pie_html_file       = static / "temp_pie.html"              # 饼图html文件
guess_file          = data_dir / 'group_guess_switch.json'  # 猜歌开关群文件
group_alias_file    = data_dir / 'group_alias_switch.json'  # 别名推送开关群文件
alias_file          = data_dir / "music_alias.json"         # 别名暂存文件
lxns_alias_file     = data_dir / "lxns_music_alias.json"    # 别名暂存文件
music_file          = data_dir / "music_data.json"          # 曲目暂存文件
lxns_music_file     = data_dir / "lxns_music_data.json"     # 曲目暂存文件
chart_file          = data_dir / "music_chart.json"         # 谱面数据暂存文件
plate_file          = data_dir / "plate_data.json"          # 牌子数据暂存文件
merge_music_file    = data_dir / "merge_music_data.json"    # 合并曲目数据文件
merge_alias_file    = data_dir / "merge_music_alias.json"   # 合并曲目别名数据文件


# 字体路径
SIYUAN      = font_dir / "ResourceHanRoundedCN-Bold.ttf"
SHANGGUMONO = font_dir / "ShangguMonoSC-Regular.otf"
TBFONT      = font_dir / "Torus SemiBold.otf"
FOTNEWRODIN = font_dir / "FOT-NewRodin Pro EB.otf"

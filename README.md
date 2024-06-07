<div align='center'>
    <a><img src='https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/favicon.png' width='200px' height='200px' akt='maimaidx'></a>
</div>

<div align='center'>

# nonebot-plugin-maimaidx

<a href='./LICENSE'>
    <img src='https://img.shields.io/github/license/Yuri-YuzuChaN/nonebot-plugin-maimaidx' alt='license'>
</a>
<img src='https://img.shields.io/badge/python-3.8+-blue.svg' alt='python'>
</div>


## 重要更新

**2024-06-07**

1. 更新至 `舞萌DX 2024`
2. 更换所有图片绘制，需删除除 `json` 后缀的所有文件，**请重新进行使用方法第二步**
3. 更改部分 `json` 文件名称，便于识别，具体文件如下，**请务必修改文件名，否则开关文件以及本地别名文件将不会被读取**
   - `all_alias.json`    修改为 `music_alias.json`
   - `local_alias.json`  修改为 `local_music_alias.json`
   - `chart_stats.json`  修改为 `music_chart.json`
   - `group_alias.json`  修改为 `group_alias_switch.json`
   - `guess_config.json` 修改为 `group_guess_switch.json`
4. 新增管理员私聊指令 `更新完成表`，用于更新 `BUDDiES` 版本 `双系` 牌子
5. 新增指令 `完成表`，可查询牌子完成表，例如：`祝极完成表`
6. 新增指令 `猜曲绘`
7. 查看谱面支持计算个人加分情况，指令包括 `是什么歌`，`id`
8. 指令 `mai什么` 支持随机发送推分谱面，指令中需包含 `加分`，`上分` 字样，例如：`今日mai打什么上分`
9.  修改指令 `分数列表` 和 `进度` 发送方式
10. 优化所有模块

**时间紧凑，以下实现未完成，将在后续更新跟进**

1. 修改牌子进度为图片形式，详细各个谱面完成进度
2. 宴会场定数表
3. 新的 `help` 图片

## 安装

1. 安装 `nonebot-plugin-maimaidx`

    - 使用 `nb-cli` 安装
        ``` python
        nb plugin install nonebot-plugin-maimaidx
        ```
    - 使用 `pip` 安装
        ``` python
        pip install nonebot-plugin-maimaidx
        ```
    - 使用源代码（不推荐） **需自行安装额外依赖**
        ``` git
        git clone https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx
        ```
    
2. 安装 `PhantomJS`，前往 https://phantomjs.org/download.html 下载对应平台支持

> [!WARNING]
> 未配置 `PhantomJS` 支持的Bot，在使用 `ginfo` 指令时会被强制关闭 Bot 进程

## 配置
   
1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static` 。[下载链接](https://share.yuzuchan.moe/d/aria/Resource.zip?sign=LOqwqDVm95dYnkEDYKX2E-VGj0xc_JxrsFnuR1BcvtI=:0)
2. 在 `.env` 文件中配置静态文件绝对路径 `MAIMAIDXPATH`

   ``` dotenv
   MAIMAIDXPATH=path.to.static

   # 例如 windows 平台，非 "管理员模式" 运行Bot尽量避免存放在C盘
   MAIMAIDXPATH=D:\bot\static
   # 例如 linux 平台
   MAIMAIDXPATH=/root/static
   ```

3. 可选，如果拥有 `diving-fish 查分器` 的开发者 `Token`，在 `.env` 文件夹中配置 `MAIMAIDXTOKEN`
   
   ``` dotenv
   MAIMAIDXTOKEN=MAIMAITOKEN
   ```

> [!NOTE]
> 插件带有别名更新推送功能，如果不需要请私聊Bot使用 `全局关闭别名推送` 指令关闭所有群组推送

## 指令

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)

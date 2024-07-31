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

**2024-07-23**

1. 更新部分牌子完成表和 `SyncPlay` 图片，下载更新图片包 `Update.zip` 解压，将 `static` 复制并覆盖。**如果怕缺少图片请进行[使用方法第二步](#使用方法)**
   - [私人云盘](https://share.yuzuchan.moe/d/aria/Update.zip?sign=PFnIZpgyB_HptU-hHIQ-S_qhuuGTNDlmEEtmaEpmJlA=:0)
   - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzuchan_yuzuai_onmicrosoft_com/EcFTIQemNF9NlNQj8RZSdhABiV64tFi-X8-8a7JKxfEKJQ?e=P5nPnx)
2. 修复 `新增机厅` 指令 `id` 未增加的问题
3. 修复 `牌子进度` 指令 `sync` 未匹配的问题
4. 修复 `别名查歌` 指令查询到已删除的曲目时发生错误的问题

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
   
1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static`

    - [私人云盘](https://share.yuzuchan.moe/d/aria/Resource.zip?sign=LOqwqDVm95dYnkEDYKX2E-VGj0xc_JxrsFnuR1BcvtI=:0)
    - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzuchan_yuzuai_onmicrosoft_com/EaS3jPYdMwxGiU3V_V64nRIBk6QA5Gdhs2TkJQ2bLssxbw?e=Mm6cWY)

2. 在 `.env` 文件中配置静态文件绝对路径 `MAIMAIDXPATH`

    ``` dotenv
    MAIMAIDXPATH=path.to.static

    # 例如 windows 平台，非 "管理员模式" 运行Bot尽量避免存放在C盘
    MAIMAIDXPATH=D:\bot\static
    # 例如 linux 平台
    MAIMAIDXPATH=/root/static
    ```

3. 在 `.env` 文件夹中配置 `MAIMAIDXTOKEN`
   
    ``` dotenv
    # 如果没有 `diving-fish 查分器` 的开发者 `Token`，请直接留空
    MAIMAIDXTOKEN=
    # 如果有请填入 `Token`
    MAIMAIDXTOKEN=MAIMAITOKEN
    ```

> [!NOTE]
> 插件带有别名更新推送功能，如果不需要请私聊Bot使用 `全局关闭别名推送` 指令关闭所有群组推送

## 指令

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)

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
   
1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static` 。[下载链接](https://cloud.yuzuchan.moe/f/DjSw/static.zip)
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

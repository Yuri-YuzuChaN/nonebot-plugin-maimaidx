<div align='center'>

<a><img src='https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/favicon.png' width='200px' height='200px' akt='maimaidx'></a>

[![python3](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![QQGroup](https://img.shields.io/badge/QQGroup-Join-blue)](https://qm.qq.com/q/gDIf3fGSPe)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>


## 重要更新

**2025-03-28**

> [!WARNING]
> 对于这个版本之前的插件和修改版的插件请注意，预更新版本别名库将全部更换成新的 `API` 地址，返回的数据结构均更改，目前旧版 `API` 将再运行一段时间，预计正式更新 `舞萌DX2025` 时将会关闭

1. 预更新 `舞萌DX2025` UI，资源全部更换，更新部分依赖和文件，**请重新进行安装**

## 安装

> [!WARNING]
> Python 3.13.X 安装插件失败解决方案: [Windows](https://github.com/LeiSureLyYrsc/nb-maimaidx-install-problem)

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
    
2. 安装 `chromium`，**相关依赖已安装，请直接使用该指令执行**
   
    ``` shell
    playwright install --with-deps chromium
    ```

3. 安装 `微软雅黑` 字体，解决使用 `ginfo` 指令字体不渲染的问题，例如 `ubuntu`：`apt install fonts-wqy-microhei`

## 配置

1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static`

   - [私人云盘](https://cloud.yuzuchan.moe/f/1bUn/Resource.7z)
   - [AList网盘](https://share.yuzuchan.moe/p/Resource.7z?sign=EvCwaGwJrneyD1Olq00NG3HXNK7fQKpx_sa3Ck9Uzjs=:0)
   - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzu_yuzuchan_moe/EdGUKRSo-VpHjT2noa_9EroBdFZci-tqWjVZzKZRTEeZkw?e=a1TM40)

2. 在 `.env` 文件中配置静态文件绝对路径 `MAIMAIDXPATH`

    ``` dotenv
    MAIMAIDXPATH=path.to.static

    # 例如 windows 平台，非 "管理员模式" 运行Bot尽量避免存放在C盘
    MAIMAIDXPATH=D:\bot\static
    # 例如 linux 平台
    MAIMAIDXPATH=/root/static
    ```

3. 可选，如果拥有 `diving-fish 查分器` 的开发者 `Token`，请在 `.env` 文件中配置 `MAIMAIDXTOKEN`
   
    ``` dotenv
    MAIMAIDXTOKEN=MAIMAITOKEN
    ```

4. 可选，如果你的服务器或主机不能顺利流畅的访问查分器和别名库的API，请在 `.env` 文件中配置代理。均为香港服务器代理中转，例如你的服务器访问查分器很困难，请设置 `MAIMAIDXPROBERPROXY` 为 `true`，别名库同理

    ``` dotenv
    # 查分器代理，推荐境外服务器使用
    MAIMAIDXPROBERPROXY=false
    # 别名代理，推荐国内服务器使用
    MAIMAIDXALIASPROXY=false
    ```

5. 可选，是否将部分图片在保存在内存中，不需要请在 `.env` 文件中配置 `SAVEINMEM` 为 `false`

    ``` dotenv
    SAVEINMEM=false
    ```

> [!NOTE]
> 安装完插件需要使用定数表或完成表指令时，需私聊Bot使用 `更新定数表` 和 `更新完成表` 进行生成

> [!NOTE]
> 插件带有别名更新推送功能，如果不需要请私聊Bot使用 `全局关闭别名推送` 指令关闭所有群组推送

## 指令

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)

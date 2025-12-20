<div align='center'>

<a><img src='https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/favicon.png' width='200px' height='200px' akt='maimaidx'></a>

[![python3](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![QQGroup](https://img.shields.io/badge/QQGroup-Join-blue)](https://qm.qq.com/q/gDIf3fGSPe)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>


## 重要更新

## 温馨提示

**首次使用请务必看完 `README.MD` 所有内容**

- 不要再问为什么 `资源文件` 的 `plate` 和 `rating` 文件夹是空的或缺少文件
- 不要再问为什么 `资源文件` 的 `plate` 和 `rating` 文件夹是空的或缺少文件
- 不要再问为什么 `资源文件` 的 `plate` 和 `rating` 文件夹是空的或缺少文件

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
    
2. 安装 `chromium`，**相关依赖已安装，请直接使用该指令执行**

    ``` shell
    playwright install --with-deps chromium
    ```

3. 安装 `微软雅黑` 字体，解决使用 `ginfo` 指令字体不渲染的问题，例如 `ubuntu`：`apt install fonts-wqy-microhei`


## 配置
   
1. 下载静态资源文件，将该压缩文件解压，且解压完为文件夹 `static`

   - [Cloudreve私人云盘](https://cloud.yuzuchan.moe/f/nXt6/Resource.7z)
   - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzu_yuzuchan_moe/IQDRlCkUqPlaR409p6Gv_RK6AZ-dJaBtbgZoJMvFI4IJiYw?e=eu5f2h)

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

5. 可选，是否开启别名推送，不需要请在 `.env` 文件中配置 `MAIMAIDXALIASPUSH` 为 `false`，**注意，该配置为 `false` 时，将不会实时更新别名库，仅会在别名查歌或者跨日更新数据的时候才会更新别名库。如果群组的推送为开启状态，也不再进行推送，推送指令也一并失效**
   
    ``` dotenv
    MAIMAIDXALIASPUSH=false
    ```

6. 可选，是否将部分图片在保存在内存中，不需要请在 `.env` 文件中配置 `SAVEINMEM` 为 `false`

    ``` dotenv
    SAVEINMEM=false
    ```

> [!NOTE]
> 安装完插件需要使用定数表或完成表指令时，需私聊Bot使用 `更新定数表` 和 `更新完成表` 进行生成

> [!NOTE]
> 插件带有别名更新推送功能，默认开启全部群组推送，不需要请私聊Bot使用 `全局关闭别名推送` 指令关闭所有群组推送。群组需要单独使用请使用指令 `开启别名推送`。

## 指令

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)

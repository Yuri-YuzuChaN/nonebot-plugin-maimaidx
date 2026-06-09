<div align='center'>
<a><img src='https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/favicon.png' width='200px' height='200px' akt='maimaidx'></a>

<h1>nonebot-plugin-maimaidx</h1>

[![python3](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

</div>

#### 欢迎加入开发交流群：[QQGroup](https://qm.qq.com/q/gDIf3fGSPe)

## 重要更新

**2026-06-09**

### 现仅支持 `Python 3.10+` ！！！

#### 最好在更新 `舞萌DX 2026` 后再使用该版本

1. 更新支持 `舞萌DX2026`，应该是最后一次大改了
2. 新支持了 `落雪查分器`
3. 新功能：
   - 新增 `舞`，`霸者` 牌子绘图
   - 新增进度绘图
   - 新增查询曲目过多时的绘图
   - 新增切换主题功能
   - 新增切换查分器功能
   - 新增 `ap50` 指令（仅限落雪查分器）
   - 新增 `lxbind`，`主题`，`数据源` 指令
   - 新增 `牌子条件` 指令
4. 修改了别名推送的发送方式，防止刷屏
5. 修复了非常多的 BUG

## 温馨提示

**请务必看完 `README.MD` 所有内容**

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
    - 使用源代码，**请自行安装额外依赖**
        ``` git
        git clone https://github.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx
        ```
    
2. 安装 `chromium`，**相关依赖已安装，请直接使用该指令执行**

    ``` shell
    playwright install --with-deps chromium
    ```

3. 安装 `微软雅黑` 字体，解决使用 `ginfo` 指令字体不渲染的问题，例如 `ubuntu`：`apt install fonts-wqy-microhei`


## 配置

1. 下载静态资源文件，将该压缩文件解压后，将 `static` 文件夹复制到随意一个文件夹进行存放。对于先前使用过的开发者，请将原先 `static` 文件夹内的所有 `json` 文件放置到 `static/data` 文件夹，字体文件放置到 `static/font` 文件夹
    
    ## 对于美术的声明，请勿将绘图设计署名进行删除

   - [Cloudreve私人云盘](https://cloud.yuzuchan.moe/f/34s7/Resource%20CN1.55.7z)
   - [onedrive](https://yuzuai-my.sharepoint.com/:u:/g/personal/yuzu_yuzuchan_moe/IQBGKHie6MAaTZy3rME7Q-ruAVKgXDCKROqz5e25KtMeeVY?e=53eC6a)
   - [openlist](https://share.yuzuchan.moe/d/downloads/Resource%20CN1.55.7z?sign=4wMRn_9n6YZiEVV2vELKCEOj9zsgxScnmgtjsEL3C6g=:0)

2. 配置可选项，请修改 `.env` 文件，并根据要求填写

   ```
   # maimaidx                           # 基本配置
   MAIMAIDX_PATH=                       # 必填项，静态文件夹路径，必须为绝对路径到 `/static`，例如：e:/SakuraBOT/nbstatic/maimaidx/static
   MAIMAIDX_ALIAS_PROXY=false           # 是否使用中转访问柚子别名服务器，适用于境内服务器
   SAVE_IN_MEMORY=true                  # 是否将部分图片保存在内存
   ASSETS_ONLINE=true                   # 对于有 `icon` 和 `plate` 资源的可将此项改为 `false`，如果没有请默认，否则使用落雪查分器时无法使用

   # diving-fish                        # 水鱼查分器配置
   DIVINGFISH_TOKEN=                    # 开发者 token，由于水鱼查分器修改了请求鉴权，未填写的仅可使用 `b50` 指令
   DIVINGFISH_PROBER_PROXY=false        # 是否使用中转访问水鱼查分器，适用于境外服务器

   # lxns                               # 落雪查分器配置，均未填写将无法使用落雪查分器
   LXNS_DEV_TOKEN=                      # 开发者 token
   LX_CLIENT_ID=                        # OAuth 应用ID
   LX_CLIENT_SECRET=                    # OAuth 应用秘钥
   REDIRECT_URI=                        # OAuth 回调地址
   ```

> [!NOTE]
> 安装完插件需要使用定数表或完成表指令时，需私聊Bot使用 `更新定数表` 和 `更新完成表` 进行生成

> [!NOTE]
> 插件带有别名更新推送功能，默认开启全部群组推送，不需要请私聊Bot使用 `全局关闭别名推送` 指令关闭所有群组推送。群组需要单独使用请使用指令 `开启别名推送`。

## 指令

**使用说明图后续再进行更换**

![img](https://raw.githubusercontent.com/Yuri-YuzuChaN/nonebot-plugin-maimaidx/master/nonebot_plugin_maimaidx/maimaidxhelp.png)


## 更新说明

<details>
<summary>Version 3.0 更新日志</summary>

**2026-06-09**

1. 更新支持 `舞萌DX2026`，应该是最后一次大改了
2. 新支持了 `落雪查分器`
3. 新功能：
   - 新增 `舞`，`霸者` 牌子绘图
   - 新增进度绘图
   - 新增查询曲目过多时的绘图
   - 新增切换主题功能
   - 新增切换查分器功能
   - 新增 `ap50` 指令（仅限落雪查分器）
   - 新增 `lxbind`，`主题`，`数据源` 指令
   - 新增 `牌子条件` 指令
4. 修改了别名推送的发送方式，防止刷屏
5. 修复了非常多的 BUG

</details>

## 鸣谢

感谢 [蓝色彗星](#) 提供的 `牌子条件` 指令图片

## License

MIT

您可以自由使用本项目的代码用于商业或非商业的用途，但必须附带 MIT 授权协议。

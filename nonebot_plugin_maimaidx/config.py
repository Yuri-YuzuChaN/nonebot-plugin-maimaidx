from loguru import logger as log  # noqa: F401
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel

driver = get_driver()


class BaseConfig(BaseModel):
    maimaidx_path: str
    maimaidx_alias_proxy: bool = False
    maimaidx_alias_push: bool = True
    save_in_memory: bool | None = True
    assets_online: bool | None = False
    bot_name: str = (
        list(driver.config.nickname)[0] if driver.config.nickname else "Sakura"
    )


class DivingFishConfig(BaseModel):
    divingfish_prober_proxy: bool = False
    divingfish_token: str | None = None


class LxnsConfig(BaseModel):
    lxns_dev_token: str | None = None
    lx_client_id: str | None = None
    lx_client_secret: str | None = None
    redirect_uri: str | None = None


maiconfig = get_plugin_config(BaseConfig)
dfconfig = get_plugin_config(DivingFishConfig)
lxnsconfig = get_plugin_config(LxnsConfig)

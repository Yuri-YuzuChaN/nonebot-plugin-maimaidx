from loguru import logger as log  # noqa: F401
from nonebot import get_driver, get_plugin_config
from pydantic import BaseModel, field_validator

from .core.clients.divingfish.models.oauth import (
    DIVINGFISH_SCOPE_NAMES,
    DIVINGFISH_SCOPE_VALUES,
    DivingFishScope,
)

driver = get_driver()


class BaseConfig(BaseModel):
    maimaidx_path: str
    maimaidx_alias_proxy: bool = False
    maimaidx_alias_push: bool = True
    save_in_memory: bool | None = True
    assets_online: bool | None = True
    bot_name: str = (
        next(iter(driver.config.nickname)) if driver.config.nickname else "Maimai"
    )


class DivingFishConfig(BaseModel):
    divingfish_prober_proxy: bool = False
    divingfish_token: str | None = None
    divingfish_client_id: str | None = None
    divingfish_client_secret: str | None = None
    divingfish_auth_url: str = "https://auth.diving-fish.com"
    divingfish_scope: DivingFishScope = DivingFishScope.PROBER_RECORDS_READ

    @field_validator("divingfish_scope", mode="before")
    @classmethod
    def validate_divingfish_scope(cls, value: str) -> DivingFishScope:
        if isinstance(value, DivingFishScope):
            return value

        if isinstance(value, int):
            return DivingFishScope(value)

        if not isinstance(value, str):
            raise TypeError("divingfish_scope 必须是字符串或整数")

        value = value.strip()
        if not value:
            raise ValueError("divingfish_scope 不能为空")

        result = DivingFishScope(0)

        for name in value.split():
            scope = DIVINGFISH_SCOPE_VALUES.get(name)
            if scope is None:
                valid_names = ", ".join(DIVINGFISH_SCOPE_VALUES)
                raise ValueError(
                    f"未知的 DivingFish scope: {name!r}；可选值：{valid_names}"
                )
            result |= scope

        return result

    @property
    def divingfish_oauth_scope(self) -> str:
        return " ".join(
            name
            for scope, name in DIVINGFISH_SCOPE_NAMES.items()
            if self.divingfish_scope & scope
        )

    @property
    def oauth_enabled(self) -> bool:
        return bool(self.divingfish_client_id and self.divingfish_client_secret)


class LxnsConfig(BaseModel):
    lxns_dev_token: str | None = None
    lx_client_id: str | None = None
    lx_client_secret: str | None = None
    redirect_uri: str | None = None
    lxns_bind_private_only: bool = False


maiconfig = get_plugin_config(BaseConfig)
dfconfig = get_plugin_config(DivingFishConfig)
lxnsconfig = get_plugin_config(LxnsConfig)

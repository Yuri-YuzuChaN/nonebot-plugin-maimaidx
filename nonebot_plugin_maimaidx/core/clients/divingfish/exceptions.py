from textwrap import dedent

from ..exceptions import HTTPError, PlayerDataError, UserNotFoundError


class DivingFishUserNotFoundError(UserNotFoundError):
    
    def __str__(self) -> str:
        return dedent("""
            未找到此玩家，请确保此玩家的用户名和查分器中的用户名相同。
            如未绑定，请前往查分器官网进行绑定
            https://www.diving-fish.com/maimaidx/prober/
        """).strip()


class UserDisabledQueryError(PlayerDataError):
    """用户关闭协议"""

    def __str__(self) -> str:
        return "该用户禁止了其他人获取数据或未同意用户协议。"


class TokenDisableError(HTTPError):
    """Token被禁用"""

    def __str__(self) -> str:
        return "开发者Token被禁用"


class TokenNotFoundError(HTTPError):
    """Token未找到"""

    def __str__(self) -> str:
        return "请先联系水鱼申请开发者token"
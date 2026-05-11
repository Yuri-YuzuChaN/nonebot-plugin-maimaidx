from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.matcher import Matcher

from ..config import maiconfig
from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user, update_user
from ..core.merge.models import ServiceName

AUTHORIZE_ERROR = (
    f"您尚未授权「{maiconfig.bot_name} BOT」"
    "访问您的落雪查分器数据，请先使用「lxbind」指令进行绑定。"
)


class GetUserModel:
    def __init__(
        self,
        auto_create: bool = True,
        check_auth: bool = False,
        check_skip: bool = False,
    ):
        """
        依赖注入类

        Params:
            `auto_create`: 自动创建用户数据
            `check_auth`: 是否检查落雪查分器 Token
            `check_skip`: 跳过是否存在用户检测
        """
        self.auto_create = auto_create
        self.check_auth = check_auth
        self.check_skip = check_skip

    async def __call__(
        self, matcher: Matcher, event: GroupMessageEvent | PrivateMessageEvent
    ) -> User | None:
        user_id = event.user_id

        try:
            user = await get_user(user_id)
        except UserNotBindError:
            if self.auto_create:
                user = await update_user(user_id)
            if self.check_skip:
                return None
            else:
                await matcher.finish(AUTHORIZE_ERROR, reply_message=True)

        if self.check_auth and user:
            if (
                user.service == ServiceName.LXNS
                and user.access_token is None
                and user.refresh_token is None
            ):
                if self.check_skip:
                    return None
                await matcher.finish(AUTHORIZE_ERROR, reply_message=True)

        return user


GetOrCreateUser = GetUserModel(auto_create=True)
"""获取用户数据，不检查授权，若不存在直接创建"""
GetUserOrNone = GetUserModel(auto_create=False, check_skip=True)
"""获取用户数据，如不存在则返回`None`"""
GetUserAndAuth = GetUserModel(auto_create=True, check_auth=True)
"""获取用户数据，并检查是否授权，未授权则提示授权"""
GetUserAndAuthOrNone = GetUserModel(auto_create=True, check_auth=True, check_skip=True)
"""获取用户数据，如不存在则创建，并检查是否授权，未授权则返回`None`"""

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


async def get_optional_user(event: GroupMessageEvent) -> User | None:
    try:
        return await get_user(event.user_id)
    except UserNotBindError:
        return None


async def get_user_db(
    matcher: Matcher, event: GroupMessageEvent | PrivateMessageEvent
) -> User:
    user_id = event.user_id
    try:
        user = await get_user(user_id)
        if (
            user.service == ServiceName.LXNS
            and user.access_token is None
            and user.refresh_token is None
        ):
            await matcher.finish(AUTHORIZE_ERROR, reply_message=True)
    except UserNotBindError:
        user = await update_user(user_id)
    return user

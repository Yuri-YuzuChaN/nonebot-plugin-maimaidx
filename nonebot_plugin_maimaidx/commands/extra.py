from nonebot.adapters.onebot.v11 import GroupMessageEvent, PrivateMessageEvent
from nonebot.matcher import Matcher

from ..core.clients.exceptions import UserNotBindError
from ..core.database.qq import User, get_user, update_user


async def get_optional_user(event: GroupMessageEvent) -> User | None:
    try:
        return await get_user(event.user_id)
    except UserNotBindError:
        return None


async def get_user_db(
    matcher: Matcher,
    event: GroupMessageEvent | PrivateMessageEvent
) -> User:
    user_id = event.user_id
    try:
        return await get_user(user_id)
    except UserNotBindError:
        await update_user(user_id)
        await matcher.finish(
            (
                "您尚未绑定Bot。\n"
                "可使用「/绑定 QQ号」进行绑定，绑定后即可查询水鱼查分器。\n"
                "绑定QQ号后，可使用「/绑定落雪」绑定落雪查分器。"
            )
        )
class HTTPError(Exception):
    """有关HTTP请求的基类异常"""


class ParamsError(HTTPError):
    """参数错误"""


class PermissionDeniedError(HTTPError):
    """权限不足"""


class NotFoundError(HTTPError):
    """未找到资源"""


class TooManyRequestsError(HTTPError):
    """过多的请求"""


class TokenError(HTTPError):
    """Token错误或失效"""
    

class OAuthError(HTTPError):
    """OAuth2错误"""


class TokenDisableError(HTTPError):
    """Token被禁用"""


class ServerError(HTTPError):
    """服务器错误"""


######
class PlayerDataError(Exception):
    """有关玩家数据的基类异常"""


class UserNotFoundError(PlayerDataError):
    """未找到用户"""


class MusicNotPlayError(PlayerDataError):
    """未游玩曲目"""


class UserNotExistsError(PlayerDataError):
    """用户不存在"""


class UnknownError(Exception):
    """通用异常，未知错误"""


class UserNotBindError(PlayerDataError):
    """用户未绑定"""
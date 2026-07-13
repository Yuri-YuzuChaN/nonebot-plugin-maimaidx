import re
from collections.abc import Callable
from time import monotonic
from urllib.parse import parse_qs, urlencode, urlparse

AUTHORIZATION_CODE_PATTERN = re.compile(
    r"^(?:[A-Z0-9]{4}-[A-Z0-9]{4}-[A-Z0-9]{4}"
    r"|(?=[A-Za-z0-9_-]{24,128}$)(?=[A-Za-z0-9_-]*[A-Za-z])"
    r"(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]+)$"
)


def build_authorize_url(client_id: str, redirect_uri: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": "read_player read_user_profile write_player",
        }
    )
    return f"https://maimai.lxns.net/oauth/authorize?{query}"


def extract_authorization_code(text: str) -> str | None:
    value = text.strip()
    if AUTHORIZATION_CODE_PATTERN.fullmatch(value):
        return value

    prefixed = re.fullmatch(r"授权码\s*[:：]?\s*(\S+)", value)
    if prefixed:
        code = prefixed.group(1)
        if AUTHORIZATION_CODE_PATTERN.fullmatch(code):
            return code

    parsed = urlparse(value)
    if parsed.scheme in {"http", "https"}:
        code = parse_qs(parsed.query).get("code", [None])[0]
        if code and AUTHORIZATION_CODE_PATTERN.fullmatch(code):
            return code

    return None


class PendingBindingStore:
    def __init__(
        self,
        ttl: float = 10 * 60,
        *,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.ttl = ttl
        self._clock = clock
        self._expires_at: dict[int, float] = {}

    def start(self, user_id: int) -> None:
        now = self._clock()
        self._clear_expired(now)
        self._expires_at[user_id] = now + self.ttl

    def is_active(self, user_id: int) -> bool:
        now = self._clock()
        self._clear_expired(now)
        return user_id in self._expires_at

    def consume(self, user_id: int) -> bool:
        now = self._clock()
        self._clear_expired(now)
        return self._expires_at.pop(user_id, None) is not None

    def discard(self, user_id: int) -> None:
        self._expires_at.pop(user_id, None)

    def _clear_expired(self, now: float) -> None:
        expired = [
            user_id
            for user_id, expires_at in self._expires_at.items()
            if expires_at <= now
        ]
        for user_id in expired:
            del self._expires_at[user_id]

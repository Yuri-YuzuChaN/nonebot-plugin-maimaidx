import importlib.util
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MODULE_PATH = (
    Path(__file__).parents[1] / "nonebot_plugin_maimaidx" / "lxns_oauth.py"
)
SPEC = importlib.util.spec_from_file_location("lxns_oauth", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"无法加载测试模块：{MODULE_PATH}")

lxns_oauth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lxns_oauth)


class AuthorizationCodeTest(unittest.TestCase):
    def test_extracts_legacy_code(self) -> None:
        code = "ABCD-EFGH-IJKL"
        self.assertEqual(lxns_oauth.extract_authorization_code(code), code)

    def test_extracts_current_code_without_changing_case(self) -> None:
        code = "ticc0aGpJz61vpUuXYuW7x6UIgt3rrrh"
        self.assertEqual(lxns_oauth.extract_authorization_code(code), code)

    def test_extracts_prefixed_code(self) -> None:
        code = "ticc0aGpJz61vpUuXYuW7x6UIgt3rrrh"
        self.assertEqual(
            lxns_oauth.extract_authorization_code(f"授权码：{code}"), code
        )

    def test_extracts_code_from_callback_url(self) -> None:
        code = "ticc0aGpJz61vpUuXYuW7x6UIgt3rrrh"
        callback_url = (
            "https://example.com/lxns/callback"
            f"?state=example&code={code}&source=qq"
        )
        self.assertEqual(
            lxns_oauth.extract_authorization_code(callback_url), code
        )

    def test_rejects_unrelated_input(self) -> None:
        invalid_values = (
            "",
            "今天天气不错",
            "abcdefghijklmnopqrstuvwx",
            "https://example.com/lxns/callback?state=example",
            "short-code",
        )
        for value in invalid_values:
            with self.subTest(value=value):
                self.assertIsNone(lxns_oauth.extract_authorization_code(value))

    def test_builds_encoded_authorize_url(self) -> None:
        authorize_url = lxns_oauth.build_authorize_url(
            "client id", "https://example.com/callback?from=qq"
        )
        parsed = urlparse(authorize_url)
        query = parse_qs(parsed.query)

        self.assertEqual(parsed.scheme, "https")
        self.assertEqual(parsed.netloc, "maimai.lxns.net")
        self.assertEqual(query["client_id"], ["client id"])
        self.assertEqual(
            query["redirect_uri"], ["https://example.com/callback?from=qq"]
        )
        self.assertEqual(
            query["scope"],
            ["read_player read_user_profile write_player"],
        )


class PendingBindingStoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.now = 100.0
        self.store = lxns_oauth.PendingBindingStore(
            ttl=10,
            clock=lambda: self.now,
        )

    def test_keeps_users_isolated(self) -> None:
        self.store.start(10001)

        self.assertTrue(self.store.is_active(10001))
        self.assertFalse(self.store.is_active(10002))

    def test_consumes_binding_once(self) -> None:
        self.store.start(10001)

        self.assertTrue(self.store.consume(10001))
        self.assertFalse(self.store.consume(10001))

    def test_expires_binding_at_deadline(self) -> None:
        self.store.start(10001)
        self.now += 10

        self.assertFalse(self.store.is_active(10001))
        self.assertFalse(self.store.consume(10001))

    def test_discard_removes_binding(self) -> None:
        self.store.start(10001)
        self.store.discard(10001)

        self.assertFalse(self.store.is_active(10001))


if __name__ == "__main__":
    unittest.main()

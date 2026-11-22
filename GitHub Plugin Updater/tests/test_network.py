import importlib.util
import io
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('network_core', ROOT / 'GitHub Plugin Updater/src/core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
API = 'https://api.github.com/repos/Example/Plugins/releases/latest'


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        core.FETCH_CACHE = Path(self.temp.name)
        core.API_TOKEN = ''
        self.opener = MagicMock()
        self.response = self.opener.open.return_value.__enter__.return_value
        self.response.url = API
        self.response.read.return_value = b'{}'
        mock = patch.object(core, 'build_opener', return_value=self.opener)
        self.factory = mock.start()
        self.addCleanup(mock.stop)

    def test_api_cache_persists_and_expires(self):
        self.assertEqual(core.fetch(API, 100), b'{}')
        core.fetch(API, 100)
        self.assertEqual(self.opener.open.call_count, 1)
        cached = next(core.FETCH_CACHE.rglob('*.json'))
        os.utime(cached, (time.time() - 301, time.time() - 301))
        core.fetch(API, 100)
        self.assertEqual(self.opener.open.call_count, 2)

    def test_token_only_sent_to_api_and_never_redirected(self):
        core.API_TOKEN = 'github_pat_test'
        core.fetch(API, 100)
        request = self.opener.open.call_args.args[0]
        self.assertEqual(request.get_header('Authorization'), 'Bearer github_pat_test')
        handler = self.factory.call_args.args[0]
        redirected = handler.redirect_request(request, None, 302, 'Found', {}, 'https://github.com/Example/Plugins')
        self.assertIsNone(redirected.get_header('Authorization'))
        self.response.url = 'https://github.com/Example/Plugins/releases/download/v1/tool.zip'
        core.fetch(self.response.url, 100)
        self.assertIsNone(self.opener.open.call_args.args[0].get_header('Authorization'))
        core.fetch(self.response.url, 100)
        self.assertEqual(self.opener.open.call_count, 3)

    def test_limit_cooldown_shared_across_repos_but_not_tokens(self):
        until = int(time.time()) + 3600
        self.opener.open.side_effect = HTTPError(API, 403, 'Forbidden', {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(until)}, io.BytesIO(b'{}'))
        with self.assertRaisesRegex(ValueError, 'GitHub API.*後重試'):
            core.fetch(API, 100)
        self.opener.open.side_effect = None
        with self.assertRaisesRegex(ValueError, 'GitHub API.*後重試'):
            core.fetch(API.replace('Example', 'Other'), 100)
        self.assertEqual(self.opener.open.call_count, 1)
        core.API_TOKEN = 'github_pat_test'
        core.fetch(API, 100)
        self.assertEqual(self.opener.open.call_count, 2)

    def test_secondary_limit_retry_after(self):
        self.opener.open.side_effect = HTTPError(API, 429, 'Too Many', {'Retry-After': '120'}, io.BytesIO(b'{}'))
        with self.assertRaisesRegex(ValueError, '限流'):
            core.fetch(API, 100)
        saved = json.loads(next(core.FETCH_CACHE.rglob('rate-limit.json')).read_text())
        self.assertGreater(saved['until'], time.time() + 110)

    def test_expired_cooldown_allows_retry(self):
        self.opener.open.side_effect = HTTPError(API, 403, 'Forbidden', {'X-RateLimit-Remaining': '0'}, io.BytesIO(b'{}'))
        with self.assertRaises(ValueError):
            core.fetch(API, 100)
        next(core.FETCH_CACHE.rglob('rate-limit.json')).write_text(json.dumps({'until': 0}))
        self.opener.open.side_effect = None
        core.fetch(API, 100)
        self.assertEqual(self.opener.open.call_count, 2)

    def test_non_rate_limit_403_not_mislabelled(self):
        self.opener.open.side_effect = HTTPError(API, 403, 'Forbidden', {}, io.BytesIO(b'access denied'))
        with self.assertRaises(HTTPError):
            core.fetch(API, 100)
        self.assertFalse(list(core.FETCH_CACHE.rglob('rate-limit.json')))

    def test_invalid_token_401_is_clear_without_echoing_secret(self):
        core.API_TOKEN = 'github_pat_test'
        self.opener.open.side_effect = HTTPError(API, 401, 'Unauthorized', {}, io.BytesIO(b'{}'))
        with self.assertRaisesRegex(ValueError, 'Token 無效或已到期') as error:
            core.fetch(API, 100)
        self.assertNotIn(core.API_TOKEN, str(error.exception))

    def test_token_validation_and_size_limit(self):
        self.assertEqual(core.validate_token(' github_pat_test '), 'github_pat_test')
        self.assertEqual(core.validate_token(''), '')
        with self.assertRaises(ValueError):
            core.validate_token('test\r\nOther: header')
        self.response.read.return_value = b'12345'
        with self.assertRaisesRegex(ValueError, '大小限制'):
            core.fetch(API, 4)
        self.assertFalse(list(core.FETCH_CACHE.rglob('*.json')))


if __name__ == '__main__':
    unittest.main()

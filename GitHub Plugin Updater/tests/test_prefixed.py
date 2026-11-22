import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('prefix_fixture', ROOT / 'GitHub Plugin Updater/src/core.py',
                                             submodule_search_locations=[str(ROOT / 'GitHub Plugin Updater/src')])
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
REPO = 'kiwidude68/calibre_plugins'
RULES = {'manage_series': 'Manage Series', 'count_pages': 'Count Pages'}


def release(tag, digest='sha256:' + 'a' * 64):
    return {'tag_name': tag, 'assets': [{'id': 123, 'name': tag + '.zip', 'size': 100, 'digest': digest,
                                       'browser_download_url': f'https://github.com/{REPO}/releases/download/{tag}/{tag}.zip'}]}


class PrefixTests(unittest.TestCase):
    def read(self, releases):
        return core.prefixed_entries(REPO, RULES, lambda *args: json.dumps(releases).encode())

    def test_pagination_and_numeric_versions_per_plugin(self):
        first = [{'tag_name': 'unrelated'}] * 99 + [release('manage_series-1.2')]
        second = [release('manage_series-1.10'), release('count_pages-2.0'),
                  dict(release('manage_series-99.0'), prerelease=True)]
        calls = []
        def get(url, limit):
            calls.append(url)
            return json.dumps(first if url.endswith('&page=1') else second).encode()
        entries = core.prefixed_entries(REPO, RULES, get)
        self.assertEqual({e['name']: e['version'] for e in entries}, {'Manage Series': [1, 10], 'Count Pages': [2, 0]})
        self.assertEqual(len(calls), 2)
        self.assertFalse(any('.zip' in url for url in calls))

    def test_optional_v_and_github_digest(self):
        entry = self.read([release('manage_series-v1.5.5')])[0]
        self.assertEqual(entry['version'], [1, 5, 5])
        self.assertEqual(entry['asset'], 'manage_series-v1.5.5.zip')
        self.assertEqual(entry['package_sha256'], 'a' * 64)
        self.assertTrue(entry['url'].endswith('calibre_asset=123'))

    def test_missing_latest_zip_does_not_fall_back_to_old_release(self):
        newest = release('manage_series-2.0'); newest['assets'] = []
        entry = self.read([release('manage_series-1.0'), newest])[0]
        self.assertEqual(entry['version'], [2, 0])
        self.assertIn('唯一', entry['error'])

    def test_duplicate_assets_and_ambiguous_aliases_are_rejected(self):
        item = release('manage_series-1.0'); item['assets'] *= 2
        self.assertIn('error', self.read([item])[0])
        self.assertIn('error', self.read([release('manage_series-1.0'), release('manage_series-v1.0')])[0])

    def test_missing_digest_falls_back_but_invalid_digest_is_error(self):
        self.assertIsNone(self.read([release('manage_series-1.0', None)])[0]['package_sha256'])
        self.assertIn('error', self.read([release('manage_series-1.0', 'sha256:wrong')])[0])

    def test_pagination_limit_does_not_return_partial_results(self):
        calls = []
        def get(url, limit):
            calls.append(url)
            return json.dumps([release('unknown-1.0')] * 100).encode()
        with self.assertRaises(ValueError):
            core.prefixed_entries(REPO, RULES, get)
        self.assertEqual(len(calls), 20)

    def test_saved_attachment_digest_short_circuits_version_comparison(self):
        entry = self.read([release('manage_series-1.0')])[0]
        current = {'Manage Series': {'version': [1, 0], 'sha256': 'b' * 64, 'identity': None}}
        binding = {'Manage Series': {'id': entry['id'], 'source': entry['source'],
                                    'accepted_sha256': 'b' * 64, 'package_sha256': 'a' * 64}}
        with patch.object(core, 'version', side_effect=AssertionError('不可比較版號')):
            row = core.plan(entry, current, binding, (9, 19), 'windows')
        self.assertEqual(row['status'], '附件相同')

    def test_same_name_keeps_source_binding_and_missing_digest_warning(self):
        entry = self.read([release('manage_series-2.0', None)])[0]
        current = {'Manage Series': {'version': [1, 0], 'sha256': 'b' * 64, 'identity': None}}
        binding = {'Manage Series': {'id': 'samlaio.manage-series', 'source': 'github:samlaio/calibremetadatimplode',
                                    'accepted_sha256': 'b' * 64}}
        self.assertEqual(core.plan(entry, current, binding, (9, 19), 'windows')['status'], '已綁定其他來源')
        binding['Manage Series'].update(id=entry['id'], source=entry['source'])
        row = core.plan(entry, current, binding, (9, 19), 'windows')
        self.assertTrue(row['eligible'])
        self.assertIn('未提供附件 SHA', row['status'])

    def test_known_repository_routes_to_prefix_rules(self):
        calls = []
        def get(url, limit):
            calls.append(url)
            return b'[]'
        self.assertEqual(core.release_entries('https://github.com/' + REPO, get), [])
        self.assertIn('per_page=100&page=1', calls[0])


if __name__ == '__main__':
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PrefixTests)).wasSuccessful())

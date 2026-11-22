import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('updater_core', ROOT / 'GitHub Plugin Updater/src/core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)
REPO = 'Example/Plugins'
SOURCE = 'github:example/plugins'


def entry():
    return {'id': 'example.tool', 'name': 'Example Tool', 'version': [1, 2],
            'minimum_calibre_version': [9, 19, 0], 'supported_platforms': ['windows', 'osx', 'linux'],
            'sha256': 'a' * 64, 'package_sha256': 'c' * 64, 'size': 100, 'asset': 'tool.zip', 'repo': REPO,
            'source': SOURCE, 'url': 'https://github.com/Example/Plugins/releases/download/v1/tool.zip'}


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.entry = entry()
        self.local = {'Example Tool': {'version': [1, 1], 'sha256': 'b' * 64,
                                       'identity': {'id': 'example.tool', 'source': SOURCE}}}
        self.bindings = {'Example Tool': {'id': 'example.tool', 'source': SOURCE}}

    def plan(self, **changes):
        self.entry.update(changes)
        return core.plan(self.entry, self.local, self.bindings, (9, 19, 0), 'windows')

    def test_sha_equal_does_not_compare_version(self):
        self.local['Example Tool']['sha256'] = 'a' * 64
        with patch.object(core, 'version', side_effect=AssertionError('不應檢查版號')):
            self.assertEqual(self.plan()['status'], '內容相同')

    def test_different_sha_newer_same_and_older(self):
        self.assertEqual(self.plan()['status'], '可更新')
        self.assertFalse(self.plan(version=[1, 1])['eligible'])
        self.assertEqual(self.plan()['status'], '同版內容不符，請來源修正版號')
        self.assertFalse(self.plan(version=[1, 0])['eligible'])

    def test_source_binding_and_explicit_switch(self):
        self.bindings['Example Tool']['source'] = 'github:another/repo'
        self.assertEqual(self.plan()['status'], '已綁定其他來源')
        self.bindings.clear()
        self.local['Example Tool']['identity'] = None
        self.assertEqual(self.plan()['status'], '需要綁定來源')
        self.bindings['Example Tool'] = {'id': 'example.tool', 'source': SOURCE, 'accepted_sha256': 'b' * 64}
        self.assertTrue(self.plan()['eligible'])
        self.local['Example Tool']['sha256'] = 'c' * 64
        self.assertEqual(self.plan()['status'], '安裝來源已變更，請重新綁定')

    def test_missing_and_incompatible_not_updated(self):
        self.assertFalse(self.plan(minimum_calibre_version=[10, 0])['eligible'])
        self.assertFalse(self.plan(minimum_calibre_version=[9, 19], supported_platforms=['osx'])['eligible'])
        self.local.clear()
        self.assertFalse(self.plan()['eligible'])

    def manifest(self):
        return {'format': core.FORMAT, 'schema': 1, 'source': SOURCE, 'plugins': [copy.deepcopy(self.entry)]}

    def test_manifest_rejects_duplicates_and_invalid_data(self):
        core.manifest(self.manifest(), REPO)
        invalid = [('sha256', 'oops'), ('version', [True]), ('size', -1), ('asset', '../tool.zip'),
                   ('minimum_calibre_version', []), ('supported_platforms', ['unknown']), ('id', '../../tool')]
        for key, value in invalid:
            data = self.manifest(); data['plugins'][0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                core.manifest(data, REPO)
        data = self.manifest(); data['plugins'] *= 2
        with self.assertRaises(ValueError):
            core.manifest(data, REPO)
        with self.assertRaises(ValueError):
            core.manifest(self.manifest(), 'Another/Repo')

    def test_check_fetches_json_only(self):
        calls = []
        prefix = 'https://github.com/Example/Plugins/releases/download/v1/'
        release = {'assets': [{'name': 'plugins.json', 'browser_download_url': prefix + 'plugins.json'},
                              {'name': 'tool.zip', 'size': 100, 'browser_download_url': prefix + 'tool.zip'}]}
        def get(url, limit):
            calls.append(url)
            return json.dumps(release if '/releases/latest' in url else self.manifest()).encode()
        self.assertEqual(len(core.release_entries(REPO, get)), 1)
        self.assertEqual(len(calls), 2)
        self.assertFalse(any(url.endswith('.zip') for url in calls))

    def test_foreign_assets_and_unpublished_manifest_rejected(self):
        with self.assertRaises(ValueError):
            core.release_entries(REPO, lambda *args: b'{"assets":[]}')
        data = {'assets': [{'name': 'plugins.json', 'browser_download_url': 'https://evil.example/plugins.json'}]}
        with self.assertRaises(ValueError):
            core.release_entries(REPO, lambda *args: json.dumps(data).encode())

    def test_github_space_to_dot_attachment_names(self):
        self.entry['asset'] = 'Example Tool.zip'
        prefix = 'https://github.com/Example/Plugins/releases/download/v1/'
        release = {'assets': [{'name': 'plugins.json', 'browser_download_url': prefix + 'plugins.json'},
                              {'name': 'Example.Tool.zip', 'size': 100,
                               'browser_download_url': prefix + 'Example.Tool.zip'}]}
        def get(url, limit):
            return json.dumps(release if '/releases/latest' in url else self.manifest()).encode()
        entries = core.release_entries(REPO, get)
        self.assertEqual(entries[0]['asset'], 'Example Tool.zip')
        self.assertTrue(entries[0]['url'].endswith('/Example.Tool.zip'))

    def test_network_and_repository_boundaries(self):
        self.assertEqual(core.repository('https://github.com/Example/Plugins/'), REPO)
        for value in ['https://evil.example/x/y', 'a/..', 'a/b/c', '']:
            with self.assertRaises(ValueError): core.repository(value)
        for value in ['http://github.com/x', 'https://evil.example/x', 'https://github.com@localhost/x', 'https://github.com:444/x']:
            with self.assertRaises(ValueError): core.github_url(value)

    def test_hash_and_identity(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'dist') as temp:
            path = Path(temp) / 'tool.zip'
            with ZipFile(path, 'w') as z:
                z.writestr(core.IDENTITY, json.dumps({'id': 'example.tool', 'source': SOURCE, 'sha256': 'a' * 64}))
            self.assertEqual(len(core.digest(path)), 64)
            self.assertEqual(core.identity(path)['source'], SOURCE)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CoreTests)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())

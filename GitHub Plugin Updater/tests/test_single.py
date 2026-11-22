import importlib.util
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('single_fixture', ROOT / 'GitHub Plugin Updater/src/core.py',
                                             submodule_search_locations=[str(ROOT / 'GitHub Plugin Updater/src')])
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
spec.loader.exec_module(core)
from single_fixture.singles import SINGLE_RULES
REPO = 'HamsterExAstris/calibre-azw6-image-merge'
RULE = SINGLE_RULES[REPO.lower()]


def release(tag='v1.0.0', stamp=None):
    return {'tag_name': tag, 'assets': [{'id': 100, 'name': 'AZW6ImageMerge.zip', 'size': 100, 'digest': stamp,
                                       'browser_download_url': f'https://github.com/{REPO}/releases/download/{tag}/AZW6ImageMerge.zip'}]}


class SingleTests(unittest.TestCase):
    def read(self, data):
        return core.single_entries(REPO, RULE, lambda *args: json.dumps(data).encode())[0]

    def local(self, entry, number):
        current = {entry['name']: {'version': number, 'identity': None, 'sha256': 'b' * 64}}
        binding = {entry['name']: {'id': entry['id'], 'source': entry['source'], 'accepted_sha256': 'b' * 64}}
        return current, binding

    def test_builtin_route_reads_one_json_without_downloading_zip(self):
        calls = []
        def get(url, limit):
            calls.append(url)
            return json.dumps(release()).encode()
        entries = core.release_entries('https://github.com/' + REPO + '/releases', get)
        self.assertEqual(len(calls), 1)
        self.assertTrue(calls[0].endswith('/releases/latest'))
        self.assertEqual(entries[0]['name'], 'AZW6 Image Merge')
        self.assertEqual(entries[0]['mode'], 'single')

    def test_optional_v_and_fixed_attachment_name(self):
        for tag in ['v1.2.10', '1.2.10']:
            entry = self.read(release(tag))
            self.assertEqual(entry['version'], [1, 2, 10])
            self.assertEqual(entry['asset'], 'AZW6ImageMerge.zip')
            self.assertIsNone(entry['package_sha256'])

    def test_no_digest_compares_version_and_warns(self):
        entry = self.read(release())
        current, binding = self.local(entry, [0, 9])
        row = core.plan(entry, current, binding, (9, 19), 'windows')
        self.assertTrue(row['eligible'])
        self.assertIn('未提供附件 SHA', row['status'])
        current[entry['name']]['version'] = [1, 0, 0, 1]
        self.assertIn('遠端較舊', core.plan(entry, current, binding, (9, 19), 'windows')['status'])

    def test_changed_asset_id_is_not_a_hash_match(self):
        entry = self.read(release())
        current, binding = self.local(entry, [1, 0, 0])
        binding[entry['name']]['asset_id'] = 99
        row = core.plan(entry, current, binding, (9, 19), 'windows')
        self.assertIn('附件已更換', row['status'])
        self.assertIn('未提供附件 SHA', row['status'])
        self.assertFalse(row['eligible'])

    def test_missing_duplicate_or_source_archive_is_not_selected(self):
        for assets in [[], release()['assets'] * 2, [{'name': 'source.zip'}]]:
            data = release(); data['assets'] = assets
            self.assertIn('error', self.read(data))

    def test_invalid_tag_and_nonfinal_release_are_rejected(self):
        for data in [release('stable'), dict(release(), draft=True), dict(release(), prerelease=True)]:
            with self.assertRaises(ValueError):
                self.read(data)

    def test_digest_can_short_circuit_version_comparison(self):
        entry = self.read(release(stamp='sha256:' + 'a' * 64))
        current, binding = self.local(entry, [1, 0, 0])
        binding[entry['name']]['package_sha256'] = 'a' * 64
        with patch.object(core, 'version', side_effect=AssertionError('不應比較版號')):
            row = core.plan(entry, current, binding, (9, 19), 'windows')
        self.assertEqual(row['status'], '附件相同')
        self.assertIn('error', self.read(release(stamp='sha256:invalid')))

    def test_same_name_preserves_other_source_binding(self):
        entry = self.read(release())
        current, binding = self.local(entry, [1, 0, 0])
        binding[entry['name']].update(id='samlaio.azw6-image-merge', source='github:samlaio/calibremetadatimplode')
        self.assertEqual(core.plan(entry, current, binding, (9, 19), 'windows')['status'], '已綁定其他來源')

    def test_foreign_download_is_rejected(self):
        data = release()
        data['assets'][0]['browser_download_url'] = 'https://example.com/AZW6ImageMerge.zip'
        self.assertIn('error', self.read(data))


if __name__ == '__main__':
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SingleTests)).wasSuccessful())

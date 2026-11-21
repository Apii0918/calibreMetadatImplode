"""Run with calibre-debug in a fresh dist/ configuration, never the real profile."""
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir
if ROOT / 'dist' not in Path(config_dir).resolve().parents:
    raise RuntimeError('請使用 dist 下的獨立設定目錄')
from calibre.customize import ui as api
from calibre_plugins.plugin_backup import core


class CalibreBackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for p in list(core.installed_plugins()):
            if p['name'].startswith('PB Test '):
                api.remove_plugin(p['name'])
        self.a = self.package('PB Test A', (1, 0, 0), 'pb_test_a')
        self.b = self.package('PB Test B', (2, 0, 0), 'pb_test_b')
        api.add_plugin(str(self.a))
        api.add_plugin(str(self.b))
        api.disable_plugin('PB Test B')
        self.backup = self.root / 'backup.zip'

    def package(self, name, version, marker, minimum=(9, 19, 0)):
        path = self.root / (name + '-' + '.'.join(map(str, version)) + '.zip')
        with ZipFile(path, 'w') as z:
            z.writestr('plugin-import-name-' + marker + '.txt', '')
            z.writestr('__init__.py', f"from calibre.customize import FileTypePlugin\nclass TestPlugin(FileTypePlugin):\n    name = {name!r}\n    version = {version!r}\n    author = 'Test only'\n    supported_platforms = ['windows', 'osx', 'linux']\n    minimum_calibre_version = {minimum!r}\n    file_types = {{'epub'}}\n")
        return path

    def test_inventory_and_enabled_state_roundtrip(self):
        entries = core.installed_plugins()
        self.assertEqual({p['name'] for p in entries}, {'PB Test A', 'PB Test B', 'Plugin Backup'})
        core.export_backup(self.backup, entries)
        api.add_plugin(str(self.package('PB Test A', (9, 0, 0), 'pb_test_a')))
        api.enable_plugin('PB Test B')
        api.add_plugin(str(self.package('PB Test Extra', (1, 0, 0), 'pb_test_extra')))
        result = core.import_backup(self.backup)
        self.assertFalse(result['failed'], result)
        self.assertEqual(api.find_plugin('PB Test A').version, (1, 0, 0))
        self.assertTrue(api.is_disabled('PB Test B'))
        self.assertIsNotNone(api.find_plugin('PB Test Extra'))

    def test_failed_install_restores_existing_package(self):
        entries = [p for p in core.installed_plugins() if p['name'] == 'PB Test A']
        core.export_backup(self.backup, entries)
        original = Path(entries[0]['path']).read_bytes()
        registry = dict(api.config['plugins'])
        def fail(path):
            Path(entries[0]['path']).write_bytes(b'broken install')
            raise OSError('simulated install failure')
        with patch.object(api, 'add_plugin', side_effect=fail):
            result = core.import_backup(self.backup)
        self.assertEqual(len(result['failed']), 1)
        self.assertEqual(Path(entries[0]['path']).read_bytes(), original)
        self.assertEqual(api.config['plugins'], registry)

    def test_incompatible_version_is_skipped(self):
        bad = self.package('PB Test A', (3, 0, 0), 'pb_test_a', minimum=(999, 0, 0))
        core.export_backup(self.backup, [{'name': 'PB Test A', 'version': [3, 0, 0], 'enabled': True, 'path': str(bad)}])
        before = (Path(api.plugin_dir) / 'PB Test A.zip').read_bytes()
        result = core.import_backup(self.backup)
        self.assertEqual(len(result['failed']), 1)
        self.assertEqual((Path(api.plugin_dir) / 'PB Test A.zip').read_bytes(), before)

    def test_settings_optional_and_customizations(self):
        setting = Path(config_dir) / 'plugins/pb-test-settings.json'
        setting.write_text('{"value":"backup"}', 'utf-8')
        api.config['plugin_customization'] = {'PB Test A': 'backup-custom'}
        api.disable_plugin('KoboTouch')
        core.export_backup(self.backup, core.installed_plugins(), settings_dir=config_dir,
                           customizations={'PB Test A': 'backup-custom'},
                           builtin_states={'enabled': [], 'disabled': ['KoboTouch']})
        setting.write_text('{"value":"local"}', 'utf-8')
        api.config['plugin_customization'] = {'PB Test A': 'local-custom'}
        api.enable_plugin('KoboTouch')
        result = core.import_backup(self.backup, include_settings=False)
        self.assertFalse(result['failed'], result)
        self.assertFalse(result['settings_restored'])
        self.assertFalse(api.is_disabled('KoboTouch'))
        self.assertEqual(json.loads(setting.read_text())['value'], 'local')
        result = core.import_backup(self.backup, include_settings=True)
        self.assertFalse(result['failed'], result)
        self.assertTrue(result['settings_restored'])
        self.assertTrue(api.is_disabled('KoboTouch'))
        self.assertEqual(json.loads(setting.read_text())['value'], 'backup')
        self.assertEqual(api.config['plugin_customization']['PB Test A'], 'backup-custom')


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CalibreBackupTests))
raise SystemExit(0 if result.wasSuccessful() else 1)

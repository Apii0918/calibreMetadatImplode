import importlib.util
import io
import json
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('plugin_backup_core', ROOT / 'Plugin Backup/src/core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.plugin = self.root / 'test.zip'
        with ZipFile(self.plugin, 'w') as z:
            z.writestr('__init__.py', 'raise RuntimeError("inspection must not execute me")')
        self.entries = [{'name': '測試外掛', 'version': [1, 0, 0], 'enabled': False, 'path': str(self.plugin)}]
        self.backup = self.root / 'backup.zip'

    def rewrite(self, change, extras=None):
        with ZipFile(self.backup) as z:
            files = {n: z.read(n) for n in z.namelist()}
        manifest = json.loads(files['manifest.json'])
        change(manifest)
        files['manifest.json'] = json.dumps(manifest).encode()
        files.update(extras or {})
        with ZipFile(self.backup, 'w') as z:
            for n, data in files.items():
                z.writestr(n, data)

    def test_selected_settings_excludes_other_plugins_and_shared_settings(self):
        config = self.root / 'config'
        (config / 'plugins').mkdir(parents=True)
        with ZipFile(self.plugin, 'w') as z:
            z.writestr('__init__.py', "prefs = JSONConfig('plugins/private_test')")
        for name in ('private_test', 'other', '測試外掛'):
            (config / 'plugins' / (name + '.json')).write_text('{}', 'utf-8')
        (config / 'gui.json').write_text('{}', 'utf-8')
        core.export_backup(self.backup, self.entries, settings_dir=config,
                           customizations={'測試外掛': 'yes'}, selected_settings=True)
        settings = core.inspect_backup(self.backup)['settings']
        self.assertEqual({f['path'] for f in settings['files']},
                         {'plugins/private_test.json', 'plugins/測試外掛.json'})
        self.assertNotIn('builtin_states', settings)
        core.export_backup(self.backup, self.entries, settings_dir=config)
        self.assertEqual(len(core.inspect_backup(self.backup)['settings']['files']), 4)

    def test_packages_and_state_without_settings(self):
        core.export_backup(self.backup, self.entries)
        manifest = core.inspect_backup(self.backup)
        self.assertEqual(manifest['plugins'][0]['name'], '測試外掛')
        self.assertFalse(manifest['plugins'][0]['enabled'])
        self.assertNotIn('settings', manifest)

    def test_optional_settings_and_local_library_path(self):
        config = self.root / 'config'
        (config / 'plugins').mkdir(parents=True)
        (config / 'caches').mkdir()
        (config / 'Library').mkdir()
        (config / 'Library/metadata.db').write_bytes(b'library database')
        (config / 'Library/book.epub').write_bytes(b'private book')
        (config / 'plugins/account.json').write_text('{"key":"example-only"}', 'utf-8')
        (config / 'plugins/Installed.zip').write_bytes(b'not a setting')
        (config / 'caches/cache.bin').write_bytes(b'cache')
        (config / 'customize.py.json').write_text('{"plugins":{}}', 'utf-8')
        (config / 'global.py.json').write_text('{"library_path":"old-machine","language":"zh_TW"}', 'utf-8')
        core.export_backup(self.backup, self.entries, settings_dir=config, customizations={'測試外掛': 'custom'})
        manifest = core.inspect_backup(self.backup)
        paths = {e['path'] for e in manifest['settings']['files']}
        self.assertEqual(paths, {'plugins/account.json', 'global.py.json'})
        (config / 'plugins/account.json').write_text('{}', 'utf-8')
        (config / 'global.py.json').write_text('{"library_path":"this-machine"}', 'utf-8')
        with ZipFile(self.backup) as z:
            core.restore_settings(z, manifest['settings'], config)
        self.assertEqual(json.loads((config / 'global.py.json').read_text())['library_path'], 'this-machine')
        self.assertIn('example-only', (config / 'plugins/account.json').read_text())

    def test_tampering_and_unsafe_package_paths(self):
        core.export_backup(self.backup, self.entries)
        self.rewrite(lambda m: m['plugins'][0].update(sha256='0' * 64))
        with self.assertRaisesRegex(ValueError, '校驗失敗'):
            core.inspect_backup(self.backup)
        core.export_backup(self.backup, self.entries)
        self.rewrite(lambda m: m['plugins'][0].update(package='../outside.zip'))
        with self.assertRaisesRegex(ValueError, '路徑無效'):
            core.inspect_backup(self.backup)

    def test_setting_path_and_registry_protection(self):
        for relative in ('../outside', '/absolute', 'C:/outside', 'customize.py.json', 'plugins/Injected.zip', 'Plugins/Injected.zip', 'NUL.json'):
            core.export_backup(self.backup, self.entries)
            data = b'{}'
            def change(m):
                m['settings'] = {'files': [{'path': relative, 'sha256': core.hashlib.sha256(data).hexdigest()}], 'customizations': {}}
            self.rewrite(change, {'settings/' + relative: data})
            with self.assertRaises(ValueError, msg=relative):
                core.inspect_backup(self.backup)

    def test_duplicate_names_and_unknown_formats(self):
        core.export_backup(self.backup, self.entries)
        self.rewrite(lambda m: m['plugins'].append(dict(m['plugins'][0])))
        with self.assertRaisesRegex(ValueError, '重複'):
            core.inspect_backup(self.backup)
        core.export_backup(self.backup, self.entries)
        self.rewrite(lambda m: m.update(version=99))
        with self.assertRaisesRegex(ValueError, '格式'):
            core.inspect_backup(self.backup)

    def test_export_failure_keeps_previous_backup(self):
        self.backup.write_bytes(b'original backup')
        self.entries[0]['path'] = str(self.root / 'missing.zip')
        with self.assertRaises(OSError):
            core.export_backup(self.backup, self.entries)
        self.assertEqual(self.backup.read_bytes(), b'original backup')
        self.assertFalse(list(self.root.glob('.plugin-backup-*')))

    def test_settings_write_failure_rolls_back(self):
        config = self.root / 'config'
        config.mkdir()
        for n in ('a.json', 'b.json'):
            (config / n).write_bytes(b'new')
        core.export_backup(self.backup, self.entries, settings_dir=config)
        manifest = core.inspect_backup(self.backup)
        for n in ('a.json', 'b.json'):
            (config / n).write_bytes(b'old')
        replace = core.os.replace
        def fail_second(source, destination):
            if Path(destination).name == 'b.json':
                raise OSError('simulated write failure')
            return replace(source, destination)
        with ZipFile(self.backup) as z, patch.object(core.os, 'replace', side_effect=fail_second):
            with self.assertRaises(OSError):
                core.restore_settings(z, manifest['settings'], config)
        self.assertEqual((config / 'a.json').read_bytes(), b'old')
        self.assertEqual((config / 'b.json').read_bytes(), b'old')

    def test_names_sizes_and_unlisted_files(self):
        for name in ('../bad', 'CON', 'bad/name', 'bad\\name', 'NUL.zip'):
            with self.assertRaises(ValueError):
                core.check_name(name)
        with patch.object(core, 'MAX_PACKAGE', 2):
            with self.assertRaises(ValueError):
                core.export_backup(self.backup, self.entries)
        core.export_backup(self.backup, self.entries)
        self.rewrite(lambda m: None, {'extra.txt': b'extra'})
        with self.assertRaisesRegex(ValueError, '清單以外'):
            core.inspect_backup(self.backup)

    def test_failed_rollback_keeps_recovery_files(self):
        config = self.root / 'config'
        config.mkdir()
        for name in ('a.json', 'b.json'):
            (config / name).write_bytes(b'new')
        core.export_backup(self.backup, self.entries, settings_dir=config)
        manifest = core.inspect_backup(self.backup)
        for name in ('a.json', 'b.json'):
            (config / name).write_bytes(b'old')
        replace, copy = core.os.replace, core.shutil.copyfile
        def fail_write(source, destination):
            if Path(destination).name == 'b.json':
                raise OSError('write failed')
            return replace(source, destination)
        def fail_rollback(source, destination):
            if Path(source).name == '0' and Path(destination).name == 'a.json':
                raise OSError('rollback failed')
            return copy(source, destination)
        with ZipFile(self.backup) as z, patch.object(core.os, 'replace', side_effect=fail_write), patch.object(core.shutil, 'copyfile', side_effect=fail_rollback):
            with self.assertRaisesRegex(RuntimeError, '原檔保存在'):
                core.restore_settings(z, manifest['settings'], config)
        recovery = next(config.glob('.plugin-backup-recovery-*'))
        self.assertEqual((recovery / '0').read_bytes(), b'old')
        self.assertIn('a.json', (recovery / 'paths.json').read_text())


if __name__ == '__main__':
    unittest.main()

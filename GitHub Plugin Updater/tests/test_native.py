"""Run with calibre-debug and CALIBRE_CONFIG_DIRECTORY inside dist/."""
import copy
import hashlib
import importlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from calibre.gui2 import Application
from calibre.customize.ui import add_plugin, config, disable_plugin, is_disabled, plugin_dir
from calibre.utils.config import config_dir
from qt.core import QEventLoop, QTimer, Qt

ROOT = Path(__file__).resolve().parents[2]
if not Path(config_dir).resolve().is_relative_to((ROOT / 'dist').resolve()):
    raise RuntimeError('測試僅能使用 dist 下的隔離設定。')
app = Application([])
plugin = add_plugin(str(ROOT / 'dist/GitHub Plugin Updater-zh_TW-release.zip'))
core = importlib.import_module('calibre_plugins.github_plugin_updater.core')
ui = importlib.import_module('calibre_plugins.github_plugin_updater.ui')
SOURCE = 'github:example/plugins'
NAME = 'Updater Native Fixture'


def package(path, version, source=SOURCE):
    with ZipFile(path, 'w') as z:
        z.writestr('__init__.py', f'''from calibre.customize import InterfaceActionBase
class Fixture(InterfaceActionBase):
 name={NAME!r}
 version={version!r}
 author='Test'
 supported_platforms=['windows','osx','linux']
 minimum_calibre_version=(9,19,0)
''')
    content_sha = core.payload_digest(path)
    with ZipFile(path, 'a') as z:
        z.writestr(core.IDENTITY, json.dumps({'id': 'example.fixture', 'source': source, 'sha256': content_sha}))
    return path.read_bytes()


class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        old = self.root / 'old.zip'
        package(old, (0, 1))
        add_plugin(str(old))
        disable_plugin(NAME)
        self.old_sha = core.payload_digest(Path(plugin_dir) / (NAME + '.zip'))
        self.old_package_sha = core.digest(Path(plugin_dir) / (NAME + '.zip'))
        self.data = package(self.root / 'new.zip', (0, 2))
        self.entry = dict(id='example.fixture', source=SOURCE, name=NAME, version=[0, 2],
                          minimum_calibre_version=[9, 19, 0], supported_platforms=['windows', 'osx', 'linux'],
                          size=len(self.data), sha256=core.payload_digest(self.root / 'new.zip'),
                          package_sha256=hashlib.sha256(self.data).hexdigest(), asset='tool.zip',
                          observed_sha256=self.old_sha, repo='Example/Plugins',
                          url='https://github.com/Example/Plugins/releases/download/v1/tool.zip')
        self.bindings = {NAME: {'id': 'example.fixture', 'source': SOURCE}}

    def run_install(self, data=None):
        return core.install([self.entry], self.bindings, self.root / 'backups', lambda *args: self.data if data is None else data)

    def test_no_backup_install_leaves_no_recovery_files(self):
        result = core.install([self.entry], self.bindings, self.root / 'backups', lambda *a: self.data, auto_backup=False)
        self.assertEqual(result['installed'], [NAME])
        self.assertEqual(result['backups'], [])
        self.assertFalse((self.root / 'backups').exists())
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.entry['package_sha256'])
        self.assertTrue(is_disabled(NAME))

    def test_no_backup_failure_still_rolls_back(self):
        before = dict(config['plugins'])
        def fail(path):
            Path(plugin_dir, NAME + '.zip').write_bytes(b'broken')
            config['plugins'] = {}
            raise RuntimeError('模擬無備份安裝失敗')
        with patch('calibre.customize.ui.add_plugin', side_effect=fail):
            result = core.install([self.entry], self.bindings, None, lambda *a: self.data, auto_backup=False)
        self.assertIn('模擬無備份安裝失敗', result['failed'][0])
        self.assertEqual(result['backups'], [])
        self.assertEqual(dict(config['plugins']), before)
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)
        self.assertTrue(is_disabled(NAME))

    def test_auto_backup_checkbox_persists_and_install_job_uses_it(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        self.addCleanup(lambda: dialog.prefs.__setitem__('auto_backup', True))
        dialog.auto_backup.setChecked(False)
        self.assertFalse(dialog.prefs['auto_backup'])
        reopened = ui.UpdaterDialog(None)
        self.addCleanup(reopened.close)
        self.assertFalse(reopened.auto_backup.isChecked())
        with patch.object(dialog, 'selected', return_value=[dict(self.entry, status='可更新')]), patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.StandardButton.Yes) as confirm, patch.object(dialog, 'start') as start:
            dialog.install_selected()
        self.assertIs(start.call_args.args[0]['auto_backup'], False)
        self.assertIn('不保留更新前備份', confirm.call_args.args[2])
        reopened.auto_backup.setChecked(True)
        self.assertTrue(reopened.prefs['auto_backup'])

    def test_token_dialog_masks_saves_clears_and_preserves_sources(self):
        dialog = ui.UpdaterDialog(None)
        dialog.prefs['sources'] = ['https://github.com/Example/Plugins']
        def accept(widget):
            field = widget.findChild(ui.QLineEdit)
            self.assertEqual(field.echoMode(), ui.QLineEdit.EchoMode.Password)
            field.setText(' github_pat_fixture ')
            return ui.QDialog.DialogCode.Accepted
        with patch.object(ui.QDialog, 'exec', accept):
            dialog.edit_token()
        self.assertEqual(dialog.prefs['github_token'], 'github_pat_fixture')
        with patch.object(ui.QDialog, 'exec', return_value=ui.QDialog.DialogCode.Rejected):
            dialog.edit_token()
        self.assertEqual(dialog.prefs['github_token'], 'github_pat_fixture')
        def clear(widget):
            widget.findChild(ui.QLineEdit).clear()
            return ui.QDialog.DialogCode.Accepted
        with patch.object(ui.QDialog, 'exec', clear):
            dialog.edit_token()
        self.assertEqual(dialog.prefs['github_token'], '')
        self.assertEqual(dialog.prefs['sources'], ['https://github.com/Example/Plugins'])
        dialog.close()

    def test_sources_dialog_has_token_button_in_footer(self):
        dialog = ui.UpdaterDialog(None)
        def inspect(widget):
            buttons = [b for b in widget.findChildren(ui.QPushButton) if b.text() == '設定 GitHub Token']
            self.assertEqual(len(buttons), 1)
            footer = widget.layout().itemAt(widget.layout().count() - 1).layout()
            self.assertIs(footer.itemAt(0).widget(), buttons[0])
            return ui.QDialog.DialogCode.Rejected
        with patch.object(ui.QDialog, 'exec', inspect):
            dialog.edit_sources()
        dialog.close()

    def test_native_install_preserves_disabled_and_recovery_package(self):
        result = self.run_install()
        self.assertEqual(result['installed'], [NAME], result)
        self.assertTrue(is_disabled(NAME))
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.entry['package_sha256'])
        backup = Path(result['backups'][0])
        self.assertEqual(core.digest(backup / (NAME + '-0.1.zip')), self.old_package_sha)
        self.assertEqual(json.loads((backup / 'state.json').read_text(encoding='utf-8'))['name'], NAME)
        self.assertEqual(self.bindings[NAME]['accepted_sha256'], self.entry['sha256'])

    def test_hash_mismatch_does_not_load_or_install(self):
        with patch('calibre.customize.ui.load_plugin', side_effect=AssertionError('不可載入')):
            result = self.run_install(b'wrong')
        self.assertEqual(result['installed'], [])
        self.assertIn('SHA-256', result['failed'][0])
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)

    def test_identity_mismatch_rejected_before_loading(self):
        self.data = package(self.root / 'wrong.zip', (0, 2), 'github:other/repo')
        self.entry.update(size=len(self.data), sha256=core.payload_digest(self.root / 'wrong.zip'), package_sha256=hashlib.sha256(self.data).hexdigest())
        with patch('calibre.customize.ui.load_plugin', side_effect=AssertionError('不可載入')):
            result = self.run_install()
        self.assertIn('身分', result['failed'][0])

    def test_declaration_mismatch_keeps_old_package(self):
        self.entry['version'] = [0, 3]
        result = self.run_install()
        self.assertIn('版號', result['failed'][0])
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)
        self.assertTrue(Path(result['backups'][0], NAME + '-0.1.zip').exists())

    def test_partial_install_failure_rolls_back_registry_and_package(self):
        before = dict(config['plugins'])
        def fail(path):
            Path(plugin_dir, NAME + '.zip').write_bytes(b'broken')
            config['plugins'] = {}
            raise RuntimeError('模擬安裝失敗')
        with patch('calibre.customize.ui.add_plugin', side_effect=fail):
            result = self.run_install()
        self.assertIn('模擬安裝失敗', result['failed'][0])
        self.assertEqual(dict(config['plugins']), before)
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)
        self.assertTrue(is_disabled(NAME))

    def test_changed_local_package_is_not_overwritten(self):
        self.entry['observed_sha256'] = '0' * 64
        with patch.object(core, 'fetch', side_effect=AssertionError('不可下載')):
            result = self.run_install()
        self.assertIn('已變更', result['failed'][0])

    def test_installed_inventory_reads_identity_sha_without_rescanning(self):
        with patch.object(core, 'payload_digest', side_effect=AssertionError('不應掃描內容')):
            current = core.installed_plugins()[NAME]
        self.assertEqual(current['sha256'], self.old_sha)
        self.assertNotIn('error', current)

    def test_multiple_sources_failure_isolated_and_binding_remembered(self):
        current = {NAME: {'version': [0, 1], 'sha256': self.old_sha,
                          'identity': {'id': 'example.fixture', 'source': SOURCE}}}
        def entries(repo):
            if repo == 'Bad/Repo': raise ValueError('來源離線')
            return [self.entry]
        bindings = {}
        with patch.object(core, 'installed_plugins', return_value=current), patch.object(core, 'release_entries', side_effect=entries):
            result = core.check(['Bad/Repo', 'Example/Plugins'], bindings)
        self.assertEqual(len(result['errors']), 1)
        self.assertTrue(result['rows'][0]['eligible'])
        self.assertEqual(bindings[NAME]['source'], SOURCE)

    def test_dialog_and_real_background_check_without_network(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        self.assertEqual(dialog.prefs.get('sources', [core.DEFAULT_REPO]), [core.DEFAULT_REPO])
        self.assertFalse(dialog.restart_button.isEnabled())
        dialog.rows = [dict(self.entry, current=[0, 1], status='可更新', eligible=True)]
        dialog.show_rows()
        dialog.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        self.assertEqual(dialog.selected()[0]['name'], NAME)
        dialog.start({'mode': 'check', 'sources': []})
        loop = QEventLoop()
        timer = QTimer()
        timer.timeout.connect(lambda: loop.quit() if dialog.process is None else None)
        timer.start(20)
        QTimer.singleShot(15000, loop.quit)
        loop.exec()
        timer.stop()
        self.assertIsNone(dialog.process)
        self.assertIn('檢查完成', dialog.status.text())
        self.assertEqual(dialog.rows, [])

    def test_header_toggles_all_selectable_rows(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, current=[0, 1], status='可更新', eligible=True)
        dialog.rows = [base, dict(base), dict(base, current=None, installed=False)]
        dialog.show_rows()
        header = dialog.table.horizontalHeader()
        self.assertEqual(dialog.table.horizontalHeaderItem(0).text(), '全選')
        header.sectionClicked.emit(0)
        self.assertEqual(len(dialog.selected()), 2)
        header.sectionClicked.emit(0)
        self.assertEqual(dialog.selected(), [])
        dialog.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        header.sectionClicked.emit(0)
        self.assertEqual(len(dialog.selected()), 2)
        header.sectionClicked.emit(1)
        self.assertEqual(len(dialog.selected()), 2)

    def test_native_preferences_entry_has_no_toolbar_action(self):
        from calibre.customize import InterfaceActionBase, PreferencesPlugin
        from calibre.customize.ui import preferences_plugins
        from calibre.gui2.preferences import AbortInitialize
        from qt.core import QWidget
        self.assertIsInstance(plugin, PreferencesPlugin)
        self.assertNotIsInstance(plugin, InterfaceActionBase)
        entry = next(p for p in preferences_plugins() if p.name == 'GitHub Plugin Updater')
        self.assertEqual(entry.category, 'Advanced')
        self.assertEqual(entry.gui_name, 'GitHub 外掛更新')
        parent = QWidget()
        widget = entry.create_widget(parent)
        widget.genesis(parent)
        with patch.object(ui.UpdaterDialog, 'exec', return_value=0) as execute:
            with self.assertRaises(AbortInitialize):
                widget.initialize()
        execute.assert_called_once()
        parent.close()

    def test_sort_keeps_checked_plugin_identity_and_numeric_versions(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, status='可更新', eligible=True)
        dialog.rows = [dict(base, name='Zulu', current=[1, 2], version=[1, 2]),
                       dict(base, name='Alpha', current=[1, 10], version=[1, 10])]
        dialog.show_rows()
        dialog.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        header = dialog.table.horizontalHeader()
        header.sectionClicked.emit(1)
        self.assertEqual(dialog.table.item(0, 1).text(), 'Alpha')
        self.assertEqual(dialog.selected()[0]['name'], 'Zulu')
        header.sectionClicked.emit(1)
        self.assertEqual(dialog.table.item(0, 1).text(), 'Zulu')
        header.sectionClicked.emit(2)
        self.assertEqual(dialog.table.item(0, 2).text(), '1.2')
        header.sectionClicked.emit(2)
        self.assertEqual(dialog.table.item(0, 2).text(), '1.10')
        self.assertEqual(dialog.selected()[0]['name'], 'Zulu')
        header.sectionClicked.emit(0)
        self.assertEqual(len(dialog.selected()), 2)
        header.sectionClicked.emit(0)
        self.assertEqual(dialog.selected(), [])

    def test_install_completion_only_refreshes_successful_rows(self):
        from types import SimpleNamespace
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, status='可更新', eligible=True, current=[0, 1])
        dialog.rows = [dict(base, name='Zulu', id='example.zulu'),
                       dict(base, name='Alpha', id='example.alpha')]
        dialog.show_rows()
        dialog.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
        dialog.table.item(1, 0).setCheckState(Qt.CheckState.Checked)
        dialog.header_clicked(1)
        dialog.pending_entries = [dialog.rows[0]]
        dialog.mode = 'install'
        dialog.report = self.root / 'result.json'
        dialog.report.write_text(json.dumps({'installed': ['Zulu'], 'failed': [], 'backups': []}), encoding='utf-8')
        dialog.process = SimpleNamespace(deleteLater=lambda: None)
        dialog.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'dist')
        dialog.finished(0, None)
        self.assertEqual(dialog.table.rowCount(), 2)
        self.assertEqual(dialog.rows[0]['current'], [0, 2])
        self.assertEqual(dialog.rows[0]['status'], '已更新（待重新啟動）')
        self.assertEqual(dialog.rows[1]['current'], [0, 1])
        self.assertEqual(dialog.rows[1]['status'], '可更新')
        self.assertEqual([e['name'] for e in dialog.selected()], ['Alpha'])
        self.assertEqual(dialog.table.item(0, 1).text(), 'Alpha')
        self.assertTrue(dialog.restart_button.isEnabled())

    def test_backup_directory_setting_is_saved_and_opened_consistently(self):
        from calibre.utils.config import JSONConfig
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        previous = dialog.prefs.get('backup_dir')
        self.addCleanup(lambda: dialog.prefs.__setitem__('backup_dir', previous))
        folder = self.root / 'chosen-backups'
        with patch.object(ui.QFileDialog, 'getExistingDirectory', return_value=str(folder)):
            dialog.choose_backup_directory()
        persisted = JSONConfig('plugins/github_plugin_updater')
        self.assertEqual(core.backup_directory(persisted, config_dir), folder)
        self.assertEqual(dialog.backup_settings_button.toolTip(), str(folder))
        with patch.object(ui, 'open_local_file') as open_folder:
            dialog.open_backups()
        open_folder.assert_called_once_with(str(folder))
        with patch.object(ui.QFileDialog, 'getExistingDirectory', return_value=''):
            dialog.choose_backup_directory()
        self.assertEqual(dialog.prefs['backup_dir'], str(folder))

    def test_checked_items_force_same_version_and_downgrade(self):
        for target in [(0, 1), (0, 0)]:
            with self.subTest(version=target):
                data = package(self.root / 'force.zip', target)
                candidate = dict(self.entry, version=list(target), size=len(data),
                                 sha256=core.payload_digest(self.root / 'force.zip'),
                                 package_sha256=hashlib.sha256(data).hexdigest())
                bindings = {NAME: {'id': 'another.fixture', 'source': 'github:another/repo'}}
                result = core.install([candidate], bindings, self.root / 'forced-backups',
                                      get=lambda *args: data, force=True)
                self.assertEqual(result['installed'], [NAME], result)
                self.assertEqual(bindings[NAME]['source'], SOURCE)
                # Restore the baseline before testing the next forced operation.
                add_plugin(str(self.root / 'old.zip'))
                disable_plugin(NAME)

    def test_force_does_not_bypass_download_hash_validation(self):
        result = core.install([self.entry], self.bindings, self.root / 'forced-backups',
                              get=lambda *args: b'wrong', force=True)
        self.assertEqual(result['installed'], [])
        self.assertIn('SHA-256', result['failed'][0])
        incompatible = dict(self.entry, minimum_calibre_version=[9999, 0])
        result = core.install([incompatible], self.bindings, self.root / 'forced-backups',
                              get=lambda *args: self.fail('不相容項目不應下載'), force=True)
        self.assertEqual(result['installed'], [])
        self.assertIn('不相容', result['failed'][0])

    def test_mixed_checked_rows_are_all_sent_for_force_install(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, current=[0, 1])
        dialog.rows = [dict(base, name='Newer', eligible=True, status='可更新'),
                       dict(base, name='Same', eligible=False, status='內容相同')]
        dialog.show_rows()
        dialog.toggle_all(0)
        with patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.StandardButton.Yes), patch.object(dialog, 'start') as start:
            dialog.install_selected()
        self.assertTrue(start.call_args.args[0]['force'])
        self.assertEqual(len(start.call_args.args[0]['entries']), 2)

    def prefix_candidate(self, change=None):
        incoming = self.root / 'upstream.zip'
        with ZipFile(self.root / 'new.zip') as original, ZipFile(incoming, 'w') as archive:
            for name in original.namelist():
                if name == core.IDENTITY:
                    continue
                data = original.read(name)
                if change and name == '__init__.py':
                    data = data.replace(*change)
                archive.writestr(name, data)
        return incoming.read_bytes(), dict(self.entry, mode='prefixed', sha256=None,
                                          minimum_calibre_version=None, supported_platforms=None,
                                          size=incoming.stat().st_size, package_sha256=core.digest(incoming))

    def test_prefixed_zip_without_identity_is_verified_and_recorded(self):
        data, entry = self.prefix_candidate()
        result = core.install([entry], self.bindings, self.root / 'upstream-backups', get=lambda *args: data)
        self.assertEqual(result['installed'], [NAME], result)
        self.assertIsNone(core.identity(Path(plugin_dir) / (NAME + '.zip')))
        self.assertEqual(self.bindings[NAME]['package_sha256'], entry['package_sha256'])
        self.assertEqual(self.bindings[NAME]['accepted_sha256'], core.payload_digest(Path(plugin_dir) / (NAME + '.zip')))

    def test_prefixed_download_still_checks_name_and_actual_compatibility(self):
        for change in [(NAME.encode(), b'Another Fixture'), (b'(9,19,0)', b'(9999,0)')]:
            with self.subTest(change=change):
                data, entry = self.prefix_candidate(change)
                result = core.install([entry], self.bindings, self.root / 'upstream-backups', get=lambda *args: data, force=True)
                self.assertEqual(result['installed'], [])
                self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)

    def test_missing_upstream_digest_is_explicit_before_install(self):
        data, entry = self.prefix_candidate()
        entry['package_sha256'] = None
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        dialog.rows = [dict(entry, current=[0, 1], eligible=True, status='可更新；來源未提供附件 SHA')]
        dialog.show_rows()
        dialog.toggle_all(0)
        with patch.object(ui.QMessageBox, 'question', return_value=ui.QMessageBox.StandardButton.No) as confirm:
            dialog.install_selected()
        self.assertIn('未提供附件 SHA', confirm.call_args.args[2])
        result = core.install([entry], self.bindings, self.root / 'upstream-backups', get=lambda *args: data, force=True)
        self.assertEqual(result['installed'], [NAME], result)
        self.assertEqual(self.bindings[NAME]['package_sha256'], hashlib.sha256(data).hexdigest())

    def test_same_name_from_two_sources_cannot_be_selected_together(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, current=[0, 1], status='可更新', eligible=True)
        dialog.rows = [base, dict(base, id='upstream.fixture', source='github:another/plugins', repo='Another/Plugins')]
        dialog.show_rows()
        dialog.toggle_all(0)
        with patch.object(ui, 'error_dialog') as error, patch.object(dialog, 'start') as start:
            dialog.install_selected()
        self.assertIn('只能勾選一個來源', error.call_args.args[2])
        start.assert_not_called()

    def test_double_click_source_opens_correct_repo_after_sorting(self):
        dialog = ui.UpdaterDialog(None)
        self.addCleanup(dialog.close)
        base = dict(self.entry, current=[0, 1], status='可更新', eligible=True)
        dialog.rows = [dict(base, name='Zulu', repo='Example/Zulu'),
                       dict(base, name='Alpha', repo='Example/Alpha')]
        dialog.show_rows()
        dialog.header_clicked(1)
        with patch.object(ui, 'open_url') as open_browser:
            dialog.table.cellDoubleClicked.emit(0, 4)
            self.assertEqual(open_browser.call_args.args[0].toString(), 'https://github.com/Example/Alpha')
            dialog.table.cellDoubleClicked.emit(1, 4)
            self.assertEqual(open_browser.call_args.args[0].toString(), 'https://github.com/Example/Zulu')
            dialog.table.cellDoubleClicked.emit(0, 1)
            self.assertEqual(open_browser.call_count, 2)

    def test_single_release_installs_original_zip_and_saves_asset_id(self):
        for stamp in [True, False]:
            with self.subTest(has_digest=stamp):
                data, entry = self.prefix_candidate()
                entry.update(mode='single', asset_id=1234)
                if not stamp:
                    entry['package_sha256'] = None
                result = core.install([entry], self.bindings, self.root / 'single-backups', get=lambda *args: data, force=True)
                self.assertEqual(result['installed'], [NAME], result)
                self.assertEqual(self.bindings[NAME]['asset_id'], 1234)
                self.assertEqual(self.bindings[NAME]['package_sha256'], hashlib.sha256(data).hexdigest())
                add_plugin(str(self.root / 'old.zip'))
                disable_plugin(NAME)

    def test_single_release_import_failure_keeps_old_plugin_and_backup(self):
        data, entry = self.prefix_candidate()
        incoming = self.root / 'broken-upstream.zip'
        with ZipFile(self.root / 'upstream.zip') as original, ZipFile(incoming, 'w') as archive:
            for name in original.namelist():
                body = original.read(name)
                if name == '__init__.py':
                    body = b'import nonexistent_upstream_dependency\n' + body
                archive.writestr(name, body)
        data = incoming.read_bytes()
        entry.update(mode='single', size=len(data), package_sha256=hashlib.sha256(data).hexdigest())
        result = core.install([entry], self.bindings, self.root / 'single-backups', get=lambda *args: data, force=True)
        self.assertEqual(result['installed'], [])
        self.assertEqual(core.digest(Path(plugin_dir) / (NAME + '.zip')), self.old_package_sha)
        self.assertTrue(Path(result['backups'][0], NAME + '-0.1.zip').exists())

    def test_reinstall_preserves_user_sources_including_empty_list(self):
        from calibre.utils.config import JSONConfig
        preferences = JSONConfig('plugins/github_plugin_updater')
        existed = 'sources' in preferences
        previous = preferences.get('sources')
        try:
            for sources in [['https://github.com/Example/MyPlugins', 'https://github.com/Another/Source'], []]:
                preferences['sources'] = sources
                add_plugin(str(ROOT / 'dist/GitHub Plugin Updater-zh_TW-release.zip'))
                self.assertEqual(JSONConfig('plugins/github_plugin_updater')['sources'], sources)
        finally:
            if existed:
                preferences['sources'] = previous
            else:
                del preferences['sources']

    def test_self_update_in_separate_worker_preserves_running_module(self):
        original = ROOT / 'dist/GitHub Plugin Updater-zh_TW-release.zip'
        incoming = self.root / 'updater-next.zip'
        next_version = (plugin.version[0] + 1, 0)
        with ZipFile(original) as src, ZipFile(incoming, 'w') as dst:
            for name in src.namelist():
                if name == core.IDENTITY:
                    continue
                data = src.read(name)
                if name == '__init__.py':
                    data = data.replace(('version = ' + repr(tuple(plugin.version))).encode(),
                                        ('version = ' + repr(next_version)).encode())
                dst.writestr(name, data)
        stamp = core.identity(original)
        stamp['sha256'] = core.payload_digest(incoming)
        with ZipFile(incoming, 'a') as dst:
            dst.writestr(core.IDENTITY, json.dumps(stamp))
        name = 'GitHub Plugin Updater'
        old = core.installed_plugins()[name]
        entry = dict(self.entry, name=name, id=stamp['id'], source=stamp['source'], version=list(next_version),
                     sha256=stamp['sha256'], package_sha256=core.digest(incoming),
                     size=incoming.stat().st_size, observed_sha256=old['sha256'])
        job = self.root / 'self-job.json'; report = self.root / 'self-result.json'
        job.write_text(json.dumps({'mode': 'install', 'entries': [entry]}), encoding='utf-8')
        from calibre.utils.config import JSONConfig
        preferences = JSONConfig('plugins/github_plugin_updater')
        previous_backup = preferences.get('backup_dir')
        custom_backup = self.root / 'custom-self-backup'
        preferences['backup_dir'] = str(custom_backup)
        script = '''import sys
from pathlib import Path
import calibre.customize.ui
from calibre_plugins.github_plugin_updater import core
original_install=core.install
data=Path(sys.argv[-3]).read_bytes()
core.install=lambda entries,bindings,backup,force=False,auto_backup=True,original_install=original_install,data=data: original_install(entries,bindings,backup,get=lambda *args:data,force=force,auto_backup=auto_backup)
core.worker()
'''
        try:
            completed = subprocess.run(['calibre-debug', '-c', script, str(incoming), str(job), str(report)],
                                       capture_output=True, timeout=30, env=os.environ.copy())
            self.assertEqual(completed.returncode, 0, completed.stderr)
            result = json.loads(report.read_text(encoding='utf-8'))
            self.assertIn('installed', result, result)
            self.assertEqual(result['installed'], [name], result)
            self.assertTrue(Path(result['backups'][0], name + '-' + '.'.join(map(str, plugin.version)) + '.zip').is_file())
            self.assertEqual(Path(result['backups'][0]).parent, custom_backup)
            self.assertEqual(core.digest(Path(plugin_dir) / (name + '.zip')), entry['package_sha256'])
            from types import SimpleNamespace
            dialog = ui.UpdaterDialog(None)
            dialog.mode, dialog.report = 'install', report
            dialog.process = SimpleNamespace(deleteLater=lambda: None)
            dialog.temporary = tempfile.TemporaryDirectory(dir=ROOT / 'dist')
            dialog.finished(0, None)
            self.assertTrue(dialog.restart_required)
            self.assertTrue(dialog.restart_button.isEnabled())
            self.assertEqual(dialog.prefs['bindings'][name]['accepted_sha256'], stamp['sha256'])
            from unittest.mock import Mock
            dialog.gui = SimpleNamespace(quit=Mock())
            dialog.restart_button.click()
            dialog.gui.quit.assert_called_once_with(restart=True)
            self.assertIn('重新啟動', dialog.status.text())
            dialog.close()
        finally:
            preferences['backup_dir'] = previous_backup
            add_plugin(str(original))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeTests)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())

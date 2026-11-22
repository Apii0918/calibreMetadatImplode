import gettext
import io
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
if (ROOT / 'dist').resolve() not in Path(config_dir).resolve().parents:
    raise RuntimeError('請使用 dist 下的獨立設定目錄。')
prefs['language'] = 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.customize.zipplugin import loader
ARCHIVE = ROOT / 'dist/Shortcuts Helper-zh_TW-release.zip'
Plugin = loader.load(str(ARCHIVE))
from calibre_plugins.shortcuts_helper import config, ui
from calibre.gui2 import Application
from qt.core import QMainWindow, QKeySequence, Qt


class ShortcutsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def setUp(self):
        self.gui = QMainWindow()
        self.gui.keyboard = SimpleNamespace(shortcuts={
            'first': {'name': '第一個動作', 'default_keys': ('Ctrl+A',)},
            'second': {'name': '第二個動作', 'default_keys': ('Ctrl+B',)},
            'third': {'name': '第三個動作', 'default_keys': ()},
            'unset': {'name': '未指定', 'default_keys': ()},
        }, groups={'測試群組': ['first', 'second', 'third', 'unset']}, keys_map={
            'first': (QKeySequence('Ctrl+Shift+A'),), 'second': (QKeySequence('Ctrl+B'),),
            'third': (QKeySequence('Alt+C'),),
        })
        self.dialog = ui.CurrentShortcutsDialog(self.gui)
        self.addCleanup(self.gui.close)
        self.addCleanup(self.dialog.close)

    def test_catalog_and_visible_controls(self):
        self.assertEqual(Plugin.version, (1, 1, 0, 1))
        self.assertEqual(self.dialog.windowTitle(), '目前快捷鍵')
        self.assertEqual(self.dialog.filter_edit.placeholderText(), '搜尋快捷鍵…')
        self.assertEqual([self.dialog.table.horizontalHeaderItem(i).text() for i in range(4)],
                         ['動作', '群組', '預設', '目前'])
        with ZipFile(ARCHIVE) as z:
            catalog = gettext.GNUTranslations(io.BytesIO(z.read('translations/zh_TW.mo')))
        self.assertGreater(len(catalog._catalog), 20)
        self.assertEqual(ui.ShortcutsButtonAction.action_spec[0], '快捷鍵助手')

    def test_filter_and_refresh_preserve_shortcut_rows(self):
        table = self.dialog.table
        expected = {'第一個動作': 'Ctrl+Shift+A', '第二個動作': 'Ctrl+B', '第三個動作': 'Alt+C'}
        for mode in ('alphabetic', 'modifier_key', 'key_modifier'):
            self.dialog.sort_current_column(mode)
            actual = {table.item(r, 0).text(): table.item(r, 3).text() for r in range(table.rowCount())}
            self.assertEqual(actual, expected)
        self.dialog.on_header_clicked(0)
        self.assertEqual({table.item(r, 0).text(): table.item(r, 3).text() for r in range(table.rowCount())}, expected)
        self.dialog.filter_edit.setText('第一個')
        self.dialog.color_custom_checkbox.setChecked(not self.dialog.color_custom_checkbox.isChecked())
        self.assertEqual(sum(not table.isRowHidden(r) for r in range(table.rowCount())), 1)
        self.assertEqual(self.gui.keyboard.keys_map['first'][0].toString(), 'Ctrl+Shift+A')

    def test_custom_marker_survives_sorting(self):
        self.dialog.color_custom_checkbox.setChecked(True)
        self.dialog.populate_table()
        self.dialog.sort_current_column('key_modifier')
        table = self.dialog.table
        actual = {table.item(r, 0).text(): table.item(r, 3).data(Qt.ItemDataRole.UserRole)
                  for r in range(table.rowCount())}
        self.assertEqual(actual, {'第一個動作': True, '第二個動作': False, '第三個動作': True})

    def test_settings_keep_identifiers_and_route_both_actions(self):
        widget = config.ConfigWidget()
        try:
            widget.main_action_combo.setCurrentIndex(widget.main_action_combo.findData('current'))
            widget.save_settings()
            self.assertEqual(config.get_main_action_key(), 'current')
            target = SimpleNamespace(_show_current_shortcuts=Mock(), _show_shortcuts_prefs=Mock())
            ui.ShortcutsButtonAction._main_button_clicked(target)
            target._show_current_shortcuts.assert_called_once()
            config.PREFS['main_action'] = 'prefs'
            ui.ShortcutsButtonAction._main_button_clicked(target)
            target._show_shortcuts_prefs.assert_called_once()
            config.PREFS['main_action'] = 'unknown'
            self.assertEqual(config.get_main_action_key(), 'prefs')
        finally:
            widget.close()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(ShortcutsTests))
    raise SystemExit(not result.wasSuccessful())

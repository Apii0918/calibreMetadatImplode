"""Run with calibre-debug -e in a fresh CALIBRE_CONFIG_DIRECTORY under dist/."""
import ast
import gettext
import json
import re
import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Columns Helper/src'
from calibre.utils.config import config_dir, prefs

CONFIG = Path(config_dir).resolve()
if not (ROOT / 'dist' in CONFIG.parents):
    raise AssertionError('請使用 dist 下的獨立設定目錄')
LIBRARY = CONFIG / 'Test Library'
REPORT = CONFIG / 'test-result.json'
from calibre.db.legacy import LibraryDatabase
from calibre.ebooks.metadata.book.base import Metadata

db = LibraryDatabase(str(LIBRARY))
if not (not db.new_api.all_book_ids()):
    raise AssertionError('請使用新的測試設定目錄')
BOOK_ID = db.create_book_entry(Metadata('欄位測試書', ['測試作者']))
db.close()
prefs['library_path'] = str(LIBRARY)
prefs['language'] = 'zh_TW'
from calibre.gui2 import dynamic
dynamic.set('welcome_wizard_was_run', True)
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2.main import init_qt, option_parser, run_gui_
from calibre.gui2.ui import get_gui
from qt.core import QCoreApplication, QEvent, QFont, QFontDatabase, QTimer

app, _, _ = init_qt(['calibre'])
font_file = Path('C:/Windows/Fonts/msjh.ttc')
if font_file.exists():
    QFontDatabase.addApplicationFont(str(font_file))
    app.setFont(QFont('Microsoft JhengHei UI', 10))
opts, args = option_parser().parse_args(['--with-library', str(LIBRARY), '--no-update-check'])


class ColumnsHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.gui = get_gui()
        cls.action = cls.gui.iactions['Columns Helper']
        from calibre_plugins.columns_helper import ui
        cls.ui = ui

    def open_dialog(self):
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        self.action.open_columns_preferences()
        dlg = self.ui._MODELESS_COLUMNS_DIALOG
        self.assertIsNotNone(dlg)
        self.addCleanup(lambda: dlg.close() if self.ui._qt_object_is_alive(dlg) else None)
        return dlg

    def test_01_catalog_and_presets(self):
        from calibre.customize.zipplugin import get_resources
        data = get_resources(self.action.plugin_path, 'translations/zh_TW.mo')
        import io
        catalog = gettext.GNUTranslations(io.BytesIO(data))
        messages = set()
        for file in SOURCE.glob('*.py'):
            for node in ast.walk(ast.parse(file.read_text('utf-8'))):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id == '_' and node.args and isinstance(node.args[0], ast.Constant)):
                    messages.add(node.args[0].value)
        messages.add('Columns Helper')
        for message in messages:
            self.assertIn(message, catalog._catalog, message)
            translated = catalog.gettext(message)
            self.assertTrue(translated)
            self.assertEqual(re.findall(r'\{[^}]*\}|%[ds]', message),
                             re.findall(r'\{[^}]*\}|%[ds]', translated), message)
        self.assertEqual(catalog.gettext('Column'), '欄位')
        self.assertEqual(catalog.gettext('Apply pack'), '套用套組')
        presets = self.action._quick_create_presets()
        self.assertEqual(presets['builtin']['read_progress']['display']['composite_template'], '{id:reading_progress()}')
        self.assertEqual(presets['tracker']['status']['lookup_name'], '#status')
        self.assertIn('Reading', presets['tracker']['status']['display']['description'])

    def test_02_open_browse_preview_and_filter(self):
        dlg = self.open_dialog()
        self.assertEqual(dlg.windowTitle(), '欄位助手')
        self.action.open_packs_dialog()
        browsers = [w for w in app.topLevelWidgets() if isinstance(w, self.ui.HelperShowroomDialog)]
        self.assertTrue(browsers)
        browser = browsers[0]
        self.assertTrue(browser._select_payload('viewer', 'read_progress'))
        self.assertEqual(browser._current_lookup_name(), '#read_progress')
        self.assertEqual(browser._current_template_for_actions(), ('composite_template', '{id:reading_progress()}'))
        from calibre.gui2.dialogs.template_dialog import TemplateDialog
        self.gui.library_view.select_rows([BOOK_ID])
        tested = []
        def close_tester():
            for window in app.topLevelWidgets():
                if isinstance(window, TemplateDialog):
                    tested.append(window.windowTitle())
                    window.reject()
        QTimer.singleShot(100, close_tester)
        browser._test_current_template()
        self.assertTrue(tested)
        browser.grab().save(str(CONFIG / 'packs.png'))
        browser.close()
        table = dlg.widget.opt_columns
        field = dlg.widget._cc_filter_edit
        field.setCurrentText('title')
        dlg.widget._cdf_refresh_filter()
        visible = sum(not table.isRowHidden(r) for r in range(table.rowCount()))
        self.assertGreater(visible, 0)
        self.assertLess(visible, table.rowCount())
        field.setCurrentText('')
        dlg.widget._cdf_refresh_filter()
        dlg.grab().save(str(CONFIG / 'main.png'))

    def test_03_reorder_buttons(self):
        dlg = self.open_dialog()
        widget = dlg.widget
        table = widget.opt_columns
        table.setCurrentCell(2, 0)
        before = table.currentRow()
        widget.column_up.click()
        self.assertEqual(table.currentRow(), before - 1)
        widget.column_down.click()
        self.assertEqual(table.currentRow(), before)
        widget._cdf_move_top_button.click()
        self.assertEqual(table.currentRow(), 0)
        widget._cdf_move_bottom_button.click()
        self.assertEqual(table.currentRow(), table.rowCount() - 1)

    def test_04_cancel_pending_column(self):
        dlg = self.open_dialog()
        dlg.widget._cdf_quick_create_columns('builtin', ['tags'])
        self.assertIn('#tags', dlg.widget.custcols)
        dlg.close()
        QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
        with sqlite3.connect(str(LIBRARY / 'metadata.db')) as conn:
            self.assertEqual(conn.execute('SELECT count(*) FROM custom_columns').fetchone()[0], 0)

    def test_05_create_apply_and_protect_metadata(self):
        dlg = self.open_dialog()
        widget = dlg.widget
        widget._cdf_quick_create_columns('builtin', ['yesno', 'read_progress'])
        widget._cdf_quick_create_columns('count_pages', ['pages'])
        widget._cdf_quick_create_columns('review', ['review'])
        count = len(widget.custcols)
        widget._cdf_quick_create_columns('builtin', ['yesno'])
        self.assertEqual(len(widget.custcols), count)
        with patch.object(self.ui, 'show_restart_warning', return_value=False):
            self.assertTrue(dlg.apply_changes())
        with sqlite3.connect(str(LIBRARY / 'metadata.db')) as conn:
            columns = {r[0]: r[1:] for r in conn.execute('SELECT label, name, datatype, display FROM custom_columns')}
            self.assertEqual(columns['yesno'][:2], ('是／否', 'bool'))
            self.assertEqual(columns['read_progress'][:2], ('閱讀進度', 'composite'))
            self.assertEqual(json.loads(columns['read_progress'][2])['composite_template'], '{id:reading_progress()}')
            self.assertEqual(columns['pp'][1], 'int')
            self.assertEqual(columns['review'][1], 'comments')
        mi = self.gui.current_db.new_api.get_metadata(BOOK_ID)
        self.assertEqual((mi.title, mi.authors), ('欄位測試書', ['測試作者']))

    def test_06_reopen_database(self):
        reopened = LibraryDatabase(str(LIBRARY))
        try:
            columns = reopened.new_api.field_metadata.custom_field_metadata()
            self.assertEqual(columns['#read_progress']['name'], '閱讀進度')
            self.assertEqual(columns['#pp']['datatype'], 'int')
            self.assertNotIn('#tags', columns)
            self.assertEqual(reopened.new_api.get_metadata(BOOK_ID).authors, ['測試作者'])
        finally:
            reopened.close()


def run_tests():
    if get_gui() is None:
        QTimer.singleShot(500, run_tests)
        return
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ColumnsHelperTests))
    REPORT.write_text(json.dumps({'tests': result.testsRun, 'failures': len(result.failures),
                                 'errors': len(result.errors), 'success': result.wasSuccessful()}, indent=2), 'utf-8')
    get_gui().quit()


QTimer.singleShot(6000, run_tests)
QTimer.singleShot(45000, lambda: app.exit(2))
run_gui_(opts, args, app)
raise SystemExit(0 if REPORT.exists() and json.loads(REPORT.read_text('utf-8'))['success'] else 1)

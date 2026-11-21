import ast
import builtins
import gettext
import importlib.util
import sys
import unittest
from collections import OrderedDict
from pathlib import Path
from tempfile import TemporaryDirectory
from types import MethodType, SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Manage Series/src'
from calibre.gui2 import Application
from calibre.utils.config import config_dir
assert ROOT / 'dist' in Path(config_dir).resolve().parents, '請使用 dist 下的隔離設定目錄'
from calibre.translations.msgfmt import make_with_stats
compiled = Path(config_dir) / 'manage-series-zh_TW.mo'
compiled.parent.mkdir(parents=True, exist_ok=True)
make_with_stats(str(SOURCE / 'translations/zh_TW.po'), str(compiled))
with compiled.open('rb') as stream:
    CATALOG = gettext.GNUTranslations(stream)

def load_translations():
    sys._getframe(1).f_globals['_'] = CATALOG.gettext

with patch.object(builtins, 'load_translations', load_translations, create=True):
    spec = importlib.util.spec_from_file_location('calibre_plugins.manage_series', SOURCE / '__init__.py', submodule_search_locations=[str(SOURCE)])
    plugin = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = plugin
    spec.loader.exec_module(plugin)
    from calibre_plugins.manage_series import action, book, dialogs, common_icons, common_dialogs, config

from calibre.db.legacy import LibraryDatabase
from calibre.ebooks.metadata.book.base import Metadata
from qt.core import QDateTime, QIcon, QStandardItemModel, QStyleOptionViewItem, Qt, QWidget


class ManageSeriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])
        common_icons.set_plugin_icon_resources('Manage Series', {p.relative_to(SOURCE).as_posix(): p.read_bytes() for p in (SOURCE / 'images').glob('*')})

    def setUp(self):
        self.temp = TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        self.db = LibraryDatabase(str(Path(self.temp.name) / 'Library'))
        self.addCleanup(lambda: self.db.close())
        self.db.create_custom_column('alternate', '另一系列', 'series', False)
        self.db.create_custom_column('unrelated', '保留欄位', 'text', False)
        self.db.close()
        self.db = LibraryDatabase(str(Path(self.temp.name) / 'Library'))
        self.ids = []
        for i in range(4):
            mi = Metadata('卷' + str(i + 1), ['作者'])
            mi.series, mi.series_index = '原系列', float(i + 1)
            mi.tags = ['保留標籤']
            self.ids.append(self.db.create_book_entry(mi))
        self.db.new_api.set_field('#alternate', {i: '原自訂系列' for i in self.ids})
        self.db.new_api.set_field('#alternate_index', {i: float(n + 10) for n, i in enumerate(self.ids)})
        self.db.new_api.set_field('#unrelated', {i: '保留值' for i in self.ids})
        self.columns = OrderedDict([('#alternate', self.db.field_metadata['#alternate'])])
        self.model = SimpleNamespace(db=self.db, custom_columns=self.columns, refresh_ids=Mock(), books_added=Mock())
        self.qtmodel = QStandardItemModel(4, 1)
        self.gui = QWidget()
        self.gui.library_view = SimpleNamespace(model=lambda: self.model, selectionModel=lambda: SimpleNamespace(selectedRows=lambda: [self.qtmodel.index(i, 0) for i in range(4)]))
        self.gui.tags_view = QWidget(self.gui)
        self.gui.tags_view.recount = Mock()
        self.windows = []
        self.icons = patch.object(dialogs, 'get_icon', return_value=QIcon())
        self.icons.start()
        book.SeriesBook.series_column = 'Series'

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.icons.stop()
        self.gui.close()

    def panel(self):
        books = [book.SeriesBook(self.db.new_api.get_metadata(i), self.columns) for i in self.ids]
        panel = dialogs.SeriesDialog(self.gui, books, self.db.all_series(), self.columns)
        self.windows.append(panel)
        return panel

    def controller(self):
        ctl = SimpleNamespace(gui=self.gui, is_library_selected=True)
        ctl.get_series_columns = MethodType(action.ManageSeriesAction.get_series_columns, ctl)
        ctl.get_selected_books = MethodType(action.ManageSeriesAction.get_selected_books, ctl)
        return ctl

    def test_integer_decimal_lock_and_restore(self):
        panel = self.panel()
        self.assertEqual(panel.windowTitle(), '系列管理')
        self.assertEqual(panel.series_column_combo.itemText(0), '系列')
        self.assertEqual(panel.series_column_combo.selected_value(), 'Series')
        panel.series_start_number.setValue(5)
        self.assertEqual([b.series_index() for b in panel.books], [5, 6, 7, 8])
        panel.books[1].set_series_indent(1)
        panel.books[2].set_series_indent(1)
        panel.renumber_series()
        self.assertEqual([b.series_index() for b in panel.books], [5, 5.1, 5.2, 6])
        for unused in range(20):
            panel.renumber_series()
        self.assertEqual([b.series_index() for b in panel.books], [5, 5.1, 5.2, 6])
        self.assertEqual([b.series_indent() for b in panel.books], [0, 1, 1, 0])
        panel.books[2].set_assigned_index(10.25)
        panel.renumber_series()
        self.assertEqual(panel.books[2].series_index(), 10.25)
        panel.restore_original_series()
        self.assertEqual([b.series_index() for b in panel.books], [1, 2, 3, 4])
        self.assertEqual(book.get_indent_for_index(1), 0)
        self.assertEqual(book.get_indent_for_index(1.01), 2)

    def test_movement_sort_and_conflict(self):
        panel = self.panel()
        panel.series_table.selectRow(1)
        panel.move_rows_up()
        self.assertEqual([b.title() for b in panel.books], ['卷2', '卷1', '卷3', '卷4'])
        panel.move_rows_down()
        self.assertEqual([b.title() for b in panel.books], ['卷1', '卷2', '卷3', '卷4'])
        panel.books[1].set_assigned_index(1)
        panel.renumber_series()
        self.assertFalse(panel.books[1].is_valid())
        panel.series_table.selectRow(1)
        panel.clear_index()
        self.assertTrue(all(b.is_valid() for b in panel.books))

    def test_accept_writes_real_library_and_cancel_does_not(self):
        ctl = self.controller()
        def accept(panel):
            self.windows.append(panel)
            panel.series_combo.setEditText('新系列')
            panel.series_start_number.setValue(7)
            panel.accept()
            return panel.result()
        self.gui.tags_view.blockSignals(True)
        with patch.object(dialogs.SeriesDialog, 'exec', accept):
            action.ManageSeriesAction.manage_series(ctl)
        self.assertTrue(self.gui.tags_view.signalsBlocked())
        for offset, i in enumerate(self.ids):
            mi = self.db.new_api.get_metadata(i)
            self.assertEqual((mi.series, mi.series_index), ('新系列', float(offset + 7)))
            self.assertEqual((mi.authors, mi.tags, mi.get('#unrelated')), (['作者'], ['保留標籤'], '保留值'))
        self.db.close()
        self.db = LibraryDatabase(str(Path(self.temp.name) / 'Library'))
        self.model.db = self.db
        self.assertEqual(self.db.new_api.field_for('series', self.ids[0]), '新系列')
        def cancel(panel):
            self.windows.append(panel)
            panel.series_combo.setEditText('不應寫入')
            panel.series_start_number.setValue(99)
            panel.reject()
            return panel.result()
        with patch.object(dialogs.SeriesDialog, 'exec', cancel):
            action.ManageSeriesAction.manage_series(ctl)
        self.assertEqual(self.db.new_api.field_for('series', self.ids[0]), '新系列')
        self.assertEqual(self.db.new_api.field_for('series_index', self.ids[0]), 7)

    def test_custom_series_only_last_selected_column_persists(self):
        def accept(panel):
            self.windows.append(panel)
            panel.series_combo.setEditText('標準欄位暫存修改')
            panel.series_column_combo.setCurrentIndex(1)
            panel.series_combo.setEditText('自訂新系列')
            panel.series_start_number.setValue(20)
            panel.accept()
            return panel.result()
        with patch.object(dialogs.SeriesDialog, 'exec', accept):
            action.ManageSeriesAction.manage_series(self.controller())
        for n, i in enumerate(self.ids):
            self.assertEqual(self.db.new_api.field_for('series', i), '原系列')
            self.assertEqual(self.db.new_api.field_for('#alternate', i), '自訂新系列')
            self.assertEqual(self.db.new_api.field_for('#alternate_index', i), float(n + 20))
        combo = dialogs.SeriesColumnComboBox(None, self.columns)
        self.windows.append(combo)
        combo.select_text('#alternate')
        self.assertEqual(combo.selected_value(), '#alternate')

    def test_native_lock_date_and_catalog_coverage(self):
        panel = self.panel()
        lock = dialogs.LockSeriesDialog(panel, '測試書本', 2.25)
        self.windows.append(lock)
        self.assertEqual(lock.windowTitle(), '鎖定系列編號')
        self.assertEqual(lock.get_value(), 2.25)
        lock.assign_same_checkbox.setChecked(True)
        self.assertTrue(lock.assign_same_value())
        index = panel.series_table.model().index(0, 2)
        delegate = panel.series_table.itemDelegateForColumn(2)
        editor = delegate.createEditor(panel.series_table, QStyleOptionViewItem(), index)
        self.windows.append(editor)
        delegate.setEditorData(editor, index)
        editor.setDateTime(QDateTime.currentDateTime())
        delegate.setModelData(editor, panel.series_table.model(), index)
        for path in SOURCE.glob('*.py'):
            for n in ast.walk(ast.parse(path.read_text(encoding='utf8'))):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == '_' and n.args and isinstance(n.args[0], ast.Constant):
                    self.assertIn(n.args[0].value, CATALOG._catalog)
        self.assertEqual(CATALOG.gettext('Alt+Up'), 'Alt+Up')
        self.assertEqual(plugin.ActionManageSeries.version, (1,5,5,1))

    def test_add_empty_book_writes_new_record(self):
        original_ids = self.db.new_api.all_book_ids()
        def accept(panel):
            self.windows.append(panel)
            with patch.object(dialogs.AddEmptyBookDialog, 'exec', return_value=dialogs.AddEmptyBookDialog.DialogCode.Accepted), \
                 patch.object(dialogs.AddEmptyBookDialog, 'qty_to_add', new_callable=lambda: property(lambda self: 1)):
                panel.add_empty_book()
            panel.series_combo.setEditText('含待購卷冊')
            panel.accept()
            return panel.result()
        with patch.object(dialogs.SeriesDialog, 'exec', accept):
            action.ManageSeriesAction.manage_series(self.controller())
        added = self.db.new_api.all_book_ids() - original_ids
        self.assertEqual(len(added), 1)
        new_id = next(iter(added))
        self.assertEqual(self.db.new_api.field_for('series', new_id), '含待購卷冊')
        self.assertEqual(self.db.new_api.formats(new_id), ())

    def test_write_failure_restores_signal_state(self):
        def accept(panel):
            self.windows.append(panel)
            panel.series_combo.setEditText('模擬寫入失敗')
            panel.accept()
            return panel.result()
        self.gui.tags_view.blockSignals(True)
        with patch.object(dialogs.SeriesDialog, 'exec', accept), patch.object(self.db, 'set_metadata', side_effect=RuntimeError('simulated failure')):
            with self.assertRaisesRegex(RuntimeError, 'simulated failure'):
                action.ManageSeriesAction.manage_series(self.controller())
        self.assertTrue(self.gui.tags_view.signalsBlocked())


result = unittest.TextTestRunner(verbosity=2, failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(ManageSeriesTests))
if not result.wasSuccessful():
    raise SystemExit(1)

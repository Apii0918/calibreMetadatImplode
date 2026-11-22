import sys
import unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir
if (ROOT / 'dist').resolve() not in Path(config_dir).resolve().parents:
    raise SystemExit('請使用 dist 下的獨立設定目錄。')
from calibre.customize.zipplugin import loader
loader.load(str(ROOT / 'dist/Hardcover Sync-zh_TW-release.zip'))
from calibre_plugins.hardcover_sync import ui, lists_cache
from calibre.gui2 import Application
from qt.core import QDialog, QMainWindow, QTimer


class InitializationLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def setUp(self):
        self.gui = QMainWindow()
        self.cache = SimpleNamespace(field_metadata={lists_cache.COLUMN_KEY: {}},
                                     all_book_ids=lambda: [7], set_field=Mock())
        self.gui.current_db = SimpleNamespace(new_api=self.cache)
        self.action = SimpleNamespace(gui=self.gui, _refresh_books_in_ui=Mock(),
                                      _refresh_tag_browser=Mock(), _schedule_list_update=Mock())
        self.action._run_without_selection_updates = lambda callback: callback()
        self.patches = ExitStack()
        self.addCleanup(self.patches.close)
        self.addCleanup(self.gui.close)
        for name in ('ensure_hardcover_lists_column', 'ensure_hc_rating_column',
                     'ensure_hc_review_column', 'ensure_hc_status_column',
                     'ensure_hc_notes_column', 'ensure_hc_quotes_column'):
            self.patches.enter_context(patch.object(ui, name, return_value=True))

    def confirm_then(self, callback):
        def confirm(*args, **kwargs):
            dialog = QDialog(self.gui)
            def finish():
                callback()
                dialog.accept()
            QTimer.singleShot(0, finish)
            return dialog.exec()
        return confirm

    def setup_details(self, confirm):
        with patch('calibre.gui2.dialogs.confirm_delete.confirm', side_effect=confirm):
            ui.HardcoverSyncAction._setup_book_details(self.action)

    def test_close_database_while_confirmation_is_open(self):
        self.setup_details(self.confirm_then(lambda: setattr(self.gui, 'current_db', None)))
        self.action._refresh_books_in_ui.assert_not_called()
        self.action._refresh_tag_browser.assert_not_called()
        self.action._schedule_list_update.assert_not_called()

    def test_switch_library_while_confirmation_is_open(self):
        other = SimpleNamespace(new_api=SimpleNamespace(field_metadata={}))
        with patch.object(ui, 'restore_lists_cache_to_column') as restore:
            self.setup_details(self.confirm_then(lambda: setattr(self.gui, 'current_db', other)))
        restore.assert_not_called()
        self.action._refresh_tag_browser.assert_not_called()
        self.action._schedule_list_update.assert_not_called()

    def test_normal_confirmation_restores_cache_and_refreshes(self):
        self.cache.field_for = lambda field, book_id: {'hardcover-id': '42'} if field == 'identifiers' else []
        with patch.object(lists_cache, 'get_lists_cache', return_value={'id:42': 'Reading'}):
            self.setup_details(self.confirm_then(lambda: None))
        self.cache.set_field.assert_called_once_with(lists_cache.COLUMN_KEY, {7: 'Reading'})
        self.action._refresh_books_in_ui.assert_called_once_with([7])
        self.action._schedule_list_update.assert_called_once()

    def test_no_database_skips_setup_and_cache_restore(self):
        self.gui.current_db = None
        self.assertEqual(lists_cache.restore_lists_cache_to_column(self.gui), [])
        with patch.object(ui, 'ensure_hardcover_lists_column') as ensure:
            ui.HardcoverSyncAction._setup_book_details(self.action)
        ensure.assert_not_called()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(InitializationLifecycleTests))
    raise SystemExit(not result.wasSuccessful())

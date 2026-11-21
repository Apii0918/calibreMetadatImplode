"""以隔離設定目錄安裝安裝包後執行；會啟動原生 GUI 並寫入暫存書庫。"""
import sys
import os
import traceback
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from calibre.utils.config import config_dir, dynamic, prefs

ROOT = Path(__file__).resolve().parents[2]
assert ROOT / 'dist' in Path(config_dir).resolve().parents, '請使用 dist 下的隔離設定目錄'
from calibre.db.legacy import LibraryDatabase
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2.main import init_qt, run_gui_
from calibre.gui2.ui import get_gui
from qt.core import QTimer

temporary = TemporaryDirectory(dir=ROOT / 'dist')
library = Path(temporary.name) / 'Library'
db = LibraryDatabase(str(library))
ids = []
for index in range(3):
    mi = Metadata('實際視窗卷冊' + str(index + 1), ['測試作者'])
    mi.series, mi.series_index = '原生測試', float(index + 1)
    ids.append(db.new_api.create_book_entry(mi))
db.close()
prefs['language'] = 'zh_TW'
dynamic.set('welcome_wizard_was_run', True)
app, opts, args = init_qt(['calibre', '--with-library', str(library)])
status = {'success': False, 'attempts': 0}

def verify():
    status['attempts'] += 1
    gui = get_gui()
    if gui is None or 'Manage Series' not in getattr(gui, 'iactions', {}):
        if status['attempts'] < 100:
            QTimer.singleShot(200, verify)
        else:
            app.quit()
        return
    try:
        from calibre_plugins.manage_series.dialogs import SeriesDialog
        plugin = gui.iactions['Manage Series']
        assert plugin.qaction.text() == '系列管理', plugin.qaction.text()
        from calibre_plugins.manage_series.config import ConfigWidget
        from calibre_plugins.manage_series.common_dialogs import KeyboardConfigDialog
        settings = ConfigWidget(plugin)
        shortcuts = KeyboardConfigDialog(gui, plugin.action_spec[0])
        assert shortcuts.windowTitle() == '鍵盤快捷鍵'
        shortcuts.close()
        settings.close()
        gui.library_view.select_rows(ids)
        def accept(dialog):
            assert dialog.windowTitle() == '系列管理'
            dialog.series_combo.setEditText('原生寫回已通過')
            dialog.series_start_number.setValue(2)
            dialog.books[1].set_series_indent(1)
            dialog.renumber_series()
            assert [b.series_index() for b in dialog.books] == [2, 2.1, 3]
            dialog.accept()
            return dialog.result()
        with patch.object(SeriesDialog, 'exec', accept):
            plugin.manage_series()
        cache = gui.current_db.new_api
        assert {cache.field_for('series', i) for i in ids} == {'原生寫回已通過'}
        assert sorted(cache.field_for('series_index', i) for i in ids) == [2, 2.1, 3]
        status['success'] = True
        print('PASS installed zh_TW catalog, native GUI action and real writeback', flush=True)
    except Exception:
        traceback.print_exc()
    finally:
        app.quit()

QTimer.singleShot(200, verify)
run_gui_(opts, args, app)
if status['success']:
    db = LibraryDatabase(str(library))
    assert {db.new_api.field_for('series', i) for i in ids} == {'原生寫回已通過'}
    db.close()
    print('PASS persisted series after library reopen', flush=True)
# Keep this synthetic library in dist; full-GUI workers may still hold SQLite files.
# Windows CRT exit can fail after full GUI teardown; terminate only this test process.
result = 0 if status['success'] else 1
if sys.platform == 'win32':
    import ctypes
    ctypes.windll.kernel32.TerminateProcess(ctypes.c_void_p(-1), result)
os._exit(result)

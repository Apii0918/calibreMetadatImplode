"""Native preferences footer and asynchronous export/import roundtrip."""
import json
import sys
import time
import traceback
from pathlib import Path
from unittest.mock import patch
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
CONFIG = Path(config_dir).resolve()
if not ROOT / 'dist' in CONFIG.parents:
    raise RuntimeError('請使用 dist 下的獨立設定目錄')
from calibre.db.legacy import LibraryDatabase
library = CONFIG / 'Library'
db = LibraryDatabase(str(library))
db.close()
prefs['library_path'] = str(library)
prefs['language'] = 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2 import dynamic, gprefs
dynamic.set('welcome_wizard_was_run', True)
from calibre.gui2.main import init_qt, option_parser, run_gui_
from calibre.gui2.ui import get_gui
from calibre.gui2.preferences import get_plugin
from calibre.gui2.preferences.main import Preferences
from qt.core import QDialog, QDialogButtonBox, QFont, QFontDatabase, QTimer, Qt
app, _, _ = init_qt(['calibre'])
if Path('C:/Windows/Fonts/msjh.ttc').exists():
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/msjh.ttc')
    app.setFont(QFont('Microsoft JhengHei UI', 10))
opts, args = option_parser().parse_args(['--with-library', str(library), '--no-update-check'])

def check(condition, message='檢查失敗'):
    if not condition:
        raise AssertionError(message)
state = {'step': 'start', 'deadline': time.monotonic() + 60}
backup = ROOT / 'dist/plugin-backup-gui-test.zip'
setting = CONFIG / 'plugins/pb-gui-setting.json'

def finish(success):
    timer.stop()
    (CONFIG / 'gui-result.json').write_text(json.dumps({'success': success, 'step': state['step']}), 'utf-8')
    for widget in app.topLevelWidgets():
        if isinstance(widget, QDialog):
            widget.reject()
    get_gui().quit()

def poll():
    try:
        check(time.monotonic() < state['deadline'], state)
        gui = get_gui()
        if gui is None:
            return
        from calibre_plugins.plugin_backup.ui import BackupDialog, ImportDialog
        from calibre_plugins.plugin_backup.core import inspect_backup
        if state['step'] == 'start':
            check('Plugin Backup' in gui.iactions)
            check(not gui.iactions['Plugin Backup'].qaction.isVisible())
            pref = Preferences(gui, ('Advanced', 'Plugins'))
            state['preferences'] = pref
            pref.show()
            state['step'] = 'footer'
        elif state['step'] == 'footer':
            pref = state['preferences']
            button = pref._plugin_backup_button
            check(button.isVisible())
            check(button.text() == '匯出／匯入外掛…')
            cancel = pref.bb.button(QDialogButtonBox.StandardButton.Cancel)
            check(button.x() < cancel.x(), (button.geometry(), cancel.geometry()))
            pref.grab().save(str(CONFIG / 'preferences-entry.png'))
            state['step'] = 'open-backup'
            QTimer.singleShot(0, button.click)
        elif state['step'] == 'open-backup':
            ds = [w for w in app.topLevelWidgets() if isinstance(w, BackupDialog) and w.isVisible()]
            if not ds:
                return
            dialog = state['dialog'] = ds[0]
            check(not dialog.include_settings.isChecked())
            setting.write_text('{"value":"before"}', 'utf-8')
            state['toolbar'] = ['Preferences', None, 'Plugin Backup']
            gprefs['action-layout-toolbar'] = state['toolbar']
            dialog.include_settings.setChecked(True)
            check(dialog.table.columnCount() == 4)
            check(dialog.table.horizontalHeaderItem(0).text() == '全選')
            dialog.table.horizontalHeader().sectionClicked.emit(0)
            check(all(dialog.table.item(r, 0).checkState() == Qt.CheckState.Checked for r in range(dialog.table.rowCount())))
            dialog.table.horizontalHeader().sectionClicked.emit(0)
            check(all(dialog.table.item(r, 0).checkState() == Qt.CheckState.Unchecked for r in range(dialog.table.rowCount())))
            dialog.table.horizontalHeader().sectionClicked.emit(1)
            check(dialog.table.item(0, 0).checkState() == Qt.CheckState.Unchecked)
            check(dialog.selected_button.y() == dialog.export_button.y())
            check(dialog.import_button.y() > dialog.selected_button.y())
            check(dialog.import_button.width() > dialog.export_button.width())
            dialog.selected_button.click()
            check(dialog.process is None and '請先勾選' in dialog.status.text())
            dialog.table.item(0, 0).setCheckState(Qt.CheckState.Checked)
            with patch('calibre_plugins.plugin_backup.ui.QFileDialog.getSaveFileName', return_value=(str(backup), '')):
                dialog.selected_button.click()
            state['step'] = 'selected-export'
        elif state['step'] == 'selected-export' and state['dialog'].process is None:
            dialog = state['dialog']
            check(dialog.status.text().startswith('已匯出'), dialog.details.toPlainText())
            selected = inspect_backup(backup)
            check(len(selected['plugins']) == 1)
            check(not selected['settings']['files'])
            check('builtin_states' not in selected['settings'])
            dialog.grab().save(str(CONFIG / 'backup-dialog.png'))
            with patch('calibre_plugins.plugin_backup.ui.QFileDialog.getSaveFileName', return_value=(str(backup), '')):
                dialog.export_button.click()
            state['step'] = 'export'
        elif state['step'] == 'export' and state['dialog'].process is None:
            dialog = state['dialog']
            check(dialog.status.text().startswith('已匯出'), dialog.status.text() + dialog.details.toPlainText())
            print('EXPORT RESULT', dialog.status.text(), 'expected', str(backup), flush=True)
            manifest = inspect_backup(backup)
            check(manifest['settings']['files'])
            check(len(manifest['plugins']) == 1)
            setting.write_text('{"value":"changed"}', 'utf-8')
            gprefs['action-layout-toolbar'] = ['Preferences']

            def accept(d):
                check(d.settings.isEnabled())
                check(not d.settings.isChecked())
                d.settings.setChecked(True)
                return QDialog.DialogCode.Accepted
            with patch('calibre_plugins.plugin_backup.ui.QFileDialog.getOpenFileName', return_value=(str(backup), '')), patch.object(ImportDialog, 'exec', new=accept):
                dialog.import_button.click()
            state['step'] = 'import'
        elif state['step'] == 'import' and state['dialog'].process is None:
            dialog = state['dialog']
            check(dialog.status.text().startswith('已匯入 1 支外掛，失敗 0 支'), dialog.status.text() + dialog.details.toPlainText())
            check('設定已還原' in dialog.status.text())
            check(list(gprefs['action-layout-toolbar']) == state['toolbar'])
            check(dialog.restart_button.isVisible())
            check(json.loads(setting.read_text('utf-8'))['value'] == 'before')
            dialog.reject()
            state['step'] = 'return'
        elif state['step'] == 'return':
            pref = state['preferences']
            pref.hide_plugin()
            check(not pref._plugin_backup_button.isVisible())
            pref.show_plugin(get_plugin('Advanced', 'Plugins'))
            buttons = [b for b in pref.bb.buttons() if b.text() == '匯出／匯入外掛…']
            check(len(buttons) == 1 and buttons[0].isVisible())
            print('PASS native preferences footer, checkbox, QProcess export/import and setting restore', flush=True)
            finish(True)
    except Exception:
        traceback.print_exc()
        finish(False)
timer = QTimer()
timer.setInterval(100)
timer.timeout.connect(poll)
QTimer.singleShot(6000, timer.start)
run_gui_(opts, args, app)

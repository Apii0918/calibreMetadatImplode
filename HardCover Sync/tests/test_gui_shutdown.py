"""Run with the installed plugin in a fresh dist/ profile; no remote credentials."""
import json
import os
import sys
import traceback
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
CONFIG = Path(config_dir).resolve()
if (ROOT / 'dist').resolve() not in CONFIG.parents or (CONFIG / 'Library').exists():
    raise RuntimeError('請使用 dist 下的新設定目錄。')
from calibre.db.legacy import LibraryDatabase
library = CONFIG / 'Library'
db = LibraryDatabase(str(library))
db.close()
prefs['library_path'] = str(library)
prefs['language'] = 'zh_TW'
from calibre.gui2 import dynamic
dynamic.set('welcome_wizard_was_run', True)
from calibre.gui2.main import init_qt, option_parser, run_gui_
from calibre.gui2.ui import get_gui
from qt.core import QDialog, QTimer

app, _, _ = init_qt(['calibre'])
opts, args = option_parser().parse_args(['--with-library', str(library), '--no-update-check'])
report = {'confirmation_seen': False, 'errors': [], 'mode': os.environ.get('HC_GUI_MODE', 'close')}
original_hook = sys.excepthook


def save_report():
    (CONFIG / 'shutdown-result.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), 'utf-8')


def capture(kind, error, tb):
    report['errors'].append(''.join(traceback.format_exception(kind, error, tb)))
    save_report()
    original_hook(kind, error, tb)


def poll():
    gui = get_gui()
    if gui is None:
        return
    sys.excepthook = capture
    for widget in app.topLevelWidgets():
        if (isinstance(widget, QDialog) and widget.isVisible()
                and type(widget).__module__ == 'calibre.gui2.dialogs.confirm_delete'):
            report['confirmation_seen'] = True
            report['version'] = list(gui.iactions['Hardcover Sync'].interface_action_base_plugin.version)
            timer.stop()
            save_report()
            if report['mode'] == 'accept':
                widget.accept()
                QTimer.singleShot(1000, gui.quit)
            else:
                gui.quit()
            break


sys.excepthook = capture
app.aboutToQuit.connect(save_report)
timer = QTimer()
timer.setInterval(50)
timer.timeout.connect(poll)
QTimer.singleShot(500, timer.start)
QTimer.singleShot(25000, lambda: get_gui().quit())
run_gui_(opts, args, app)

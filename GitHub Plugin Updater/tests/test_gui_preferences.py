"""Native main-window check; use a fresh CALIBRE_CONFIG_DIRECTORY under dist/."""
import json
import traceback
from pathlib import Path

from calibre.utils.config import config_dir, prefs

ROOT = Path(__file__).resolve().parents[2]
profile = Path(config_dir)
if not profile.resolve().is_relative_to((ROOT / 'dist').resolve()):
    raise RuntimeError('Use an isolated profile under dist/.')
from calibre.db.legacy import LibraryDatabase
library = profile / 'Library'
db = LibraryDatabase(str(library))
db.close()
prefs['library_path'], prefs['language'] = str(library), 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2 import dynamic
dynamic.set('welcome_wizard_was_run', True)
from calibre.gui2.main import init_qt, option_parser, run_gui_
from calibre.gui2.ui import get_gui
from calibre.gui2.preferences.main import Preferences, Category
from qt.core import QTimer, QDialog
app, _, _ = init_qt(['calibre'])
opts, args = option_parser().parse_args(['--with-library', str(library), '--no-update-check'])
state = {'step': 'start'}


def finish(ok, error=None):
    (profile / 'gui-result.json').write_text(json.dumps({'success': ok, 'error': error}, ensure_ascii=False), encoding='utf-8')
    timer.stop()
    gui = get_gui()
    if gui is not None:
        gui.quit()


def poll():
    try:
        gui = get_gui()
        if gui is None:
            return
        if state['step'] == 'start':
            if 'GitHub Plugin Updater' in gui.iactions:
                raise RuntimeError('Updater still registered a toolbar action.')
            panel = Preferences(gui)
            panel.show()
            state['panel'] = panel
            category = next(c for c in panel.findChildren(Category)
                            if any(p.name == 'GitHub Plugin Updater' for p in c.plugins))
            if category.label.text() != '進階':
                raise RuntimeError('Wrong preferences category.')
            button = next(button for button, text in category.buttons if text == 'GitHub 外掛更新')
            app.processEvents()
            if not all(button.mapTo(category, button.rect().topLeft()).y() >
                       other.mapTo(category, other.rect().topLeft()).y()
                       for other, text in category.buttons if other is not button):
                raise RuntimeError('Updater did not move to the second row.')
            state['step'] = 'dialog'
            QTimer.singleShot(0, button.click)
        elif state['step'] == 'dialog':
            dialogs = [w for w in app.topLevelWidgets() if isinstance(w, QDialog) and w.isVisible()
                       and w.windowTitle().startswith('GitHub 外掛更新器')]
            if dialogs:
                state['step'] = 'closed'
                dialogs[0].reject()
        elif state['step'] == 'closed':
            if state['panel'].stack.currentIndex() != 0:
                raise RuntimeError('Closing updater did not return to preferences grid.')
            state['panel'].reject()
            finish(True)
    except Exception:
        finish(False, traceback.format_exc())


timer = QTimer()
timer.setInterval(100)
timer.timeout.connect(poll)
QTimer.singleShot(6500, timer.start)
QTimer.singleShot(30000, lambda: finish(False, 'timeout'))
run_gui_(opts, args, app)

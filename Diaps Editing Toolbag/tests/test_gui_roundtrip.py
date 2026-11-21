"""Run edit/reopen phases in separate isolated Edit Book processes."""
import json
import os
import sys
import time
import traceback
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
if not (ROOT / 'dist' in Path(config_dir).resolve().parents):
    raise AssertionError("檢查失敗：ROOT / 'dist' in Path(config_dir).resolve().parents")
prefs['language'] = 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.utils.webengine import setup_fake_protocol, setup_default_profile
setup_fake_protocol()
import calibre.customize.ui
from calibre.gui2 import Application, set_gui_prefs
from calibre.gui2.tweak_book import tprefs, current_container
from calibre.gui2.tweak_book.main import option_parser
from qt.core import QDialog, QFont, QFontDatabase, QTimer, sip
set_gui_prefs(tprefs)
app = Application(['ebook-edit'], color_prefs=tprefs)
app.setQuitOnLastWindowClosed(False)
setup_default_profile()
app.load_builtin_fonts()
if Path('C:/Windows/Fonts/msjh.ttc').exists():
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/msjh.ttc')
    app.setFont(QFont('Microsoft JhengHei UI', 10))
from calibre.gui2.tweak_book.ui import Main
from calibre.gui2.tweak_book.plugin import _tool_memory
opts, args = option_parser().parse_args(['ebook-edit'])
gui = Main(opts)
gui.show()
book = Path(os.environ['TOOLBAG_GUI_BOOK']).resolve()
if not (ROOT / 'dist' in book.parents):
    raise AssertionError("檢查失敗：ROOT / 'dist' in book.parents")
phase = os.environ.get('TOOLBAG_GUI_PHASE', 'edit')
gui.boss.open_book(str(book))
state = {'step': 'open', 'deadline': time.monotonic() + 60}
exit_code = 1


def finish(ok):
    global exit_code
    exit_code = 0 if ok else 1
    timer.stop()
    (Path(config_dir) / ('gui-' + phase + '.json')).write_text(json.dumps({'success': ok, 'phase': phase}), 'utf-8')
    if not ok:
        gui.action_save.setEnabled(False)
    gui.close()


def check_content(container):
    for name in ('a.xhtml', 'b.xhtml'):
        raw = container.raw_data(name)
        if not ('class="junk"' not in raw):
            raise AssertionError('檢查失敗：\'class="junk"\' not in raw')
        if not ('<span class="keep">保留</span>' in raw):
            raise AssertionError('檢查失敗：\'<span class="keep">保留</span>\' in raw')
        if not ('“Hello”' in raw and '—' in raw and '…' in raw):
            raise AssertionError("檢查失敗：'“Hello”' in raw and '—' in raw and '…' in raw")
        if not ('&amp;' in raw and 'id="keep"' in raw):
            raise AssertionError('檢查失敗：\'&amp;\' in raw and \'id="keep"\' in raw')
    if not ('cm' not in container.raw_data('style.css')):
        raise AssertionError("檢查失敗：'cm' not in container.raw_data('style.css')")
    if not ('2.37em' in container.raw_data('style.css')):
        raise AssertionError("檢查失敗：'2.37em' in container.raw_data('style.css')")
    if not ('cm' not in container.raw_data('other.css')):
        raise AssertionError("檢查失敗：'cm' not in container.raw_data('other.css')")


def poll():
    try:
        if not (time.monotonic() < state['deadline']):
            raise AssertionError(state)
        if state['step'] == 'open':
            c = current_container()
            if c is None or not hasattr(gui.boss, 'global_undo') or gui.boss.global_undo.pos < 1:
                return
            if not (Path(c.path_to_ebook) == book):
                raise AssertionError('檢查失敗：Path(c.path_to_ebook) == book')
            if phase == 'reopen':
                check_content(c)
                print('PASS native Edit Book reopen: all three changes persisted', flush=True)
                finish(True)
                return
            from calibre_plugins.diaps_toolbag import dialogs
            tools = {t.name: t for t in _tool_memory if t.plugin.name == 'Diaps Editing Toolbag'}
            if not (set(tools) == {'SpanDivEdit', 'SmarterPunct', 'CSScm2em'}):
                raise AssertionError("檢查失敗：set(tools) == {'SpanDivEdit', 'SmarterPunct', 'CSScm2em'}")
            for t in tools.values():
                if not (not t.create_action(True).icon().isNull()):
                    raise AssertionError('檢查失敗：not t.create_action(True).icon().isNull()')
                t.parse_current = False
            def accept_span(d):
                d.tag_combo.setCurrentText('span')
                d.attr_combo.setCurrentText('class')
                d.srch_txt.setText('junk')
                d.grab().save(str(Path(config_dir) / 'span-dialog.png'))
                d._ok_clicked()
                return d.result()
            def accept_punct(d):
                d.edu_quotes.setChecked(True)
                d.ellipses.setChecked(True)
                d.unicode.setChecked(True)
                d.grab().save(str(Path(config_dir) / 'punct-dialog.png'))
                d._ok_clicked()
                return d.result()
            with patch.object(dialogs.ResultsDialog, 'exec', return_value=QDialog.DialogCode.Rejected), patch.object(dialogs.RemoveDialog, 'exec', new=accept_span), patch.object(dialogs.PunctDialog, 'exec', new=accept_punct):
                tools['SpanDivEdit'].dispatcher()
                tools['SmarterPunct'].dispatcher()
                tools['CSScm2em'].dispatcher()
            if not (gui.boss.global_undo.pos >= 4):
                raise AssertionError('檢查失敗：gui.boss.global_undo.pos >= 4')
            if not (gui.action_save.isEnabled()):
                raise AssertionError('檢查失敗：gui.action_save.isEnabled()')
            gui.action_save.trigger()
            state['step'] = 'saved'
        elif state['step'] == 'saved' and not gui.boss.save_manager.has_tasks:
            if not (not gui.action_save.isEnabled()):
                raise AssertionError('檢查失敗：not gui.action_save.isEnabled()')
            with ZipFile(book) as z:
                if not ('“Hello”' in z.read('a.xhtml').decode('utf-8')):
                    raise AssertionError("檢查失敗：'“Hello”' in z.read('a.xhtml').decode('utf-8')")
                if not ('2.37em' in z.read('style.css').decode('utf-8')):
                    raise AssertionError("檢查失敗：'2.37em' in z.read('style.css').decode('utf-8')")
            print('PASS native Edit Book: three tools, savepoints and real Save', flush=True)
            finish(True)
    except Exception:
        traceback.print_exc()
        finish(False)


timer = QTimer()
timer.setInterval(50)
timer.timeout.connect(poll)
timer.start()
app.exec()
from calibre.gui2.tweak_book.preview import parse_worker
deadline = time.monotonic() + 15
while parse_worker.is_alive() and time.monotonic() < deadline:
    time.sleep(0.05)
from calibre.ebooks.oeb.polish.check.css import shutdown
shutdown()
sip.delete(gui)
raise SystemExit(exit_code)

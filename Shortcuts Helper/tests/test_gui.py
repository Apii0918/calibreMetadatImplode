import json,sys,traceback
from pathlib import Path
from calibre.utils.config import config_dir,prefs
profile=Path(config_dir);root=Path.cwd()
if (root/'dist') not in profile.parents:raise RuntimeError('Wrong profile')
from calibre.db.legacy import LibraryDatabase
library=profile/'Library';db=LibraryDatabase(str(library));db.close();prefs['library_path']=str(library);prefs['language']='zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2 import dynamic
dynamic.set('welcome_wizard_was_run',True)
from calibre.gui2.main import init_qt,option_parser,run_gui_
from calibre.gui2.ui import get_gui
from qt.core import QTimer,QDialog,QWidget
app,_,_=init_qt(['calibre']);opts,args=option_parser().parse_args(['--with-library',str(library),'--no-update-check'])
state={'step':'start'}
def finish(ok,error=None):
 (profile/'gui-result.json').write_text(json.dumps({'success':ok,'error':error},ensure_ascii=False),'utf-8');timer.stop();get_gui().quit()
def poll():
 try:
  gui=get_gui()
  if gui is None:return
  action=gui.iactions['Shortcuts Helper']
  if state['step']=='start':
   if action.qaction.text()!='快捷鍵助手' or action.qaction.icon().isNull():raise RuntimeError('Chinese action/icon missing')
   action._show_current_shortcuts();dialog=action._current_shortcuts_dialog
   if dialog.windowTitle()!='目前快捷鍵' or dialog.table.rowCount()==0:raise RuntimeError('Listing missing')
   dialog.close();state['step']='prefs';QTimer.singleShot(0,action._show_shortcuts_prefs)
  elif state['step']=='prefs':
   dialogs=[w for w in app.topLevelWidgets() if isinstance(w,QDialog) and w.isVisible() and type(w).__module__=='calibre.gui2.preferences.main']
   if not dialogs:return
   panel=dialogs[0]
   modules={type(w).__module__ for w in panel.findChildren(QWidget)}
   if not any('keyboard' in m for m in modules):raise RuntimeError('Wrong preferences panel '+str(modules))
   panel.reject();state['step']='done'
  elif state['step']=='done':
   print('PASS native Chinese action/icon, real shortcut listing and keyboard preferences',flush=True);finish(True)
 except Exception:finish(False,traceback.format_exc())
timer=QTimer();timer.setInterval(100);timer.timeout.connect(poll);QTimer.singleShot(6500,timer.start);QTimer.singleShot(30000,lambda:finish(False,'timeout'));run_gui_(opts,args,app)

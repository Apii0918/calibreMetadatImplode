import sys
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.preferences import TWEAKS
from calibre.gui2 import Application
from calibre.gui2.preferences.look_feel import ConfigWidget
from calibre.gui2.preferences.tweaks import ConfigWidget as TweaksWidget, Tweaks
from qt.core import QWidget, QLabel, QComboBox, QLineEdit, QPlainTextEdit, Qt
from unittest.mock import Mock
app=Application([])
w=ConfigWidget()
snapshots=[(c,c.currentIndex(),[c.itemData(i) for i in range(c.count())]) for c in w.findChildren(QComboBox)]
for child in [w,*w.findChildren(QWidget)]:
    translate_widget(child)
for c,index,data in snapshots:
    assert c.currentIndex()==index
    assert data==[c.itemData(i) for i in range(c.count())]
assert w.tabWidget.tabText(2)=='書架檢視'
assert not any(x.text() in ('Change &icon theme','&Recount pages') for x in w.findChildren(QLabel))
tw=TweaksWidget()
tw.tweaks_view.setModel(Tweaks())
tw.current_changed=Mock()
before=[(dict(t.default_values),dict(t.custom_values)) for t in tw.tweaks_view.model().tweaks]
translate_widget(tw)
after=[(dict(t.default_values),dict(t.custom_values)) for t in tw.tweaks_view.model().tweaks]
assert before==after
assert all(t.name==TWEAKS[t.var_names[0]][0] for t in tw.tweaks_view.model().tweaks if t.var_names[0] in TWEAKS)
tw.help.setPlainText('Help for this tweak\n\nID: example')
assert tw.help.toPlainText().startswith('此調校設定的說明')
root=type('ConfigWidget',(QWidget,),{'__module__':'calibre.gui2.preferences.search'})()
label=QLabel('Show text next to buttons in the search bar',root)
edit=QLineEdit('title, authors',root)
translate_widget(label); translate_widget(edit)
assert label.text()=='在搜尋列按鈕旁顯示文字'
assert edit.text()=='title, authors'
print('PASS real look/feel tabs and tweak models; identifiers, values and user text preserved')

from calibre.gui2.preferences.search import ConfigWidget as SearchWidget
from calibre_plugins.traditional_chinese_supplement.preferences import TEXT
search_widget = SearchWidget()
source = next(text for text in TEXT if text.startswith('<b>Grouped search terms</b>'))
search_widget.gst_explanation.setHtml(source)
translate_widget(search_widget)
assert search_widget.gst_explanation.toPlainText().startswith('群組搜尋字詞')
print('PASS real read-only grouped-search explanation')

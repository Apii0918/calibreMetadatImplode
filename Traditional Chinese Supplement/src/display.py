from qt.core import (QAbstractButton, QAbstractItemView, QAction, QGroupBox, QLabel,
                     QLineEdit, QMainWindow, QMenu, QPlainTextEdit, QTextEdit, QToolButton, QWidget)
from calibre_plugins.traditional_chinese_supplement.strings import COMMON, SCOPES
from calibre_plugins.traditional_chinese_supplement.editor_strings import EDITOR_SCOPE, EDITOR_TEXT
from pathlib import Path
import re
import sys
import html
from calibre_plugins.traditional_chinese_supplement.preferences import (
    DIALOG_MODULES, RULE_HELP, TEXT, translate_hover, translate_preferences,
)


def scope_for(widget):
    node = widget
    while isinstance(node, QWidget):
        if isinstance(node, (QAbstractItemView, QLineEdit, QPlainTextEdit, QTextEdit)):
            return None
        module = type(node).__module__
        if module == 'config':
            archive = getattr(getattr(sys.modules.get(module), '__loader__', None), 'archive', '')
            if Path(archive).name == 'DeDRM.zip':
                return 'dedrm'
        for scope in SCOPES:
            prefix = scope if scope.startswith('calibre.') else 'calibre_plugins.' + scope
            if module == prefix or module.startswith(prefix + '.'):
                return scope
        node = node.parentWidget()
    return None


SAVE_TEMPLATE_HELP = re.compile(
    r'\s+'.join((
        r'The template to control the filename and folder structure of the saved files\. Default is',
        r'"([^"]+)" which will save books into a per-author subfolder with filenames containing title and author\.',
        r'Available controls are: (\{[^}]+\})',
    )).replace(' ', r'\s+')
)


def translate_save_help(text):
    def replace(match):
        template, controls = match.groups()
        result = f'指定儲存檔案的名稱與資料夾結構。預設範本為「{template}」，會依作者建立子資料夾'
        if controls:
            result += f'，檔名包含書名與作者。可用欄位：{{' '.join(controls.split())}'
        return result + '。'
    return SAVE_TEMPLATE_HELP.sub(replace, text)


def translate_save_template(widget):
    description = widget.help_label.text()
    translated = description.replace(
        '<b>Title and series</b> will have articles moved to the end unless you change the tweak "save_template_title_series_sorting"',
        '除非調整「儲存範本的書名與系列排序」微調設定（<code>save_template_title_series_sorting</code>），否則會將<b>書名與系列名稱</b>開頭的冠詞移到末尾。',
    )
    if translated != description:
        widget.help_label.setText(translated)
    browser = widget.template_variables
    html = browser.toHtml()
    if 'The calibre internal page count' in html:
        browser.setHtml(html.replace('The calibre internal page count', 'calibre 內建頁數統計'))
    combo = widget.opt_template
    for field in (combo, combo.lineEdit()):
        if field is not None:
            for getter, setter in ((field.toolTip, field.setToolTip),
                                   (field.statusTip, field.setStatusTip),
                                   (field.whatsThis, field.setWhatsThis)):
                original = getter()
                translated = translate_save_help(original)
                if translated != original:
                    setter(translated)



def translate_widget(widget):
    if not isinstance(widget, QWidget):
        return
    translate_hover(widget)
    if (
        type(widget).__module__.startswith('calibre.gui2.preferences.')
        or type(widget).__module__ in DIALOG_MODULES
    ):
        translate_preferences(widget)
    scope = scope_for(widget)
    if scope is None:
        return
    if type(widget).__module__ == 'calibre.gui2.preferences.save_template':
        translate_save_template(widget)
    texts = SCOPES[scope]
    def translated(text):
        if scope.startswith('calibre.gui2'):
            text = text.replace(
                ' (only one template dialog allowed)', '（同時只能開啟一個範本視窗）',
            )
            plain_text = re.sub('<[^>]*>', '', text)
            plain_text = re.sub(r'&(?!#\d+;|#x[0-9a-fA-F]+;|[A-Za-z][A-Za-z0-9]+;)', '', plain_text)
            normalized = ' '.join(html.unescape(plain_text).split())
            if text in TEXT:
                return TEXT[text]
            if normalized in TEXT:
                return TEXT[normalized]
            if normalized.startswith('default: #') and re.fullmatch(r'default: #[0-9a-fA-F]{6}', normalized):
                return normalized.replace('default:', '預設值：', 1)
            for source in ('Change color', 'Change texture', 'Read progress'):
                text = text.replace('>' + source + '</a>', '>' + TEXT[source] + '</a>')
            for source, target in RULE_HELP.items():
                text = text.replace(source, target)
        if scope == EDITOR_SCOPE and text in SCOPES['calibre.gui2']:
            return SCOPES['calibre.gui2'][text]
        return texts.get(text, COMMON.get(text, text))
    for getter, setter in (('toolTip', 'setToolTip'), ('statusTip', 'setStatusTip'), ('whatsThis', 'setWhatsThis')):
        old = getattr(widget, getter)()
        new = translated(old)
        if new != old:
            getattr(widget, setter)(new)
    if scope.startswith('calibre.gui2'):
        title = widget.windowTitle()
        new_title = translated(title)
        if new_title != title:
            QWidget.setWindowTitle(widget, new_title)
    if scope == EDITOR_SCOPE:
        if isinstance(widget, QMainWindow):
            for action in widget.findChildren(QAction):
                for getter, setter in ((action.text, action.setText), (action.toolTip, action.setToolTip),
                                       (action.statusTip, action.setStatusTip)):
                    old = getter()
                    new = EDITOR_TEXT.get(old, old)
                    if new != old:
                        setter(new)
        elif isinstance(widget, QMenu):
            old = widget.title()
            new = EDITOR_TEXT.get(old, old)
            if new != old:
                widget.setTitle(new)
    # Combo/list/table values can be program identifiers; never change their models.
    if isinstance(widget, (QLabel, QAbstractButton)) and (
        not isinstance(widget, QToolButton) or scope.startswith('calibre.gui2')
    ):
        old = widget.text()
        new = translated(old)
        if scope.startswith('calibre.gui2') and isinstance(widget, QLabel):
            new = translate_save_help(new)
        if scope == 'dedrm':
            new = new.replace('>Plugin Help</a>', '>外掛說明</a>')
        if new != old:
            widget.setText(new)
    elif isinstance(widget, QGroupBox):
        old = widget.title()
        new = translated(old)
        if new != old:
            widget.setTitle(new)

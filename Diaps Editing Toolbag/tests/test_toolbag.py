"""Native Qt/container regression tests; install the ZIP in an isolated config first."""
import ast
import gettext
import io
import os
import re
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
if not (ROOT / 'dist' in Path(config_dir).resolve().parents):
    raise AssertionError("檢查失敗：ROOT / 'dist' in Path(config_dir).resolve().parents")
prefs['language'] = 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2 import Application
from qt.core import QDialog, QFont, QFontDatabase, QWidget
app = Application([])
app.setQuitOnLastWindowClosed(False)
if Path('C:/Windows/Fonts/msjh.ttc').exists():
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/msjh.ttc')
    app.setFont(QFont('Microsoft JhengHei UI', 10))
from calibre.customize.ui import all_edit_book_tool_plugins
from calibre.gui2.tweak_book.plugin import load_plugin_tools
from calibre.gui2.tweak_book import editors, set_current_container
from calibre.gui2.tweak_book.editor.widget import Editor
from calibre.ebooks.oeb.polish.container import get_container
plugin = next(p for p in all_edit_book_tool_plugins() if p.name == 'Diaps Editing Toolbag')
tools = {t.name: t for t in load_plugin_tools(plugin)}
from calibre_plugins.diaps_toolbag import main, dialogs, span_div_config


def make_fixture(path):
    with ZipFile(path, 'w') as z:
        z.writestr('mimetype', 'application/epub+zip')
        z.writestr('META-INF/container.xml', '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        z.writestr('content.opf', '<package xmlns="http://www.idpf.org/2007/opf" version="2.0" unique-identifier="id"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:identifier id="id">test-toolbag</dc:identifier><dc:title>工具測試</dc:title><dc:language>zh-TW</dc:language></metadata><manifest><item id="a" href="a.xhtml" media-type="application/xhtml+xml"/><item id="b" href="b.xhtml" media-type="application/xhtml+xml"/><item id="css" href="style.css" media-type="text/css"/><item id="css2" href="other.css" media-type="text/css"/></manifest><spine><itemref idref="a"/><itemref idref="b"/></spine></package>')
        for name in ('a.xhtml', 'b.xhtml'):
            z.writestr(name, '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>測試</title><link rel="stylesheet" href="style.css"/></head><body><p id="keep"><span class="junk">中文<span class="keep">保留</span></span><i class="em">強調</i> "Hello" -- ... &amp; &#160;</p><p>\'tis nice</p><p>\'tis again</p></body></html>')
        z.writestr('style.css', 'p {margin: 1cm -0.5cm 0 12px; font-size: 1em} @page {margin: 2cm}')
        z.writestr('other.css', 'p {text-indent: 0.5cm}')


class ToolbagTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        path = Path(self.temp.name) / 'book.epub'
        make_fixture(path)
        self.container = get_container(str(path))
        set_current_container(self.container)
        self.gui = QWidget()
        self.gui.central = SimpleNamespace(current_editor=None)
        self.boss = SimpleNamespace(gui=self.gui, commit_all_editors_to_container=Mock(),
                                    add_savepoint=Mock(), show_current_diff=Mock(),
                                    apply_container_update_to_gui=Mock(), revert_requested=Mock(),
                                    global_undo=SimpleNamespace(previous_container=object()))
        self.addCleanup(patch.stopall)
        patch('calibre.gui2.tweak_book.plugin.get_boss', return_value=self.boss).start()
        patch.object(main, 'info_dialog').start()
        patch.object(main, 'error_dialog').start()
        patch.object(dialogs.ResultsDialog, 'exec', return_value=QDialog.DialogCode.Rejected).start()
        for t in tools.values():
            t.create_action(True)
            t.parse_current = True
        editors.clear()

    def current(self, name):
        editor = Editor('css' if name.endswith('.css') else 'html')
        editor.data = self.container.raw_data(name)
        editors[name] = editor
        self.gui.central.current_editor = editor

    def accept_span(self, dialog):
        dialog.tag_combo.setCurrentText('span')
        dialog.attr_combo.setCurrentText('class')
        dialog.srch_txt.setText('junk')
        dialog._ok_clicked()
        return dialog.result()

    def test_span_current_and_all(self):
        self.current('a.xhtml')
        tool = tools['SpanDivEdit']
        with patch.object(dialogs.RemoveDialog, 'exec', new=lambda d: self.accept_span(d)):
            tool.dispatcher()
            self.assertEqual(tool.changed_files, ['a.xhtml'])
            self.assertIn('<span class="keep">保留</span>', self.container.raw_data('a.xhtml'))
            self.assertNotIn('class="junk"', self.container.raw_data('a.xhtml'))
            self.assertIn('class="junk"', self.container.raw_data('b.xhtml'))
            tool.parse_current = False
            tool.dispatcher()
        self.assertNotIn('class="junk"', self.container.raw_data('b.xhtml'))
        self.assertIn('id="keep"', self.container.raw_data('b.xhtml'))

    def test_modify_regex_and_naked_tags(self):
        tool = tools['SpanDivEdit']
        s = '<p><i class="em">甲</i><i>乙</i></p>'
        changed = tool.delete_modify(s, ('e.*', 'regex', 'i', 'class', 'modify', 'em', '', True))
        self.assertEqual(changed, '<p><em class="em">甲</em><i>乙</i></p>')
        self.assertEqual(tool.delete_modify(changed, (None, 'normal', 'i', None, 'delete', None, '', False)), '<p><em class="em">甲</em>乙</p>')

    def test_punctuation_options_and_exception_file(self):
        tool = tools['SmarterPunct']
        s = '<p>"Hello" -- ... &amp; &#160;</p>'
        self.assertEqual(tool.smarten(s, ('0', True, [])), s)
        out = tool.smarten(s, ('qde', True, []))
        self.assertIn('“Hello” — … &amp; &#160;', out)
        self.assertIn('&#8220;', tool.smarten(s, ('q', False, [])))
        f = Path(self.temp.name) / 'exceptions.txt'
        f.write_text('tis\n\n', 'utf-8')
        d = dialogs.PunctDialog(self.gui)
        words = d.parseExceptionsFile(str(f))
        self.assertEqual(words, ['tis'])
        out = tool.smarten("<p>'tis nice</p><p>'tis again</p>", ('q', True, words))
        self.assertEqual(out.count('’tis'), 2)

    def test_punctuation_dispatch_all_and_roundtrip(self):
        self.current('a.xhtml')
        tool = tools['SmarterPunct']
        tool.parse_current = False
        def accept(d):
            d.edu_quotes.setChecked(True)
            d.ellipses.setChecked(True)
            d.unicode.setChecked(True)
            d._ok_clicked()
            return d.result()
        with patch.object(dialogs.PunctDialog, 'exec', new=accept):
            tool.dispatcher()
        self.assertEqual(set(tool.changed_files), {'a.xhtml', 'b.xhtml'})
        out = Path(self.temp.name) / 'saved.epub'
        self.container.commit(str(out))
        reopened = get_container(str(out))
        self.assertIn('“Hello”', reopened.raw_data('b.xhtml'))
        self.assertIn('&amp;', reopened.raw_data('b.xhtml'))

    def test_css_current_all_and_roundtrip(self):
        self.current('style.css')
        tool = tools['CSScm2em']
        original = self.container.raw_data('a.xhtml')
        tool.dispatcher()
        css = self.container.parsed('style.css').cssText.decode('utf-8')
        self.assertIn('2.37em', css)
        self.assertIn('-1.19em', css)
        self.assertIn('4.74em', css)
        self.assertIn('12px', css)
        self.assertIn('0.5cm', self.container.raw_data('other.css'))
        tool.parse_current = False
        tool.dispatcher()
        out = Path(self.temp.name) / 'css.epub'
        self.container.commit(str(out))
        reopened = get_container(str(out))
        self.assertNotIn('cm', reopened.raw_data('other.css'))
        self.assertEqual(reopened.raw_data('a.xhtml'), original)

    def test_dialogs_translations_and_help(self):
        ds = [dialogs.RemoveDialog(self.gui), dialogs.PunctDialog(self.gui), span_div_config.ConfigWidget(self.gui)]
        self.assertEqual(ds[0].windowTitle(), '編輯 span 與 div')
        self.assertEqual(ds[1].windowTitle(), '進階智慧標點')
        for suffix in ('span_div', 'smarten'):
            html = dialogs.load_resource('resources/diaps_editing_toolbag_' + suffix + '_help.html').decode('utf-8')
            self.assertIn('lang="zh-Hant"', html)
            self.assertNotIn('Stuff.', html)
        with ZipFile(plugin.plugin_path) as z:
            cat = gettext.GNUTranslations(io.BytesIO(z.read('translations/zh_TW.mo')))
        for p in (ROOT / 'Diaps Editing Toolbag/src').glob('*.py'):
            for n in ast.walk(ast.parse(p.read_text('utf-8'))):
                if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == '_' and n.args and isinstance(n.args[0], ast.Constant):
                    msg = n.args[0].value
                    self.assertIn(msg, cat._catalog)
                    self.assertEqual(re.findall(r'\{[^}]*\}', msg), re.findall(r'\{[^}]*\}', cat.gettext(msg)))

    def test_cancel_and_progress_errors(self):
        self.current('a.xhtml')
        tool = tools['SpanDivEdit']
        before = self.container.raw_data('a.xhtml')
        with patch.object(dialogs.RemoveDialog, 'exec', return_value=QDialog.DialogCode.Rejected):
            tool.dispatcher()
        self.assertEqual(self.container.raw_data('a.xhtml'), before)
        self.boss.add_savepoint.assert_not_called()
        tool.parse_current = False
        with patch.object(dialogs.RemoveDialog, 'exec', new=lambda d: self.accept_span(d)), patch.object(tool, 'delete_modify', side_effect=ValueError('test rollback')):
            tool.dispatcher()
        self.boss.revert_requested.assert_called_once_with(self.boss.global_undo.previous_container)
        self.assertEqual(self.container.raw_data('a.xhtml'), before)


if __name__ == '__main__':
    if os.environ.get('TOOLBAG_FIXTURE'):
        make_fixture(os.environ['TOOLBAG_FIXTURE'])
    else:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToolbagTests))
        raise SystemExit(0 if result.wasSuccessful() else 1)

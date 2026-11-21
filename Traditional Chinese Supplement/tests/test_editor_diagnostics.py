import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from html import unescape

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre_plugins.traditional_chinese_supplement.main import TranslationTool
from calibre.gui2 import Application
from calibre.gui2.tweak_book import grammar
from calibre.gui2.tweak_book.check import Check, build_error_message
from calibre.ebooks.oeb.polish.check import accessibility as a
from calibre.ebooks.oeb.polish.check.base import BaseError
from qt.core import QAction, QLabel, QMainWindow, Qt, QWidget


class EditorDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_native_grammar_panels_and_existing_actions(self):
        root = type('EditorWindow', (QMainWindow,), {'__module__': 'calibre.gui2.tweak_book.ui'})()
        rewrite = QAction('Rewrite suggestions', root)
        rewrite.setData('rewrite-suggestions')
        check = QAction('Check &grammar', root)
        check.setData('grammar-check-book')
        with patch.object(ui, 'get_lang', return_value='zh_TW'):
            tool = TranslationTool()
        windows = []
        try:
            root.show()
            self.app.processEvents()
            self.assertEqual(rewrite.text(), '改寫建議')
            self.assertEqual(check.text(), '檢查文法(&G)')
            self.assertEqual(rewrite.data(), 'rewrite-suggestions')
            self.assertEqual(check.data(), 'grammar-check-book')
            panel = grammar.RewriteSuggestionsPanel(root)
            windows.append(panel)
            panel.show()
            panel.update_target()
            self.assertIn('將游標放在 HTML', panel.suggestions.status.text())
            self.assertEqual(set(panel.suggestions.kind_boxes), {'grammar', 'fluency', 'clarity', 'simplify', 'formal', 'paraphrase'})
            checker = grammar.GrammarCheck(root)
            windows.append(checker)
            self.assertEqual(checker.windowTitle(), '檢查文法')
            self.assertIn('重新檢查書本', '\n'.join(c.toolTip() for c in checker.findChildren(QWidget)))
        finally:
            for window in windows:
                window.close()
            tool.translator.stop()
            root.close()

    def test_accessibility_messages_help_and_locations(self):
        with patch.object(ui, 'get_lang', return_value='zh_TW'):
            tool = TranslationTool()
        panel = None
        try:
            errors = [a.MissingAltText('OEBPS/Text/cover.xhtml', [8]),
                      a.MissingAccessibilityMetadata('OEBPS/content.opf', ['schema:accessMode']),
                      a.MissingAccessibilitySummary('OEBPS/content.opf'),
                      a.MissingRole('OEBPS/nav.xhtml', [12]),
                      a.MissingLanguage([('chapter.xhtml', 3)], 'zh-TW'),
                      a.MissingPackageLanguage('content.opf', 2, 'zh-TW'),
                      a.SkippedHeadingLevel('chapter.xhtml', [4, 18])]
            locations = [(e.name, e.line, e.col, e.level) for e in errors]
            panel = Check()
            with patch('calibre.gui2.tweak_book.check.show_accessibility_problems', return_value=True):
                panel.populate(errors)
            self.assertEqual(panel.items.count(), len(errors))
            for row in range(panel.items.count()):
                item = panel.items.item(row)
                error = item.data(Qt.ItemDataRole.UserRole)
                self.assertRegex(error.msg, '[\u4e00-\u9fff]')
                self.assertRegex(unescape(error.HELP), '[\u4e00-\u9fff]')
                self.assertIn(error.name, build_error_message(error))
                panel.items.setCurrentRow(row)
                self.assertIn('自動', panel.help.toPlainText())
                self.assertIn(error.name, panel.help.toPlainText())
            self.assertIn('alt=""', unescape(errors[0].HELP))
            self.assertIn('aria-hidden="true"', unescape(errors[0].HELP))
            self.assertIn('schema:accessMode', unescape(errors[1].HELP))
            self.assertIn('role="doc-noteref"', unescape(errors[3].HELP))
            self.assertEqual(locations, [(e.name, e.line, e.col, e.level) for e in errors])
            self.assertEqual(a.MissingAltText('x.xhtml', [1, 2]).msg, '2 張圖片缺少替代文字')
            for name, module in tuple(sys.modules.items()):
                if name.startswith('calibre.ebooks.oeb.polish.check.'):
                    for cls in vars(module).values():
                        if isinstance(cls, type) and issubclass(cls, BaseError) and cls.__module__ == name:
                            for attribute in ('HELP', 'RULE_NAME', 'INDIVIDUAL_FIX'):
                                text = vars(cls).get(attribute)
                                if isinstance(text, str) and text:
                                    self.assertRegex(text, '[\u4e00-\u9fff]', f'{cls.__name__}.{attribute}')
        finally:
            if panel is not None:
                panel.close()
            tool.translator.stop()


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(EditorDiagnosticsTests))
if not result.wasSuccessful():
    raise SystemExit(1)

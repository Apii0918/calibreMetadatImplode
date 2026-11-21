import ast
import re
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.template_help import FUNCTION_HELP, STORED_HELP
from calibre.gui2 import Application
from calibre.db.legacy import LibraryDatabase
from calibre.gui2.preferences.template_functions import ConfigWidget
from qt.core import QWidget, QLineEdit, QPlainTextEdit, QTextEdit, QTabWidget, QLabel, QAbstractButton, QAbstractSpinBox


class TemplateFunctionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_native_tabs_help_tooltips_preserve_user_programs(self):
        with TemporaryDirectory() as temporary:
            db = LibraryDatabase(str(Path(temporary) / 'Library'))
            gui = QWidget()
            gui.current_db = db
            gui.library_view = SimpleNamespace(model=lambda: SimpleNamespace(db=db), get_selected_ids=lambda: [])
            gui.current_view = lambda: SimpleNamespace(selectionModel=lambda: SimpleNamespace(selectedRows=lambda: []))
            translator = ui.TranslationFilter()
            panel = None
            try:
                with patch('calibre.gui2.ui.get_gui', return_value=gui), patch.object(ui, 'get_lang', return_value='zh_TW'):
                    panel = ConfigWidget()
                    panel.genesis(gui)
                    panel.initialize()
                    panel.program.setPlainText('def evaluate(self, formatter, kwargs, mi, locals, value):\n    return value')
                    panel.documentation.setPlainText('User documentation must stay unchanged')
                    before = [(c, c.text()) for c in panel.findChildren(QLineEdit)
                              if not isinstance(c.parentWidget(), QAbstractSpinBox)]
                    numbers = [(c, c.value()) for c in panel.findChildren(QAbstractSpinBox) if hasattr(c, 'value')]
                    before += [(c, c.toPlainText()) for c in panel.findChildren(QPlainTextEdit)]
                    before += [(c, c.toPlainText()) for c in panel.findChildren(QTextEdit) if not c.isReadOnly()]
                    stored = db.prefs.get('user_template_functions', [])
                    translator.start()
                    panel.show()
                    self.app.processEvents()
                    for tab in panel.findChildren(QTabWidget):
                        for index in range(tab.count()):
                            tab.setCurrentIndex(index)
                            self.app.processEvents()
                            self.assertNotEqual(tab.tabText(index).replace('&', ''), 'Template functions')
                    self.assertTrue(panel.textBrowser.toPlainText().startswith('您可以在此加入或移除'))
                    self.assertTrue(panel.st_textBrowser.toPlainText().startswith('您可以在此建立'))
                    for c in panel.findChildren(QWidget):
                        tip = c.toolTip()
                        if tip:
                            self.assertRegex(tip, '[\u4e00-\u9fff]', c.objectName())
                        if isinstance(c, (QLabel, QAbstractButton)):
                            self.assertNotIn(c.text().replace('&', ''), ('Import', 'Edit docs', 'Go'))
                    for c, expected in before:
                        actual = c.text() if isinstance(c, QLineEdit) else c.toPlainText()
                        self.assertEqual(actual, expected, c.objectName())
                    self.assertTrue(all(c.value() == value for c, value in numbers))
                    translate_widget(panel)
                    self.assertEqual(stored, db.prefs.get('user_template_functions', []))
                    self.assertFalse(translator.failures)
            finally:
                translator.stop()
                if panel is not None:
                    panel.close()
                db.close()
                gui.close()

    def test_help_examples_remain_valid(self):
        code = re.search(r'<pre>(.*?)</pre>', FUNCTION_HELP, re.S).group(1)
        ast.parse(code)
        namespace = {}
        exec(code, namespace)
        self.assertEqual(namespace['evaluate'](None, None, None, None, None, 'value'), 'value')
        self.assertEqual(namespace['evaluate'](None, None, None, None, None, ''), 'EMPTY')
        for token in ('formatter', 'kwargs', 'mi', 'locals', '*args', '{tags:my_ifempty()}',
                      "{tags:'my_ifempty($)'}", "program: my_ifempty(field('tags'))"):
            self.assertIn(token, FUNCTION_HELP)
        for token in ('program:', 'python:', 'arguments()', 'context', 'arguments',
                      "arguments(lst='No list argument given', items='');",
                      "program: items_in_list($#genre, 'comics, foo')"):
            self.assertIn(token, STORED_HELP)


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TemplateFunctionTests))
if not result.wasSuccessful():
    raise SystemExit(1)

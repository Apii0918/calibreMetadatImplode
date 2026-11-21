import re
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.preferences import TWEAKS
from calibre_plugins.traditional_chinese_supplement.tweak_strings import TWEAK_DOCS
from calibre.gui2 import Application
from calibre.gui2.preferences.tweaks import ConfigWidget
from qt.core import Qt


class TweakHelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_every_tweak_help_and_selection_preserve_values(self):
        panel = ConfigWidget()
        panel.genesis(SimpleNamespace())
        panel.initialize()
        model = panel.tweaks_view.model()
        originals = deepcopy([(t.var_names, t.default_values, t.custom_values) for t in model.tweaks])
        english_ids = {t.var_names[0] for t in model.tweaks if not re.search('[\u4e00-\u9fff]', t.doc)}
        self.assertTrue(english_ids.issubset(TWEAK_DOCS))
        self.assertEqual(len(model.tweaks), 43)
        panel.set_edit_text('# 啟用翻譯前尚未儲存的編輯\n' + panel.edit_tweak.toPlainText())
        initial_edit = panel.edit_tweak.toPlainText()
        translator = ui.TranslationFilter()
        try:
            with patch.object(ui, 'get_lang', return_value='zh_TW'):
                translator.start()
                self.assertEqual(panel.edit_tweak.toPlainText(), initial_edit)
                panel.set_edit_text(model.tweaks[0].edit_text)
                panel.show()
                self.app.processEvents()
                for row, tweak in enumerate(model.tweaks):
                    panel.tweaks_view.setCurrentIndex(model.index(row, 0))
                    self.app.processEvents()
                    displayed = panel.help.toPlainText()
                    self.assertTrue(displayed.startswith('此調校設定的說明'), tweak.var_names[0])
                    self.assertIn('ID: ' + tweak.var_names[0], displayed)
                    self.assertRegex(tweak.doc.split('\n\n', 1)[1], '[\u4e00-\u9fff]')
                    if tweak.var_names[0] in TWEAK_DOCS:
                        self.assertEqual(tweak.doc.split('\n\n', 1)[1], TWEAK_DOCS[tweak.var_names[0]].strip())
                    self.assertEqual(panel.edit_tweak.toPlainText(), tweak.edit_text)
                self.assertEqual(originals, [(t.var_names, t.default_values, t.custom_values) for t in model.tweaks])
                panel.edit_tweak.insertPlainText('# 尚未儲存的使用者編輯\n')
                edited = panel.edit_tweak.toPlainText()
                translate_widget(panel)
                self.app.processEvents()
                self.assertEqual(panel.edit_tweak.toPlainText(), edited)
                self.assertFalse(translator.failures)
        finally:
            translator.stop()
            panel.close()

    def test_author_sort_and_format_examples_remain_usable(self):
        author = TWEAK_DOCS['author_sort_copy_method']
        for token in ('invert', 'copy', 'comma', 'nocomma', 'author_name_suffixes',
                      'author_name_prefixes', 'author_name_copywords', 'author_use_surname_prefixes',
                      'author_surname_prefixes', 'von Neumann, John'):
            self.assertIn(token, author)
        for token in ('d', 'dd', 'ddd', 'dddd', 'M', 'MM', 'MMM', 'MMMM', 'yy', 'yyyy',
                      'h', 'hh', 'm', 'mm', 's', 'ss', 'ap', 'AP', 'aP', 'Ap', 'iso'):
            self.assertIn('    ' + token + '：', TWEAK_DOCS['gui_pubdate_display_format'])
        self.assertIn("sony_collection_name_template='{category:||: }{value}'", TWEAK_DOCS['sony_collection_renaming_rules'])


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TweakHelpTests))
if not result.wasSuccessful():
    raise SystemExit(1)

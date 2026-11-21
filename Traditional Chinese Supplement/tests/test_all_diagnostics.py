import json
import re
import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre_plugins.traditional_chinese_supplement.main import TranslationTool
from calibre_plugins.traditional_chinese_supplement.diagnostic_strings import translate_css_message
from calibre.gui2 import Application
from calibre.ebooks.oeb.polish.check import css, parsing, images
from calibre.utils import localization

FIXTURES = Path(__file__).resolve().parent / 'fixtures'


class AllDiagnosticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def setUp(self):
        with patch.object(ui, 'get_lang', return_value='zh_TW'):
            self.tool = TranslationTool()

    def tearDown(self):
        self.tool.translator.stop()

    def test_every_calibre_919_check_message_is_translated(self):
        messages = json.loads((FIXTURES / 'check_messages_919.json').read_text(encoding='utf8'))
        self.assertEqual(len(messages), 196)
        namespace = {'__name__': 'calibre.ebooks.oeb.polish.check.translation_audit', '_': localization._}
        for source in messages:
            with self.subTest(source=source):
                translated = eval('_(' + repr(source) + ')', namespace)
                self.assertRegex(translated, '[\u4e00-\u9fff]')

    def test_all_enabled_stylelint_rules_keep_metadata_and_values(self):
        samples = json.loads((FIXTURES / 'stylelint_messages_919.json').read_text(encoding='utf8'))
        self.assertEqual(len(samples), 36)
        self.assertEqual(len({s['rule'] for s in samples}), 32)
        for sample in samples:
            with self.subTest(rule=sample['rule'], kind=sample['kind']):
                message = {'rule': sample['rule'], 'text': sample['text'], 'severity': 'warning', 'line': 7, 'column': 4}
                original = deepcopy(message)
                metadata = {sample['rule']: {'url': 'https://stylelint.io/user-guide/rules/' + sample['rule'], 'fixable': True}}
                error = css.message_to_error(message, 'Styles/book.css', 10, metadata)
                self.assertRegex(error.msg, '[\u4e00-\u9fff]')
                self.assertRegex(error.HELP, '[\u4e00-\u9fff]')
                self.assertIn(sample['rule'], error.HELP)
                self.assertIn(metadata[sample['rule']]['url'], error.HELP)
                for token in ('ARG1', 'ARG2'):
                    if token in sample['text']:
                        self.assertIn(token, error.msg)
                        self.assertIn(token, error.HELP)
                self.assertEqual((error.name, error.line, error.col), ('Styles/book.css', 17, 3))
                self.assertEqual(error.css_rule_id, sample['rule'])
                self.assertTrue(error.FIXABLE_CSS_ERROR)
                self.assertEqual(message, original)
        suppressed = css.message_to_error({'rule': 'property-no-unknown', 'text': 'Unexpected unknown property "panose-1" (property-no-unknown)'}, 'font.css', 0, {})
        self.assertIsNone(suppressed)

    def test_syntax_errors_and_unknown_messages_preserve_context(self):
        self.assertEqual(translate_css_message('Unexpected }'), '不應出現右大括號 }')
        self.assertEqual(translate_css_message('Unclosed block'), '區塊尚未關閉')
        value = 'a[data-label="自訂(foo)"]'
        translated = translate_css_message('Unexpected unknown type selector "' + value + '" (selector-type-no-unknown)')
        self.assertIn(value, translated)
        unknown = 'New future diagnostic with author text'
        self.assertEqual(translate_css_message(unknown), unknown)
        error = parsing.XMLParseError('Opening and ending tag mismatch: div line 2 and p, line 6', 'Text/test.xhtml', 6, 3)
        self.assertTrue(error.msg.startswith('解析失敗：'))
        self.assertEqual(error.all_locations, [('Text/test.xhtml', 2, None), ('Text/test.xhtml', 6, 3)])
        image = images.InvalidImage('raw decoder detail', 'Images/cover.jpg', 1, 2)
        self.assertEqual(image.msg, '無效圖片：raw decoder detail')
        self.assertEqual((image.name, image.line, image.col), ('Images/cover.jpg', 1, 2))


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(AllDiagnosticsTests))
if not result.wasSuccessful():
    raise SystemExit(1)

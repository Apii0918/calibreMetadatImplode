import importlib
import re
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.hover_strings import HOVER_TEXT
from calibre.gui2 import Application
from qt.core import QLineEdit, QWidget


class HoverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_input_help_translates_without_changing_input(self):
        root_type = type('ConfigWidget', (QWidget,), {
            '__module__': 'calibre.gui2.preferences.look_feel',
        })
        root = root_type()
        edit = QLineEdit('{title} - {authors}', root)
        for source, translated in HOVER_TEXT.items():
            for getter, setter in (
                (edit.toolTip, edit.setToolTip),
                (edit.statusTip, edit.setStatusTip),
                (edit.whatsThis, edit.setWhatsThis),
            ):
                setter(source)
                translate_widget(edit)
                self.assertEqual(getter(), translated)
                translate_widget(edit)
                self.assertEqual(getter(), translated)
                self.assertEqual(edit.text(), '{title} - {authors}')
        root.close()

    def test_unrelated_input_help_stays_unchanged(self):
        root = QWidget()
        edit = QLineEdit('user text', root)
        source = next(iter(HOVER_TEXT))
        edit.setToolTip(source)
        translate_widget(edit)
        self.assertEqual(edit.toolTip(), source)
        self.assertEqual(edit.text(), 'user text')
        root.close()

    def test_preference_panels_have_no_remaining_english_help(self):
        for name in ('look_feel', 'adding', 'behavior', 'search', 'metadata_sources', 'tweaks'):
            with self.subTest(panel=name):
                module = importlib.import_module('calibre.gui2.preferences.' + name)
                panel = module.ConfigWidget()
                widgets = [panel, *panel.findChildren(QWidget)]
                for widget in widgets:
                    translate_widget(widget)
                for widget in widgets:
                    for getter in (widget.toolTip, widget.statusTip, widget.whatsThis):
                        text = getter()
                        # Technical identifiers in Chinese help remain verbatim.
                        untranslated = re.search(r'[A-Za-z]{3} [A-Za-z]{2}', text)
                        if untranslated and not re.search(r'[\u3400-\u9fff]', text):
                            self.fail(f'{name}: {widget.objectName()}: {text}')
                panel.close()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(HoverTests))
    raise SystemExit(not result.wasSuccessful())

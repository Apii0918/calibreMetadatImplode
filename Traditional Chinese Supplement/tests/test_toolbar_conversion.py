import importlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.preferences import TEXT
from calibre.gui2 import Application
from calibre.gui2.preferences.toolbar import ConfigWidget
from qt.core import QLabel, QLineEdit, QWidget, Qt

ACTION_MODULES = '''add add_to_library airdrop all_actions annotate author_mapper auto_scroll
booklist_context_menu browse_annots browse_notes catalog choose_library column_tooltips convert
copy_to_library cyoa delete device edit_collections edit_metadata embed fetch_news fts help
layout_actions llm_book llm_cover manage_categories mark_books match_books next_match open
plugin_updates polish preferences random restart save_to_disk saved_searches show_book_details
show_quickview show_stored_templates show_template_tester similar_books sort store tag_mapper
toc_edit tweak_epub unpack_book view virtual_library'''.split()


class ToolbarConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_all_toolbar_locations_and_action_help_keep_identifiers(self):
        actions = {}
        for name in ACTION_MODULES:
            module = importlib.import_module('calibre.gui2.actions.' + name)
            for cls in vars(module).values():
                if isinstance(cls, type) and cls.__module__ == module.__name__ and getattr(cls, 'action_spec', None):
                    actions[cls.name] = SimpleNamespace(name=cls.name, action_spec=cls.action_spec,
                        dont_add_to=cls.dont_add_to, dont_remove_from=cls.dont_remove_from)
        panel = ConfigWidget()
        panel.genesis(SimpleNamespace(iactions=actions))
        originals = {key: [[a.name for a in model._data] for model in pair]
                     for key, pair in panel.models.items()}
        specs = {name: action.action_spec for name, action in actions.items()}
        translator = ui.TranslationFilter()
        try:
            with patch.object(ui, 'get_lang', return_value='zh_TW'):
                translator.start()
                panel.show()
                self.app.processEvents()
                for location in range(1, panel.what.count()):
                    key = panel.what.itemData(location)
                    panel.what.setCurrentIndex(location)
                    self.app.processEvents()
                    self.assertRegex(panel.what.itemText(location), '[\u4e00-\u9fff]')
                    for model in panel.models[key]:
                        for row in range(model.rowCount()):
                            index = model.index(row, 0)
                            text = model.data(index, Qt.ItemDataRole.DisplayRole)
                            tip = model.data(index, Qt.ItemDataRole.ToolTipRole)
                            self.assertRegex(text, '[\u4e00-\u9fff]')
                            if tip:
                                self.assertRegex(tip, '[\u4e00-\u9fff]')
                            if model is panel.current_actions.model():
                                panel.current_entered(index)
                            else:
                                panel.all_entered(index)
                            self.assertEqual(panel.help_text.text(), tip or '')
                self.assertEqual(originals, {key: [[a.name for a in model._data] for model in pair]
                                            for key, pair in panel.models.items()})
                self.assertEqual(specs, {name: action.action_spec for name, action in actions.items()})
                self.assertFalse(translator.failures)
        finally:
            translator.stop()
            panel.close()

    def test_conversion_labels_and_input_hint(self):
        from calibre.gui2.convert.structure_detection import StructureDetectionWidget
        from calibre.gui2.convert.structure_detection_ui import Ui_Form
        panel = StructureDetectionWidget.__new__(StructureDetectionWidget)
        QWidget.__init__(panel)
        Ui_Form.setupUi(panel, panel)
        editor = QLineEdit('user rule', panel)
        editor.setPlaceholderText('Press Enter to find the next matching rule')
        label = QLabel('Find rule:', panel)
        for child in [panel, *panel.findChildren(QWidget)]:
            translate_widget(child)
        self.assertEqual(editor.text(), 'user rule')
        self.assertEqual(editor.placeholderText(), TEXT['Press Enter to find the next matching rule'])
        self.assertEqual(label.text(), '尋找規則：')
        self.assertIn('為圖片加入替代文字', [x.text() for x in panel.findChildren(QWidget) if hasattr(x, 'text') and callable(x.text)])
        panel.close()

    def test_native_css_and_html_rules(self):
        from calibre.gui2 import css_transform_rules, html_transform_rules
        from calibre.gui2.convert.structure_detection import StructureDetectionWidget
        parent = StructureDetectionWidget.__new__(StructureDetectionWidget)
        QWidget.__init__(parent)
        for cls in (css_transform_rules.RulesWidget, html_transform_rules.HtmlRulesWidget):
            rules = cls(parent)
            for child in [parent, rules, *rules.findChildren(QWidget)]:
                translate_widget(child)
            labels = [child.text() for child in rules.findChildren(QLabel)]
            self.assertIn('尋找規則：', labels)
            self.assertFalse(any('You can specify rules to transform HTML' in text for text in labels))
            self.assertIn(TEXT['Press Enter to find the next matching rule'],
                          [child.placeholderText() for child in rules.findChildren(QLineEdit)])
        parent.close()


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ToolbarConversionTests))
if not result.wasSuccessful():
    raise SystemExit(1)

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
from calibre_plugins.traditional_chinese_supplement.preferences import TEXT
from calibre.gui2 import Application
from calibre.db.legacy import LibraryDatabase
from calibre.gui2.preferences.look_feel_tabs import EditRulesWidget
from calibre.gui2.preferences.look_feel_tabs.bookshelf_view import BookshelfTab
from calibre.gui2.preferences.look_feel_tabs.tb_hierarchy import TbHierarchyTab
from qt.core import QLabel, QIcon, Qt, QWidget


class LatePreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_shortcut_letters_are_not_html_entities(self):
        panel = BookshelfTab()
        for source, expected in (
            ('Text on the &divider', '分隔標題文字'),
            ('The &current book highlight', '目前書本的醒目顏色'),
            ('&Recount pages', '重新計算頁數'),
            ('Draw text flush with the &bottom of the rendered cover', '文字緊貼顯示封面的底部'),
        ):
            label = QLabel(source, panel)
            translate_widget(label)
            self.assertEqual(label.text(), expected)
        panel.close()

    def test_rule_pages_translate_after_native_show_initialization(self):
        with TemporaryDirectory() as temporary:
            db = LibraryDatabase(str(Path(temporary) / 'Library'))
            gui = SimpleNamespace(current_db=db)
            translator = ui.TranslationFilter()
            panels = []
            try:
                with patch.object(ui, 'get_lang', return_value='zh_TW'), patch(
                    'calibre.gui2.ui.get_gui', return_value=gui,
                ), patch('calibre.gui2.preferences.look_feel_tabs.get_gui', return_value=gui):
                    translator.start()
                    for kind in (
                        'cover_grid_icon_rules', 'bookshelf_icon_rules',
                        'column_color_rules', 'column_icon_rules',
                    ):
                        panel = EditRulesWidget()
                        panel.rule_set_name = kind
                        panels.append(panel)
                        panel.show()
                        for _ in range(3):
                            self.app.processEvents()
                        editor = panel.rules_editor
                        self.assertNotIn('You can', editor.l1.text())
                        self.assertIn('編輯現有規則', editor.l1.text())
                        if kind == 'cover_grid_icon_rules':
                            self.assertEqual(editor.choices.currentText(), '不顯示徽章')
                            self.assertEqual(editor.choices.currentData(), 'none')
            finally:
                translator.stop()
                for panel in panels:
                    panel.close()
                db.close()

    def test_populated_search_order_preserves_identifiers(self):
        panel = TbHierarchyTab()
        icons = {index: QIcon() for index in range(5)}
        panel.gui = SimpleNamespace(
            tags_view=SimpleNamespace(model=lambda: SimpleNamespace(icon_state_map=icons)),
        )
        panel.fill_tb_search_order_box()
        before = [panel.tb_search_order.item(i).data(Qt.ItemDataRole.UserRole)
                  for i in range(panel.tb_search_order.count())]
        translate_widget(panel)
        for i in range(panel.tb_search_order.count()):
            self.assertTrue(panel.tb_search_order.item(i).text().startswith('搜尋'))
        self.assertEqual(before, [
            panel.tb_search_order.item(i).data(Qt.ItemDataRole.UserRole)
            for i in range(panel.tb_search_order.count())
        ])
        panel.close()

    def test_default_font_hint_preserves_font_value(self):
        panel = BookshelfTab()
        panel.bookshelf_font_display.setPlaceholderText('Use default font')
        original = panel.bookshelf_font_display.text()
        translate_widget(panel.bookshelf_font_display)
        self.assertEqual(panel.bookshelf_font_display.placeholderText(), '使用預設字型')
        self.assertEqual(panel.bookshelf_font_display.text(), original)
        panel._recount_button_txt = '&Recount pages'
        translate_widget(panel)
        panel.update_recount_txt(0)
        self.assertEqual(panel.recount_button.text(), '重新計算頁數')
        panel.close()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(LatePreferencesTests))
    raise SystemExit(not result.wasSuccessful())

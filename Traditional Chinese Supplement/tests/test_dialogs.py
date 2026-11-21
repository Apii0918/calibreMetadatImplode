import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement.display import translate_widget
from calibre_plugins.traditional_chinese_supplement.dialog_strings import DIALOG_TEXT
from calibre.gui2 import Application
from calibre.db.legacy import LibraryDatabase
from calibre.ebooks.metadata.book.base import Metadata
from calibre.gui2.preferences.create_custom_column import CreateCustomColumn
from calibre.gui2.preferences.coloring import RuleEditor, pref_name_map
from calibre.gui2.dialogs.palette import PaletteConfig
from calibre.gui2.dialogs.template_dialog import TemplateDialog
from calibre.gui2.dialogs.plugin_updater import PluginUpdaterDialog, FILTER_NOT_INSTALLED, Category
from qt.core import QComboBox, QLineEdit, QPlainTextEdit, QWidget


class DialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_native_dialogs_preserve_inputs_and_option_values(self):
        with TemporaryDirectory() as temporary:
            db = LibraryDatabase(str(Path(temporary) / 'Library'))
            gui = QWidget()
            gui.current_db = db
            metadata = Metadata('Dialog Test', ['Author'])
            book_id = db.new_api.create_book_entry(metadata)
            metadata = db.new_api.get_metadata(book_id)
            gui.library_view = SimpleNamespace(
                get_selected_ids=lambda: [book_id],
                model=lambda: SimpleNamespace(db=db),
            )
            windows = []
            try:
                with patch.object(CreateCustomColumn, 'exec', return_value=0):
                    custom = CreateCustomColumn(gui, SimpleNamespace(custcols={}), None, {})
                windows.append(custom)
                for kind in pref_name_map:
                    editor = RuleEditor(db.field_metadata, kind)
                    editor.add_blank_condition()
                    windows.append(editor)
                windows.append(PaletteConfig())
                with patch('calibre.gui2.ui.get_gui', return_value=gui):
                    template = TemplateDialog(
                        gui, '{title} - {authors}', mi=metadata, fm=db.field_metadata,
                    )
                windows.append(template)
                with patch('calibre.gui2.dialogs.plugin_updater.read_available_plugins', return_value=[]):
                    windows.append(PluginUpdaterDialog(
                        gui, initial_filter=FILTER_NOT_INSTALLED,
                        initial_category=Category.MetadataSource,
                    ))
                for window in windows:
                    with self.subTest(dialog=type(window).__name__):
                        widgets = [window, *window.findChildren(QWidget)]
                        combos = [
                            (combo, combo.currentIndex(),
                             [combo.itemData(i) for i in range(combo.count())])
                            for combo in window.findChildren(QComboBox)
                        ]
                        inputs = [
                            (edit, edit.text()) for edit in window.findChildren(QLineEdit)
                        ]
                        programs = [
                            (edit, edit.toPlainText())
                            for edit in window.findChildren(QPlainTextEdit)
                        ]
                        with patch('calibre.gui2.ui.get_gui', return_value=gui):
                            for widget in widgets:
                                translate_widget(widget)
                            for widget in widgets:
                                translate_widget(widget)
                        for combo, index, values in combos:
                            self.assertEqual(combo.currentIndex(), index)
                            self.assertEqual(
                                [combo.itemData(i) for i in range(combo.count())], values,
                            )
                        for edit, value in inputs:
                            self.assertEqual(edit.text(), value)
                        for edit, value in programs:
                            self.assertEqual(edit.toPlainText(), value)
                        for widget in widgets:
                            for getter in (widget.toolTip, widget.statusTip, widget.whatsThis):
                                self.assertNotIn(getter(), DIALOG_TEXT)
                self.assertEqual(template.template_value.cellWidget(0, 2).text(), 'Dialog Test - Author')
                self.assertEqual(template.template_value.horizontalHeaderItem(2).text(), '範本結果')
                self.assertNotIn('only one template dialog allowed', template.windowTitle())
                self.assertEqual(template.windowTitle().count('同時只能開啟一個範本視窗'), 1)
            finally:
                for window in windows:
                    window.close()
                gui.close()
                db.close()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(DialogTests))
    raise SystemExit(not result.wasSuccessful())

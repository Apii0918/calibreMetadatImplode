import sys
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import plugin
from calibre_plugins.traditional_chinese_supplement import ui
from calibre.gui2 import Application, keyboard
from qt.core import QKeySequence, Qt, QWidget


class ShortcutTranslationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Application.instance() or Application([])

    def test_render_search_edit_and_restore_preserve_bindings(self):
        manager = keyboard.Manager(config_name='shortcuts/translation-test')
        manager.register_shortcut('test-action', 'Bulk generate covers', default_keys=('Ctrl+Alt+G',),
                                  group='AI generate cover')
        manager.register_shortcut('test-layout', 'Toggle layout between wide and narrow',
                                  default_keys=('Ctrl+Alt+L',), group='Main window layout')
        manager.finalize()
        original_shortcuts = deepcopy(manager.shortcuts)
        original_groups = deepcopy(manager.groups)
        original_keys = {key: tuple(k.toString() for k in keys) for key, keys in manager.keys_map.items()}
        original_methods = keyboard.Delegate.to_doc, keyboard.Editor.initialize, keyboard.ConfigModel.get_matches
        config = keyboard.ShortcutConfig()
        config.initialize(manager)
        model = config._model
        translator = ui.TranslationFilter()
        try:
            with patch.object(ui, 'get_lang', return_value='zh_TW'):
                translator.start()
                config.show()
                self.app.processEvents()
                self.assertEqual(config.search.lineEdit().placeholderText(), '依名稱或按鍵組合搜尋快捷鍵')
                group = model.index(0, 0)
                child = model.index(0, 0, group)
                self.assertEqual(config.delegate.to_doc(group).toPlainText(), '使用 AI 產生封面')
                rendered = config.delegate.to_doc(child).toPlainText()
                self.assertIn('批次產生封面', rendered)
                self.assertIn('Ctrl+Alt+G', rendered)
                self.assertEqual(model.find('批次產生').internalPointer(), child.internalPointer())
                self.assertTrue(model.find('主視窗版面').isValid())
                self.assertTrue(model.find('Bulk generate').isValid())
                self.assertTrue(model.find('Ctrl+Alt+G').isValid())
                editor = keyboard.Editor(config)
                config.delegate.setEditorData(editor, child)
                self.assertIn('批次產生封面', editor.header.text())
                self.assertEqual(editor.current_keys, list(manager.keys_map['test-action']))
                editor.use_custom.setChecked(True)
                editor.button1.setObjectName('Ctrl+Alt+J')
                self.assertEqual(editor.custom_keys, (QKeySequence('Ctrl+Alt+J'),))
                self.assertEqual(manager.shortcuts, original_shortcuts)
                self.assertEqual(manager.groups, original_groups)
                self.assertEqual(original_keys, {key: tuple(k.toString() for k in keys) for key, keys in manager.keys_map.items()})
                self.assertEqual(model.parent(child), group)
                self.assertFalse(translator.failures)
        finally:
            translator.stop()
            config.close()
        self.assertEqual(original_methods, (keyboard.Delegate.to_doc, keyboard.Editor.initialize, keyboard.ConfigModel.get_matches))


result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ShortcutTranslationTests))
if not result.wasSuccessful():
    raise SystemExit(1)

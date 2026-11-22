import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_translation import TranslationTests, ui
from qt.core import QAction, QEvent, QMainWindow, QMenu


class MainMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TranslationTests.setUpClass()
        cls.app = TranslationTests.app

    def setUp(self):
        self.gui = QMainWindow()
        self.gui.iactions = {}
        self.actions = []
        for name, module, label, children in (
            ('Open Folder', 'calibre.gui2.actions.open', 'Open book folder',
             ['Open book data folder']),
            ('Show Book Details', 'calibre.gui2.actions.show_book_details', '書本詳細資料',
             ['Show Book details in a separate window',
              'Show Book details in a separate locked window', 'Close all Book details windows']),
        ):
            owner = type('NativeAction', (), {'__module__': module})()
            owner.qaction = QAction(label, self.gui)
            owner.qaction.setMenu(QMenu(self.gui))
            self.actions.append(owner.qaction)
            for text in children:
                self.actions.append(owner.qaction.menu().addAction(text))
            self.gui.iactions[name] = owner
        self.filter = ui.TranslationFilter(self.gui)

    def tearDown(self):
        self.filter.stop()
        self.gui.close()
        self.gui.deleteLater()
        self.app.processEvents()

    def test_translate_native_labels_preserves_action_state_and_callbacks(self):
        callbacks = []
        for i, action in enumerate(self.actions):
            callback = Mock()
            callbacks.append(callback)
            action.triggered.connect(callback)
            action.setData({'identity': i})
            action.setShortcut('Ctrl+Alt+' + str(i))
        shortcuts = [a.shortcut().toString() for a in self.actions]
        ui.translate_library_actions(self.gui)
        self.assertEqual([a.text() for a in self.actions], [
            '開啟書本資料夾', '開啟書本資料檔案資料夾', '書本詳細資料',
            '在獨立視窗顯示書本詳細資料', '在獨立的鎖定視窗顯示書本詳細資料',
            '關閉所有書本詳細資料視窗',
        ])
        self.assertEqual([a.shortcut().toString() for a in self.actions], shortcuts)
        for i, (action, callback) in enumerate(zip(self.actions, callbacks)):
            self.assertEqual(action.data(), {'identity': i})
            action.trigger()
            callback.assert_called_once()

    def test_late_submenu_action_translates_on_show(self):
        with patch.object(ui, 'get_lang', return_value='zh_TW'):
            self.filter.start()
        menu = self.gui.iactions['Show Book Details'].qaction.menu()
        late = menu.addAction('Close all Book details windows')
        self.filter.eventFilter(menu, QEvent(QEvent.Type.Show))
        self.assertEqual(late.text(), '關閉所有書本詳細資料視窗')
        ui.translate_library_actions(self.gui)
        self.assertEqual(late.text(), '關閉所有書本詳細資料視窗')

    def test_other_plugins_and_non_chinese_interface_stay_unchanged(self):
        owner = self.gui.iactions['Open Folder']
        owner.__class__ = type('OtherPlugin', (), {'__module__': 'calibre_plugins.other'})
        ui.translate_library_actions(self.gui)
        self.assertEqual(owner.qaction.text(), 'Open book folder')
        other = QMenu(self.gui)
        action = other.addAction('Open book folder')
        native = self.gui.iactions['Show Book Details'].qaction.menu().actions()[0]
        native.setText('Show Book details in a separate window')
        with patch.object(ui, 'get_lang', return_value='en'):
            self.filter.start()
        self.filter.eventFilter(other, QEvent(QEvent.Type.Show))
        self.assertEqual(action.text(), 'Open book folder')
        self.assertEqual(native.text(), 'Show Book details in a separate window')


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(MainMenuTests))
    raise SystemExit(not result.wasSuccessful())

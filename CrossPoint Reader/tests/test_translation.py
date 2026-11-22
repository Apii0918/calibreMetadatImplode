import gettext
import importlib
import io
import re
import sys
import unittest
from collections import Counter
from pathlib import Path
from string import Formatter
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir, prefs
if (ROOT / 'dist').resolve() not in Path(config_dir).resolve().parents:
    raise RuntimeError('請使用 dist 下的獨立設定目錄。')
prefs['language'] = 'zh_TW'
from calibre.utils.localization import set_translators
set_translators()
from calibre.gui2 import Application
app = Application.instance() or Application([])
from calibre.customize.zipplugin import loader
ARCHIVE = ROOT / 'dist/CrossPoint Reader-zh_TW-release.zip'
Plugin = loader.load(str(ARCHIVE))
package = Plugin.__module__
config = importlib.import_module(package + '.config')
summary = importlib.import_module(package + '.summary')
ws = importlib.import_module(package + '.ws_client')
from qt.core import QLabel


class TranslationTests(unittest.TestCase):
    def test_catalog_preserves_all_format_parameters(self):
        with ZipFile(ARCHIVE) as z:
            catalog = gettext.GNUTranslations(io.BytesIO(z.read('translations/zh_TW.mo')))
        messages = {k: v for k, v in catalog._catalog.items() if isinstance(k, str) and k}
        self.assertEqual(len(messages), 134)
        pattern = r'%(?:\([^)]+\))?[-+0-9.#]*[sdfiv]'
        for source, target in messages.items():
            with self.subTest(source=source):
                self.assertEqual(re.findall(pattern, source), re.findall(pattern, target))
                self.assertEqual(Counter(field for _, field, _, _ in Formatter().parse(source) if field is not None),
                                 Counter(field for _, field, _, _ in Formatter().parse(target) if field is not None))

    def test_config_is_chinese_and_identifiers_survive_save(self):
        widget = config.CrossPointConfigWidget()
        try:
            self.assertEqual(widget.debug.text(), '啟用偵錯記錄')
            self.assertEqual(widget.optimize.text(), '傳輸前最佳化 EPUB')
            self.assertIn('主機', [x.text() for x in widget.findChildren(QLabel)])
            self.assertFalse(widget.optimize.isChecked())
            widget.host.setText('192.0.2.20')
            widget.port.setValue(81)
            widget.path.setText('/書籍')
            widget.device_target.setCurrentIndex(widget.device_target.findData('X3'))
            widget.save()
            self.assertEqual(config.PREFS['host'], '192.0.2.20')
            self.assertEqual(config.PREFS['path'], '/書籍')
            self.assertEqual(config.PREFS['device_target'], 'X3')
        finally:
            widget.close()

    def test_progress_and_summary_are_chinese(self):
        payload = {'books': [{'orig_size': 100, 'new_size': 80, 'images': 2, 'fixes': 1, 'errors': 0}]}
        text = '\n'.join(summary._summary_lines(payload))
        self.assertIn('完成：1 本書、2 張圖片、1 項修正', text)
        dialog = summary._ProgressDialog('測試書籍')
        try:
            self.assertEqual(dialog.dlg.windowTitle(), 'CrossPoint 最佳化')
            dialog.finish(payload)
            self.assertEqual(dialog.header.text(), '最佳化完成。')
        finally:
            dialog.dlg.close()

    def test_translation_does_not_change_wire_protocol(self):
        with TemporaryDirectory(dir=ROOT / 'dist') as temp:
            path = Path(temp) / 'sample.epub'
            path.write_bytes(b'abc')
            client = Mock()
            client.read_text.side_effect = ['READY', 'DONE']
            with patch.object(ws, 'WebSocketClient', return_value=client):
                ws.upload_file('192.0.2.20', 81, '/', 'sample.epub', str(path))
            client.send_text.assert_called_once_with('START:sample.epub:3:/')
            client.send_binary.assert_called_once_with(b'abc')
            client.close.assert_called_once()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(TranslationTests))
    raise SystemExit(not result.wasSuccessful())

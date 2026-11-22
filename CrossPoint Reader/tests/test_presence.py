import importlib
import json
import socket
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import Mock, patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
from calibre.utils.config import config_dir
if (ROOT / 'dist').resolve() not in Path(config_dir).resolve().parents:
    raise RuntimeError('請使用 dist 下的獨立設定目錄。')
from calibre.customize.zipplugin import loader
ARCHIVE = ROOT / 'dist/CrossPoint Reader-zh_TW-release.zip'
Plugin = loader.load(str(ARCHIVE))
driver = importlib.import_module(Plugin.__mro__[1].__module__)
ws = driver.ws_client
from calibre.devices.errors import ControlError
from calibre.devices.usbms.books import BookList


class PresenceTests(unittest.TestCase):
    def setUp(self):
        self.device = Plugin(str(ARCHIVE))
        self.device._discover = Mock(return_value=('127.0.0.1', 81))
        self.device._detect_device_model = Mock()

    def discover(self, packets):
        sock = Mock()
        sock.recvfrom.side_effect = [*packets, socket.timeout(), socket.timeout(), socket.timeout()]
        with (patch.object(ws.socket, 'socket', return_value=sock),
              patch.object(ws, '_local_broadcast_addrs', return_value=[])):
            found = ws.discover_device(timeout=0.05)
        sock.close.assert_called_once()
        return found

    def test_unrelated_udp_and_invalid_ports_are_ignored(self):
        for message in (b'hello', b'not a device', b'crosspointX;81', b'crosspoint;0',
                        b'crosspoint;65536', b'crosspoint;abc', b'crosspoint;81\xff'):
            with self.subTest(message=message):
                self.assertEqual(self.discover([(message, ('127.0.0.1', 8134))]), (None, None))

    def test_genuine_udp_after_noise_is_accepted(self):
        self.assertEqual(self.discover([(b'hello', ('127.0.0.2', 8134)),
                                       (b'crosspoint (on reader);81', ('127.0.0.1', 8134))]),
                         ('127.0.0.1', 81))

    def test_invalid_or_unreachable_file_service_never_connects(self):
        for response in ({}, [None], [{'name': 'bad'}], TimeoutError('offline')):
            with self.subTest(response=response):
                self.device._retry_at = 0
                self.device._http_get_json = Mock()
                if isinstance(response, Exception):
                    self.device._http_get_json.side_effect = response
                else:
                    self.device._http_get_json.return_value = response
                self.assertIsNone(self.device.detect_managed_devices([]))
                self.assertFalse(self.device.is_connected)
                self.assertIsNone(self.device.device_host)

    def test_empty_valid_reader_connects_and_loss_disconnects(self):
        self.device._http_get_json = Mock(return_value=[])
        self.assertIs(self.device.detect_managed_devices([]), self.device)
        self.device._http_get_json.side_effect = TimeoutError('offline')
        self.assertIsNone(self.device.detect_managed_devices([], force_refresh=True))
        self.assertFalse(self.device.is_connected)
        self.device._discover.reset_mock()
        self.assertIsNone(self.device.detect_managed_devices([]))
        self.device._discover.assert_not_called()

    def test_eject_or_stop_does_not_immediately_rediscover(self):
        self.device._http_get_json = Mock(return_value=[])
        self.device.detect_managed_devices([])
        self.device.eject()
        self.device._discover.reset_mock()
        self.assertFalse(self.device.is_running())
        self.assertIsNone(self.device.detect_managed_devices([]))
        self.device._discover.assert_not_called()
        self.device.start_plugin()
        self.assertIs(self.device.detect_managed_devices([]), self.device)

    def test_books_uses_native_booklist_and_failure_is_not_an_empty_library(self):
        self.device._build_library_index = Mock(return_value=None)
        self.device._http_get_json = Mock(return_value=[
            {'name': 'Sample.epub', 'size': 100, 'isDirectory': False, 'isEpub': True}])
        result = self.device.books()
        self.assertIsInstance(result, BookList)
        self.assertEqual(result[0].lpath, '/Sample.epub')
        self.device._http_get_json.side_effect = TimeoutError('offline')
        with self.assertRaises(ControlError):
            self.device.books()

    def test_actual_http_service_gate(self):
        state = {'good': False}
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                payload = [] if state['good'] else {'error': 'not a reader'}
                raw = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            self.device._http_base = lambda: f'http://127.0.0.1:{server.server_port}'
            self.assertIsNone(self.device.detect_managed_devices([]))
            state['good'] = True
            self.device._retry_at = 0
            self.assertIs(self.device.detect_managed_devices([]), self.device)
            state['good'] = False
            self.assertIsNone(self.device.detect_managed_devices([], force_refresh=True))
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PresenceTests))
    raise SystemExit(not result.wasSuccessful())

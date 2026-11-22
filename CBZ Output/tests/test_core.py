import importlib.util
import posixpath
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock
from xml.etree import ElementTree
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('cbz_core', ROOT / 'CBZ Output/src/core.py')
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)


def image(href, data=b'picture', media_type='image/png', ident=None):
    return SimpleNamespace(href=href, id=ident or href, media_type=media_type,
                           bytes_representation=data)


def document(href, body):
    return SimpleNamespace(href=href, media_type='application/xhtml+xml',
                           data=ElementTree.fromstring('<body>' + body + '</body>'),
                           abshref=lambda ref: posixpath.normpath(posixpath.join(posixpath.dirname(href), ref)))


def book(images, spine=(), cover=(), guide=None):
    return SimpleNamespace(manifest=[*images, *spine], spine=spine,
                           metadata=SimpleNamespace(cover=cover), guide=guide or {})


class CBZTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(dir=ROOT / 'dist')
        self.addCleanup(self.temp.cleanup)
        self.destination = Path(self.temp.name) / 'comic.cbz'
        self.log = Mock()

    def test_reading_order_and_same_basename(self):
        a, b = image('a/page.png', b'red'), image('b/page.png', b'blue')
        chapter = document('text/chapter.xhtml', '<img src="../b/page.png"/><img src="../a/page.png"/>')
        pages = core.ordered_images(book([a, b], [chapter]), self.log)
        core.write_cbz(self.destination, pages)
        with ZipFile(self.destination) as z:
            self.assertEqual(z.namelist(), ['000001.png', '000002.png'])
            self.assertEqual([z.read(n) for n in z.namelist()], [b'blue', b'red'])

    def test_cover_first_and_only_once(self):
        cover, a = image('cover.png', ident='front'), image('page.png')
        chapter = document('chapter.xhtml', '<img src="page.png"/><img src="cover.png"/><img src="page.png"/>')
        pages = core.ordered_images(book([cover, a], [chapter], cover=['front']), self.log)
        self.assertEqual(pages, [cover, a, a])

    def test_guide_cover_document_and_natural_fallback(self):
        cover = image('front.png')
        a, b = image('page2.png'), image('page10.png')
        front = document('front.xhtml', '<img src="front.png"/>')
        source = book([b, a, cover, front], guide={'cover': SimpleNamespace(href='front.xhtml')})
        self.assertEqual(core.ordered_images(source, self.log), [cover, a, b])

    def test_encoded_paths_svg_reference_and_unused_images(self):
        a, unused = image('圖 片.png'), image('unused.png')
        chapter = document('chapter.xhtml', '<svg xmlns:xlink="http://www.w3.org/1999/xlink"><image xlink:href="%E5%9C%96%20%E7%89%87.png"/></svg>')
        self.assertEqual(core.ordered_images(book([unused, a], [chapter]), self.log), [a])

    def test_external_reference_is_not_loaded(self):
        a = image('page.png')
        chapter = document('chapter.xhtml', '<img src="https://example.com/page.png"/><img src="page.png"/>')
        self.assertEqual(core.ordered_images(book([a], [chapter]), self.log), [a])
        self.log.warning.assert_called_once()

    def test_missing_local_picture_and_no_pictures(self):
        with self.assertRaisesRegex(ValueError, '沒有可匯出'):
            core.ordered_images(book([]), self.log)
        chapter = document('chapter.xhtml', '<img src="missing.png"/>')
        with self.assertRaisesRegex(ValueError, '找不到'):
            core.ordered_images(book([image('other.png')], [chapter]), self.log)

    def test_failed_write_preserves_destination_and_cleans_temp(self):
        self.destination.write_bytes(b'original')
        broken = image('bad.png', b'')
        with self.assertRaisesRegex(ValueError, '內容為空'):
            core.write_cbz(self.destination, [image('first.png'), broken])
        self.assertEqual(self.destination.read_bytes(), b'original')
        self.assertEqual(list(self.destination.parent.iterdir()), [self.destination])

    def test_image_formats_and_safe_names(self):
        pages = [image('../../unsafe.jpg', b'jpeg', 'image/jpeg'),
                 image('animation.gif', b'gif', 'image/gif')]
        core.write_cbz(self.destination, pages)
        with ZipFile(self.destination) as z:
            self.assertEqual(z.namelist(), ['000001.jpg', '000002.gif'])
            self.assertEqual(z.read('000001.jpg'), b'jpeg')
            self.assertIsNone(z.testzip())


if __name__ == '__main__':
    unittest.main()

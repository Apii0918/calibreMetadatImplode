"""Exercise the installed ZIP through calibre's real conversion pipeline."""
import hashlib
import os
import struct
import subprocess
import sys
import unittest
import zlib
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def png(color):
    def chunk(kind, data):
        return (struct.pack('>I', len(data)) + kind + data
                + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff))
    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', 16, 16, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' + bytes(color) * 16) * 16))
            + chunk(b'IEND', b''))


class ConversionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory(dir=ROOT / 'dist')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.env = dict(os.environ, CALIBRE_CONFIG_DIRECTORY=str(cls.root / 'profile'),
                       QT_QPA_PLATFORM='offscreen', PYTHONIOENCODING='utf-8')
        subprocess.run(['calibre-customize', '-a', str(ROOT / 'dist/CBZ Output-zh_TW-release.zip')],
                       env=cls.env, check=True, capture_output=True)

    def fixture(self, cover=False, no_images=False):
        source = self.root / 'source.epub'
        self.red, self.blue = png((255, 0, 0)), png((0, 0, 255))
        images = '' if no_images else ('<item id="red" href="a/page.png" media-type="image/png"/>'
                                       '<item id="blue" href="b/page.png" media-type="image/png"/>')
        cover_meta = '<meta name="cover" content="red"/>' if cover else ''
        with ZipFile(source, 'w', ZIP_DEFLATED) as z:
            z.writestr('mimetype', 'application/epub+zip')
            z.writestr('META-INF/container.xml', '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container" version="1.0"><rootfiles><rootfile full-path="content.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
            z.writestr('content.opf', '<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="id" version="2.0"><metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>CBZ test</dc:title><dc:language>en</dc:language><dc:identifier id="id">urn:test:cbz</dc:identifier>' + cover_meta + '</metadata><manifest>' + images + '<item id="a" href="one.xhtml" media-type="application/xhtml+xml"/><item id="b" href="two.xhtml" media-type="application/xhtml+xml"/><item id="toc" href="toc.ncx" media-type="application/x-dtbncx+xml"/></manifest><spine toc="toc"><itemref idref="b"/><itemref idref="a"/></spine></package>')
            z.writestr('toc.ncx', '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1"><head><meta name="dtb:uid" content="urn:test:cbz"/></head><docTitle><text>CBZ test</text></docTitle><navMap><navPoint id="n1" playOrder="1"><navLabel><text>Test</text></navLabel><content src="two.xhtml"/></navPoint></navMap></ncx>')
            for file, picture in [('one.xhtml', 'a/page.png'), ('two.xhtml', 'b/page.png')]:
                body = 'Text only' if no_images else '<img src="' + picture + '" alt="page"/>'
                z.writestr(file, '<html xmlns="http://www.w3.org/1999/xhtml"><head><title>Test</title></head><body><p>' + body + '</p></body></html>')
            if not no_images:
                z.writestr('a/page.png', self.red)
                z.writestr('b/page.png', self.blue)
        return source

    def convert(self, source):
        target = self.root / 'result.cbz'
        result = subprocess.run(['ebook-convert', str(source), str(target)], env=self.env,
                                capture_output=True, text=True, encoding='utf-8', timeout=60)
        return target, result

    def test_spine_order_unique_names_and_original_bytes(self):
        source = self.fixture()
        before = hashlib.sha256(source.read_bytes()).digest()
        target, result = self.convert(source)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with ZipFile(target) as z:
            self.assertEqual(z.namelist(), ['000001.png', '000002.png'])
            self.assertEqual([z.read(n) for n in z.namelist()], [self.blue, self.red])
        self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)

    def test_explicit_cover_first(self):
        target, result = self.convert(self.fixture(cover=True))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        with ZipFile(target) as z:
            self.assertEqual([z.read(n) for n in z.namelist()], [self.red, self.blue])

    def test_text_only_fails_clearly(self):
        target, result = self.convert(self.fixture(no_images=True))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('書中沒有可匯出的圖片', result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()

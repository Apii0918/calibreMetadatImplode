import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('build_release', ROOT / 'build_release.py')
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
spec2 = importlib.util.spec_from_file_location('updater_core', ROOT / 'GitHub Plugin Updater/src/core.py')
core = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(core)


class BuildTests(unittest.TestCase):
    def test_same_content_different_mtime_is_identical(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'dist') as temp:
            root = Path(temp); source = root / 'source'; source.mkdir()
            text = source / 'file.py'; text.write_bytes(b'print("hello")\n')
            one, two = root / 'one.zip', root / 'two.zip'
            build.build_zip(source, one)
            os.utime(text, (1900000000, 1900000000))
            build.build_zip(source, two)
            self.assertEqual(one.read_bytes(), two.read_bytes())
            with ZipFile(one) as z:
                self.assertEqual(z.getinfo('file.py').date_time, (1980, 1, 1, 0, 0, 0))
            text.write_bytes(b'print("changed")\n')
            build.build_zip(source, two)
            self.assertNotEqual(core.digest(one), core.digest(two))

    def test_content_sha_ignores_identity_and_zip_envelope(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'dist') as temp:
            root = Path(temp)
            one, two = root / 'one.zip', root / 'two.zip'
            with ZipFile(one, 'w') as z:
                z.writestr('a.py', b'code')
                z.writestr(core.IDENTITY, '{"sha256":"old"}')
            with ZipFile(two, 'w') as z:
                z.writestr(core.IDENTITY, '{"sha256":"new"}')
                z.writestr('empty/', b'')
                z.writestr('a.py', b'code')
            self.assertEqual(core.payload_digest(one), core.payload_digest(two))
            self.assertNotEqual(core.digest(one), core.digest(two))

    def test_full_catalog_matches_all_packages_and_identities(self):
        data = json.loads((ROOT / 'dist/plugins.json').read_text(encoding='utf-8'))
        self.assertEqual(data, json.loads((ROOT / 'plugins.json').read_text(encoding='utf-8')))
        entries = core.manifest(data, core.DEFAULT_REPO)
        self.assertEqual(len(entries), len(build.PROJECTS))
        for entry in entries:
            path = ROOT / 'dist' / entry['asset']
            self.assertEqual(core.digest(path), entry['package_sha256'])
            self.assertEqual(core.payload_digest(path), entry['sha256'])
            self.assertEqual(path.stat().st_size, entry['size'])
            self.assertEqual(core.identity(path), {'source': data['source'], 'id': entry['id'], 'sha256': entry['sha256']})
            with ZipFile(path) as z:
                self.assertIsNone(z.testzip())
                self.assertFalse(any(n.endswith(('.po', '.pyc')) or '__pycache__' in n or any(p.startswith('.') for p in Path(n).parts) for n in z.namelist()))
                self.assertTrue(all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in z.infolist()))


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(BuildTests)
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())

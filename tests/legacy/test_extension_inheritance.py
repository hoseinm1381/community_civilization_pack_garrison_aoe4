"""Reproduce the real burn regression using pre-repair files and official IDs."""
from pathlib import Path
import hashlib, json, sys, unittest, zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from check_extension_inheritance import Resolver, load_local, summarize
EVIDENCE = ROOT/'work/vietnam_redesign/district_build_repair_20261022'

class ExtensionInheritanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.official = json.loads((EVIDENCE/'official-extensions.json').read_text(encoding='utf-8'))['records']

    def test_actual_failed_build_is_detected_through_both_parent_kinds(self):
        old = {}
        with zipfile.ZipFile(EVIDENCE/'before.zip') as archive:
            for name in archive.namelist():
                if name.startswith(('assets/attrib/instances/ebps/', 'assets/attrib/instances/sbps/')):
                    old[name[len('assets/attrib/instances/'):-4].replace('/', '\\')] = summarize(archive.read(name))
        errors = Resolver(old, self.official).audit()
        districts = [x for x in errors if x.get('extension') == 'ebpextensions\\district_generator_ext']
        self.assertEqual(len(districts), 9)
        self.assertEqual(len({x['blueprint'] for x in districts}), 5)
        self.assertEqual({x['variant'] for x in districts}, {'default', 'campaign'})
        # A direct-only uniqueness check passed despite all nine native errors.
        for error in districts:
            items = old[error['blueprint']][error['variant']]['items']
            self.assertEqual(sum(i.get('value') == error['extension'] for i in items), 1)
        self.assertEqual(len(errors), 10)  # Also finds an older campaign projectile mismatch.

    def test_current_authored_contexts_have_unique_effective_extensions(self):
        self.assertEqual(Resolver(load_local(), self.official).audit(), [])

    def test_historical_repairs_change_only_identity_attributes(self):
        repairs = json.loads((EVIDENCE/'repairs.json').read_text(encoding='utf-8'))
        by_file = {}
        for repair in repairs: by_file.setdefault(repair['file'], []).append(repair)
        self.assertEqual(len(by_file), 6)
        final_hashes = json.loads((EVIDENCE/'final-hashes.json').read_text(encoding='utf-8'))
        self.assertEqual(set(final_hashes), set(by_file))
        with zipfile.ZipFile(EVIDENCE/'before.zip') as archive:
            for name, file_repairs in by_file.items():
                original = archive.read(name)
                repaired = original
                for repair in file_repairs:
                    before, after = repair['before_tag'].encode(), repair['after_tag'].encode()
                    variant = repair['variant']
                    start = 0 if variant == 'default' else repaired.index(('<variant name="' + variant + '">').encode())
                    end = repaired.find(b'<variant ', start + 1)
                    if end < 0: end = len(repaired)
                    scope = repaired[start:end]
                    self.assertEqual(scope.count(before), 1, name)
                    repaired = repaired[:start] + scope.replace(before, after, 1) + repaired[end:]
                    # The live pack must still retain every repaired identity.
                    self.assertEqual((ROOT/name).read_bytes().count(after), 1, name)
                # Pin to the actual post-repair receipt, rather than freezing
                # live localization and gameplay against an older milestone.
                self.assertEqual(hashlib.sha256(repaired).hexdigest(), final_hashes[name], name)
                for repair in reversed(file_repairs):
                    repaired = repaired.replace(repair['after_tag'].encode(), repair['before_tag'].encode(), 1)
                self.assertEqual(repaired, original, name)

    def test_build_entrypoint_runs_fresh_inheritance_preflight_before_editor(self):
        source = (ROOT/'tools/build.ps1').read_text(encoding='utf-8')
        self.assertIn('check_extension_inheritance.py', source)
        self.assertIn('--refresh', source)
        self.assertLess(source.index('check_extension_inheritance.py'), source.index('Start-Process'))

if __name__ == '__main__': unittest.main()

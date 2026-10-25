"""Use the actual broken 0.7.2 inputs to prevent recurrence of the port defect."""
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from check_identity import ROOT, check

class PortIdentity(unittest.TestCase):
    def test_original_port_is_rejected_even_with_correct_project_and_attrib_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            dest=Path(directory)
            with zipfile.ZipFile(ROOT/'output/release_073/before-source.zip') as z:
                for key in ('workspace.json','community_civilization_pack.aoe4mod','assets/attrib/community_civilization_pack.xml','assets/_default.burnproj'):
                    target=dest/key;target.parent.mkdir(parents=True,exist_ok=True)
                    target.write_bytes(z.read(key))
            with self.assertRaisesRegex(AssertionError,'NiceName'):
                check(dest)

    def test_broken_archive_is_rejected_even_when_source_is_fixed(self):
        with self.assertRaisesRegex(AssertionError,'SGA namespace'):
            check(ROOT,ROOT/'output/release_072/delivery/community_civilization_pack.sga')

    def test_current_source_uses_destination_namespace(self):
        self.assertEqual(check(ROOT),'b7fcea91257b408fb9e8ae4d8bc402e1')

if __name__=='__main__':
    unittest.main()

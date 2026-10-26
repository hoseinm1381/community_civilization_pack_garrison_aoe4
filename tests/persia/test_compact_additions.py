import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/compact'))
from current_package import apply_verification_delta

class NewCivilizationDeltaTests(unittest.TestCase):
    def test_explicit_new_blueprint_retains_old_mounts_and_input(self):
        original={'member_sha256':{'old':'a'},'mounts':{'old':'data'}}
        before=copy.deepcopy(original)
        updated=apply_verification_delta(original,{'added_members':{'attrib/ebps/persia/ps_test.rgd':{'sha256':'b'*64,'mount':'attrib'}}})
        self.assertEqual(updated['mounts']['old'],'data')
        self.assertEqual(updated['mounts']['attrib/ebps/persia/ps_test.rgd'],'attrib')
        self.assertEqual(original,before)

    def test_added_member_cannot_override_existing_or_escape_or_use_wrong_mount(self):
        original={'member_sha256':{'attrib/old.rgd':'a'},'mounts':{'attrib/old.rgd':'attrib'}}
        for name,mount in [('attrib/old.rgd','attrib'),('../escape','data'),('attrib/new.rgd','data')]:
            with self.subTest(name=name),self.assertRaises(ValueError):
                apply_verification_delta(original,{'added_members':{name:{'sha256':'b'*64,'mount':mount}}})

if __name__=='__main__':unittest.main()

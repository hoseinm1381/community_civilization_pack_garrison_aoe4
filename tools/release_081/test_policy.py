import unittest
from policy import validate_changes,validate_cook_input,validate_readback

class PreservationPolicy(unittest.TestCase):
    def test_rejects_stale_texture_readback(self):
        with self.assertRaises(ValueError):validate_readback({'model.rrtex':'archive-bytes'},{'model.rrtex':'stale-bytes'})
    def test_accepts_fresh_archive_readback(self):
        validate_readback({'model.rrtex':'archive-bytes'},{'model.rrtex':'archive-bytes'})
    def test_rejects_stale_cook_even_if_both_receipts_are_valid(self):
        with self.assertRaises(ValueError):
            validate_cook_input([{'family':'buffalo','revision':'r3','export_receipt_sha256':'old'}],'r5','new',[3,2,1],[3,2,1])
    def test_rejects_decoded_geometry_drift(self):
        with self.assertRaises(ValueError):
            validate_cook_input([{'family':'buffalo','revision':'r5','export_receipt_sha256':'new'}],'r5','new',[3,2,0],[3,2,1])
    def test_accepts_exact_selected_cook(self):
        validate_cook_input([{'family':'buffalo','revision':'r5','export_receipt_sha256':'new'}],'r5','new',[3,2,1],[3,2,1])
    def test_rejects_gameplay_and_unrelated_art(self):
        for name in ('attrib/ebps/unit.rgd','scar/vietnam.scar','art/other/model.rgm'):
            with self.assertRaises(ValueError): validate_changes({name},set())
    def test_animation_requires_native_qualification(self):
        with self.assertRaises(ValueError):
            validate_changes({'art/animation/cow.rhka'},set())
    def test_only_explicit_ministry_members(self):
        name='art/scenario/cc075/ministry/model.rgm'
        validate_changes({name},{name})
        with self.assertRaises(ValueError): validate_changes({name},set())
    def test_buffalo_media_but_not_animator(self):
        validate_changes({'art/scenario/garrison/cc076/buffalo/model.rrgeom'},set())
        with self.assertRaises(ValueError):
            validate_changes({'art/scenario/garrison/cc076/buffalo/model.rgo'},set())

if __name__=='__main__': unittest.main()

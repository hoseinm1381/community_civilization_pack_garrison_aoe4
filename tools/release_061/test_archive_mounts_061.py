import unittest
from repair_archive_mounts_061 import validate_tocs,mount_delta


def listing(*rows):return {'members':[{'path':p,'toc':t} for p,t in rows]}


class MountTests(unittest.TestCase):
    def test_all_bytes_present_is_insufficient_for_native_loading(self):
        with self.assertRaises(ValueError):validate_tocs(listing(('attrib/attachments/private.rgd','data')))

    def test_correct_engine_sections_pass(self):
        validate_tocs(listing(('attrib/ebps/private.rgd','attrib'),('art/model.rgm','data'),('scar/init.scar','data')))

    def test_wrong_art_section_fails(self):
        with self.assertRaises(ValueError):validate_tocs(listing(('art/model.rgm','attrib')))

    def test_only_explicit_private_mounts_may_change(self):
        old=listing(('attrib/ebps/new.rgd','data'),('art/model.rgm','data'))
        new=listing(('attrib/ebps/new.rgd','attrib'),('art/model.rgm','data'))
        self.assertEqual(len(mount_delta(old,new,{'attrib/ebps/new.rgd'})),1)
        with self.assertRaises(ValueError):mount_delta(old,new,set())

    def test_mount_fix_cannot_silently_remove_resources(self):
        with self.assertRaises(ValueError):mount_delta(listing(('attrib/x.rgd','data')),listing(),{'attrib/x.rgd'})

    def test_case_collision_is_not_resolved_by_mount_selection(self):
        with self.assertRaises(ValueError):validate_tocs(listing(('attrib/x.rgd','attrib'),('ATTRIB/X.RGD','data')))


if __name__=='__main__':unittest.main()

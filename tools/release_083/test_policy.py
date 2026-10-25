import unittest
from policy import *
class PolicyTests(unittest.TestCase):
    def test_all_new_geometry_allowed(self):validate_changes({PREFIX+f+'/model.rrgeom' for f in FAMILIES})
    def test_rejects_gameplay_and_buffalo_animation(self):
        for path in ['attrib/ebps/vietnam/units/skirmisher.rgd','art/scenario/garrison/cc082/buffalo_animator/animator.rhka',PREFIX+'skirmisher2/model.rgo',PREFIX+'skirmisher2/folder/albedo.rrtex']:
            with self.assertRaises(ValueError):validate_changes({PREFIX+f+'/model.rrgeom' for f in FAMILIES}|{path})
    def test_requires_every_age_and_weapon(self):
        with self.assertRaises(ValueError):validate_changes({PREFIX+'skirmisher2/model.rrgeom'})
if __name__=='__main__':unittest.main()

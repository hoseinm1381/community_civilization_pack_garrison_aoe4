from pathlib import Path
import unittest
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[2]


class DynastyRequirementTests(unittest.TestCase):
    def setUp(self):
        root=E.parse(ROOT/'assets/attrib/instances/upgrade/persia/ps_persia_unit_feudal_to_castle.xml').getroot()
        self.requirements=root.find("group/list[@name='requirements']")

    def allowed(self,completed,queued=()):
        def check(node):
            kind=node.get('value')
            if kind=='requirements\\required_any_in_list':
                return any(check(n) for n in node.find("list[@name='requirements']"))
            self.assertEqual(kind,'requirements\\required_player_upgrade')
            name=node.find("instance_reference[@name='upgrade_name']").get('value').split('\\')[-1]
            include_queued=node.find("bool[@name='include_queued']").get('value')=='True'
            present=name in completed or (include_queued and name in queued)
            expected=node.find("bool[@name='is_present']").get('value')=='True'
            return bool(present)==expected
        return all(check(n) for n in self.requirements)

    def test_feudal_needs_preceding_dynasty_and_functioning_gundeshapur(self):
        previous='ps_persia_unit_dark_to_feudal';marker='ps_gundeshapur_functioning'
        self.assertFalse(self.allowed({marker}))
        self.assertFalse(self.allowed({previous}))
        self.assertTrue(self.allowed({previous,marker}))

    def test_castle_keeps_ordinary_prerequisite_path(self):
        self.assertTrue(self.allowed({'ps_persia_unit_dark_to_feudal','castle_age'}))

    def test_completed_or_queued_dynasty_cannot_be_bought_twice(self):
        ready={'ps_persia_unit_dark_to_feudal','ps_gundeshapur_functioning'}
        self.assertFalse(self.allowed(ready|{'ps_persia_unit_feudal_to_castle'}))
        self.assertFalse(self.allowed(ready,{'ps_persia_unit_feudal_to_castle'}))


if __name__=='__main__':unittest.main()

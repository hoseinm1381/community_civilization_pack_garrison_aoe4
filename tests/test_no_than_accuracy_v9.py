"""Actual v9 baseline regression and exact preservation for narrower No Than scatter.

Static only: native hit rates, moving targets, burst completion and multiplayer
still require an engine run.
"""
from pathlib import Path
import copy
import unittest
import xml.etree.ElementTree as ET
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'work/vietnam_redesign/runtime_v9_20261023/weapon'
BASELINE = EVIDENCE.parent / 'before.zip'
BASE = 'assets/attrib/instances/weapon/vietnam/vn_weapon_no_than_vit.xml'
REINFORCED = BASE.replace('_vit.xml', '_vit_reinforced.xml')
VARIANTS = ['default', 'campaign', 'xp3', 'hre_brawl', 'cordoba']
BAG = "group[@name='weapon_bag']"
SCATTER = BAG + "/group[@name='scatter']"
AREA = SCATTER + "/template_reference[@name='area_scatter_option']/template_reference[@name='area_info']"
EDITS = {
    SCATTER + "/float[@name='angle_scatter']": ('30', '3'),
    AREA + "/float[@name='width']": ('48', '4'),
    AREA + "/float[@name='outer_length']": ('2', '1'),
}


def scopes(root):
    return {'default': root, **{n.get('name'): n for n in root.findall('variant')}}


def assert_tight_scatter(root):
    for name, scope in scopes(root).items():
        for path, (_, expected) in EDITS.items():
            actual = scope.find(path)
            assert actual is not None and actual.get('value') == expected, (name, path)


class AccuracyRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with ZipFile(BASELINE) as z:
            cls.before_bytes = z.read(BASE)
            cls.reinforced_before = z.read(REINFORCED)
        cls.before = ET.fromstring(cls.before_bytes)
        cls.after = ET.parse(ROOT / BASE).getroot()

    def test_actual_pre_repair_source_fails_new_accuracy_contract(self):
        with self.assertRaises(AssertionError):
            assert_tight_scatter(self.before)
        self.assertEqual(list(scopes(self.before)), VARIANTS)
        for scope in scopes(self.before).values():
            for path, (old, _) in EDITS.items():
                self.assertEqual(scope.find(path).get('value'), old)

    def test_all_variants_have_tight_nonzero_random_scatter(self):
        assert_tight_scatter(self.after)
        for scope in scopes(self.after).values():
            self.assertEqual(scope.find(AREA).get('value'), r'options\area_info_options\rectangle_area_option')
            for distance in ('near', 'mid', 'far'):
                self.assertEqual(scope.find(BAG + f"/group[@name='accuracy']/float[@name='{distance}']").get('value'), '0')
            self.assertEqual(scope.find(SCATTER + "/bool[@name='burst_pattern_enable']").get('value'), 'False')

    def test_only_allowlisted_values_and_description_changed(self):
        restored = copy.deepcopy(self.after)
        restored.set('description', self.before.get('description'))
        for scope in scopes(restored).values():
            for path, (old, _) in EDITS.items():
                scope.find(path).set('value', old)
        # Includes all identities, projectile, 7-shot burst, range, reload,
        # damage and impact-area data; also rejects broad serialization churn.
        self.assertEqual(ET.tostring(restored), ET.tostring(self.before))
        self.assertEqual(self.after.get('description'), self.before.get('description').replace('wide scatter', 'tight scatter'))

    def test_reinforced_inherits_every_variant_without_shadowing_scatter(self):
        data = (ROOT / REINFORCED).read_bytes()
        self.assertEqual(data, self.reinforced_before)
        child = ET.fromstring(data)
        parent = child.find("instance_reference[@name='parent_pbg']")
        self.assertEqual(parent.get('value'), r'weapon\vietnam\vn_weapon_no_than_vit')
        self.assertEqual(parent.get('mod'), 'a743d7d1d7534cf78817e29d8ded7366')
        self.assertEqual(list(scopes(child)), VARIANTS)
        for name, scope in scopes(child).items():
            self.assertIsNone(scope.find(SCATTER))
            self.assertEqual(scope.find(BAG + "/group[@name='burst']/group[@name='rate_of_fire']/float[@name='max']").get('value'), '9')
            assert_tight_scatter(scopes(self.after)[name])

    def test_current_official_parent_chain_and_rectangle_schema(self):
        parent = self.after.find("instance_reference[@name='parent_pbg']")
        self.assertEqual(parent.get('value'), r'weapon\races\common\ranged\weapon_springald_3')
        official = ET.parse(EVIDENCE / 'official_weapon_springald_3.xml').getroot()
        for scope in scopes(official).values():
            link = scope.find("instance_reference[@name='parent_pbg']")
            if link is not None:
                self.assertEqual(link.get('value'), '')
        donor = ET.parse(EVIDENCE / 'official_weapon_ribauldequin_4.xml').getroot()
        area = donor.find(AREA)
        self.assertEqual(area.get('value'), r'options\area_info_options\rectangle_area_option')
        for field in ('outer_length', 'inner_length', 'width'):
            self.assertIsNotNone(area.find(f"float[@name='{field}']"))
        self.assertEqual(area.find("enum[@name='dynamic_length_type']").get('value'), 'fixed')


if __name__ == '__main__':
    unittest.main(verbosity=2)

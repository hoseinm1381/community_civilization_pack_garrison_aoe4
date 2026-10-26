"""Preserve the user's native fix. Source checks do not prove game stealth."""
from pathlib import Path
import hashlib, json, re, sys, unittest, xml.etree.ElementTree as E, zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'work/vietnam_redesign/runtime_v8_20261023/stealth'
BEFORE = EVIDENCE.parent/'before.zip'
ABILITY = 'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'

def assert_native_requirement(case, data):
    root = E.fromstring(data)
    requirements = root.find("group[@name='ability_bag']/list[@name='requirements']")
    case.assertEqual(len(requirements), 1)
    gate = requirements[0]
    case.assertEqual(gate.get('value'), r'requirements\required_near_entity',
                     'Preserve the user-fixed native proximity requirement; do not restore the failed SCAR bool gate')
    case.assertEqual(gate.get('List.ItemID'), '320707938')
    near = gate.find("list[@name='near_entity_requirement']/template_reference")
    case.assertEqual(near.get('value'), r'requirements\required_unit_type')
    case.assertEqual(near.get('List.ItemID'), '-1499231217')
    case.assertEqual(near.find("enum[@name='unit_type']").get('value'), 'age2_landmark1')
    case.assertEqual(gate.find("enum[@name='nearby_collision_filter']").get('value'), 'executing_player')
    area = gate.find("template_reference[@name='area_option']")
    case.assertEqual(area.get('value'), r'options\area_info_options\circle_area_option')
    case.assertEqual({n.get('name'):n.get('value') for n in area},
                     {'outer_radius':'64','inner_radius':'0','is_two_dimensional':'True','dynamic_radius_type':'fixed'})
    case.assertEqual(root.find("group/enum[@name='activation']").get('value'), 'always_on')
    case.assertEqual(root.find("group/state_tree_node[@name='entity_tree']").get('value'),
                     r'activate_stealth_mal\Master\Defer_EnableStealth\EnableStealth')

class HeadquartersManualFixV8(unittest.TestCase):
    def test_native_user_requirement_preserved(self):
        assert_native_requirement(self, (ROOT/ABILITY).read_bytes())

    def test_actual_failed_v7_receiver_is_rejected(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v7_20261023/resume/before.zip') as z:
            failed = z.read(ABILITY)
        self.assertEqual(hashlib.sha256(failed).hexdigest(), '97070debf1926d84210757765350f6b5dec49dea583221ac1b7a02b8df498268')
        with self.assertRaisesRegex(AssertionError, 'Preserve the user-fixed native proximity'):
            assert_native_requirement(self, failed)

    def test_all_three_actual_manual_files_are_byte_preserved(self):
        changes = json.loads((EVIDENCE/'manual-changes.json').read_text())
        self.assertEqual(len(changes), 3)
        with zipfile.ZipFile(BEFORE) as z:
            for change in changes:
                with self.subTest(file=change['file']):
                    actual = (ROOT/change['file']).read_bytes()
                    self.assertEqual(actual, z.read(change['file']))
                    self.assertEqual(hashlib.sha256(actual).hexdigest(),change['manual_sha256'])

    def test_every_receiver_ebps_sbps_schema_and_all_variants_are_preserved(self):
        count = 0
        with zipfile.ZipFile(BEFORE) as z:
            for name in z.namelist():
                if not name.startswith('assets/attrib/instances/'):continue
                if not any(key in name for key in ('vn_unit_villager_', 'vn_unit_trade_cart_chi', 'vn_headquarters_')):continue
                self.assertEqual((ROOT/name).read_bytes(),z.read(name),name)
                count += 1
        self.assertEqual(count, 9)

    def test_scar_only_changes_comments_and_diagnostic_print(self):
        path = 'assets/scar/vietnam/landmarks.scar'
        with zipfile.ZipFile(BEFORE) as z:before = z.read(path).decode()
        current = (ROOT/path).read_text()
        def gameplay(source):
            source = re.sub(r'print\("VIETNAM_V[78]_HQ_RECEIVER.*?(?=\s*record.signature=signature)', '', source, flags=re.S)
            return '\n'.join(line.strip() for line in source.splitlines() if line.strip() and not line.lstrip().startswith('--'))
        self.assertEqual(gameplay(current),gameplay(before))

    def test_current_inherited_receiver_extension_identities_are_unique(self):
        sys.path.insert(0,str(ROOT/'tools'))
        from check_extension_inheritance import Resolver, load_local
        receipt = json.loads((EVIDENCE/'official-extensions.json').read_text())
        self.assertTrue(Path(receipt['archive']).exists())
        resolver = Resolver(load_local(), receipt['records'])
        checked = 0
        for key, record in resolver.local.items():
            if not any(name in key for name in ('vn_unit_villager_', 'vn_unit_trade_cart_chi')):continue
            for variant in record:
                items = resolver.effective(key, variant)
                values = [i['value'] for i in items]
                self.assertEqual(len(values),len(set(values)),(key,variant))
                checked += 1
        self.assertGreaterEqual(checked, 12)

if __name__ == '__main__':unittest.main()

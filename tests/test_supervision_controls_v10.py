"""Current native hotkey and Buffalo command ownership; no runtime claim."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as E
import zipfile

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'work/vietnam_redesign/runtime_v10_20261023/tuning'
ABILITY = 'assets/attrib/instances/abilities/vietnam/vn_buffalo_work_paddy_vit.xml'
SQUAD = 'assets/attrib/instances/sbps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml'
BINDING = r'hotkeys\hotkey_binding\abilities\ability_supervise'


class SupervisionControlsV10(unittest.TestCase):
    def test_actual_pre_repair_snapshot_has_missing_binding_and_stop_button(self):
        with zipfile.ZipFile(ROOT / 'work/vietnam_redesign/runtime_v10_20261023/before.zip') as archive:
            ability = E.fromstring(archive.read(ABILITY))
            squad = archive.read(SQUAD)
        self.assertEqual(ability.find("group/instance_reference[@name='hotkey_binding']").get('value'), '')
        self.assertEqual(squad.count(b'vn_buffalo_leave_paddy_vit'), 2)

    def test_remappable_native_supervise_binding_and_economic_slot(self):
        root = E.parse(ROOT / ABILITY).getroot()
        bag = root.find('group')
        self.assertEqual(bag.find("instance_reference[@name='hotkey_binding']").get('value'), BINDING)
        official = E.parse(EVIDENCE / 'official_supervise_building_target_chi.xml').getroot()
        self.assertEqual(official.find("group/instance_reference[@name='hotkey_binding']").get('value'), BINDING)
        binding = E.parse(EVIDENCE / 'ability_supervise.xml').getroot()
        self.assertEqual(binding.find("group/string[@name='combo_primary']").get('value'), 'E')
        self.assertEqual(binding.find("group/bool[@name='user_remappable']").get('value'), 'True')
        for position in bag.findall(".//group[@name='ui_position']"):
            self.assertEqual(position.find("int[@name='ui_position_row']").get('value'), '1')
            self.assertEqual(position.find("int[@name='ui_position_column']").get('value'), '3')
        self.assertEqual(bag.find(".//enum[@name='category']").get('value'), 'Economic')

    def test_only_leave_references_removed_from_full_replacement_ability_lists(self):
        with zipfile.ZipFile(ROOT / 'work/vietnam_redesign/runtime_v10_20261023/before.zip') as archive:
            before = archive.read(SQUAD)
        expected = b''.join(line for line in before.splitlines(keepends=True)
                            if b'vn_buffalo_leave_paddy_vit' not in line)
        self.assertEqual((ROOT / SQUAD).read_bytes(), expected)
        root = E.parse(ROOT / SQUAD).getroot()
        for scope in [root, *root.findall('variant')]:
            abilities = scope.find("list/template_reference[@value='sbpextensions\\squad_ability_ext']/list[@name='abilities']")
            self.assertEqual(abilities.get('overrideParent'), 'True')
            names = [node.get('value') for node in abilities]
            self.assertEqual(sum(name.endswith('vn_buffalo_work_paddy_vit') for name in names), 1)
            self.assertFalse(any(name.endswith('vn_buffalo_leave_paddy_vit') for name in names))

    def test_no_active_local_unit_references_leave_ability(self):
        for category in ['ebps', 'sbps']:
            for path in (ROOT / 'assets/attrib/instances' / category).rglob('*.xml'):
                self.assertNotIn('vn_buffalo_leave_paddy_vit', path.read_text(encoding='utf-8-sig'), str(path))

    def test_native_approach_requires_centre_and_only_two_ability_values_change(self):
        bag = E.parse(ROOT / ABILITY).getroot().find('group')
        for name, value in [('range', '0.25'), ('use_simbox_to_simbox_range', 'False'),
                            ('can_move_to_cast', 'True'), ('final_close_in_distance', '0'),
                            ('caster_close_in_distance', '0'), ('range_ignore', 'False')]:
            self.assertEqual(bag.find("*[@name='" + name + "']").get('value'), value)
        with zipfile.ZipFile(ROOT / 'work/vietnam_redesign/runtime_v10_20261023/before.zip') as archive:
            before = archive.read(ABILITY)
        expected = before.replace(b'<float name="range" value="5"', b'<float name="range" value="0.25"')
        expected = expected.replace(b'<instance_reference name="hotkey_binding" value=""',
                                    ('<instance_reference name="hotkey_binding" value="' + BINDING + '"').encode())
        self.assertEqual((ROOT / ABILITY).read_bytes(), expected)


if __name__ == '__main__':
    unittest.main()

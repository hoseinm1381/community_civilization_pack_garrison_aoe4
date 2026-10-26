"""Paddy command reachability on the actual worker-elephant Buffalo."""
from pathlib import Path
import copy
import unittest
import zipfile
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "work/vietnam_redesign/runtime_v7_20261023"
REL = "assets/attrib/instances/sbps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml"
FAKE = r"ebps\vietnam\buildings\economy\rice_paddies\vn_building_resource_farm2_chi"

def scopes(root):
    return [root, *root.findall("variant")]

def engineer(scope):
    return scope.find("list[@name='extensions']/template_reference[@value='sbpextensions\\squad_engineer_ext']")

def direct_paddy_errors(root):
    errors = []
    for scope in scopes(root):
        eng = engineer(scope)
        groups = eng.findall("list[@name='construction_groups']/group")
        if len(groups) != 1:
            errors.append("not exactly one construction group")
            continue
        group = groups[0]
        if group.find("instance_reference[@name='construction_menu']").get("value"):
            errors.append(scope.get("name", "default") + ": Paddy is inside a secondary menu")
        items = group.findall("list[@name='construction_items']/group")
        if len(items) != 1 or items[0].find("instance_reference[@name='ebp']").get("value") != FAKE:
            errors.append("not exclusively fake Paddy")
        else:
            pos = items[0].find("group[@name='ui_position']")
            if [n.get("value") for n in pos] != ["1", "5"]:
                errors.append("not in free direct build slot")
    return errors

class BuffaloBuildV7(unittest.TestCase):
    def test_actual_pre_repair_unit_has_secondary_menu_only(self):
        with zipfile.ZipFile(EVIDENCE / "before.zip") as archive:
            old = E.fromstring(archive.read(REL))
        errors = direct_paddy_errors(old)
        self.assertEqual(len(errors), 4)
        self.assertEqual(sum("secondary menu" in issue for issue in errors), 2)

    def test_active_buffalo_exposes_only_fake_paddy_as_direct_command(self):
        self.assertEqual(direct_paddy_errors(E.parse(ROOT / REL).getroot()), [])

    def test_only_menu_route_and_direct_position_change(self):
        with zipfile.ZipFile(EVIDENCE / "before.zip") as archive:
            old = E.fromstring(archive.read(REL))
        new = E.parse(ROOT / REL).getroot()
        for before, after in zip(scopes(old), scopes(new)):
            b = engineer(before).find("list[@name='construction_groups']/group")
            a = engineer(after).find("list[@name='construction_groups']/group")
            for path in ["instance_reference[@name='construction_menu']", "list/group/group[@name='ui_position']/int[@name='ui_position_row']", "list/group/group[@name='ui_position']/int[@name='ui_position_column']"]:
                x, y = b.find(path), a.find(path)
                y.attrib.clear()
                y.attrib.update(x.attrib)
        def norm(n):
            return n.tag, tuple(sorted(n.attrib.items())), tuple(norm(c) for c in n)
        self.assertEqual(norm(old), norm(new))

    def test_current_native_direct_builder_analogue_and_schema(self):
        base = EVIDENCE / "buffalo/official"
        donor = E.parse(base / "sbps__unit_archer_2_byz_ha_mac.xml").getroot()
        groups = donor.findall(".//group[@name='construction_group']")
        direct = [g for g in groups if g.find("instance_reference[@name='construction_menu']") is not None and not g.find("instance_reference[@name='construction_menu']").get("value")]
        self.assertTrue(direct)
        self.assertTrue(any([n.get("value") for n in g.find("list/group/group[@name='ui_position']")] == ["1", "5"] for g in direct))
        schema = E.parse(base / "squad_engineer_ext.xml").getroot()
        menu = schema.find("list/group/instance_reference[@name='construction_menu']")
        self.assertEqual(menu.get("can_be_null"), "True")
        for name in ["ui_position_row", "ui_position_column"]:
            field = schema.find("list/group/list/group/group[@name='ui_position']/int[@name='" + name + "']")
            self.assertLessEqual(int(field.get("min")), 1)
            self.assertGreaterEqual(int(field.get("max")), 5)

    def test_supervise_leave_have_no_direct_slot_collision(self):
        for name in ["work", "leave"]:
            r = E.parse(ROOT / ("assets/attrib/instances/abilities/vietnam/vn_buffalo_" + name + "_paddy_vit.xml")).getroot()
            pos = r.find("group[@name='ability_bag']/group[@name='ui_position']")
            self.assertNotEqual([n.get("value") for n in pos], ["1", "5"])

if __name__ == "__main__":
    unittest.main()

from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTANCES = ROOT / "assets/attrib/instances"
TOWERS = (
    "vn_building_defense_outpost_chi",
    "vn_building_defense_outpost_2_chi",
    "vn_building_landmark_age1_gatehouse_control_chi",
)


class MigrationBehaviorTests(unittest.TestCase):
    def test_towers_produce_regular_squads(self):
        for name in TOWERS:
            path = INSTANCES / "ebps/vietnam" / f"{name}.xml"
            root = parse_current_xml(path).getroot()
            squads = [node.get("value") for node in root.iter("instance_reference") if node.get("name") == "squad"]
            self.assertTrue(squads, name)
            self.assertFalse([s for s in squads if "_outpost_" in s], name)
            for squad in squads:
                if squad.startswith("sbps\\vietnam\\"):
                    self.assertTrue((current_path(INSTANCES / (squad + ".xml"))).exists(), squad)

    def test_private_blueprints_have_prematch_precache_hooks(self):
        root = parse_current_xml(ROOT / "assets/scar/winconditions/VietnamMode.rdo").getroot()
        prefix = "a743d7d1d7534cf78817e29d8ded7366:"
        source = (current_path(ROOT / "assets/scar/vietnam/prematch_precache.scar")).read_text()
        for kind in ("EntityPrecacheItem", "SquadPrecacheItem"):
            for item in root.iter("DataObject"):
                if item.get("Type") == kind:
                    names = [node.get("Value") for node in item.iter("DataProperty") if node.get("Name") == "m_fileName"]
                    if names and names[0].startswith(prefix):
                        self.assertIn('"' + names[0] + '"', source)
        self.assertIn("Scar_AddInit(VietnamPrecache_Init)", source)
        for kind, directory in (("EntityPrecacheItem", "ebps/vietnam"), ("SquadPrecacheItem", "sbps/vietnam")):
            listed = {
                node.get("Value")
                for item in root.iter("DataObject") if item.get("Type") == kind
                for node in item.iter("DataProperty") if node.get("Name") == "m_fileName"
            }
            for path in (INSTANCES / directory).rglob("*.xml"):
                self.assertIn(prefix + path.stem, listed, str(path))

    def test_towers_use_persistent_native_unlock_and_reciprocal_training_rates(self):
        source = (current_path(ROOT / "assets/scar/vietnam/tower_training.scar")).read_text()
        self.assertIn('"vn_building_landmark_age1_gatehouse_control_chi"', source)
        # Defensive self research must remain usable without the landmark.
        # Executable queue-isolation cases live in test_hideout_redesign.py.
        self.assertIn("Entity_EnableProductionQueue(entity, true)", source)
        self.assertIn("Player_CompleteUpgrade(player.id, unlock)", source)
        self.assertIn("rate = phoMinhAlive and 2 / 3 or 1 / 6", source)
        self.assertNotIn('"cost_ticks_modifier"', source)
        landmark = parse_current_xml(INSTANCES / "ebps/vietnam/vn_building_landmark_age1_gatehouse_control_chi.xml").getroot()
        times = [node.get("value") for node in landmark.iter("float") if node.get("name") == "time_seconds"]
        self.assertEqual(times, ["190", "190"])

    def test_rattan_armor_has_single_runtime_owner(self):
        self.assertFalse(list((INSTANCES / "ebps/vietnam").rglob("vn_unit_*ratten*.xml")))
        self.assertFalse(list((INSTANCES / "sbps/vietnam").rglob("vn_unit_*ratten*.xml")))
        for age in (2, 3, 4):
            path = INSTANCES / "ebps/vietnam" / f"vn_unit_archer_{age}_vit.xml"
            root = parse_current_xml(path).getroot()
            # Ordinary Archers now inherit current stock armor instead of freezing
            # an explicit zero override. Rattan remains the single private owner.
            self.assertEqual(root.find('instance_reference[@name="parent_pbg"]').get('value'),
                             f"ebps\\races\\chinese\\units\\unit_archer_{age}_chi")
            self.assertFalse(any(node.get("name") == "Ranged" for node in root.iter("float")), str(path))
        source = (current_path(ROOT / "assets/scar/vietnam/rattan_armor.scar")).read_text()
        self.assertIn('"armor_scalar_for_ranged_damage"', source)
        self.assertIn("Player_HasUpgrade", source)
        self.assertIn("MAT_EntityType", source)
        self.assertIn("Modifier_ApplyToPlayer", source)
        self.assertIn(":vn_ratten_shield_vit", source)
        self.assertNotIn(":vn_upgrade_rattan_shields_vit", source)

    def test_runtime_private_blueprints_use_archive_owned_identity(self):
        mode = (current_path(ROOT / "assets/scar/winconditions/VietnamMode.scar")).read_text()
        helper = (current_path(ROOT / "assets/scar/vietnam/blueprints.scar")).read_text()
        self.assertIn('import("vietnam/blueprints.scar")', mode)
        self.assertIn("Entity_GetBlueprint(entity) == VietnamBlueprints_Entity(name)", helper)
        for name in ("tower_training.scar", "traps.scar"):
            source = (current_path(ROOT / "assets/scar/vietnam" / name)).read_text()
            self.assertNotIn("BP_GetName(Entity_GetBlueprint", source)



    def test_vietnam_building_times_are_normalized(self):
        expected = {
            "vn_building_house_control_chi.xml": ["15", "15"],
            "vn_building_house_control_faster_chi.xml": ["7.5", "7.5"],
            "vn_building_resource_farm_chi.xml": ["60", "60"],
            "vn_building_resource_farm2_chi.xml": ["60", "60"],
            "vn_building_town_center_chi.xml": ["150", "150"],
        }
        for name, times in expected.items():
            root = parse_current_xml(INSTANCES / "ebps/vietnam" / name).getroot()
            actual = [node.get("value") for node in root.iter("float") if node.get("name") == "time_seconds"]
            self.assertEqual(actual, times, name)
        native_market = (
            "ebps\\races\\chinese\\buildings\\building_econ_market_chi"
            "\\building_econ_market_control_chi"
        )
        standard_market = (
            "ebps\\races\\chinese_ha_01\\buildings\\building_econ_market_chi_ha_01"
            "\\building_econ_market_control_chi_ha_01"
        )
        for name in ("vn_unit_villager_1_chi.xml", "vn_unit_villager_3_chi.xml"):
            source = (current_path(INSTANCES / "sbps/vietnam" / name)).read_text()
            self.assertNotIn(f'value="{native_market}"', source)
            self.assertEqual(source.count(f'value="{standard_market}"'), 2)
        mode = (current_path(ROOT / "assets/scar/winconditions/VietnamMode.scar")).read_text()
        lifecycle = (current_path(ROOT / "assets/scar/vietnam/lifecycle.scar")).read_text()
        self.assertNotIn("building_times.scar", mode)
        self.assertNotIn("VietnamBuildingTimes", lifecycle)
        self.assertFalse((current_path(ROOT / "assets/scar/vietnam/building_times.scar")).exists())

    def test_chinese_influence_note_is_removed_from_private_buildings(self):
        for path in (INSTANCES / "ebps/vietnam").rglob("*.xml"):
            source = current_path(path).read_text()
            self.assertNotIn("influence_decorator", source, str(path))
            self.assertNotIn('name="formatter" value="11199432"', source, str(path))

    def test_dock_and_monastery_inherit_the_existing_production_roster(self):
        parents = {
            "vn_building_unit_naval_chi": (
                "ebps\\races\\chinese\\buildings\\building_unit_naval_chi\\building_unit_naval_chi", 2
            ),
            "vn_building_unit_religious_control_chi": (
                "ebps\\races\\chinese\\buildings\\building_unit_religious_chi\\building_unit_religious_control_chi", 1
            ),
        }
        for name, (parent, menu_count) in parents.items():
            root = parse_current_xml(INSTANCES / "ebps/vietnam" / (name + ".xml")).getroot()
            self.assertEqual(root.find("instance_reference[@name='parent_pbg']").get("value"), parent)
            # Visible district relays are authorized; production still inherits.
            extensions = [node.get("value") for node in root.iter("template_reference")
                          if node.get("value") != "ebpextensions\\district_generator_ext"]
            self.assertEqual(extensions, ["ebpextensions\\ui_ext", "ebpextensions\\ui_ext"])
            for menu in ("vn_unit_villager_1_chi.xml", "vn_unit_villager_3_chi.xml"):
                source = (current_path(INSTANCES / "sbps/vietnam" / menu)).read_text()
                self.assertNotIn(f'value="{parent}"', source)
                self.assertEqual(source.count('value="'+blueprint_key('ebps',name)+'"'), menu_count)


if __name__ == "__main__":
    unittest.main()

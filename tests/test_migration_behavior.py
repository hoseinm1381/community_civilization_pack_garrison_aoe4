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
            root = ET.parse(path).getroot()
            squads = [node.get("value") for node in root.iter("instance_reference") if node.get("name") == "squad"]
            self.assertTrue(squads, name)
            self.assertFalse([s for s in squads if "_outpost_" in s], name)
            for squad in squads:
                if squad.startswith("sbps\\vietnam\\"):
                    self.assertTrue((INSTANCES / (squad + ".xml")).exists(), squad)

    def test_private_blueprints_have_prematch_precache_hooks(self):
        root = ET.parse(ROOT / "assets/scar/winconditions/VietnamMode.rdo").getroot()
        prefix = "b7fcea91257b408fb9e8ae4d8bc402e1:"
        source = (ROOT / "assets/scar/vietnam/prematch_precache.scar").read_text()
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
            for path in (INSTANCES / directory).glob("*.xml"):
                self.assertIn(prefix + path.stem, listed, str(path))

    def test_towers_pause_without_pho_minh(self):
        source = (ROOT / "assets/scar/vietnam/tower_training.scar").read_text()
        self.assertIn('"vn_building_landmark_age1_gatehouse_control_chi"', source)
        self.assertIn("Entity_EnableProductionQueue(entity, phoMinhAlive)", source)
        self.assertIn('"production_speed_modifier", MUT_Multiplication, false, 2 / 3', source)
        landmark = ET.parse(INSTANCES / "ebps/vietnam/vn_building_landmark_age1_gatehouse_control_chi.xml").getroot()
        times = [node.get("value") for node in landmark.iter("float") if node.get("name") == "time_seconds"]
        self.assertEqual(times, ["190", "190"])

    def test_rattan_armor_has_single_runtime_owner(self):
        self.assertFalse(list((INSTANCES / "ebps/vietnam").glob("vn_unit_*ratten*.xml")))
        self.assertFalse(list((INSTANCES / "sbps/vietnam").glob("vn_unit_*ratten*.xml")))
        for age in (2, 3, 4):
            path = INSTANCES / "ebps/vietnam" / f"vn_unit_archer_{age}_vit.xml"
            root = ET.parse(path).getroot()
            self.assertTrue(any(node.get("name") == "Ranged" and node.get("value") == "0" for node in root.iter("float")), str(path))
        source = (ROOT / "assets/scar/vietnam/rattan_armor.scar").read_text()
        self.assertIn('"armor_scalar_for_ranged_damage"', source)
        self.assertIn("Player_HasUpgrade", source)
        self.assertIn("MAT_EntityType", source)
        self.assertIn("Modifier_ApplyToPlayer", source)
        self.assertIn(":vn_ratten_shield_vit", source)
        self.assertNotIn(":vn_upgrade_rattan_shields_vit", source)

    def test_runtime_private_blueprints_use_archive_owned_identity(self):
        mode = (ROOT / "assets/scar/winconditions/VietnamMode.scar").read_text()
        helper = (ROOT / "assets/scar/vietnam/blueprints.scar").read_text()
        self.assertIn('import("vietnam/blueprints.scar")', mode)
        self.assertIn("Entity_GetBlueprint(entity) == VietnamBlueprints_Entity(name)", helper)
        for name in ("tower_training.scar", "traps.scar"):
            source = (ROOT / "assets/scar/vietnam" / name).read_text()
            self.assertNotIn("BP_GetName(Entity_GetBlueprint", source)



    def test_vietnam_building_times_are_normalized(self):
        expected = {
            "vn_building_house_control_chi.xml": ["15", "15"],
            "vn_building_house_control_faster_chi.xml": ["7.5", "7.5"],
            "vn_building_resource_farm_chi.xml": ["6", "6"],
            "vn_building_resource_farm2_chi.xml": ["6", "6"],
            "vn_building_town_center_chi.xml": ["150", "150"],
        }
        for name, times in expected.items():
            root = ET.parse(INSTANCES / "ebps/vietnam" / name).getroot()
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
        private_market = "ebps\\vietnam\\release_040\\vn_040_market_actor"
        for name in ("vn_unit_villager_1_chi.xml", "vn_unit_villager_3_chi.xml"):
            source = (INSTANCES / "sbps/vietnam" / name).read_text()
            self.assertNotIn(f'value="{native_market}"', source)
            self.assertNotIn(f'value="{standard_market}"', source)
            self.assertEqual(source.count(f'value="{private_market}"'), 2)
        private_actor = ET.parse(INSTANCES / "ebps/vietnam/release_040/vn_040_market_actor.xml").getroot()
        self.assertEqual(private_actor.find("instance_reference[@name='parent_pbg']").get("value"), standard_market)
        mode = (ROOT / "assets/scar/winconditions/VietnamMode.scar").read_text()
        lifecycle = (ROOT / "assets/scar/vietnam/lifecycle.scar").read_text()
        self.assertNotIn("building_times.scar", mode)
        self.assertNotIn("VietnamBuildingTimes", lifecycle)
        self.assertFalse((ROOT / "assets/scar/vietnam/building_times.scar").exists())

    def test_chinese_influence_note_is_removed_from_private_buildings(self):
        for path in (INSTANCES / "ebps/vietnam").glob("*.xml"):
            source = path.read_text()
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
            root = ET.parse(INSTANCES / "ebps/vietnam" / (name + ".xml")).getroot()
            self.assertEqual(root.find("instance_reference[@name='parent_pbg']").get("value"), parent)
            extensions = [node.get("value") for node in root.iter("template_reference")]
            self.assertEqual(extensions, ["ebpextensions\\ui_ext", "ebpextensions\\ui_ext"])
            for menu in ("vn_unit_villager_1_chi.xml", "vn_unit_villager_3_chi.xml"):
                source = (INSTANCES / "sbps/vietnam" / menu).read_text()
                self.assertNotIn(f'value="{parent}"', source)
                self.assertEqual(source.count(f'value="ebps\\vietnam\\{name}"'), menu_count)


if __name__ == "__main__":
    unittest.main()

"""Hideout source contracts and Lua behavior; not native engine acceptance."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX

BASES = ('vn_building_defense_outpost_chi', 'vn_building_defense_outpost_2_chi')
UPGRADE = 'upgrade\\vietnam\\vn_upgrade_hideout_upgrade_vit'


def parse(name):
    return parse_current_xml(ROOT / 'assets/attrib/instances/ebps/vietnam' / (name + '.xml')).getroot()


def ext(scope, name):
    return scope.find(f"list/template_reference[@value='ebpextensions\\{name}']")


class HideoutSourceTests(unittest.TestCase):
    def test_both_base_variants_have_exact_cost_health_capacity_and_dropoff(self):
        for name in BASES:
            root = parse(name)
            for scope in [root, *root.findall('variant')]:
                with self.subTest(name=name, variant=scope.get('name', 'normal')):
                    self.assertEqual(ext(scope, 'cost_ext').find("group/enum_table/float[@name='wood']").get('value'), '50')
                    self.assertEqual(ext(scope, 'cost_ext').find("group/float[@name='time_seconds']").get('value'), '30')
                    self.assertEqual(ext(scope, 'health_ext').find("float[@name='hitpoints']").get('value'), '400')
                    for field in ['num_slots', 'num_squad_slots']:
                        self.assertEqual(ext(scope, 'hold_ext').find(f"float[@name='{field}']").get('value'), '1')
                    drop = ext(scope, 'resource_drop_off_ext')
                    self.assertIsNotNone(drop)
                    for resource in ['food', 'wood', 'gold', 'stone']:
                        self.assertEqual(drop.find(f"enum_table[@name='accepted_resources']/bool[@name='{resource}']").get('value'), 'True')
                    tags = ext(scope, 'type_ext').find("list[@name='unit_type_list']")
                    self.assertIn('resource_drop_off', [x.get('value') for x in tags])
                    links = ext(scope, 'upgrade_ext').find("list[@name='standard_upgrades']")
                    self.assertEqual([x.get('value') for x in links], [UPGRADE])

    def test_fortification_is_per_entity_and_has_no_old_economy_action(self):
        t = parse_current_xml(ROOT / 'assets/attrib/instances/upgrade/vietnam/vn_upgrade_hideout_upgrade_vit.xml').getroot()
        bag = t.find('group')
        self.assertEqual(bag.find("enum[@name='owner_type']").get('value'), 'self')
        costs = bag.find("group[@name='time_cost']/enum_table")
        for key, value in [('food', '0'), ('wood', '50'), ('gold', '0'), ('stone', '50')]:
            self.assertEqual(costs.find(f"float[@name='{key}']").get('value'), value)
        self.assertEqual(bag.find("group[@name='time_cost']/float").get('value'), '6')  # Upgrade-only speed correction targets 30 in game.
        reqs = bag.find("list[@name='requirements']")
        self.assertEqual(sum(x.get('value') == 'requirements\\required_entity_upgrade' for x in reqs), 2)
        self.assertTrue(any(x.get('value') == 'upgrade\\dev\\ages\\feudal_age' for x in reqs.iter()))
        self.assertNotIn('upgrade_official_movement_speed', ET.tostring(t, encoding='unicode'))

    def test_fortified_children_inherit_same_visuals_and_dropoff(self):
        for base in BASES:
            t = parse(base + '_fortified')
            parent = t.find("instance_reference[@name='parent_pbg']")
            self.assertEqual(parent.get('value'), blueprint_key('ebps',base))
            for scope in [t, *t.findall('variant')]:
                self.assertEqual(ext(scope, 'health_ext').find("float[@name='hitpoints']").get('value'), '1200')
                self.assertEqual(ext(scope, 'health_ext').find("enum_table/float[@name='Fire']").get('value'), '5')
                self.assertEqual(ext(scope, 'hold_ext').find("float[@name='num_slots']").get('value'), '3')
                self.assertEqual(ext(scope, 'hold_ext').find("float[@name='num_squad_slots']").get('value'), '3')
                self.assertIsNone(ext(scope, 'sight_ext'))
                self.assertEqual(len(ext(scope, 'upgrade_ext').find('list')), 0)


class HideoutBehaviorTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        function Entity_HasUpgrade(e,u) return e.fortification == true end
        function Entity_ConvertBlueprint(e,bp)
            e.bp=bp;e.maximum=1200;e.health=1200;e.conversions=(e.conversions or 0)+1
        end
        ''')
        self.runlua((current_path(ROOT / 'assets/scar/vietnam/hideouts.scar')).read_text())

    def test_upgrade_changes_only_purchased_building_and_preserves_half_health(self):
        self.runlua("a=building(501,'vn_building_defense_outpost_chi',0);a.maximum=400;a.health=200;a.fortification=true;b=building(502,'vn_building_defense_outpost_2_chi',0);b.maximum=400")
        self.runlua('VietnamHideouts_Update(PLAYERS[1],entities);VietnamHideouts_Update(PLAYERS[1],entities)')
        self.assertEqual(self.g.a.bp, PREFIX + BASES[0] + '_fortified')
        self.assertEqual(self.g.a.health, 600)
        self.assertEqual(self.g.a.conversions, 1)
        self.assertEqual(self.g.b.bp, PREFIX + BASES[1])

    def test_dead_and_unfinished_buildings_do_not_convert(self):
        self.runlua("a=building(503,'vn_building_defense_outpost_chi',0);a.fortification=true;a.dead=true;b=building(504,'vn_building_defense_outpost_2_chi',0);b.fortification=true;b.incomplete=true")
        self.runlua('VietnamHideouts_Update(PLAYERS[1],entities)')
        self.assertIsNone(self.g.a.conversions)
        self.assertIsNone(self.g.b.conversions)

    def test_second_variant_keeps_identity_owner_location_and_occupant_reference(self):
        self.runlua("a=building(505,'vn_building_defense_outpost_2_chi',7,22);a.maximum=400;a.health=100;a.fortification=true;a.occupants={99}")
        self.runlua('VietnamHideouts_Update(PLAYERS[2],entities)')
        self.assertEqual(self.g.a.bp, PREFIX + BASES[1] + '_fortified')
        self.assertEqual((self.g.a.id, self.g.a.owner, self.g.a.x, self.g.a.health), (505, 22, 7, 300))
        self.assertEqual(self.g.a.occupants[1], 99)


class HideoutQueueTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        MAT_Entity=1;MAT_Upgrade=394;MUT_Multiplication=1;PITEM_Upgrade=1;PITEM_Spawn=2
        function Modifier_Create(_,name,_,_,value) return {name=name,value=value} end
        function Modifier_ApplyToEntity(m,e) m.active=true;return m end
        function Modifier_ApplyToPlayer(m,p) m.active=true;return m end
        function Modifier_Remove(m) assert(m~=nil);m.active=false end
        function Entity_GetProductionQueueSize(e) return e.queue and 1 or 0 end
        function Entity_GetProductionQueueItemType(e,i) return e.queue.kind end
        function Entity_GetProductionQueueItem(e,i) return e.queue.blueprint end
        function Entity_EnableProductionQueue(e,enabled) e.enabled=enabled end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Player_CompleteUpgrade(p,bp) upgrades[bp]=true end
        ''')
        for module in ['hideouts', 'tower_training']:
            self.runlua((current_path(ROOT / f'assets/scar/vietnam/{module}.scar')).read_text())
        self.runlua("a=building(601,'vn_building_defense_outpost_chi',0)")

    def tick(self):
        self.runlua('VietnamTowerTraining_BeginTick();VietnamTowerTraining_Update(PLAYERS[1],entities);VietnamTowerTraining_EndTick()')

    def test_idle_hideout_can_accept_fortification_without_landmark(self):
        self.tick()
        self.assertTrue(self.g.a.enabled)

    def test_fortification_runs_without_landmark_and_without_research_time_tax(self):
        self.runlua("a.queue={kind=PITEM_Upgrade,blueprint='" + PREFIX + "vn_upgrade_hideout_upgrade_vit'}")
        self.tick()
        self.assertTrue(self.g.a.enabled)
        self.assertEqual(self.g.VietnamTowerTrainingState.applied[601].production.name,'production_speed_modifier')
        self.runlua('VietnamTowerTraining_Cleanup()')  # No removal of nil handles.

    def test_queue_stays_open_and_native_squad_requirement_owns_military_gate(self):
        self.runlua("a.queue={kind=PITEM_Spawn,blueprint='ordinary_unit'}")
        self.tick()
        self.assertTrue(self.g.a.enabled)
        self.assertEqual(self.g.VietnamTowerTrainingState.applied[601].rate, 1 / 6)
        # Native squad prerequisites are covered in test_tower_training_gate.py;
        # do not reintroduce the broad queue pause that blocked fortification.

    def test_fortified_building_remains_a_tower_and_training_resumes_with_landmark(self):
        self.runlua("a.bp='" + PREFIX + BASES[0] + "_fortified';a.queue={kind=PITEM_Spawn,blueprint='ordinary_unit'};tower=building(602,'vn_building_landmark_age1_gatehouse_control_chi',0)")
        self.tick()
        self.assertTrue(self.g.a.enabled)
        self.assertAlmostEqual(self.g.VietnamTowerTrainingState.applied[601].rate, 2 / 3)


if __name__ == '__main__':
    unittest.main()

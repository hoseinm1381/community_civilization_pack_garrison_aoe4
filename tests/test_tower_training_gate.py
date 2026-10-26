"""Native source graph + executable SCAR state transitions; not engine acceptance."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import json
import unittest
import xml.etree.ElementTree as E
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX

UNLOCK='vn_upgrade_pho_minh_training_unlocked_vit'
TOWER='vn_building_landmark_age1_gatehouse_control_chi'
BASE='vn_building_defense_outpost_chi'
W=ROOT/'work/vietnam_redesign'

class TowerGateSourceTests(unittest.TestCase):
    def test_only_hideout_and_tower_producers_use_gated_squad_children(self):
        a=ROOT/'assets/attrib/instances';graph=json.loads((current_path(W/'TOWER_GATE_GRAPH.json')).read_text(encoding='utf-8'))
        self.assertEqual(len(graph['aliases']),14)
        for alias,parent in graph['aliases'].items():
            t=parse_current_xml(a/'sbps/vietnam'/(alias+'.xml')).getroot()
            self.assertEqual(t.find('instance_reference[@name="parent_pbg"]').get('value'),blueprint_key('sbps',parent))
            self.assertFalse(t.findall('.//instance_reference[@name="type"]'))
            for s in [t,*t.findall('variant')]:
                table=s.find('list/template_reference/list[@name="requirement_table"]')
                self.assertNotEqual(table.get('overrideParent'),'True')
                self.assertEqual(table.find('template_reference/instance_reference[@name="upgrade_name"]').get('value'),'upgrade\\vietnam\\'+UNLOCK)
                self.assertEqual(table.find('template_reference/bool[@name="is_present"]').get('value'),'True')
        for name in [BASE,'vn_building_defense_outpost_2_chi',TOWER]:
            t=parse_current_xml(a/'ebps/vietnam'/(name+'.xml')).getroot()
            refs=[n.get('value') for n in t.findall('.//list[@name="spawn_items"]/group/instance_reference[@name="squad"]') if n.get('value')]
            self.assertTrue(refs)
            self.assertTrue(all(ref.split('\\')[-1] in graph['aliases'] for ref in refs))
        for name in ['vn_building_unit_ranged_control_chi','vn_building_unit_infantry_control_chi','vn_building_landmark_age3_trung_foundaries_vit']:
            t=parse_current_xml(a/'ebps/vietnam'/(name+'.xml')).getroot()
            self.assertFalse(any(n.get('value','').split('\\')[-1] in graph['aliases'] for n in t.iter('instance_reference')))

    def test_unlock_marker_is_silent_free_effectless_and_not_offered(self):
        a=ROOT/'assets/attrib/instances';key='upgrade\\vietnam\\'+UNLOCK
        t=parse_current_xml(a/'upgrade/vietnam'/(UNLOCK+'.xml')).getroot();bag=t.find('group')
        self.assertEqual(bag.find('enum[@name="owner_type"]').get('value'),'player')
        self.assertTrue(all(float(n.get('value'))==0 for n in bag.findall('group[@name="time_cost"]//float')))
        self.assertFalse(list(bag.find('list[@name="float_properties"]')))
        self.assertTrue(all(not n.get('value') for n in bag.findall('group[@name="state_tree_references"]//state_tree_node')))
        for p in (a/'ebps').rglob('*.xml'):
            self.assertFalse(any(n.get('value')==key for n in parse_current_xml(p).getroot().findall('.//list[@name="standard_upgrades"]/instance_reference')))

class TowerGateRuntimeTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        MAT_Entity=1;MAT_Upgrade=394;MUT_Multiplication=1; playerUpgrades={};grants={};allModifiers={};playerModifiers={}
        function Player_HasUpgrade(p,bp) return playerUpgrades[p] and playerUpgrades[p][bp] == true or false end
        function Player_CompleteUpgrade(p,bp)
            playerUpgrades[p]=playerUpgrades[p] or {};playerUpgrades[p][bp]=true
            grants[#grants+1]={player=p,bp=bp}
        end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) assert(not g[i].despawned);return g[i] end
        function Modifier_Create(kind,name,_,_,value,target) return {kind=kind,name=name,value=value,target=target} end
        function Modifier_ApplyToEntity(m,e) m.active=true;m.entity=e.id;allModifiers[#allModifiers+1]=m;return m end
        function Modifier_ApplyToPlayer(m,p) m.active=true;m.player=p;playerModifiers[#playerModifiers+1]=m;return m end
        function Modifier_Remove(m) assert(m~=nil);m.active=false end
        function Entity_EnableProductionQueue(e,enabled) e.enabled=enabled end
        function Entity_GetProductionQueueSize(e) return e.queue and 1 or 0 end
        function Entity_GetProductionQueueItemType(e,i) return e.queue.kind end
        function Entity_GetProductionQueueItem(e,i) return e.queue.blueprint end
        PITEM_Upgrade=1;PITEM_Spawn=2
        function activeModifiers(id)
            local count=0;local value=nil
            for _,m in ipairs(allModifiers) do
                if m.active and m.entity==id then count=count+1;value=m.value end
            end
            return count,value
        end
        ''')
        for module in ['hideouts','tower_training']:
            self.runlua((current_path(ROOT/f'assets/scar/vietnam/{module}.scar')).read_text(encoding='utf-8'))
        self.runlua("a=building(801,'"+BASE+"',0)")

    def tick(self,code='VietnamTowerTraining_Update(PLAYERS[1],entities)'):
        self.runlua('VietnamTowerTraining_BeginTick();'+code+';VietnamTowerTraining_EndTick()')

    def test_no_landmark_or_unfinished_landmark_does_not_grant_unlock_but_queue_accepts_fortification(self):
        self.tick();self.assertEqual(len(self.g.grants),0);self.assertTrue(self.g.a.enabled)
        self.runlua("tower=building(802,'"+TOWER+"',0);tower.incomplete=true;tower.progress=0.5")
        self.tick();self.assertEqual(len(self.g.grants),0)

    def test_completion_unlocks_once_and_applies_one_training_modifier_only(self):
        self.runlua("tower=building(802,'"+TOWER+"',0)")
        self.tick();self.tick()
        self.assertEqual(len(self.g.grants),1)
        self.assertTrue(self.g.playerUpgrades[11][PREFIX+UNLOCK])
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,2/3))
        self.assertEqual(self.lua.eval('activeModifiers(802)'),(1,2/3))

    def test_destroyed_landmark_keeps_unlock_and_switches_to_six_times_then_repairs(self):
        self.runlua("tower=building(802,'"+TOWER+"',0)");self.tick()
        self.runlua('tower.dead=true;tower.health=0');self.tick()
        self.assertTrue(self.g.playerUpgrades[11][PREFIX+UNLOCK]);self.assertTrue(self.g.a.enabled)
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,1/6))
        self.assertEqual(self.lua.eval('activeModifiers(802)')[0],0)
        self.runlua('tower.dead=false;tower.health=1;tower.incomplete=true;tower.progress=0.7');self.tick()
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,1/6))
        self.runlua('tower.incomplete=false;tower.progress=1');self.tick()
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,1/6))
        self.assertEqual(self.lua.eval('activeModifiers(802)')[0],0)
        self.runlua('tower.health=100');self.tick()
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,2/3));self.assertEqual(len(self.g.grants),1)

    def test_ordinary_damage_to_live_tower_does_not_disable_normal_training(self):
        self.runlua("tower=building(802,'"+TOWER+"',0)");self.tick()
        self.runlua('tower.health=50');self.tick()
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,2/3))

    def test_fortification_specific_correction_keeps_thirty_seconds_in_all_tower_states(self):
        self.tick()
        correction=self.g.VietnamTowerTrainingState.fortifications[1]
        self.assertAlmostEqual(correction.speed,1.2)
        self.assertEqual(correction.handle.kind,394)
        self.assertEqual(correction.handle.target,PREFIX+'vn_upgrade_hideout_upgrade_vit')
        self.assertAlmostEqual(6/(1/6)/correction.speed,30)
        self.runlua("tower=building(802,'"+TOWER+"',0)");self.tick()
        self.assertFalse(correction.handle.active)
        correction=self.g.VietnamTowerTrainingState.fortifications[1]
        self.assertAlmostEqual(correction.speed,0.3)
        self.assertAlmostEqual(6/(2/3)/correction.speed,30)
        self.runlua('tower.dead=true;tower.health=0');self.tick()
        self.assertAlmostEqual(self.g.VietnamTowerTrainingState.fortifications[1].speed,1.2)
        self.runlua('VietnamTowerTraining_Cleanup()')
        self.assertTrue(all(not self.g.playerModifiers[i].active for i in range(1,len(self.g.playerModifiers)+1)))

    def test_zero_health_ruin_does_not_count_as_operational_even_if_alive_flag_remains(self):
        self.runlua("tower=building(802,'"+TOWER+"',0);tower.health=0")
        self.tick();self.assertEqual(len(self.g.grants),0)

    def test_fortification_conversion_and_new_hideouts_keep_one_current_modifier(self):
        self.runlua("tower=building(802,'"+TOWER+"',0)");self.tick()
        old_modifier=self.g.VietnamTowerTrainingState.applied[801].production
        self.runlua("a.bp='"+PREFIX+BASE+"_fortified';b=building(803,'vn_building_defense_outpost_2_chi',0)")
        self.tick()
        self.assertEqual(self.lua.eval('activeModifiers(801)'),(1,2/3))
        self.assertEqual(self.lua.eval('activeModifiers(803)'),(1,2/3))
        self.assertTrue(self.g.b.enabled)
        self.assertFalse(old_modifier.active)

    def test_independent_players_regular_range_and_cleanup(self):
        self.runlua("tower=building(802,'"+TOWER+"',0);b=building(804,'"+BASE+"',0,22);range=building(805,'vn_building_unit_ranged_control_chi',0)")
        self.tick('VietnamTowerTraining_Update(PLAYERS[1],{a,tower,range});VietnamTowerTraining_Update(PLAYERS[2],{b})')
        self.assertTrue(self.g.playerUpgrades[11][PREFIX+UNLOCK]);self.assertIsNone(self.g.playerUpgrades[22])
        self.assertEqual(self.lua.eval('activeModifiers(804)'),(1,1/6))
        self.assertEqual(self.lua.eval('activeModifiers(805)')[0],0)
        self.runlua('VietnamTowerTraining_Cleanup()')
        self.assertEqual(self.lua.eval('activeModifiers(801)')[0],0)
        self.assertEqual(self.lua.eval('activeModifiers(804)')[0],0)

if __name__=='__main__':unittest.main()

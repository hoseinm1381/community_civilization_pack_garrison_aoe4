"""Foundries discount lifecycle mocks and source graph; not native acceptance."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest
import xml.etree.ElementTree as E
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX

LANDMARK='vn_building_landmark_age3_trung_foundaries_vit'
A=ROOT/'assets/attrib/instances'

class FoundriesSourceTests(unittest.TestCase):
    def test_no_active_cheap_production_or_chemistry_paths(self):
        for p in (A/'ebps/vietnam').rglob('*.xml'):
            t=parse_current_xml(p).getroot()
            for n in t.findall('.//list[@name="spawn_items"]/group/instance_reference[@name="squad"]'):
                self.assertNotIn(n.get('value','').split('\\')[-1],[
                    'vn_unit_handcannon_4_chi_cheap','vn_tower_train_handcannon_4_chi_cheap','vn_unit_culverin_4_chi_cheap'])
            for n in t.findall('.//list[@name="standard_upgrades"]/instance_reference'):
                self.assertNotIn('vn_upgrade_siege_chemistry_vit_cheap',n.get('value',''))

    def test_regular_squads_not_blocked_by_foundries(self):
        for name in ['vn_unit_handcannon_4_chi','vn_unit_culverin_4_chi']:
            t=parse_current_xml(A/'sbps/vietnam'/(name+'.xml')).getroot()
            self.assertFalse(t.findall('.//instance_reference[@name="structure_name"]'))

    def test_single_normal_chemistry_at_both_producers(self):
        key=r'upgrade\vietnam\vn_upgrade_siege_chemistry_vit'
        for name in ['vn_building_landmark_age3_trung_foundaries_vit','vn_building_tech_university_control_chi']:
            t=parse_current_xml(A/'ebps/vietnam'/(name+'.xml')).getroot()
            table=t.find('list/template_reference[@value="ebpextensions\\upgrade_ext"]/list')
            self.assertEqual(sum(n.get('value')==key for n in table),1)
        t=parse_current_xml(A/'upgrade/vietnam/vn_upgrade_siege_chemistry_vit.xml').getroot()
        self.assertFalse(any('cheap' in n.get('value','') for n in t.iter('instance_reference')))
        cost=t.find('group/group[@name="time_cost"]')
        self.assertEqual([cost.find('enum_table/float[@name="'+k+'"]').get('value') for k in ['food','gold']],['300','700'])
        self.assertEqual(cost.find('float').get('value'),'90')

class FoundriesBehaviorTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        modifiers={}; MAT_EntityType=1;MAT_Upgrade=2;MUT_Multiplication=3
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Modifier_Create(kind,name,usage,exclusive,value,bp)
            return {kind=kind,name=name,usage=usage,value=value,bp=bp}
        end
        function Modifier_ApplyToPlayer(m,p,time)
            m.player=p;m.active=true;modifiers[#modifiers+1]=m;return m
        end
        function Modifier_Remove(m) assert(m.active);m.active=false end
        function activeCount(p)
            local n=0;for _,m in ipairs(modifiers) do if m.active and m.player==p then n=n+1 end end;return n
        end
        ''')
        path=ROOT/'assets/scar/vietnam/foundries_discount.scar'
        self.assertTrue(current_path(path).exists(),'Foundries controller not implemented')
        self.runlua(current_path(path).read_text(encoding='utf-8'))
        self.runlua("forge=building(501,'"+LANDMARK+"',0)")

    def tick(self,player='PLAYERS[1]',group='entities'):
        self.runlua('VietnamFoundries_Update('+player+','+group+')')

    def test_completion_applies_once_exact_roster_and_no_time_discount(self):
        self.runlua('forge.incomplete=true;forge.progress=0.5');self.tick()
        self.assertEqual(self.lua.eval('activeCount(11)'),0)
        self.runlua('forge.incomplete=false;forge.progress=1');self.tick();self.tick()
        self.assertEqual(self.lua.eval('activeCount(11)'),16)
        targets=set()
        for m in self.g.modifiers.values():
            self.assertEqual(m.value,0.8);self.assertNotIn('speed',m.name);self.assertNotIn('ticks',m.name)
            targets.add(m.bp)
        self.assertEqual(targets,{PREFIX+'vn_unit_handcannon_4_chi',r'ebps\races\chinese\units\unit_culverin_4_chi',PREFIX+'vn_upgrade_siege_chemistry_vit',PREFIX+'vn_upgrade_serpentine_powder_vit'})

    def test_destroy_partial_repair_full_repair_repeated_cycles(self):
        self.tick()
        for _ in range(2):
            self.runlua('forge.dead=true;forge.health=0');self.tick();self.assertEqual(self.lua.eval('activeCount(11)'),0)
            self.runlua('forge.dead=false;forge.health=40;forge.incomplete=false');self.tick();self.assertEqual(self.lua.eval('activeCount(11)'),0)
            self.runlua('forge.health=100');self.tick();self.assertEqual(self.lua.eval('activeCount(11)'),16)

    def test_ordinary_damage_stays_active_and_cleanup_removes_once(self):
        self.tick();self.runlua('forge.health=40');self.tick();self.assertEqual(self.lua.eval('activeCount(11)'),16)
        self.runlua('VietnamFoundries_Cleanup();VietnamFoundries_Cleanup()');self.assertEqual(self.lua.eval('activeCount(11)'),0)

    def test_players_are_independent_and_defeat_removes_modifiers(self):
        self.tick();self.tick('PLAYERS[2]','{}')
        self.assertEqual(self.lua.eval('activeCount(11)'),16);self.assertEqual(self.lua.eval('activeCount(22)'),0)
        self.runlua("forge2=building(502,'"+LANDMARK+"',0,22)")
        self.tick('PLAYERS[2]','{forge2}');self.assertEqual(self.lua.eval('activeCount(22)'),16)
        self.runlua('function Player_IsAlive(p) return p~=11 end');self.tick(group='{forge}')
        self.assertEqual(self.lua.eval('activeCount(11)'),0);self.assertEqual(self.lua.eval('activeCount(22)'),16)

    def test_real_lifecycle_filters_china_and_removes_defeated_player_discount(self):
        self.runlua('''
        function VietnamTowerTraining_BeginTick() end
        function VietnamTowerTraining_EndTick() end
        function VietnamTowerTraining_Update() end
        function VietnamRattanArmor_Update() end
        function VietnamPaddyFood_Update() end
        function VietnamPaddyConstruction_Update() end
        function VietnamPaddyWood_Update() end
        function VietnamPagodaBuffalo_Update() end
        function VietnamGarden_Update() end
        function VietnamTunnels_Update() end
        function VietnamTunnels_Step() end
        function VietnamTunnels_UpdateUI() end
        function VietnamScorchedEarth_Update() end
        function VietnamDynasty_Update() end
        function VietnamLandmarks_Update() end
        function VietnamHideouts_Update() end
        function VietnamTraps_Update() end
        function VietnamTraps_Tick() end
        ''')
        self.runlua((current_path(ROOT/'assets/scar/vietnam/flooded_citadel.scar')).read_text(encoding='utf-8'))
        self.runlua((current_path(ROOT/'assets/scar/vietnam/lifecycle.scar')).read_text(encoding='utf-8'))
        self.runlua("building(502,'"+LANDMARK+"',0,22);VietnamLifecycleState.active=true;VietnamLifecycleState.civilizations={[1]='vietnam',[2]='china'};VietnamLifecycle_Tick()")
        self.assertEqual(self.lua.eval('activeCount(11)'),16)
        self.assertEqual(self.lua.eval('activeCount(22)'),0)
        self.runlua('function Player_IsAlive(p) return p~=11 end;VietnamLifecycle_Tick()')
        self.assertEqual(self.lua.eval('activeCount(11)'),0)

if __name__=='__main__':unittest.main()

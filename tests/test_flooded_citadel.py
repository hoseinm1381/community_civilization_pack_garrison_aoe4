"""Footprint geometry and lifecycle mocks; native field acceptance is separate."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest,xml.etree.ElementTree as E
from test_runtime_repairs import RuntimeFixture,ROOT,PREFIX
KEY='vn_building_landmark_age2_imperrial_citadel_vit'

class FloodedCitadelTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        p=ROOT/'assets/scar/vietnam/flooded_citadel.scar';self.assertTrue(current_path(p).exists(),'Field not implemented')
        self.runlua('''
        MAT_Entity=1;MUT_Multiplication=2;R_ENEMY=3;R_ALLY=4;GE_EntityKilled=7
        function Player_GetAllEntities(id) local g={};for _,e in ipairs(entities) do if e.owner==id then g[#g+1]=e end end;return g end
        function Entity_GetStateModelBool(e,key) assert(key=="landmark_active");return e.landmarkActive~=false end
        mods={};listeners=0;removed=0;relations={};speeds={};deadPlayers={}
        function Player_IsAlive(p) return not deadPlayers[p] end
        function Player_ObserveRelationship(a,b)
          if a==b then return R_ALLY end
          return relations[a..':'..b] or R_ENEMY
        end
        function EGroup_CountSpawned(g) local n=0;for _,e in ipairs(g) do if not e.unspawned then n=n+1 end end;return n end
        function EGroup_GetSpawnedEntityAt(g,i) local n=0;for _,e in ipairs(g) do if not e.unspawned then n=n+1;if n==i then return e end end end end
        function BP_GetEntityBPDefaultSpeed(bp,modified,p) assert(not modified);return speeds[bp] or 4 end
        function Modifier_Create(kind,name,usage,exclusive,value,bp) assert(kind==MAT_Entity and name=='speed_maximum_modifier');return {value=value} end
        function Modifier_ApplyToEntity(m,e,time) m.id=e.id;m.active=true;mods[#mods+1]=m;return m end
        function Modifier_Remove(m) assert(m.active);m.active=false end
        function Rule_AddGlobalEvent(f,event) assert(event==GE_EntityKilled);listeners=listeners+1 end
        function Rule_RemoveGlobalEvent(f) removed=removed+1 end
        function activeCount(id) local n=0;for _,m in ipairs(mods) do if m.id==id and m.active then n=n+1 end end;return n end
        function factor(id) local f=1;for _,m in ipairs(mods) do if m.id==id and m.active then f=f*m.value end end;return f end
        civs={[1]='vietnam',[2]='china',[3]='china'}
        function tick()
          local groups={};for _,p in ipairs(PLAYERS) do local g={};Player_GetEntitiesEGroup(p.id,g);groups[p.index]=g end
          VietnamFloodedCitadel_Update(groups,civs)
        end
        ''')
        self.runlua(current_path(p).read_text(encoding='utf-8'))
        self.runlua("citadel=building(701,'"+KEY+"',0);enemy=unit(702,39,22);enemy.bp='enemy';VietnamFloodedCitadel_Start()")

    def tick(self):self.runlua('tick()')

    def test_persistent_living_ruin_has_no_field_until_native_reactivation(self):
        self.tick()
        self.runlua('citadel.landmarkActive=false')
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.health=40')
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.landmarkActive=true;citadel.health=100')
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)

    def test_squad_members_are_scanned_even_when_owned_building_group_omits_them(self):
        self.runlua("function Player_GetEntitiesEGroup(id,g) for _,e in ipairs(entities) do if e.owner==id and e.building then g[#g+1]=e end end end")
        self.tick();self.assertAlmostEqual(self.lua.eval('factor(702)'),.7)

    def test_empty_gardens_has_dedicated_command_slot(self):
        tree=parse_current_xml(ROOT/'assets/attrib/instances/upgrade/vietnam/vn_upgrade_empty_gardens_vit.xml')
        for position in tree.findall('.//group[@name="ui_position"]'):
            if position.find('int[@name="ui_position_row"]').get('value')=='-1':continue
            self.assertEqual(position.find('int[@name="ui_position_row"]').get('value'),'2')
            self.assertEqual(position.find('int[@name="ui_position_column"]').get('value'),'4')

    def test_edge_and_corner_measurement_is_from_footprint(self):
        self.tick();self.assertAlmostEqual(self.lua.eval('factor(702)'),.7)
        self.runlua('enemy.x=40');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('enemy.x=40.01');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('enemy.x=30.6;enemy.z=30.6');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('enemy.x=31;enemy.z=31');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_construction_damage_destruction_and_full_repair(self):
        self.runlua('citadel.incomplete=true;citadel.progress=.5');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.incomplete=false;citadel.progress=1');self.tick()
        self.runlua('citadel.health=40');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('citadel.dead=true;citadel.health=0;VietnamFloodedCitadel_OnEntityKilled({victim=citadel})')
        self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.dead=false;citadel.health=40');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.health=100');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)

    def test_destruction_between_ticks_requires_full_repair(self):
        self.runlua('citadel.dead=true;citadel.health=0;VietnamFloodedCitadel_OnEntityKilled({victim=citadel});citadel.dead=false;citadel.health=10')
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.health=100');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)

    def test_poll_detects_missing_unspawned_and_defeated_source(self):
        self.tick();self.runlua('citadel.unspawned=true');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.unspawned=false;citadel.health=40');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua('citadel.health=100');self.tick();self.runlua('deadPlayers[11]=true');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_allies_owner_neutral_and_diplomacy(self):
        self.runlua("own=unit(703,30,11);own.bp='own';ally=unit(704,30,33);ally.bp='ally';relations['11:33']=R_ALLY")
        self.tick();self.assertEqual(self.lua.eval('activeCount(703)'),0);self.assertEqual(self.lua.eval('activeCount(704)'),0)
        self.runlua("relations['11:22']=R_ALLY");self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_land_roster_animals_and_naval_props_exclusions(self):
        self.runlua("enemy.types={animal=true};ship=unit(703,30,22);ship.bp='ship';ship.types={naval_unit=true};prop=unit(704,30,22);prop.bp='prop';speeds['prop']=0;building(705,'enemyhouse',30,22)")
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        for id in [703,704,705]:self.assertEqual(self.lua.eval('activeCount('+str(id)+')'),0)
        self.runlua('enemy.held=true');self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_overlap_does_not_stack_and_source_death_preserves_other_field(self):
        self.runlua("second=building(703,'"+KEY+"',0)");self.tick();self.tick()
        self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('citadel.dead=true;VietnamFloodedCitadel_OnEntityKilled({victim=citadel})');self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('second.dead=true;VietnamFloodedCitadel_OnEntityKilled({victim=second})');self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_independent_trap_slow_survives_exit_and_cleanup(self):
        self.runlua('trap={id=702,active=true,value=.8};mods[#mods+1]=trap');self.tick()
        self.assertAlmostEqual(self.lua.eval('factor(702)'),.56)
        self.runlua('enemy.x=100');self.tick();self.assertAlmostEqual(self.lua.eval('factor(702)'),.8)
        self.runlua('enemy.x=30');self.tick();self.runlua('VietnamFloodedCitadel_Cleanup()');self.assertAlmostEqual(self.lua.eval('factor(702)'),.8)

    def test_blueprint_conversion_and_target_death_do_not_leave_stacked_handles(self):
        self.tick();self.runlua("enemy.bp='veteran'");self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('enemy.dead=true;VietnamFloodedCitadel_OnEntityKilled({victim=enemy})');self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_cleanup_registration_and_china_source_is_not_active(self):
        self.runlua('VietnamFloodedCitadel_Start()');self.assertEqual(self.g.listeners,1)
        self.tick();self.runlua('VietnamFloodedCitadel_Cleanup();VietnamFloodedCitadel_Cleanup()')
        self.assertEqual(self.g.removed,1);self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua("VietnamFloodedCitadel_Start();civs[1]='china'");self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),0)

    def test_two_vietnamese_owners_observe_independent_enemy_relationships(self):
        self.runlua("second=building(703,'"+KEY+"',0,33);civs[3]='vietnam';relations['33:22']=R_ALLY")
        self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)
        self.runlua('citadel.dead=true;VietnamFloodedCitadel_OnEntityKilled({victim=citadel})')
        self.assertEqual(self.lua.eval('activeCount(702)'),0)
        self.runlua("relations['33:22']=R_ENEMY");self.tick();self.assertEqual(self.lua.eval('activeCount(702)'),1)

    def test_real_lifecycle_reuses_owned_groups_without_leaks(self):
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
        function VietnamFoundries_Update() end
        function VietnamDynasty_Update() end
        function VietnamLandmarks_Update() end
        function VietnamHideouts_Update() end
        function VietnamTraps_Update() end
        function VietnamTraps_Tick() end
        ''')
        self.runlua((current_path(ROOT/'assets/scar/vietnam/lifecycle.scar')).read_text(encoding='utf-8'))
        self.runlua('VietnamLifecycleState.active=true;VietnamLifecycleState.civilizations=civs;VietnamLifecycle_Tick()')
        self.assertEqual(self.lua.eval('activeCount(702)'),1);self.assertEqual(self.g.liveGroups,0)

    def test_geometry_constants_are_tied_to_unchanged_native_footprint(self):
        p=ROOT/'assets/attrib/instances/ebps/vietnam'/(KEY+'.xml');t=parse_current_xml(p).getroot()
        for scope in [t,*t.findall('variant')]:
            ext=scope.find('list/template_reference[@value="ebpextensions\\site_ext"]')
            if ext is not None:
                self.assertEqual([n.get('value') for n in ext.findall('group[@name="footprint_scale"]/float')],['8','8'])
                self.assertEqual(ext.find('bool[@name="forced_axis_aligned_footprint"]').get('value'),'True')

if __name__=='__main__':unittest.main()

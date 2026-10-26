"""Failed v8 snapshot plus wrapped-player/native-resource regressions; not engine proof."""
import zipfile
from test_paddy_wood import PaddyWoodFixture
from test_runtime_repairs import ROOT

WOOD='assets/scar/vietnam/paddy_wood.scar'
SNAP=ROOT/'work/vietnam_redesign/runtime_v9_20261023/before.zip'

class PaddyV9(PaddyWoodFixture):
    def wrapped(self, source):
        self.runlua(source)
        self.runlua("""
        function Player_GetID(p) return type(p)=='table' and p.playerID or p end
        function Player_OwnsEntity(p,e) return not World_OwnsEntity(e) and Player_GetID(p)==Player_GetID(Entity_GetPlayerOwner(e)) end
        function Entity_GetPlayerOwner(e) return {playerID=e.owner} end
        function Squad_GetPlayerOwner(s) return {playerID=s.owner} end
        """)
    def test_actual_failed_v8_rejects_same_player_in_distinct_handle_wrappers(self):
        with zipfile.ZipFile(SNAP) as z:self.wrapped(z.read(WOOD).decode())
        self.start()
        self.assertEqual(self.g.bank[11],0)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))
    def test_current_accepts_equivalent_wrapped_owner_and_pays_explicit_assignment(self):
        self.wrapped((ROOT/WOOD).read_text())
        self.start()
        self.assertAlmostEqual(self.g.bank[11],.375*.25)
    def test_pending_native_replacement_is_not_a_scripted_income_target(self):
        self.runlua('VietnamPaddyConstructionState={replacements={[501]=true}}')
        self.start();self.assertEqual(self.g.bank[11],0)
        self.runlua('VietnamPaddyConstructionState.replacements[501]=nil');self.tick(.75);self.runlua('assign(buffalo)')
        self.tick(1);self.tick(1.25);self.assertAlmostEqual(self.g.bank[11],.375*.25)
    def test_current_rejects_distinct_player_and_world(self):
        for change in ['paddy.owner=22','paddy.world=true','buffalo.owner=22']:
            self.setUp();self.wrapped((ROOT/WOOD).read_text());self.runlua(change);self.start()
            self.assertEqual(self.g.bank[11],0)


from test_runtime_repairs import RuntimeFixture, PREFIX
import xml.etree.ElementTree as E

class PaddyCreationV9(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua("""
        function Player_GetID(p) return type(p)=='table' and p.playerID or p end
        function Entity_GetPlayerOwner(e) return {playerID=e.owner} end
        function Player_OwnsEntity(p,e) return not World_OwnsEntity(e) and Player_GetID(p)==Player_GetID(Entity_GetPlayerOwner(e)) end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Entity_GetHeading(e) return {x=1,y=0,z=0} end
        function World_Pos(x,y,z) return {x=x,y=y,z=z} end
        foundation=building(501,'vn_building_resource_farm2_chi',12)
        foundation.health=270;foundation.maximum=450;foundation.z=24
        creates=0;destroyed={}
        function Entity_CreateFacing(bp,owner,pos,toward,snap)
            creates=creates+1
            if failCreate then return nil end
            replacement={id=900+creates,bp=bp,owner=owner,x=pos.x,z=pos.z,health=450,maximum=450,building=true,incomplete=true,food=240,toward=toward}
            registry[replacement.id]=replacement
            return replacement
        end
        function Entity_Spawn(e) e.spawned=true end
        function Entity_ForceConstruct(e) assert(e.spawned and e.building);if not failComplete then e.incomplete=false end end
        function Entity_GetRemainingResourceDepositAmount(e) return emptyFood and 0 or e.food end
        function Entity_Destroy(e) destroyed[e.id]=true;registry[e.id]=nil;e.dead=true end
        """)
        self.runlua((ROOT/'assets/scar/vietnam/paddy_construction.scar').read_text())
    def update(self,t=0):self.runlua(f'now={t};VietnamPaddyConstruction_Update(PLAYERS[1],entities)')
    def test_native_factory_completion_commits_once_and_preserves_damage_transform_owner(self):
        self.update();self.assertIsNone(self.g.destroyed[501]);self.update(.25);self.update(.5)
        self.assertEqual(self.g.creates,1)
        self.assertTrue(self.g.destroyed[501])
        self.assertEqual(self.g.replacement.health,270)
        self.assertEqual(self.g.replacement.owner,11)
        self.assertEqual(self.g.replacement.x,12);self.assertEqual(self.g.replacement.z,24)
        self.assertEqual(self.g.replacement.toward.x,13)
        self.assertFalse(self.g.replacement.incomplete)
    def test_failed_create_or_completion_or_food_keeps_foundation_and_removes_failed_replacement(self):
        for failure in ['failCreate=true','failComplete=true','emptyFood=true']:
            self.setUp();self.runlua(failure);self.update();self.update(5)
            self.assertIsNone(self.g.destroyed[501])
            self.assertEqual(self.g.foundation.health,270)
            if failure!='failCreate=true':self.assertTrue(self.g.destroyed[901])
    def test_unfinished_dead_foreign_world_foundations_never_spawn_resource(self):
        for condition in ['foundation.incomplete=true','foundation.progress=.99','foundation.dead=true','foundation.owner=22','foundation.world=true','foundation.health=0']:
            self.setUp();self.runlua(condition);self.update();self.assertEqual(self.g.creates,0)
    def test_native_resource_subclass_can_be_ready_without_building_only_apis(self):
        self.runlua("""
        local nativeCreate=Entity_CreateFacing
        function Entity_CreateFacing(...)
            local e=nativeCreate(...);e.building=false;e.incomplete=false;return e
        end
        function Entity_ForceConstruct(e) error('resource is not a building') end
        """)
        self.update();self.update(.25);self.assertTrue(self.g.destroyed[501]);self.assertEqual(self.g.replacement.food,240)
    def test_delayed_native_completion_retains_one_resource_across_ticks(self):
        self.runlua('failComplete=true');self.update()
        self.update(.25);self.update(1);self.update(2)
        self.assertEqual(self.g.creates,1);self.assertIsNone(self.g.destroyed[501]);self.assertIsNone(self.g.destroyed[901])
        self.runlua('replacement.incomplete=false');self.update(2.25);self.update(3)
        self.assertEqual(self.g.creates,1);self.assertTrue(self.g.destroyed[501]);self.assertIsNone(self.g.destroyed[901])
    def test_timeout_preserves_foundation_and_does_not_recreate_each_tick(self):
        self.runlua('failComplete=true');self.update();self.update(5);self.update(5.25);self.update(10)
        self.assertEqual(self.g.creates,1);self.assertIsNone(self.g.destroyed[501]);self.assertTrue(self.g.destroyed[901])
    def test_capture_or_destruction_cleans_pending_without_committing(self):
        for change in ['foundation.owner=22','foundation.dead=true','foundation.health=0']:
            self.setUp();self.update();self.runlua(change);self.update(.25)
            self.assertTrue(self.g.destroyed[901]);self.assertIsNone(self.g.destroyed[501]);self.assertEqual(self.g.creates,1)
    def test_cleanup_destroys_only_pending_resource_and_clears_state(self):
        self.update();self.runlua('VietnamPaddyConstruction_Cleanup();VietnamPaddyConstruction_Cleanup()')
        self.assertTrue(self.g.destroyed[901]);self.assertIsNone(self.g.destroyed[501])
    def test_damage_during_settle_is_preserved_on_commit(self):
        self.update();self.runlua('foundation.health=180');self.update(.25)
        self.assertEqual(self.g.replacement.health,180)
    def test_two_completed_foundations_are_not_skipped_when_destroy_mutates_group(self):
        self.runlua("""
        second=building(502,'vn_building_resource_farm2_chi',36);second.health=450;second.maximum=450
        local oldDestroy=Entity_Destroy
        function Entity_Destroy(e)
            oldDestroy(e)
            for i=#entities,1,-1 do if entities[i]==e then table.remove(entities,i) end end
        end
        """)
        self.update();self.update(.25);self.assertEqual(self.g.creates,2)
        self.assertTrue(self.g.destroyed[501]);self.assertTrue(self.g.destroyed[502])
    def test_actual_v8_used_cross_subclass_blueprint_change_and_new_route_does_not(self):
        with zipfile.ZipFile(SNAP) as z:old=z.read('assets/scar/vietnam/paddy_construction.scar').decode()
        current=(ROOT/'assets/scar/vietnam/paddy_construction.scar').read_text()
        self.assertIn('Entity_ConvertBlueprint(entity,',old)
        self.assertNotIn('Entity_ConvertBlueprint(',current)
        self.assertIn('Entity_CreateFacing(',current)

class PaddyTuningV9(__import__('unittest').TestCase):
    def test_actual_v8_hard_collision_replaced_by_current_native_farm_walkability(self):
        rel='assets/attrib/instances/ebps/vietnam/buildings/economy/rice_paddies/vn_building_resource_farm2_chi.xml'
        with zipfile.ZipFile(SNAP) as z:old=E.fromstring(z.read(rel))
        current=E.parse(ROOT/rel).getroot()
        donor=E.parse(ROOT/'work/vietnam_redesign/runtime_v9_20261023/paddy/6_building_resource_farm.xml').getroot()
        path="list/template_reference[@value='ebpextensions\\impass_ext']"
        for a,b in zip([old,*old.findall('variant')],[current,*current.findall('variant')]):
            a,b=a.find(path),b.find(path)
            self.assertEqual(a.find("group/bool[@name='default_simbox']").get('value'),'True')
            self.assertEqual(b.find("group/bool[@name='default_simbox']").get('value'),donor.find(path+"/group/bool[@name='default_simbox']").get('value'))
            self.assertGreater(len(a.find("list[@name='block_path']")),0)
            self.assertEqual(len(b.find("list[@name='block_path']")),0)
            self.assertEqual(a.attrib,b.attrib)
    def test_native_supervise_distance_comparison_and_unique_target_radius(self):
        p=ROOT/'assets/attrib/instances/abilities/vietnam/vn_buffalo_work_paddy_vit.xml'
        donor=E.parse(ROOT/'work/vietnam_redesign/runtime_v9_20261023/paddy/official_supervise_building_target_chi.xml').getroot()
        current=E.parse(p).getroot()
        self.assertEqual(current.find("group/float[@name='range']").get('value'),donor.find("group/float[@name='range']").get('value'))
        self.assertEqual(current.find("group/bool[@name='use_simbox_to_simbox_range']").get('value'),'False')
        self.assertIn('local radiusSquared = 25',(ROOT/WOOD).read_text())


class PaddyBuildStartV9(PaddyWoodFixture):
    def setUp(self):
        super().setUp()
        self.runlua("""
        SCMD_BuildStructure=12
        function Squad_IsConstructing(s) return s.constructing==true end
        function Squad_IsMoving(s) return s.moving==true end
        function Cmd_Stop() error('observer must not stop builder') end
        function Cmd_Move() error('observer must not move builder') end
        function LocalCommand_SquadEntity() error('observer must not retry build') end
        function LocalCommand_Squad() error('observer must not issue commands') end
        """)
    def build(self):self.tick(0);self.runlua('nativeCommand(buffalo,SCMD_BuildStructure)')
    def test_issued_then_native_construction_logs_without_changing_order_or_income(self):
        self.build();self.runlua('buffalo.busy=true;buffalo.constructing=true')
        self.tick(.25);self.tick(.5)
        self.assertTrue(self.has_log('VIETNAM_V9_BUFFALO_BUILD_ISSUED'))
        self.assertTrue(self.has_log('constructing=true'))
        self.assertTrue(self.g.buffalo.busy);self.assertEqual(self.g.bank[11],0)
        self.assertEqual(sum('BUILD_STATE' in self.g.logs[i] for i in range(1,len(self.g.logs)+1)),1)
    def test_dropped_or_pending_build_is_reported_once_without_retries(self):
        for busy,when in [(False,1),(True,10)]:
            self.setUp();self.build();self.g.buffalo.busy=busy
            self.tick(.25);self.assertFalse(self.has_log('BUILD_STATE'))
            self.tick(when);self.tick(when+1)
            self.assertTrue(self.has_log('constructing=false'))
            self.assertEqual(sum('BUILD_STATE' in self.g.logs[i] for i in range(1,len(self.g.logs)+1)),1)
            self.assertEqual(self.g.buffalo.busy,busy)
    def test_new_command_cancels_build_observation_without_stopping_unit(self):
        self.build();self.runlua('order(buffalo);buffalo.busy=true');self.tick(10)
        self.assertFalse(self.has_log('BUILD_STATE'));self.assertTrue(self.g.buffalo.busy)

    def test_repeated_rightclick_build_orders_are_observed_without_automated_reissue(self):
        self.build();self.tick(.25);self.runlua('nativeCommand(buffalo,SCMD_BuildStructure)')
        self.tick(.5);self.runlua('nativeCommand(buffalo,SCMD_BuildStructure);buffalo.busy=true;buffalo.constructing=true')
        self.tick(.75);self.tick(1)
        logs=[self.g.logs[i] for i in range(1,len(self.g.logs)+1)]
        self.assertEqual(sum('BUILD_ISSUED' in x for x in logs),3)
        self.assertEqual(sum('BUILD_STATE' in x for x in logs),1)
        self.assertTrue(any('elapsed=0.25' in x and 'constructing=true' in x for x in logs))
        self.assertTrue(self.g.buffalo.busy);self.assertEqual(self.g.bank[11],0)

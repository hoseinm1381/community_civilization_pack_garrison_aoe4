"""Explicit worker assignments: Lua mocks, not native acceptance."""
from test_runtime_repairs import RuntimeFixture,ROOT,PREFIX

class PaddyWoodFixture(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua(r''' 
        bank={[11]=0,[22]=0};RT_Wood=1;events={};commands={};warnings={}
        GE_AbilityExecuted=8;GE_SquadCommandIssued=9;SCMD_Ability=10;SCMD_Move=11
        function UIWarning_Show(message) warnings[#warnings+1]=message end
        function Player_GetID(p) return type(p)=='table' and p.playerID or p end
        function Player_OwnsEntity(p,e) return not World_OwnsEntity(e) and Player_GetID(p)==Player_GetID(Entity_GetPlayerOwner(e)) end
        function Player_AddResource(p,r,n) bank[p]=bank[p]+n end
        function BP_GetSquadBlueprint(n) return n end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_GetPlayerOwner(s) return s.owner end
        function Entity_GetPlayerOwner(e) return e.owner end
        function World_OwnsEntity(e) return e.world==true end
        function Squad_IsValid(id) for _,s in ipairs(squads) do if s.id==id then return true end end;return false end
        function Squad_IsInHoldEntity(s) return s.held==true end
        function Squad_IsInHoldSquad(s) return false end
        function Squad_IsIdle(s) return not s.busy end
        function Squad_IsDoingAbility(s,bp) return s.doingWork==true end
        function Squad_HasActiveCommand(s) return s.busy==true end
        function Squad_HasAcceptedCommands(s) return s.queued==true end
        function Squad_GetPosition(s) return {x=s.x or 0,z=0} end
        function SGroup_CountSpawned(g) return #g end
        function SGroup_GetSpawnedSquadAt(g,i) return g[i] end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Rule_AddEntityEvent(f,e,k,d) assert(k==8);assert(events[e.id]==nil);events[e.id]={f=f,d=d} end
        function Rule_RemoveEntityEvent(f,e) events[e.id]=nil end
        function Rule_AddSquadEvent(f,s,k,d) assert(k==9);commands[s.id]={f=f,d=d} end
        function Rule_RemoveSquadEvent(f,s) commands[s.id]=nil end
        function addBuffalo(id)
            local e=building(id+1000,'buffalo',0)
            local s={id=id,owner=11,entity=e,bp='a743d7d1d7534cf78817e29d8ded7366:vn_unit_water_buffalo_vit'}
            squads[#squads+1]=s;return s
        end
        function cast(s,leave)
            local v=events[s.entity.id]
            if v then v.f({ability='a743d7d1d7534cf78817e29d8ded7366:vn_buffalo_'..(leave and 'leave' or 'work')..'_paddy_vit'},v.d) end
        end
        function nativeCommand(s,kind)
            local v=commands[s.id]
            if v then v.f({command=kind,squad=s},v.d) end
        end
        function assign(s,leave)
            nativeCommand(s,SCMD_Ability);cast(s,leave)
        end
        function order(s) nativeCommand(s,SCMD_Move) end
        paddy=building(501,'vn_building_resource_farm_chi',0);buffalo=addBuffalo(100)
        ''')
        self.runlua((ROOT/'assets/scar/vietnam/paddy_wood.scar').read_text())

    def tick(self,t,player=1):self.runlua(f'now={t};VietnamPaddyWood_Update(PLAYERS[{player}],entities,now)')

    def start(self):
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25);self.tick(.5)


class PaddyWoodTests(PaddyWoodFixture):
    def test_explicit_assignment_idle_income_and_duplicate_tick(self):
        self.tick(0);self.tick(.25);self.assertEqual(self.g.bank[11],0)
        self.runlua('assign(buffalo)');self.tick(.5);self.tick(.75);self.tick(.75)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_new_orders_unassign_leaving_death_capture_stop_without_backfill(self):
        for mutation in ['order(buffalo)','assign(buffalo,true)','buffalo.entity.x=11','buffalo.dead=true','buffalo.owner=22','paddy.owner=22','paddy.incomplete=true','paddy.dead=true']:
            with self.subTest(mutation=mutation):
                self.setUp();self.start();earned=self.g.bank[11]
                self.runlua(mutation);self.tick(.75);self.tick(1)
                self.assertAlmostEqual(self.g.bank[11],earned)

    def test_native_execution_chooses_only_unique_completed_owned_paddy(self):
        self.tick(0);self.runlua('cast(buffalo)')
        self.assertEqual(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'),501)
        self.assertIsNone(self.g.network['VietnamPaddyWood_NetAssign'])

    def test_adjacent_paddies_within_five_metres_reject_ambiguity(self):
        self.runlua("other=building(502,'vn_building_resource_farm_chi',.8)")
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25);self.tick(.5)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))
        self.assertEqual(self.g.bank[11],0);self.assertEqual(len(self.g.warnings),1)

    def test_nearby_foreign_and_unfinished_paddy_do_not_create_ambiguity(self):
        self.runlua("foreign=building(502,'vn_building_resource_farm_chi',0,22);foundation=building(503,'vn_building_resource_farm_chi',0);foundation.incomplete=true")
        self.start();self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_actual_caster_centre_not_squad_position_is_used(self):
        self.runlua('buffalo.x=50;buffalo.entity.x=1');self.start()
        self.assertAlmostEqual(self.g.bank[11],.375*.25)
        self.runlua('buffalo.entity.x=5.00001');self.tick(.75)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_one_buffalo_per_paddy_and_separate_paddies_can_work(self):
        self.runlua("other=building(502,'vn_building_resource_farm_chi',12);second=addBuffalo(101)")
        self.tick(0);self.runlua('assign(buffalo);assign(second)')
        self.assertEqual(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'),501)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[101].paddy'))
        self.runlua('second.entity.x=12;assign(second)');self.tick(.25);self.tick(.5)
        self.assertAlmostEqual(self.g.bank[11],2*.375*.25)

    def test_command_and_execution_order_both_admit_but_later_move_cancels(self):
        for sequence in ['nativeCommand(buffalo,SCMD_Ability);cast(buffalo)',
                         'cast(buffalo);nativeCommand(buffalo,SCMD_Ability)']:
            with self.subTest(sequence=sequence):
                self.setUp();self.tick(0);self.runlua(sequence);self.tick(.25);self.tick(.5)
                earned=self.g.bank[11];self.assertAlmostEqual(earned,.375*.25)
                self.runlua('order(buffalo)');self.tick(.75);self.tick(1)
                self.assertAlmostEqual(self.g.bank[11],earned)

    def test_execution_before_own_command_after_previous_cancellation_admits(self):
        self.tick(0);self.runlua('order(buffalo);now=.25;cast(buffalo);nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.5);self.tick(.75)
        self.assertEqual(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'),501)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_stale_execution_without_fresh_same_tick_command_never_admits(self):
        self.tick(0);self.runlua('order(buffalo);cast(buffalo)');self.tick(.25)
        self.runlua('nativeCommand(buffalo,SCMD_Ability)');self.tick(.5);self.tick(.75)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))
        self.assertEqual(self.g.bank[11],0)

    def test_intervening_move_discards_buffered_execution(self):
        self.tick(0);self.runlua('order(buffalo);cast(buffalo);order(buffalo);nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.25);self.tick(.5)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))
        self.assertEqual(self.g.bank[11],0)

    def test_pending_native_approach_earns_nothing_until_execution_at_five_metres(self):
        self.tick(0);self.runlua('buffalo.entity.x=20;buffalo.busy=true;buffalo.doingWork=true;nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.25);self.tick(.5);self.assertEqual(self.g.bank[11],0)
        self.runlua('now=2;buffalo.entity.x=.9;cast(buffalo);buffalo.busy=false;buffalo.doingWork=false')
        self.tick(2);self.tick(2.25)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_failed_native_approach_and_timeout_notify_owner_once_and_reject_late_execution(self):
        for timeout in [False,True]:
            with self.subTest(timeout=timeout):
                self.setUp();self.tick(0)
                self.runlua('buffalo.entity.x=20;buffalo.busy=true;buffalo.doingWork=true;nativeCommand(buffalo,SCMD_Ability)')
                if timeout:
                    self.tick(59.75);self.assertEqual(len(self.g.warnings),0);self.tick(60)
                else:
                    self.tick(.25);self.runlua('buffalo.busy=false;buffalo.doingWork=false');self.tick(.5);self.assertEqual(len(self.g.warnings),0);self.tick(1)
                self.assertEqual(len(self.g.warnings),1)
                self.runlua('buffalo.entity.x=0;buffalo.busy=false;cast(buffalo)')
                self.tick(60.25);self.tick(60.5)
                self.assertEqual(self.g.bank[11],0);self.assertEqual(len(self.g.warnings),1)

    def test_new_command_cancels_pending_and_late_execution_cannot_admit(self):
        self.tick(0);self.runlua('buffalo.busy=true;nativeCommand(buffalo,SCMD_Ability);order(buffalo);cast(buffalo);buffalo.busy=false')
        self.tick(.25);self.tick(.5)
        self.assertEqual(self.g.bank[11],0)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].pending'))
        self.runlua('assign(buffalo)');self.tick(.75);self.tick(1)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_unrelated_native_ability_never_produces_supervision_failure(self):
        self.tick(0);self.runlua('buffalo.busy=true;nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.25);self.tick(60);self.tick(61)
        self.assertEqual(len(self.g.warnings),0);self.assertEqual(self.g.bank[11],0)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].pending'))

    def test_another_ability_after_own_command_cancels_same_tick_assignment(self):
        self.tick(0);self.runlua('cast(buffalo);nativeCommand(buffalo,SCMD_Ability);nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.25);self.tick(.5)
        self.assertEqual(self.g.bank[11],0)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))

    def test_confirmed_pending_capture_or_death_never_grants_income(self):
        for mutation in ['buffalo.owner=22','buffalo.dead=true','buffalo.entity.dead=true']:
            with self.subTest(mutation=mutation):
                self.setUp();self.tick(0)
                self.runlua('buffalo.busy=true;buffalo.doingWork=true;nativeCommand(buffalo,SCMD_Ability)')
                self.tick(.25);self.runlua(mutation);self.tick(60);self.tick(60.25)
                self.assertEqual(self.g.bank[11],0)
                self.assertEqual(len(self.g.warnings),0)

    def test_failure_warning_is_local_to_owner(self):
        self.tick(0);self.runlua('localPlayer=22;buffalo.entity.x=20;assign(buffalo)')
        self.assertEqual(len(self.g.warnings),0)
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))

    def test_busy_and_long_gap_earn_nothing(self):
        self.start();earned=self.g.bank[11]
        self.runlua('buffalo.busy=true');self.tick(.75)
        self.runlua('buffalo.busy=false');self.tick(100);self.tick(99)
        self.assertAlmostEqual(self.g.bank[11],earned)

    def test_transfer_new_owner_first_has_single_watch_and_no_assignment(self):
        self.start();self.runlua('buffalo.owner=22;buffalo.entity.owner=22;paddy.owner=22')
        self.tick(.75,2);self.tick(.75,1)
        self.assertIsNotNone(self.g.events[1100])
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[2].watches[100].paddy'))
        self.runlua('assign(buffalo)');self.tick(1,2);self.tick(1.25,2)
        self.assertAlmostEqual(self.g.bank[22],.375*.25)

    def test_cleanup_removes_callbacks(self):
        self.start();self.runlua('VietnamPaddyWood_Cleanup();VietnamPaddyWood_Cleanup()')
        self.assertIsNone(self.g.events[1100]);self.assertIsNone(self.g.commands[100])
        self.assertIsNone(self.g.network['VietnamPaddyWood_NetAssign'])

    def test_wood_tech_and_champa_no_retroactive_bonus_or_double_stage(self):
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25)
        for age in [2,3,4]:
            for key in [r'upgrade\races\common\research\economy\upgrade_econ_resource_wood_harvest_rate_'+str(age),r'upgrade\races\japanese\research\economy\upgrade_econ_resource_wood_harvest_rate_'+str(age)+'_kura_jpn']:
                self.runlua('upgrades["'+key.replace('\\','\\\\')+'"]=true')
        self.runlua('upgrades["'+PREFIX+'vn_upgrade_champa_rice_vit"]=true')
        self.tick(.5);self.assertAlmostEqual(self.g.bank[11],.375*.25)
        self.tick(.75);self.assertAlmostEqual(self.g.bank[11],.375*.25+.375*1.45*1.1*.25)

    def test_non_paddy_entities_never_query_construction(self):
        self.runlua("function Entity_IsUnderConstruction(e) assert(e.id==501,'only deposits');return e.incomplete==true end")
        self.start();self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_target_filters_unrelated_and_world_entities_before_owner_query(self):
        self.runlua("""
        unrelated=building(700,'tree',0);worldPaddy=building(701,'vn_building_resource_farm_chi',0);worldPaddy.world=true
        function Entity_GetPlayerOwner(e) assert(e.id==501,'only owned private Paddy');return e.owner end
        assert(not VietnamPaddyWood_IsPaddyTarget(nil,11))
        assert(not VietnamPaddyWood_IsPaddyTarget(unrelated,11))
        assert(not VietnamPaddyWood_IsPaddyTarget(worldPaddy,11))
        assert(VietnamPaddyWood_IsPaddyTarget(paddy,11))
        """)

    def test_native_execution_outside_five_metres_is_rejected(self):
        self.runlua('buffalo.entity.x=5.001');self.start()
        self.assertEqual(self.g.bank[11],0)

    def test_old_worker_elephant_is_not_registered_or_paid(self):
        self.runlua("buffalo.bp='"+PREFIX+"vn_unit_war_elephant_1_vit'")
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25);self.tick(.5)
        self.assertIsNone(self.g.events[1100]);self.assertEqual(self.g.bank[11],0)

    def test_foundation_is_never_a_supervision_target_even_when_complete(self):
        self.runlua("paddy.bp='"+PREFIX+"vn_building_resource_farm2_chi'")
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25);self.tick(.5)
        self.assertFalse(self.g.VietnamPaddyWood_IsPaddyTarget(self.g.paddy,11))
        self.assertEqual(self.g.bank[11],0)

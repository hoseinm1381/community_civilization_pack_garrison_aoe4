"""Actual controller under deferred native spawn/position mutations; not engine proof."""
import zipfile
import unittest
from test_runtime_repairs import ROOT, PREFIX
from tunnel_fixture_v6 import TunnelNativeFixture
import test_tunnel_v7 as v7


class TunnelV9Tests(TunnelNativeFixture):
    cast = v7.TunnelV7Tests.cast
    request = v7.TunnelV7Tests.request

    def setUp(self):
        super().setUp()
        self.runlua('''
        ST_ENTITY=1;warnings={};targetReads=0
        function scartype(e) return type(e)=='table' and e.id~=nil and ST_ENTITY or 0 end
        function UIWarning_Show(t) warnings[#warnings+1]=t end
        function Entity_GetStateTreeTargeting_Vector3f(e,kind,key)
            assert(kind=='statetree_commited_target_type' and key=='COMMITTED_ABILITY')
            targetReads=targetReads+1;return e.click
        end
        function Cmd_Stop(g)
            stopCount=stopCount+1
            for _,squad in ipairs(g) do squad.entity.click=nil end
        end
        local oldAdd=addTraveler
        function addTraveler(id,x) local squad=oldAdd(id,x);squad.entity.squad=squad;return squad end
        s.entity.squad=s
        VietnamTunnelBuildings={tunnel_fixture={hx=4,hz=4,axis=true}}
        ''')

        self.runlua('''
        spawnAttempts=0;positionChanges=0;teleportBlocked=false;pendingEngine={}
        function Player_GetID(p) return type(p)=='table' and p.id or p end
        function Squad_IsOfType(s,t) return s.types and s.types[t]==true end
        function Squad_Spawn(s,p,k)
            assert(s.despawned and k=='');spawnAttempts=spawnAttempts+1
            pendingEngine[#pendingEngine+1]=function() s.despawned=false end
        end
        function Squad_TryFindClosestFreePosition(s,p) assert(not s.despawned);return p end
        function Squad_SetPosition(s,p,toward)
            assert(not s.despawned);positionChanges=positionChanges+1
            pendingEngine[#pendingEngine+1]=function()
                if not teleportBlocked and not s.despawned then s.pos=p;arrivals=arrivals+1 end
            end
        end
        function flushEngine()
            local q=pendingEngine;pendingEngine={};for _,f in ipairs(q) do f() end
        end
        ''')

    def step(self, t):
        self.runlua('flushEngine()')
        v7.TunnelV7Tests.step(self,t)

    def complete(self):
        for i in range(max(25,int(self.g.now*4)+1),65): self.step(i/4)

    def test_deferred_spawn_and_position_preserve_original_and_finish(self):
        self.request();self.step(3.1);self.step(6.1);self.complete()
        self.assertFalse(self.g.s.despawned)
        self.assertGreater(self.g.s.pos.x,32)
        self.assertEqual(self.g.s.health,45)
        self.assertEqual(self.g.s.id,2001)
        self.assertEqual(self.g.departures,1)
        self.assertEqual(self.g.spawnAttempts,1)
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.assertTrue(self.has_log('boundary=arrival'))

    def test_permanent_position_failure_leaves_visible_original_and_releases(self):
        self.request();self.step(3.1);self.runlua('teleportBlocked=true')
        self.step(6.1);self.complete()
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.departures,1)
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.assertFalse(self.has_log('result=destination'))
        self.assertLessEqual(self.g.positionChanges,2)

    def test_blocked_destination_solver_returns_origin_without_rehiding(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) assert(not s.despawned);return s.pos end')
        self.step(6.1);self.complete()
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.departures,1)
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.assertFalse(self.has_log('result=destination'))

    def test_both_no_than_blueprints_excluded_even_without_entity_tags(self):
        for name in ('vn_unit_no_than_vit','vn_unit_no_than_vit_reinforced'):
            self.runlua(f"s.bp='{PREFIX}{name}'")
            self.cast()
        self.assertEqual(self.g.targetReads,0)

    def test_squad_siege_tag_excludes_when_first_entity_is_crew(self):
        self.runlua('s.types={siege=true}')
        self.cast();self.assertEqual(self.g.targetReads,0)

    def test_unknown_squad_without_ability_extension_never_receives_add(self):
        self.runlua('''
        s.bp='unknown_animal';s.ability=false;addAttempts=0
        function Squad_AddAbility(s,a) addAttempts=addAttempts+1;error('no ability extension') end
        VietnamTunnels_Update(PLAYERS[1],{})
        ''')
        self.assertEqual(self.g.addAttempts,0)

    def test_known_capable_blueprint_receives_ability(self):
        self.runlua((ROOT/'assets/scar/vietnam/tunnel_ability_squads.scar').read_text())
        self.runlua('''
        s.bp='unit_spearman_1_chi';s.ability=false;addAttempts=0
        function Squad_AddAbility(s,a) addAttempts=addAttempts+1;s.ability=true end
        VietnamTunnels_Update(PLAYERS[1],{})
        ''')
        self.assertEqual(self.g.addAttempts,1)

    def test_blueprint_name_collision_does_not_authorize_unknown_archive(self):
        self.runlua((ROOT/'assets/scar/vietnam/tunnel_ability_squads.scar').read_text())
        self.runlua('''
        s.bp='foreign:unit_spearman_1_chi';s.ability=false;addAttempts=0
        function BP_GetName(bp) return 'unit_spearman_1_chi' end
        function Squad_AddAbility(s,a) addAttempts=addAttempts+1;error('wrong archive') end
        VietnamTunnels_Update(PLAYERS[1],{})
        ''')
        self.assertEqual(self.g.addAttempts,0)

    def test_cleanup_drains_async_recovery_without_losing_original(self):
        self.request();self.step(3.1)
        self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertIsNotNone(self.g.VietnamTunnelsRecovery.records[2001])
        for i in range(14,32):
            self.runlua(f'flushEngine();now={i/4};tick={i+200};VietnamTunnels_RecoveryTick()')
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.health,45)
        self.assertIsNone(self.g.VietnamTunnelsRecovery.records[2001])
        self.assertFalse(self.g.VietnamTunnelsRecovery.active)
        self.assertEqual(self.g.tempGroups,0)

    def test_conversion_during_placement_returns_original_to_origin(self):
        self.request();self.step(3.1);self.step(6.1);self.step(6.25);self.step(6.5)
        self.runlua('s.owner=22')
        self.complete()
        self.assertEqual(self.g.s.owner,22)
        self.assertLess(self.g.s.pos.x,0)
        self.assertFalse(self.g.s.despawned)
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_exit_death_during_placement_returns_original_to_origin(self):
        self.request();self.step(3.1);self.step(6.1);self.step(6.25);self.step(6.5)
        self.runlua('registry[3].dead=true;VietnamTunnels_OnEntityKilled({victim=registry[3]})')
        self.complete()
        self.assertFalse(self.g.s.despawned)
        self.assertLess(self.g.s.pos.x,0)
        self.assertFalse(self.has_log('result=destination'))

    def test_multi_caster_deferred_landings_preserve_health_and_groups(self):
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        self.request(','.join(str(2000+i) for i in range(1,36)))
        self.step(3.1);self.step(6.1);self.complete()
        self.assertEqual(self.g.spawnAttempts,35)
        self.assertEqual(self.g.departures,35)
        self.assertEqual(self.g.tempGroups,0)
        self.runlua('for _,squad in ipairs(squads) do assert(not squad.despawned and squad.health==45 and squad.pos.x>32) end')

    def test_native_spawn_refusal_retains_reference_and_emits_actionable_diagnostic(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_Spawn(s,p,k) spawnAttempts=spawnAttempts+1 end')
        self.step(6.1);self.complete()
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.assertTrue(self.has_log('boundary=spawn-recovery-required'))
        self.assertLessEqual(self.g.spawnAttempts,11)

    def test_distinct_owner_wrappers_keep_owned_targets_and_owner_warning(self):
        self.runlua('''
        function Entity_GetPlayerOwner(e) return {id=e.owner or 11} end
        function Squad_GetPlayerOwner(s) return {id=s.owner} end
        function Core_GetPlayersTableEntry(owner)
            for _,p in ipairs(PLAYERS) do if Player_GetID(p.id)==Player_GetID(owner) then return p end end
        end
        function Player_IsAlive(owner) return Player_GetID(owner)~=99 end
        function Game_GetLocalPlayer() return {id=11} end
        ''')
        self.request();self.assertEqual(self.g.moveCount,1)
        self.step(3.1);self.step(6.1);self.complete()
        self.assertGreater(self.g.s.pos.x,32)
        self.cast(x=9999);self.assertGreater(len(self.g.warnings),0)

    def test_distinct_owner_wrappers_stop_cancelled_approach(self):
        self.request();before=self.g.stopCount
        self.runlua('function Squad_GetPlayerOwner(s) return {id=s.owner} end')
        self.step(16)
        self.assertEqual(self.g.stopCount,before+1)

    def test_minimum_travel_and_unloading_before_staged_landing(self):
        self.request(dest=2);self.step(3.1);self.step(4.1)
        self.assertTrue(self.g.s.despawned);self.assertEqual(self.g.spawnAttempts,0)
        self.step(5.1);self.assertEqual(self.g.spawnAttempts,1)
        self.complete();self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.pos.x,24)

    def test_fast_repair_after_destination_death_still_returns_original(self):
        self.request();self.step(3.1)
        self.runlua('VietnamTunnels_OnEntityKilled({victim=registry[3]})')
        self.step(6.1);self.complete()
        self.assertFalse(self.g.s.despawned);self.assertLess(self.g.s.pos.x,0)

    def test_relay_loss_after_departure_keeps_committed_exit(self):
        self.request();self.step(3.1)
        self.runlua('VietnamTunnelsState.players[1].graph.byID[1]=nil;n3.component=nil')
        self.step(6.1);self.complete()
        self.assertEqual(self.g.s.pos.x,48)

    def test_captured_exit_returns_original_and_keeps_cast_cooldown(self):
        self.request();self.step(3.1);self.runlua('registry[3].owner=22')
        self.step(6.1);self.complete()
        self.assertFalse(self.g.s.despawned);self.assertLess(self.g.s.pos.x,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)

    def test_dynamic_ability_conversion_cleanup_uses_proven_blueprint(self):
        self.runlua((ROOT/'assets/scar/vietnam/tunnel_ability_squads.scar').read_text())
        self.runlua("s.bp='unit_spearman_1_chi';VietnamTunnelBuildings={};s.ability=false;VietnamTunnels_Update(PLAYERS[1],entities)")
        self.assertTrue(self.g.s.ability)
        self.runlua('s.owner=22;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertFalse(self.g.s.ability)
        self.runlua('s.owner=11;VietnamTunnels_Update(PLAYERS[1],entities);VietnamTunnels_Cleanup()')
        self.assertFalse(self.g.s.ability)

    def test_arrival_does_not_extend_cast_cooldown_and_later_cast_works(self):
        self.request();self.step(3.1);self.step(6.1);self.complete()
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)
        self.cast();self.assertEqual(self.g.moveCount,1)
        self.step(30);self.cast(x=0);self.step(30.25)
        self.assertEqual(self.g.moveCount,2)

    def test_frozen_v8_adds_ability_to_an_untyped_squad_without_capability(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v9_20261023/before.zip') as z:
            self.runlua(z.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig'))
        self.runlua("VietnamTunnels_Start({[1]='vietnam'});s.bp='unknown_animal';s.ability=false")
        self.runlua("function Squad_AddAbility(s,a) error('no ability extension') end")
        with self.assertRaisesRegex(Exception,'no ability extension'):
            self.runlua('VietnamTunnels_Update(PLAYERS[1],{})')

    def test_frozen_v8_reproduces_endless_rehide_with_deferred_placement(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v9_20261023/before.zip') as z:
            self.runlua(z.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig'))
        self.runlua("VietnamTunnels_Start({[1]='vietnam'});VietnamTunnelsState.players[1].graph=VietnamTunnelCore.Build({n1,n2,n3})")
        # Match the observed log: Spawn has completed, SetPosition has not.
        self.runlua("function Squad_Spawn(s,p,k) assert(s.despawned);s.despawned=false;spawnAttempts=spawnAttempts+1 end")
        self.request();self.step(3.1);self.step(6.1);self.complete()
        self.assertTrue(self.g.s.despawned)
        self.assertGreater(self.g.departures,30)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.assertFalse(self.has_log('boundary=arrival'))


for name in (
    'test_native_click_captured_before_stop_and_no_second_move',
    'test_later_tick_or_different_target_cannot_join_batch',
    'test_no_target_rejects_without_sampling_mouse_or_reusing_move',
    'test_group_formation_offset_inside_entrance_loads',
    'test_outside_entrance_never_loads_and_timeout_retains_cast_cooldown',
    'test_pending_new_order_cancels_without_overwriting_it',
    'test_admission_waits_until_after_native_dispatch_tick',
    'test_nearest_foundation_or_disconnected_exit_is_not_skipped',
    'test_capture_or_death_before_admission_never_moves_squad',
    'test_cleanup_removes_pending_observer_and_events',
    'test_invalid_target_warning_is_owner_only',
    'test_ineligible_units_do_not_join_native_batch',
    'test_valid_zero_coordinate_target_is_not_treated_as_missing',
    'test_final_source_has_no_mouse_modal_or_paddy_dispatcher',
    'test_equal_footprint_distance_uses_lower_entity_id',
    'test_unknown_footprint_is_visible_failure_not_guessed_distance',
    'test_blocked_entrance_cannot_issue_nil_move',
    'test_loading_requires_three_continuous_seconds_near_entrance',
    'test_destination_destroyed_before_loading_cancels',
    'test_command_during_approach_keeps_players_new_order',
    'test_marker_visibility_preserves_allies_and_ordinary_enemy_vision',
    'test_graph_adapter_rejects_foundations_and_ruins_until_full_repair',
):
    setattr(TunnelV9Tests,name,getattr(v7.TunnelV7Tests,name))

if __name__=='__main__': unittest.main()

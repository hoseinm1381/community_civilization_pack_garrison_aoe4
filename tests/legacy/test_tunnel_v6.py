"""Native-event tunnel contract; mocks do not establish native dispatch ordering."""
import unittest
import zipfile
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX
from tunnel_fixture_v6 import TunnelNativeFixture


class TunnelV6Tests(TunnelNativeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        ST_ENTITY=1;CMD_Move=4;warnings={};destinationReads=0;activeMove=false
        function scartype(e) return type(e)=='table' and e.id~=nil and ST_ENTITY or 0 end
        function UIWarning_Show(t) warnings[#warnings+1]=t end
        function Entity_ActiveCommandIs(e,c) assert(c==CMD_Move);return e.squad.activeMove==true end
        function Squad_HasDestination(s) return s.destination~=nil and tick>(s.destinationTick or -1) end
        function Squad_GetDestination(s)
            assert(Squad_HasDestination(s),'unsafe destination read')
            destinationReads=destinationReads+1;return s.destination
        end
        function Cmd_Stop(g)
            stopCount=stopCount+1
            for _,squad in ipairs(g) do squad.activeMove=false;squad.destination=nil end
        end
        local oldAdd=addTraveler
        function addTraveler(id,x) local squad=oldAdd(id,x);squad.entity.squad=squad;return squad end
        s.entity.squad=s
        VietnamTunnelBuildings={tunnel_fixture={hx=4,hz=4,axis=true}}
        ''')

    def arm(self, ids='2001'):
        self.runlua(f'''for _,squad in ipairs(squads) do
            if string.find(',{ids},',','..squad.id..',',1,true) then
                VietnamTunnels_OnAbilityExecuted({{ability='{PREFIX}vn_vietnam_unit_mov_vit',executer=squad.entity}})
            end
        end''')

    def move(self, ids='2001', x=48, z=0):
        self.runlua(f'''for _,squad in ipairs(squads) do
            if string.find(',{ids},',','..squad.id..',',1,true) then
                squad.activeMove=true;squad.destination={{x={x},y=0,z={z}}};squad.destinationTick=tick
                if callbacks[squad.id] then callbacks[squad.id]({{squad=squad,command=4}}) end
            end
        end''')

    def step(self,t):
        self.runlua(f'now={t};tick=101+math.floor(now*8);VietnamTunnels_Step(now,tick)')

    def request(self,ids='2001',dest=3):
        self.arm(ids);self.move(ids,24*(dest-1));self.step(.1)

    def test_native_ability_arms_without_selection_or_mouse(self):
        self.runlua('selected={};s.destination={x=999,z=0};s.activeMove=true')
        self.arm();self.step(.5)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].armed[2001])
        self.assertEqual(self.g.destinationReads,0)
        self.assertEqual(self.g.moveCount,0)
        self.assertIsNone(self.g.s.destination)

    def test_destination_is_read_only_on_a_later_tick(self):
        self.arm();self.move()
        self.runlua('VietnamTunnels_Step(now,tick)')
        self.assertEqual(self.g.destinationReads,0)
        self.step(.1)
        self.assertEqual(self.g.destinationReads,1)
        self.assertEqual(self.g.moveCount,1)

    def test_delayed_native_destination_waits_then_admits(self):
        self.arm();self.move();self.runlua('s.destinationTick=tick+2')
        self.step(.1);self.assertEqual(self.g.destinationReads,0)
        self.step(.5);self.assertEqual(self.g.moveCount,1)

    def test_missing_destination_expires_without_any_unsafe_read(self):
        self.arm();self.move();self.runlua('s.destination=nil')
        self.step(.5);self.step(10)
        self.assertEqual(self.g.destinationReads,0)
        self.assertIsNone(self.g.callbacks[2001])
        self.assertTrue(any('move-destination-unavailable' in s for s in self.g.logs.values()))

    def test_unarmed_move_or_existing_order_never_selects_a_destination(self):
        self.move();self.step(.5)
        self.assertEqual(self.g.destinationReads,0)
        self.arm();self.step(1)
        self.assertEqual(self.g.destinationReads,0)

    def test_arm_expires_at_ten_seconds_and_cleans_observer(self):
        self.arm();self.step(10)
        self.assertIsNone(self.g.callbacks[2001])
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].armed[2001])
        self.assertTrue(len(self.g.warnings)>0)

    def test_actual_frozen_v5_fails_the_native_activation_contract(self):
        frozen=ROOT/'work/vietnam_redesign/runtime_v6_20261023/before.zip'
        with zipfile.ZipFile(frozen) as archive:
            before=archive.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig')
        self.assertIn('Misc_IsMouseOverEntity',before)
        self.runlua('VietnamTunnels_OnAbilityExecuted=nil')
        self.runlua(before)
        with self.assertRaisesRegex(Exception,'VietnamTunnels_OnAbilityExecuted'):
            self.arm()

    def test_final_source_has_no_mouse_modal_or_paddy_dispatcher(self):
        source=(ROOT/'assets/scar/vietnam/tunnels.scar').read_text()
        for retired in ('Misc_GetMouse','Misc_IsMouseOverEntity','UI_SetModal','UI_ClearModal',
                        'AbilityPhase','NetRequest','Network_CallEvent','vn_buffalo_work_paddy'):
            self.assertNotIn(retired,source)

    def test_newer_command_cancels_capture_without_overwriting_order(self):
        self.arm();self.move();self.runlua('callbacks[2001]({squad=s,command=6});s.pos.x=-100')
        self.step(.25)
        self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.stopCount,1) # only the arm stop
        self.assertEqual(self.g.s.pos.x,-100)

    def test_non_move_command_cannot_consume_stale_destination(self):
        self.arm();self.runlua('s.activeMove=false;s.destination={x=48,z=0};callbacks[2001]({squad=s,command=6})')
        self.step(.25)
        self.assertEqual(self.g.destinationReads,0)
        self.assertEqual(self.g.moveCount,0)

    def test_multiselect_native_callbacks_admit_unlimited_same_tick_batch(self):
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        ids=','.join(str(2000+i) for i in range(1,36))
        self.request(ids)
        self.assertEqual(self.g.moveCount,35)
        self.assertEqual(self.g.tempGroups,35)

    def test_nearest_disconnected_building_rejects_farther_connected(self):
        self.runlua('extra={id=4,x=56,z=0,hx=4,hz=4};building(4,"tunnel_fixture",56);VietnamTunnelsState.players[1].graph.byID[4]=extra')
        self.arm();self.move(x=55);self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertIn('disconnected',self.g.logs[len(self.g.logs)])

    def test_nearest_foundation_is_not_skipped_for_connected_building(self):
        self.runlua('building(4,"tunnel_fixture",56).incomplete=true')
        self.arm();self.move(x=55);self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertTrue(any('foundation' in s for s in self.g.logs.values()))

    def test_nearest_unsupported_building_is_not_skipped(self):
        self.runlua('VietnamTunnelTargetBuildings={unsupported={hx=4,hz=4,axis=true}};building(4,"unsupported",56)')
        self.arm();self.move(x=55);self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertTrue(any('not-in-network' in s for s in self.g.logs.values()))

    def test_official_captured_building_uses_official_footprint_identity(self):
        self.runlua('''
        VietnamTunnelTargetBuildings={stock={native=true,hx=4,hz=4,axis=true}}
        building(4,'stock',56).bp='stock'
        ''')
        self.arm();self.move(x=55);self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertTrue(any('not-in-network' in s for s in self.g.logs.values()))

    def test_destination_distance_limit_is_eight_metres_from_footprint(self):
        self.arm();self.move(x=48,z=12.01);self.step(.1)
        self.assertEqual(self.g.moveCount,0)

    def test_equal_footprint_distance_uses_lower_entity_id(self):
        self.runlua('building(4,"tunnel_fixture",48).incomplete=true')
        self.request();self.assertEqual(self.g.VietnamTunnelsState.players[1].records[2001].destination.id,3)

    def test_warnings_are_owner_only(self):
        self.runlua('localPlayer=22');self.arm();self.step(10)
        self.assertEqual(len(self.g.warnings),0)

    def test_multiselect_destination_delay_does_not_drop_later_ready_squad(self):
        self.runlua('other=addTraveler(2002)')
        self.arm('2001,2002');self.move('2001,2002')
        self.runlua('other.destinationTick=tick+2')
        self.step(.1);self.assertEqual(self.g.moveCount,1)
        self.step(.5);self.assertEqual(self.g.moveCount,2)

    def test_separate_later_move_cannot_join_committed_batch(self):
        self.runlua('other=addTraveler(2002)')
        self.arm('2001,2002');self.move();self.step(.1)
        self.move('2002');self.step(.5)
        self.assertEqual(self.g.moveCount,1)

    def test_rearm_invalidates_old_callback_without_losing_current_observer(self):
        self.arm();self.runlua('staleCallback=callbacks[2001]')
        self.arm();self.runlua('staleCallback({squad=s,command=4})')
        self.step(.1);self.assertEqual(self.g.destinationReads,0)
        self.move();self.step(.5);self.assertEqual(self.g.moveCount,1)

    def test_ineligible_economic_siege_naval_and_buffalo_never_arm(self):
        self.runlua('''
        s.entity.types.villager=true
        a=addTraveler(2002);a.entity.types.siege=true
        b=addTraveler(2003);b.entity.types.naval_unit=true
        c=addTraveler(2004);c.entity.types.trade_cart=true
        d=addTraveler(2005);d.bp='''+repr(PREFIX+'vn_unit_water_buffalo_vit')+'''
        ''')
        self.arm('2001,2002,2003,2004,2005')
        self.assertEqual(len(self.g.VietnamTunnelsState.players[1].armed),0)

    def test_heavy_elephant_is_eligible_without_replacing_its_identity(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_war_elephant_1_vit'")
        self.request();self.assertEqual(self.g.moveCount,1)

    def test_hold_or_conversion_after_arm_removes_observer(self):
        self.arm();self.runlua('s.owner=22');self.step(.1)
        self.assertIsNone(self.g.callbacks[2001])
        self.assertEqual(self.g.destinationReads,0)

    def test_unknown_footprint_is_visible_failure_not_guessed_distance(self):
        self.runlua('building(4,"unknown",56)')
        self.request();self.assertEqual(self.g.moveCount,0)
        self.assertTrue(any('unknown-building-footprint' in s for s in self.g.logs.values()))

    def test_blocked_entrance_cannot_issue_nil_move(self):
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return nil end')
        self.request();self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.tempGroups,0)

    def test_unreachable_entrance_times_out_without_despawn_or_cooldown(self):
        self.runlua('autoArrive=false;s.pos.x=-1000')
        self.request();self.step(15.2)
        self.assertEqual(self.g.departures,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,0)
        self.assertEqual(self.g.tempGroups,0)

    def test_loading_requires_three_continuous_seconds_near_entrance(self):
        self.request();self.step(2)
        self.runlua('s.pos.x=-100');self.step(3)
        self.runlua('s.pos.x=-4');self.step(4);self.step(6.9)
        self.assertEqual(self.g.departures,0)
        self.step(7);self.assertEqual(self.g.departures,1)

    def test_minimum_travel_and_one_second_unloading(self):
        self.request(dest=2);self.step(3.1);self.step(4.1)
        self.assertTrue(self.g.s.despawned)
        self.step(5.1);self.assertFalse(self.g.s.despawned)

    def test_destination_destroyed_before_loading_cancels(self):
        self.request();self.runlua('VietnamTunnels_OnEntityKilled({victim=registry[3]})')
        self.step(3.1);self.assertEqual(self.g.departures,0)

    def test_fast_repair_after_destination_kill_still_returns_original(self):
        self.request();self.step(3.1)
        self.runlua('VietnamTunnels_OnEntityKilled({victim=registry[3]})')
        self.step(6.1);self.assertLess(self.g.s.pos.x,0)

    def test_later_arrivals_do_not_extend_first_successful_cooldown(self):
        self.runlua('other=addTraveler(2002)')
        self.arm('2001,2002');self.move('2001',x=24);self.move('2002',x=48)
        self.step(.1);self.step(3.1);self.step(5.1)
        self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,35.1)
        self.step(6.1);self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,35.1)

    def test_cooldown_blocks_native_reactivation(self):
        self.request();self.step(3.1);self.step(6.1);self.arm()
        self.assertEqual(len(self.g.VietnamTunnelsState.players[1].armed),0)
        self.assertTrue(any('cooldown' in s for s in self.g.logs.values()))

    def test_original_identity_health_and_success_cooldown(self):
        self.request();self.step(3.1);self.assertTrue(self.g.s.despawned)
        self.step(5.1);self.assertTrue(self.g.s.despawned)
        self.step(6.1);self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.id,2001);self.assertEqual(self.g.s.health,45)
        self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,36.1)
        self.assertEqual(self.g.tempGroups,0)

    def test_command_during_approach_keeps_players_new_order(self):
        self.request();self.runlua('callbacks[2001]({squad=s,command=4});s.pos.x=-100')
        self.step(4);self.assertEqual(self.g.departures,0)
        self.assertEqual(self.g.s.pos.x,-100)

    def test_relay_break_after_departure_finishes_committed_journey(self):
        self.request();self.step(3.1)
        self.runlua('VietnamTunnelsState.players[1].graph.byID[1]=nil;n3.component=nil')
        self.step(6.1);self.assertEqual(self.g.s.pos.x,48)

    def test_captured_exit_returns_original_without_cooldown(self):
        self.request();self.step(3.1);self.runlua('registry[3].owner=22')
        self.step(6.1);self.assertLess(self.g.s.pos.x,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,0)

    def test_blocked_exit_retains_original_until_retry_succeeds(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return nil end')
        self.step(6.1);self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return p end')
        self.step(6.5);self.assertFalse(self.g.s.despawned)

    def test_blocked_cleanup_retains_recovery_record_and_rule(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return nil end;VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsRecovery.records[2001])
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return p end;VietnamTunnels_RecoveryTick()')
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(len(self.g.VietnamTunnelsRecovery.records),0)

    def test_cleanup_removes_native_events_and_armed_observers(self):
        self.arm();self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.callbacks[2001])
        self.assertIsNone(self.g.globals[self.g.VietnamTunnels_OnAbilityExecuted])
        self.assertIsNone(self.g.globals[self.g.VietnamTunnels_OnEntityKilled])

    def test_converted_traveler_and_blocked_origin_keep_new_owner(self):
        self.request();self.step(3.1)
        self.runlua('s.owner=22;function Squad_TryFindClosestFreePosition(s,p) return nil end')
        self.step(6.1);self.assertTrue(self.g.s.despawned)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return p end')
        self.step(6.5);self.assertFalse(self.g.s.despawned);self.assertEqual(self.g.s.owner,22)

    def test_marker_visibility_preserves_allies_and_ordinary_enemy_vision(self):
        self.request();self.runlua('localPlayer=22;VietnamTunnels_UpdateUI()')
        self.assertIsNone(self.g.hints)
        self.runlua('vision=true;VietnamTunnels_UpdateUI()');self.assertFalse(self.g.hints[3].fow)
        self.runlua('vision=false;VietnamTunnels_UpdateUI()');self.assertIsNone(self.g.hints[3])
        self.runlua('relationship=R_ALLY;VietnamTunnels_UpdateUI()');self.assertTrue(self.g.hints[3].fow)

    def test_graph_adapter_rejects_foundations_and_ruins_until_full_repair(self):
        self.runlua('''
        VietnamTunnelBuildings={test_tc={hx=4,hz=4,axis=true,root=true},test_landmark={hx=4,hz=4,axis=true}}
        tc=building(10,'test_tc',0);tc.owner=11
        lm=building(11,'test_landmark',0);lm.owner=11;lm.x=12;lm.types={landmark=true};lm.incomplete=true
        VietnamTunnels_Update(PLAYERS[1],entities)
        ''')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].graph.byID[11])
        self.runlua('lm.incomplete=false;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertEqual(self.g.VietnamTunnelsState.players[1].graph.byID[11].component,10)
        self.runlua('VietnamTunnels_OnEntityKilled({victim=lm});lm.health=50;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].graph.byID[11])
        self.runlua('lm.health=100;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertEqual(self.g.VietnamTunnelsState.players[1].graph.byID[11].component,10)

    def test_dynamic_ability_cleanup_and_conversion_preserve_other_bindings(self):
        self.runlua('VietnamTunnelBuildings={};s.ability=false;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertTrue(self.g.s.ability)
        self.runlua('s.owner=22;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertFalse(self.g.s.ability)
        self.runlua('s.owner=11;VietnamTunnels_Update(PLAYERS[1],entities);VietnamTunnels_Cleanup()')
        self.assertFalse(self.g.s.ability)


if __name__=='__main__': unittest.main()

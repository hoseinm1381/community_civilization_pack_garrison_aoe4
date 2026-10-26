"""Real Lua controller against simulated engine boundaries; no native timing proof."""
import unittest
import zipfile
from test_runtime_repairs import ROOT, PREFIX
from tunnel_fixture_v6 import TunnelNativeFixture


class TunnelV7Tests(TunnelNativeFixture):
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

    def cast(self, ids='2001', x=48, z=0):
        self.runlua(f'''for _,squad in ipairs(squads) do
            if string.find(',{ids},',','..squad.id..',',1,true) then
                squad.entity.click={{x={x},y=0,z={z}}}
                VietnamTunnels_OnAbilityExecuted({{ability='{PREFIX}vn_vietnam_unit_mov_vit',executer=squad.entity}})
            end
        end''')

    def step(self,t):
        self.runlua(f'now={t};tick=101+math.floor(now*8);VietnamTunnels_Step(now,tick)')

    def request(self,ids='2001',dest=3):
        self.cast(ids,24*(dest-1));self.step(.1)

    def test_native_click_captured_before_stop_and_no_second_move(self):
        self.cast();self.step(.1)
        self.assertEqual(self.g.targetReads,1)
        self.assertEqual(self.g.moveCount,1)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].records[2001].destination.id,3)

    def test_all_35_native_casters_admitted_once_despite_shared_cooldown(self):
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        ids=','.join(str(2000+i) for i in range(1,36))
        self.cast(ids);self.cast(ids);self.step(.1)
        self.assertEqual(self.g.moveCount,35)
        self.assertEqual(self.g.tempGroups,35)
        self.step(3.1);self.step(6.1)
        self.assertEqual(self.g.arrivals,35)
        self.assertEqual(self.g.tempGroups,0)

    def test_cooldown_starts_on_cast_and_arrival_does_not_extend_it(self):
        self.cast();self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)
        self.step(.1);self.step(3.1);self.step(6.1)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)
        self.assertEqual(self.g.s.id,2001);self.assertEqual(self.g.s.health,45)
        self.cast();self.step(7)
        self.assertEqual(self.g.moveCount,1)
        self.step(30);self.cast();self.step(30.25)
        self.assertEqual(self.g.moveCount,2)

    def test_later_tick_or_different_target_cannot_join_batch(self):
        self.runlua('other=addTraveler(2002);third=addTraveler(2003)')
        self.cast();self.cast('2002',24);self.step(.1);self.cast('2003')
        self.step(.5);self.assertEqual(self.g.moveCount,1)

    def test_no_target_rejects_without_sampling_mouse_or_reusing_move(self):
        self.runlua(f"VietnamTunnels_OnAbilityExecuted({{ability='{PREFIX}vn_vietnam_unit_mov_vit',executer=s.entity}})")
        self.step(.1);self.assertEqual(self.g.moveCount,0)
        self.assertTrue(self.has_log('native-target-unavailable'))

    def test_group_formation_offset_inside_entrance_loads(self):
        self.runlua('autoArrive=false;s.pos={x=-6,y=0,z=3}')
        self.request();self.step(3.1)
        self.assertEqual(self.g.departures,1)

    def test_outside_entrance_never_loads_and_timeout_retains_cast_cooldown(self):
        self.runlua('autoArrive=false;s.pos.x=-100')
        self.request();self.step(16)
        self.assertEqual(self.g.departures,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)
        self.assertEqual(self.g.tempGroups,0)

    def test_pending_new_order_cancels_without_overwriting_it(self):
        self.cast()
        self.runlua('callbacks[2001]({squad=s,command=4});s.pos.x=-100')
        self.step(.1);self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.s.pos.x,-100)

    def test_admission_waits_until_after_native_dispatch_tick(self):
        self.cast();self.runlua('VietnamTunnels_Step(now,tick)')
        self.assertEqual(self.g.moveCount,0)
        self.runlua('other=addTraveler(2002)');self.cast('2002');self.step(.1)
        self.assertEqual(self.g.moveCount,2)

    def test_nearest_foundation_or_disconnected_exit_is_not_skipped(self):
        for kind in ('foundation','disconnected'):
            with self.subTest(kind=kind):
                self.setUp()
                self.runlua('building(4,"tunnel_fixture",56)')
                if kind=='foundation':self.runlua('registry[4].incomplete=true')
                else:self.runlua('VietnamTunnelsState.players[1].graph.byID[4]={id=4,x=56,z=0,hx=4,hz=4}')
                self.cast(x=55);self.step(.1)
                self.assertEqual(self.g.moveCount,0);self.assertTrue(self.has_log(kind))
                self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,30)
                self.tearDown()

    def test_capture_or_death_before_admission_never_moves_squad(self):
        self.cast();self.runlua('s.owner=22');self.step(.1)
        self.assertEqual(self.g.moveCount,0);self.assertIsNone(self.g.callbacks[2001])

    def test_cleanup_removes_pending_observer_and_events(self):
        self.cast();self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.callbacks[2001])
        self.assertIsNone(self.g.globals[self.g.VietnamTunnels_OnAbilityExecuted])

    def test_invalid_target_warning_is_owner_only(self):
        self.runlua('localPlayer=22');self.cast(x=9999);self.step(.1)
        self.assertEqual(len(self.g.warnings),0)
        self.assertEqual(self.g.moveCount,0)

    def test_ineligible_units_do_not_join_native_batch(self):
        self.runlua('s.entity.types.villager=true;other=addTraveler(2002);other.entity.types.siege=true')
        self.cast('2001,2002');self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.targetReads,0)

    def test_valid_zero_coordinate_target_is_not_treated_as_missing(self):
        self.cast(x=0);self.step(.1)
        self.assertEqual(self.g.moveCount,1)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].records[2001].destination.id,1)

    def test_actual_frozen_v6_reproduces_missing_single_click_admission(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v7_20261023/before.zip') as z:
            old=z.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig')
        self.runlua(old);self.runlua("VietnamTunnels_Start({[1]='vietnam'})")
        self.cast();self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.targetReads,0)


# Exercise retained journey/recovery behavior with the NEW input route. The old
# arm/Move and arrival-cooldown tests remain unchanged as historical v6 contracts.
import test_tunnel_v6 as v6
for name in (
    'test_final_source_has_no_mouse_modal_or_paddy_dispatcher',
    'test_equal_footprint_distance_uses_lower_entity_id',
    'test_unknown_footprint_is_visible_failure_not_guessed_distance',
    'test_blocked_entrance_cannot_issue_nil_move',
    'test_loading_requires_three_continuous_seconds_near_entrance',
    'test_minimum_travel_and_one_second_unloading',
    'test_destination_destroyed_before_loading_cancels',
    'test_fast_repair_after_destination_kill_still_returns_original',
    'test_command_during_approach_keeps_players_new_order',
    'test_relay_break_after_departure_finishes_committed_journey',
    'test_blocked_exit_retains_original_until_retry_succeeds',
    'test_blocked_cleanup_retains_recovery_record_and_rule',
    'test_converted_traveler_and_blocked_origin_keep_new_owner',
    'test_marker_visibility_preserves_allies_and_ordinary_enemy_vision',
    'test_graph_adapter_rejects_foundations_and_ruins_until_full_repair',
    'test_dynamic_ability_cleanup_and_conversion_preserve_other_bindings',
):
    setattr(TunnelV7Tests,name,getattr(v6.TunnelV6Tests,name))

if __name__=='__main__':unittest.main()

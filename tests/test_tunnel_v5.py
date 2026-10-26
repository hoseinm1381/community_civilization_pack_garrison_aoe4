"""Regression input sequences from the v4 target boundary, not native proof."""
import os
from pathlib import Path
import test_systems_20261022 as systems
from test_runtime_repairs import ROOT, PREFIX


class TunnelV5Tests(systems.TunnelJourneyTests):
    def setUp(self):
        super().setUp()
        source = os.environ.get('VIETNAM_TUNNEL_SOURCE')
        if source:
            self.runlua('savedGraph=VietnamTunnelsState.players[1].graph')
            self.runlua(Path(source).read_text(encoding='utf-8'))
            self.runlua("VietnamTunnels_Start({[1]='vietnam',[2]='vietnam'});VietnamTunnelsState.players[1].graph=savedGraph")
        self.runlua('''
        TP_Position=1;TP_Cancelled=2;selected={s}
        terrain={x=500,y=0,z=500}
        function Misc_GetMouseOnTerrain() return terrain end
        ''')

    def begin(self):
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")

    def issue(self):
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")

    def execute(self):
        self.assertIsNotNone(self.g.entityCallbacks[3001], 'target capture wrongly removed selected squad observer')
        self.runlua("entityCallbacks[3001]({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'})")

    def test_v5_capture_does_not_require_current_graph_connectivity(self):
        self.runlua("target=building(3,'custom_keep',48);hovered=target;n3.component=nil")
        self.begin();self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')
        self.assertTrue(self.has_log('boundary=simulation reason=disconnected'))
        self.assertEqual(len(self.g.VietnamTunnelsState.players[1].pending),0)

    def test_v5_post_click_cursor_clear_keeps_live_target_snapshot(self):
        self.runlua("target=building(3,'custom_keep',48);hovered=target")
        self.begin()
        self.runlua('hovered=nil;terrain={x=500,y=0,z=500}')
        self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_v5_hover_clear_callback_does_not_overwrite_last_target(self):
        self.runlua("target=building(3,'custom_keep',48);hovered=target")
        self.begin()
        self.runlua('hovered=nil;VietnamTunnels_OnModalHover(nil)')
        self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_v5_false_mouseover_flag_does_not_read_stale_entity_handle(self):
        self.runlua('''
        function Misc_IsMouseOverEntity() return false end
        function Misc_GetMouseOverEntity() error('must gate stale getter') end
        terrain={x=48,y=0,z=0}
        ''')
        self.begin();self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_v5_attachment_visual_uses_unique_owned_footprint_hit(self):
        self.runlua("visual=building(700,'attachment',48);visual.building=false;visual.world=true;hovered=visual;terrain={x=48,y=0,z=0}")
        self.begin();self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')
        self.assertTrue(self.has_log('route=footprint'))

    def test_v5_ambiguous_footprint_rejects_instead_of_choosing_nearest(self):
        self.runlua('''
        extra={id=4,x=48,z=0,hx=4,hz=4,reach=16}
        VietnamTunnelsState.players[1].graph=VietnamTunnelCore.Build({n1,n2,n3,extra})
        terrain={x=48,y=0,z=0};hovered=nil
        ''')
        self.begin();self.issue()
        self.assertIsNone(self.g.sentMessage)
        self.assertTrue(self.has_log('reason=ambiguous-footprint'))

    def test_v5_invalid_direct_building_never_falls_back_to_other_footprint(self):
        self.runlua("target=building(9,'enemy',48,22);hovered=target;terrain={x=48,y=0,z=0}")
        self.begin();self.issue()
        self.assertIsNone(self.g.sentMessage)
        self.assertTrue(self.has_log('reason=foreign-owner'))

    def test_v5_snapshot_expires_instead_of_using_stale_destination(self):
        self.runlua("target=building(3,'custom_keep',48);hovered=target")
        self.begin();self.runlua('hovered=nil;now=2');self.issue()
        self.assertIsNone(self.g.sentMessage)

    def test_v5_live_hover_moving_to_empty_terrain_invalidates_prior_target(self):
        self.runlua("target=building(3,'custom_keep',48);hovered=target")
        self.begin();self.runlua('hovered=nil;VietnamTunnels_UpdateUI()');self.issue()
        self.assertIsNone(self.g.sentMessage)

    def test_v5_malformed_network_selection_is_rejected_without_lua_error(self):
        self.runlua("VietnamTunnels_NetRequest(11,'3;');VietnamTunnels_NetRequest(11,'3;2001,,2002');VietnamTunnels_NetRequest(11,'3;2001,')")
        self.assertEqual(len(self.g.VietnamTunnelsState.players[1].pending),0)

    def test_v5_nil_blocked_exit_position_keeps_original_in_transit_until_clear(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return nil end;function Squad_Spawn(s,p,kind) assert(p~=nil);s.despawned=false;s.pos=p;arrivals=arrivals+1 end')
        self.step(6.1)
        self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return p end')
        self.step(6.5)
        self.assertFalse(self.g.s.despawned)

    def test_v5_network_revalidates_converted_destination_owner(self):
        self.runlua("target=building(3,'custom_keep',48,22)")
        self.request();self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertTrue(self.has_log('boundary=simulation reason=foreign-owner'))

    def test_v5_heavy_elephant_original_squad_is_admitted(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_war_elephant_1_vit'")
        self.request();self.step(.1)
        self.assertEqual(self.g.moveCount,1)

    def test_v5_unavailable_entrance_position_never_issues_nil_move(self):
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return nil end;function Cmd_Move(g,p) assert(p~=nil);moveCount=moveCount+1 end')
        self.request();self.step(.1)
        self.assertEqual(self.g.moveCount,0)
        self.assertEqual(self.g.tempGroups,0)

    def test_v5_completed_paddy_deposit_does_not_use_building_progress(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';hovered=building(501,'vn_building_resource_farm_chi',48);hovered.building=false")
        self.runlua('''
        function Entity_GetBuildingProgress(e) assert(e.building,'resource deposit is not a building');return 1 end
        function VietnamPaddyWood_NetAssign(sender,message) paddyMessage=message end
        ''')
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_buffalo_work_paddy_vit',TP_Position);VietnamTunnels_AbilityPhase('"+PREFIX+"vn_buffalo_work_paddy_vit',TP_Issued)")
        self.assertIsNotNone(self.g.entityCallbacks[3001], 'completed resource deposit must be targetable')
        self.runlua("entityCallbacks[3001]({ability='"+PREFIX+"vn_buffalo_work_paddy_vit'})")
        self.assertEqual(self.g.paddyMessage,'501;2001')

    def test_v5_new_owner_and_blocked_origin_keeps_same_squad_for_retry(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('s.owner=22;function Squad_TryFindClosestFreePosition(s,p) return nil end;function Squad_Spawn(s,p,kind) assert(p~=nil);s.despawned=false;s.pos=p;arrivals=arrivals+1 end')
        self.step(6.1)
        self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return p end')
        self.step(6.5)
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.owner,22)

    def test_v5_fast_click_captures_direct_target_available_only_at_issued(self):
        self.begin()
        self.runlua("hovered=building(3,'custom_keep',48)")
        self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_v5_issued_does_not_replace_valid_snapshot_with_different_building(self):
        self.runlua("hovered=building(3,'custom_keep',48)")
        self.begin();self.runlua("hovered=building(2,'other_keep',24)")
        self.issue();self.execute()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_v5_issued_does_not_ignore_explicit_foreign_snapshot(self):
        self.runlua("hovered=building(900,'foreign',90,22)")
        self.begin();self.runlua("hovered=building(3,'custom_keep',48)")
        self.issue()
        self.assertIsNone(self.g.sentMessage)
        self.assertIsNone(self.g.entityCallbacks[3001])

    def test_v5_issued_does_not_ignore_explicit_foundation_snapshot(self):
        self.runlua("hovered=building(900,'foundation',90);hovered.incomplete=true")
        self.begin();self.runlua("hovered=building(3,'custom_keep',48)")
        self.issue()
        self.assertIsNone(self.g.sentMessage)
        self.assertIsNone(self.g.entityCallbacks[3001])

    def test_v5_issued_direct_capture_never_uses_late_terrain_footprint(self):
        self.begin();self.runlua('terrain={x=48,y=0,z=0}')
        self.issue()
        self.assertIsNone(self.g.sentMessage)
        self.assertIsNone(self.g.entityCallbacks[3001])

    def test_v5_capture_log_explains_owner_terrain_and_graph_membership(self):
        self.runlua("hovered=building(3,'custom_keep',48);terrain={x=48,y=0,z=0}")
        self.begin()
        self.assertTrue(self.has_log('owner=11 terrainX=48 terrainZ=0 graphEntry=true component=1'))

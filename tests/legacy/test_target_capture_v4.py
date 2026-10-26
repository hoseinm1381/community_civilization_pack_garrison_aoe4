"""Prior targeting cases carried forward with the current v5 worker contract."""
import test_systems_20261022 as systems
from test_runtime_repairs import PREFIX, ROOT

class TargetCaptureV4Tests(systems.TunnelJourneyTests):
    def setUp(self):
        super().setUp()
        self.runlua('''
        TP_Position=1;TP_Cancelled=2;selected={s}
        function UI_SetModalHoverCallback(f) hoverCallback=f end
        function UI_ClearModalHoverCallback() hoverCallback=nil end
        function Misc_GetMouseOnTerrain() return mousePosition end
        function VietnamPaddyWood_NetAssign(sender,message) paddyMessage=message end
        VietnamTunnels_Cleanup();VietnamTunnels_Start({[1]='vietnam',[2]='vietnam'})
        VietnamTunnelsState.players[1].graph=VietnamTunnelCore.Build({n1,n2,n3})
        ''')

    def phase(self,phase,work=False):
        name='vn_buffalo_work_paddy_vit' if work else 'vn_vietnam_unit_mov_vit'
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+name+"',"+phase+")")

    def executed(self,work=False):
        name='vn_buffalo_work_paddy_vit' if work else 'vn_vietnam_unit_mov_vit'
        self.runlua("entityCallbacks[3001]({ability='"+PREFIX+name+"'})")

    def test_hover_snapshot_survives_issued_phase_losing_mouse_target(self):
        self.phase('TP_Position')
        self.runlua("hovered=building(3,'target',48);hoverCallback('target');hovered=nil;mousePosition=nil")
        self.phase('TP_Issued');self.executed()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_ground_snapshot_is_captured_before_native_phase_clears_cursor(self):
        self.phase('TP_Position')
        self.runlua('mousePosition={x=48,z=0};VietnamTunnels_UpdateUI();mousePosition=nil')
        self.phase('TP_Issued');self.executed()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_new_invalid_hover_clears_old_destination_instead_of_teleporting_there(self):
        self.phase('TP_Position')
        self.runlua("hovered=building(3,'target',48);hoverCallback('target');hovered=building(900,'foreign',90,22);hoverCallback('foreign');hovered=nil")
        self.phase('TP_Issued')
        self.assertIsNone(self.g.sentMessage)
        self.assertIsNone(self.g.entityCallbacks[3001])

    def test_new_valid_live_sample_replaces_previous_invalid_snapshot(self):
        self.phase('TP_Position')
        self.runlua("hovered=building(900,'foreign',90,22);hoverCallback('foreign')")
        self.assertEqual(self.g.VietnamTunnelsLocal.selection.hoverDestination,0)
        self.runlua("hovered=building(3,'target',48);hoverCallback('target');hovered=nil;mousePosition=nil")
        self.phase('TP_Issued');self.executed()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_clicked_paddy_uses_work_ability_acknowledgement_and_separate_network_owner(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';paddy=building(501,'vn_building_resource_farm_chi',48);paddy.owner=11;paddy.building=false;hovered=paddy")
        self.phase('TP_Position',True)
        self.runlua("hoverCallback('paddy')")
        self.phase('TP_Issued',True)
        self.assertIsNone(self.g.paddyMessage)
        self.runlua('now=3;VietnamTunnels_UpdateUI()')
        self.executed(True)
        self.assertEqual(self.g.paddyMessage,'501;2001')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_foundation_or_foreign_paddy_cannot_be_selected(self):
        for condition in ['paddy.incomplete=true','paddy.owner=22',"paddy.bp='"+PREFIX+"vn_building_resource_farm2_chi'"]:
            with self.subTest(condition=condition):
                self.setUp()
                self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';paddy=building(501,'vn_building_resource_farm_chi',48);paddy.owner=11;paddy.building=false;hovered=paddy;"+condition)
                self.phase('TP_Position',True);self.phase('TP_Issued',True)
                self.assertIsNone(self.g.paddyMessage)
                self.assertIsNone(self.g.entityCallbacks[3001])

    def test_cleanup_releases_hover_callback_and_native_cancel_releases_selection(self):
        self.phase('TP_Position');self.phase('TP_Cancelled')
        self.assertIsNone(self.g.entityCallbacks[3001])
        self.runlua('VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.hoverCallback)

    def test_single_cast_from_multiple_buffalo_assigns_after_first_ack(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';other=addTraveler(2002);other.bp=s.bp;selected={s,other};hovered=building(501,'vn_building_resource_farm_chi',48);hovered.owner=11;hovered.building=false")
        self.phase('TP_Position',True);self.phase('TP_Issued',True);self.executed(True)
        self.assertEqual(self.g.paddyMessage,'501;2001')
        self.assertIsNone(self.g.entityCallbacks[3002])

    def test_second_paddy_order_does_not_cancel_first_buffalos_approach(self):
        self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';other=addTraveler(2002);other.bp=s.bp;hovered=building(501,'vn_building_resource_farm_chi',48);hovered.owner=11;hovered.building=false")
        self.phase('TP_Position',True);self.phase('TP_Issued',True)
        self.runlua("ackA=entityCallbacks[3001];selected={other};hovered=building(502,'vn_building_resource_farm_chi',72);hovered.owner=11;hovered.building=false")
        self.phase('TP_Position',True);self.phase('TP_Issued',True)
        self.runlua("ackA({ability='"+PREFIX+"vn_buffalo_work_paddy_vit'})")
        self.assertEqual(self.g.paddyMessage,'501;2001')
        self.runlua("entityCallbacks[3002]({ability='"+PREFIX+"vn_buffalo_work_paddy_vit'})")
        self.assertEqual(self.g.paddyMessage,'502;2002')

    def test_world_owned_hover_never_queries_player_owner(self):
        self.phase('TP_Position')
        self.runlua("hovered=building(950,'gold',48);hovered.world=true;function Entity_GetPlayerOwner(e) assert(not e.world);return e.owner or 11 end;hoverCallback('gold')")
        self.phase('TP_Issued');self.assertIsNone(self.g.sentMessage)

    def test_real_paddy_network_handler_receives_click_then_earns_and_stops_income(self):
        self.runlua('''
        RT_Wood=1;bank=0
        function Player_AddResource(owner,kind,amount) bank=bank+amount end
        function Squad_IsIdle(squad) return true end
        ''')
        self.runlua((ROOT/'assets/scar/vietnam/paddy_wood.scar').read_text())
        self.runlua("s.bp='"+PREFIX+"vn_unit_water_buffalo_vit';paddy=building(501,'vn_building_resource_farm_chi',48);paddy.owner=11;paddy.building=false;hovered=paddy;VietnamPaddyWood_Update(PLAYERS[1],entities,0)")
        self.phase('TP_Position',True);self.phase('TP_Issued',True)
        self.runlua('s.pos={x=48,y=0,z=0}')
        self.executed(True)
        self.assertEqual(self.g.VietnamPaddyWoodState.players[1].watches[2001].paddy,501)
        self.runlua('VietnamPaddyWood_Update(PLAYERS[1],entities,.25);VietnamPaddyWood_Update(PLAYERS[1],entities,.5)')
        self.assertAlmostEqual(self.g.bank,.375*.25)
        self.runlua('VietnamPaddyWood_OnCommand({},VietnamPaddyWoodState.players[1].watches[2001]);VietnamPaddyWood_Update(PLAYERS[1],entities,.75)')
        self.assertAlmostEqual(self.g.bank,.375*.25)

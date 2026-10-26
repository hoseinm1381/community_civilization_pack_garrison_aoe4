"""Regression coverage for actual carrier dispatch and UI cost failures."""
import test_systems_20261022 as systems
from test_runtime_repairs import ROOT, PREFIX
import xml.etree.ElementTree as ET

class TunnelFeedbackTests(systems.TunnelJourneyTests):
    def target(self):
        self.runlua("TP_Position=1;TP_Cancelled=2;selected={s};hovered=building(3,'target',0)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")

    def executed(self, entity_id=3001):
        self.runlua("entityCallbacks["+str(entity_id)+"]({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'})")

    def test_native_carrier_command_precedes_network_observers(self):
        self.target()
        self.runlua('callbacks[2001]({});VietnamTunnels_UpdateUI()')
        self.assertIsNone(self.g.sentMessage)
        self.executed()
        self.step(.25);self.step(3.25)
        self.assertEqual(self.g.departures,1)

    def test_ground_footprint_target_works_when_roof_has_no_mouseover_entity(self):
        self.runlua('TP_Position=1;selected={s};hovered=nil;function Misc_GetMouseOnTerrain() return {x=48,z=0} end')
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.executed()
        self.assertEqual(self.g.sentMessage,'3;2001')

    def test_manual_order_before_carrier_execution_never_admits_without_execute_event(self):
        self.target();self.runlua('callbacks[2001]({});s.pos={x=-100,y=0,z=0};now=1.1;VietnamTunnels_UpdateUI()')
        self.step(2)
        self.assertEqual(self.g.moveCount,0)
        self.assertIsNone(self.g.callbacks[2001]);self.assertIsNone(self.g.entityCallbacks[3001])

    def test_manual_order_after_execute_before_target_snapshot_is_preserved(self):
        self.runlua("TP_Position=1;selected={s};hovered=building(3,'target',0)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.executed();self.runlua('callbacks[2001]({});s.pos={x=-100,y=0,z=0}')
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.step(.25)
        self.assertEqual(self.g.moveCount,0);self.assertIsNone(self.g.sentMessage)

    def test_manual_order_in_prior_quarter_second_race_is_preserved(self):
        self.target();self.executed()
        self.runlua('callbacks[2001]({});s.pos={x=-100,y=0,z=0}')
        self.step(.25)
        self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.s.pos.x,-100)

    def test_other_ability_does_not_acknowledge_carrier(self):
        self.target();self.runlua("entityCallbacks[3001]({ability='other'});now=1.1;VietnamTunnels_UpdateUI()")
        self.assertIsNone(self.g.sentMessage)

    def test_batch_waits_for_each_carrier_and_sends_once(self):
        self.runlua("TP_Position=1;other=addTraveler(2002);selected={s,other};hovered=building(3,'target',0)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.executed();self.assertIsNone(self.g.sentMessage)
        self.executed(3002);self.assertEqual(self.g.sentMessage,'3;2001,2002')
        self.assertIsNone(self.g.entityCallbacks[3001]);self.assertIsNone(self.g.entityCallbacks[3002])

    def test_partial_execution_timeout_preserves_cancelled_squad_and_cleans_watchers(self):
        self.runlua("TP_Position=1;other=addTraveler(2002);selected={s,other};hovered=building(3,'target',0)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.executed();self.runlua('callbacks[2001]({});now=1.1;VietnamTunnels_UpdateUI()')
        self.assertIsNone(self.g.sentMessage)
        self.assertIsNone(self.g.callbacks[2001]);self.assertIsNone(self.g.callbacks[2002])
        self.assertIsNone(self.g.entityCallbacks[3001]);self.assertIsNone(self.g.entityCallbacks[3002])

    def test_killed_unacknowledged_member_does_not_block_surviving_batch(self):
        self.runlua("TP_Position=1;other=addTraveler(2002);selected={s,other};hovered=building(3,'target',0)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.executed();self.runlua('other.dead=true;other.entity.dead=true;now=1.1;VietnamTunnels_UpdateUI()')
        self.assertEqual(self.g.sentMessage,'3;2001')
        self.assertIsNone(self.g.callbacks[2002]);self.assertIsNone(self.g.entityCallbacks[3002])

    def test_target_cancel_and_cleanup_remove_handshake_watchers(self):
        self.target()
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Cancelled)")
        self.assertIsNone(self.g.callbacks[2001]);self.assertIsNone(self.g.entityCallbacks[3001])
        self.target();self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.callbacks[2001]);self.assertIsNone(self.g.entityCallbacks[3001])

    def test_duplicate_squad_ids_are_admitted_once(self):
        self.request('2001,2001,2001');self.step(.1)
        self.assertEqual(self.g.moveCount,1)
        self.assertEqual(self.g.tempGroups,1)

    def test_idle_step_does_not_scan_all_armies(self):
        self.runlua('function Player_GetSquads(p) error("idle full-army scan") end')
        self.step(.1)

    def test_carrier_has_no_per_caster_global_range_reticule(self):
        t=ET.parse(ROOT/'assets/attrib/instances/abilities/vietnam/vn_vietnam_unit_mov_vit.xml')
        self.assertEqual(t.find('.//instance_reference[@name="ui_range"]').get('value'),'')
        self.assertEqual(t.find('.//bool[@name="ui_range_reticule_first_caster_only"]').get('value'),'True')
        self.assertEqual(t.find('.//bool[@name="range_ignore"]').get('value'),'True')
        self.assertEqual(t.find('.//float[@name="range"]').get('value'),'0')

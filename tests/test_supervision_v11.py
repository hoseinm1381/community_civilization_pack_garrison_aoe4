"""Reproduce native edge execution; Lua doubles are not native match proof."""
from test_runtime_v10_supervision import SupervisionV10
from test_runtime_repairs import ROOT
import unittest, zipfile, re, xml.etree.ElementTree as E

class SupervisionV11(SupervisionV10):
    # Do not inherit historical geometry assertions as current acceptance tests.
    def setUp(self):
        super().setUp()
        self.runlua('''
        committed=paddy;moveCount=0
        function Entity_GetStateTreeTargeting_EntityTarget(e,t,k)
            assert(t=='statetree_commited_target_type' and k=='COMMITTED_ABILITY')
            return committed
        end
        function SGroup_CreateUniqueWithPrefix(n) liveGroups=liveGroups+1;return {} end
        function SGroup_Add(g,s) g[1]=s end
        function SGroup_Destroy(g) liveGroups=liveGroups-1 end
        function Cmd_Move(g,p,q,d,f,o,dist,cover,split,proximity)
            assert(not q and proximity==.1);moveCount=moveCount+1
            moveTarget=p;g[1].busy=true;nativeCommand(g[1],SCMD_Move)
        end
        ''')

    def test_edge_cast_centers_exact_clicked_paddy_before_payment(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo)')
        self.tick(.25)
        self.assertEqual(self.g.moveCount,1);self.assertEqual(self.g.moveTarget.x,0)
        self.assertEqual(self.g.bank[11],0);self.assertEqual(self.g.tagAdds,0)
        self.runlua('buffalo.entity.x=.1;buffalo.busy=false')
        self.tick(.5);self.tick(.75)
        self.assertAlmostEqual(self.g.bank[11],.375*.25)
        self.assertEqual(self.g.reasons[1],7);self.assertIsNotNone(self.marker())
        self.assertEqual(self.g.moveCount,1);self.assertEqual(self.g.liveGroups,0)

    def test_native_target_wins_over_closer_adjacent_paddy(self):
        self.tick(0)
        self.runlua("other=building(502,'vn_building_resource_farm_chi',4);buffalo.entity.x=4;assign(buffalo)")
        self.tick(.25);self.assertEqual(self.g.moveTarget.x,0)

    def test_no_target_never_guesses_nearby_farm(self):
        self.tick(0);self.runlua('committed=nil;assign(buffalo)');self.tick(.25)
        self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.bank[11],0)

    def test_move_cancels_pending_center_before_it_can_override_player(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo);order(buffalo)')
        self.tick(.25);self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.bank[11],0)

    def test_move_during_centering_cancels_without_retry(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo)');self.tick(.25)
        self.runlua('order(buffalo);buffalo.entity.x=0;buffalo.busy=false')
        self.tick(.5);self.tick(.75);self.assertEqual(self.g.moveCount,1);self.assertEqual(self.g.bank[11],0)

    def test_failed_center_has_deadline_and_does_not_pay(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo)');self.tick(.25)
        self.tick(60.5);self.assertEqual(self.g.bank[11],0);self.assertEqual(len(self.g.warnings),1)

    def test_two_buffalo_cannot_reserve_same_target(self):
        self.tick(0);self.runlua('second=addBuffalo(101)');self.tick(.25)
        self.runlua('buffalo.entity.x=4;second.entity.x=4;assign(buffalo);assign(second)')
        self.tick(.5);self.assertEqual(self.g.moveCount,1)

    def test_invalid_target_and_owner_reject(self):
        for change in ['paddy.owner=22','paddy.incomplete=true','paddy.dead=true',"paddy.bp='wrong'"]:
            self.setUp();self.tick(0);self.runlua(change+';assign(buffalo)');self.tick(.25)
            self.assertEqual(self.g.bank[11],0);self.assertEqual(self.g.moveCount,0)

    def test_same_tick_execution_command_order(self):
        for sequence in ['nativeCommand(buffalo,SCMD_Ability);cast(buffalo)','cast(buffalo);nativeCommand(buffalo,SCMD_Ability)']:
            self.setUp();self.tick(0);self.runlua('buffalo.entity.x=4;'+sequence);self.tick(.25)
            self.assertEqual(self.g.moveCount,1)

    def test_assignment_marker_cleanup_and_displacement(self):
        for change in ['buffalo.owner=22','buffalo.dead=true','buffalo.entity.dead=true','buffalo.held=true',
                       'paddy.owner=22','paddy.dead=true','paddy.incomplete=true','registry[501]=nil','buffalo.entity.x=.51']:
            self.setUp();self.start();earned=self.g.bank[11]
            self.runlua(change);self.tick(.75);self.tick(1)
            self.assertEqual(self.g.bank[11],earned);self.assertIsNone(self.marker())

    def test_arrival_still_busy_or_queued_never_earns(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo)');self.tick(.25)
        self.runlua('buffalo.entity.x=0');self.tick(.5);self.tick(.75)
        self.assertEqual(self.g.bank[11],0);self.assertEqual(self.g.tagAdds,0)

    def test_separate_native_targets_work_independently(self):
        self.runlua("second=addBuffalo(101);other=building(502,'vn_building_resource_farm_chi',4)")
        self.tick(0);self.runlua('assign(buffalo);committed=other;second.entity.x=4;assign(second)')
        self.tick(.25);self.tick(.5)
        self.assertAlmostEqual(self.g.bank[11],2*.375*.25);self.assertEqual(self.g.tagAdds,2)

    def test_center_target_destroyed_before_move_cannot_be_retargeted(self):
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo);paddy.dead=true')
        self.tick(.25);self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.bank[11],0)

    def test_v10_snapshot_reproduces_reported_edge_rejection(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v11_20261023/before.zip') as z:
            self.runlua(z.read('assets/scar/vietnam/paddy_wood.scar').decode())
        self.tick(0);self.runlua('buffalo.entity.x=4;assign(buffalo)');self.tick(.25)
        self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.bank[11],0)
        self.assertTrue(any('no_completed_owned_paddy' in self.g.logs[i] for i in range(1,len(self.g.logs)+1)))

class ControlsV11(unittest.TestCase):
    def test_speed_ui_key_and_presentation_preserve_graph(self):
        r=ROOT/'assets/attrib/instances'
        t=E.parse(r/'ebps/vietnam/units/economy/experimental_cattle/vn_unit_water_buffalo_vit.xml')
        self.assertEqual([x.get('value') for x in t.findall('.//float[@name="default_speed"]')],['3.5','3.5'])
        t=E.parse(r/'abilities/vietnam/vn_buffalo_work_paddy_vit.xml')
        self.assertEqual(t.find('.//string[@name="hotkey_name"]').get('value'),'E')
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v11_20261023/before.zip') as z:
            for name in ['tunnel_core.scar','tunnel_buildings.scar','tunnels.scar']:
                path='assets/scar/vietnam/'+name
                self.assertEqual((ROOT/path).read_bytes(),z.read(path))

    def test_only_requested_visual_fields_change_in_buildings(self):
        count=0;badges=0
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v11_20261023/before.zip') as z:
            for name in z.namelist():
                if not name.startswith('assets/attrib/instances/ebps/vietnam/buildings/') or not name.endswith('.xml'):continue
                before=z.read(name);after=(ROOT/name).read_bytes()
                def shrink(m):
                    return re.sub(rb'(name="range_metres" value=")(4|8)(")',
                        lambda v:v[1]+str(int(v[2])-2).encode()+v[3],m[0])
                expected=re.sub(rb'<template_reference name="exts" value="ebpextensions\\district_generator_ext"[^>]*>.*?</template_reference>',shrink,before,flags=re.S)
                if 'town_center' in name:
                    badges+=before.count(b'name="district_info" value="ui_district_info\\chinese\\dib_chi_town_center"')
                    expected=expected.replace(b'name="district_info" value="ui_district_info\\chinese\\dib_chi_town_center"',b'name="district_info" value=""')
                self.assertEqual(after,expected,name)
                count+=before!=after
        self.assertEqual(count,36);self.assertEqual(badges,4)

# Inherited tests describe v10 contracts; only explicitly named v11 tests run.
def load_tests(loader,tests,pattern):
    names=[n for n in SupervisionV11.__dict__ if n.startswith('test_')]
    names+=['test_one_marker_per_active_farm_and_idempotent_cleanup',
            'test_restore_rebuilds_marker_without_changing_assignment_or_income',
            'test_local_ui_has_no_effect_on_synchronized_income',
            'test_wrapped_owner_uses_numeric_identity_for_marker_and_income',
            'test_income_rate_formula_and_no_retroactive_tech_bonus_are_preserved',
            'test_active_or_queued_order_hides_marker_and_never_pays',
            'test_move_same_tick_and_later_both_cancel_and_never_reissue',
            'test_command_execution_order_both_work_then_any_move_cancels',
            'test_failed_native_path_times_out_without_income_or_marker']
    return unittest.TestSuite([*(SupervisionV11(n) for n in names),loader.loadTestsFromTestCase(ControlsV11)])

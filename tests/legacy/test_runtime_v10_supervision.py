"""Native center admission, income classification and marker lifetime; not engine proof."""
import zipfile
import xml.etree.ElementTree as ET
from test_paddy_wood import PaddyWoodFixture
from test_runtime_repairs import ROOT

WOOD='assets/scar/vietnam/paddy_wood.scar'
SNAP=ROOT/'work/vietnam_redesign/runtime_v10_20261023/before.zip'

class SupervisionV10(PaddyWoodFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        RES_Resourcing=7;reasons={};tags={};tagAdds=0;tagRemoves=0
        function Player_AddResource(p,r,n,reason)
            bank[Player_GetID(p)]=bank[Player_GetID(p)]+n;reasons[#reasons+1]=reason or -1
        end
        function UI_CreateTagForPosition(p,data)
            assert(p.native,'tag requires native ScarPos')
            local key=p.x..':'..p.z
            assert(tags[key]==nil,'duplicate working tag')
            assert(data.DataTemplate=='TagArrowDataTemplate')
            tags[key]=data;tagAdds=tagAdds+1
        end
        function UI_DestroyTagForPosition(p)
            local key=p.x..':'..p.z
            assert(tags[key]~=nil,'remove absent working tag')
            tags[key]=nil;tagRemoves=tagRemoves+1
        end
        function Cmd_Move() error('native ability owns center approach') end
        function Squad_SetPosition() error('supervision must not teleport') end
        function Entity_SetPosition() error('supervision must not teleport') end
        ''')

    def marker(self):return self.g.tags['0:0']

    def test_actual_v9_snapshot_pays_off_center_without_reason_or_marker(self):
        with zipfile.ZipFile(SNAP) as z:self.runlua(z.read(WOOD).decode())
        self.runlua('buffalo.entity.x=.75');self.start()
        self.assertAlmostEqual(self.g.bank[11],.375*.25)
        self.assertEqual(self.g.reasons[1],-1);self.assertEqual(self.g.tagAdds,0)

    def test_native_approach_has_no_income_or_marker_before_centered_execution(self):
        self.runlua('buffalo.entity.x=12;buffalo.busy=true;buffalo.doingWork=true')
        self.tick(0);self.runlua('nativeCommand(buffalo,SCMD_Ability)');self.tick(.25);self.tick(.5)
        self.assertEqual(self.g.bank[11],0);self.assertIsNone(self.marker())
        self.runlua('buffalo.entity.x=.20;cast(buffalo);buffalo.busy=false;buffalo.doingWork=false')
        self.tick(.75);self.assertIsNotNone(self.marker());self.assertEqual(self.g.bank[11],0)
        self.tick(1);self.assertAlmostEqual(self.g.bank[11],.375*.25);self.assertEqual(self.g.reasons[1],7)

    def test_outside_center_range_rejects_execution_despite_old_five_metre_admission(self):
        for x in [.250001,.75,4.99]:
            self.setUp();self.runlua(f'buffalo.entity.x={x}');self.start()
            self.assertEqual(self.g.bank[11],0);self.assertIsNone(self.marker())
            self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))

    def test_range_and_idle_invariant_matches_native_tuning(self):
        root=ET.parse(ROOT/'assets/attrib/instances/abilities/vietnam/vn_buffalo_work_paddy_vit.xml').getroot()
        self.assertEqual(float(root.find("group/float[@name='range']").get('value')),.25)
        self.assertEqual(root.find("group/bool[@name='use_simbox_to_simbox_range']").get('value'),'False')
        self.assertIn('local radiusSquared = 0.0625',(ROOT/WOOD).read_text())
        self.runlua('buffalo.entity.x=.25');self.start();self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_adjacent_farm_no_longer_makes_centered_target_ambiguous(self):
        self.runlua("other=building(502,'vn_building_resource_farm_chi',.8)");self.start()
        self.assertAlmostEqual(self.g.bank[11],.375*.25);self.assertIsNotNone(self.marker())

    def test_truly_ambiguous_overlapping_centers_fail_closed(self):
        self.runlua("other=building(502,'vn_building_resource_farm_chi',.20)");self.start()
        self.assertEqual(self.g.bank[11],0);self.assertIsNone(self.marker())

    def test_move_same_tick_and_later_both_cancel_and_never_reissue(self):
        for later in [False,True]:
            self.setUp();self.tick(0);self.runlua('assign(buffalo)')
            if later:self.tick(.25)
            self.runlua('order(buffalo)');self.tick(.5);self.tick(.75)
            self.assertEqual(self.g.bank[11],0);self.assertIsNone(self.marker())
            self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'))

    def test_command_execution_order_both_work_then_any_move_cancels(self):
        for sequence in ['nativeCommand(buffalo,SCMD_Ability);cast(buffalo)','cast(buffalo);nativeCommand(buffalo,SCMD_Ability)']:
            self.setUp();self.tick(0);self.runlua(sequence);self.tick(.25);self.tick(.5)
            self.assertAlmostEqual(self.g.bank[11],.375*.25)
            self.runlua('order(buffalo)');self.assertIsNone(self.marker())

    def test_failed_native_path_times_out_without_income_or_marker(self):
        self.tick(0);self.runlua('buffalo.busy=true;buffalo.doingWork=true;nativeCommand(buffalo,SCMD_Ability)')
        self.tick(.25);self.tick(60);self.tick(60.25)
        self.assertEqual(self.g.bank[11],0);self.assertIsNone(self.marker());self.assertEqual(len(self.g.warnings),1)

    def test_active_or_queued_order_hides_marker_and_never_pays(self):
        for change in ['buffalo.busy=true','buffalo.queued=true']:
            self.setUp();self.start();earned=self.g.bank[11]
            self.runlua(change);self.tick(.75);self.tick(1)
            self.assertEqual(self.g.bank[11],earned);self.assertIsNone(self.marker())

    def test_marker_cleanup_on_capture_death_destruction_hold_and_displacement(self):
        for change in ['buffalo.owner=22','buffalo.dead=true','buffalo.entity.dead=true','buffalo.held=true','paddy.owner=22','paddy.dead=true','paddy.incomplete=true','registry[501]=nil','buffalo.entity.x=.26']:
            self.setUp();self.start();earned=self.g.bank[11];self.assertIsNotNone(self.marker())
            self.runlua(change);self.tick(.75);self.tick(1)
            self.assertEqual(self.g.bank[11],earned);self.assertIsNone(self.marker());self.assertEqual(self.g.tagRemoves,1)

    def test_one_marker_per_active_farm_and_idempotent_cleanup(self):
        self.start();self.tick(.75);self.tick(1);self.assertEqual(self.g.tagAdds,1)
        self.runlua('VietnamPaddyWood_Cleanup();VietnamPaddyWood_Cleanup()')
        self.assertEqual(self.g.tagRemoves,1);self.assertIsNone(self.marker())
        self.assertIsNone(self.g.events[1100]);self.assertIsNone(self.g.commands[100])

    def test_restore_rebuilds_marker_without_changing_assignment_or_income(self):
        self.start();earned=self.g.bank[11]
        self.runlua('VietnamPaddyWood_RestoreUI()')
        self.assertIsNone(self.marker());self.assertEqual(self.g.bank[11],earned)
        self.assertEqual(self.lua.eval('VietnamPaddyWoodState.players[1].watches[100].paddy'),501)
        self.tick(.75);self.assertIsNotNone(self.marker());self.assertEqual(self.g.tagAdds,2)
        self.assertAlmostEqual(self.g.bank[11],earned+.375*.25)

    def test_local_ui_has_no_effect_on_synchronized_income(self):
        self.runlua('localPlayer=22');self.start()
        self.assertAlmostEqual(self.g.bank[11],.375*.25);self.assertEqual(self.g.tagAdds,0)
        self.runlua('localPlayer=11');self.tick(.75);self.assertIsNotNone(self.marker())
        self.runlua('localPlayer=22');self.tick(1);self.assertIsNone(self.marker())
        self.assertAlmostEqual(self.g.bank[11],.375*.75)

    def test_one_buffalo_per_paddy_and_separate_farms_have_separate_markers(self):
        self.runlua("second=addBuffalo(101);other=building(502,'vn_building_resource_farm_chi',.8)")
        self.tick(0);self.runlua('assign(buffalo);assign(second)')
        self.assertIsNone(self.lua.eval('VietnamPaddyWoodState.players[1].watches[101].paddy'))
        self.runlua('second.entity.x=.8;assign(second)');self.tick(.25);self.tick(.5)
        self.assertAlmostEqual(self.g.bank[11],2*.375*.25);self.assertEqual(self.g.tagAdds,2)

    def test_wrapped_owner_uses_numeric_identity_for_marker_and_income(self):
        self.runlua('''
        function Squad_GetPlayerOwner(s) return {playerID=s.owner} end
        function Entity_GetPlayerOwner(e) return {playerID=e.owner} end
        function Game_GetLocalPlayer() return {playerID=localPlayer} end
        ''')
        self.start();self.assertIsNotNone(self.marker());self.assertAlmostEqual(self.g.bank[11],.375*.25)

    def test_income_rate_formula_and_no_retroactive_tech_bonus_are_preserved(self):
        self.start();earned=self.g.bank[11]
        self.runlua('''
        for age=2,4 do
            upgrades['upgrade\\\\races\\\\common\\\\research\\\\economy\\\\upgrade_econ_resource_wood_harvest_rate_'..age]=true
            upgrades['upgrade\\\\races\\\\japanese\\\\research\\\\economy\\\\upgrade_econ_resource_wood_harvest_rate_'..age..'_kura_jpn']=true
        end
        upgrades['a743d7d1d7534cf78817e29d8ded7366:vn_upgrade_champa_rice_vit']=true
        ''')
        self.tick(.75);self.assertAlmostEqual(self.g.bank[11],earned+.375*.25)
        self.tick(1);self.assertAlmostEqual(self.g.bank[11],earned+.375*.25+.375*1.45*1.1*.25)


import test_paddy_wood as _historical

class SupervisionV10Compatibility(_historical.PaddyWoodTests):
    """Unchanged old assertions: 24 current checks and 3 frozen geometry contracts."""
    HISTORICAL_GEOMETRY = {
        'test_actual_caster_centre_not_squad_position_is_used',
        'test_adjacent_paddies_within_five_metres_reject_ambiguity',
        'test_pending_native_approach_earns_nothing_until_execution_at_five_metres',
    }

    def setUp(self):
        super().setUp()
        self.runlua('''
        RES_Resourcing=7;tags={}
        function UI_CreateTagForPosition(p,data)
            assert(p.native and data.DataTemplate=='TagArrowDataTemplate')
            local key=p.x..':'..p.z;assert(tags[key]==nil);tags[key]=data
        end
        function UI_DestroyTagForPosition(p)
            local key=p.x..':'..p.z;assert(tags[key]~=nil);tags[key]=nil
        end
        function Cmd_Move() error('native ability owns approach') end
        function Squad_SetPosition() error('no supervision teleport') end
        ''')
        if self._testMethodName in self.HISTORICAL_GEOMETRY:
            # User-authorized v10 center range replaces these v9 assumptions.
            # Preserve their assertions against the actual accepted v9 source;
            # current center/range/adjacency contracts are tested above.
            with zipfile.ZipFile(SNAP) as z:self.runlua(z.read(WOOD).decode())


import test_runtime_v9_paddy as _v9

class PaddyOwnershipV9Compatibility(_v9.PaddyV9):
    """All four v9 owner/replacement assertions against their original sources."""
    def setUp(self):
        super().setUp()
        self.runlua('''
        RES_Resourcing=7;tags={}
        function UI_CreateTagForPosition(p,data)
            assert(p.native and data.DataTemplate=='TagArrowDataTemplate')
            local key=p.x..':'..p.z;assert(tags[key]==nil);tags[key]=data
        end
        function UI_DestroyTagForPosition(p)
            local key=p.x..':'..p.z;assert(tags[key]~=nil);tags[key]=nil
        end
        ''')


class PaddyTuningV9Compatibility(_v9.PaddyTuningV9):
    """Current foundation walkability; frozen v9 five-metre supervision contract."""
    def test_native_supervise_distance_comparison_and_unique_target_radius(self):
        rel='assets/attrib/instances/abilities/vietnam/vn_buffalo_work_paddy_vit.xml'
        donor=ET.parse(ROOT/'work/vietnam_redesign/runtime_v9_20261023/paddy/official_supervise_building_target_chi.xml').getroot()
        with zipfile.ZipFile(SNAP) as z:
            accepted_v9=ET.fromstring(z.read(rel));accepted_scar=z.read(WOOD).decode()
        self.assertEqual(accepted_v9.find("group/float[@name='range']").get('value'),donor.find("group/float[@name='range']").get('value'))
        self.assertEqual(accepted_v9.find("group/bool[@name='use_simbox_to_simbox_range']").get('value'),'False')
        self.assertIn('local radiusSquared = 25',accepted_scar)

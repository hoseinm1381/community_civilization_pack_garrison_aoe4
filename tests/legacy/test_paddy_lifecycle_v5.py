"""Actual lifecycle ordering with mocked engine calls; no native-build claim."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX
from test_paddy_wood import PaddyWoodFixture


class PaddyLifecycleV5Tests(PaddyWoodFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        function Entity_GetHeading(e) return {x=e.hx or 0,y=0,z=e.hz or 1} end
        function Entity_GetBuildingProgress(e) assert(e.building,'building only');return e.progress or 1 end
        function Entity_ConvertBlueprint(e,bp)
            e.bp=bp;e.conversions=(e.conversions or 0)+1
            e.health=450;e.maximum=450;e.building=false;e.progress=0
        end
        MAT_Entity=1;MUT_Multiplication=2;mods={}
        function Player_OwnsEntity(p,e) return e.owner==p end
        function Modifier_Create(kind,name,usage,exclusive,value,arg)
            assert(name=='resource_entity_harvest_rate_food' and value==1.1)
            return {value=value}
        end
        function Modifier_ApplyToEntity(m,e,duration)
            assert(duration==0);m.entity=e;m.active=true;mods[#mods+1]=m;return m
        end
        function Modifier_Remove(m) assert(m.active);m.active=false end
        paddy.bp='a743d7d1d7534cf78817e29d8ded7366:vn_building_resource_farm2_chi'
        paddy.incomplete=true;paddy.progress=.5;paddy.health=270;paddy.maximum=450
        upgrades['a743d7d1d7534cf78817e29d8ded7366:vn_upgrade_champa_rice_vit']=true
        ''')
        for module in ['paddy_construction','paddy_food','lifecycle']:
            self.runlua((ROOT/f'assets/scar/vietnam/{module}.scar').read_text())
        # Keep the actual lifecycle ordering/group lifetime while isolating other
        # independently owned systems from this Paddy integration fixture.
        stubs=['VietnamTowerTraining_BeginTick','VietnamTowerTraining_EndTick',
               'VietnamPagodaBuffalo_Update','VietnamGarden_Update','VietnamLandmarks_Update',
               'VietnamTunnels_Update','VietnamRattanArmor_Update','VietnamSiegeResearch_Update',
               'VietnamScorchedEarth_Update','VietnamFoundries_Update','VietnamDynasty_Update',
               'VietnamHideouts_Update','VietnamTowerTraining_Update','VietnamTraps_Update',
               'VietnamTraps_Tick','VietnamFloodedCitadel_Update','VietnamTunnels_Step','VietnamTunnels_UpdateUI']
        for name in stubs:
            self.runlua(f'function {name}() end')
        self.runlua('VietnamLifecycleState.active=true;VietnamLifecycleState.civilizations[1]="vietnam"')

    def tick(self,t):
        self.runlua(f'now={t};VietnamLifecycle_Tick()')

    def test_native_completion_then_conversion_food_modifier_and_explicit_supervision_income(self):
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25)
        self.assertIsNone(self.g.paddy.conversions)
        self.assertEqual(len(self.g.mods),0);self.assertEqual(self.g.bank[11],0)
        self.runlua('paddy.incomplete=false;paddy.progress=1')
        self.tick(.5)
        self.assertEqual(self.g.paddy.bp,PREFIX+'vn_building_resource_farm_chi')
        self.assertEqual(self.g.paddy.conversions,1);self.assertEqual(self.g.paddy.health,270)
        self.assertEqual(len(self.g.mods),1)
        self.assertEqual(self.g.mods[1].entity.id,501)
        self.assertTrue(self.g.VietnamPaddyWood_IsPaddyTarget(self.g.paddy,11))
        self.runlua('assign(buffalo)');self.tick(.75);self.tick(1);self.tick(1)
        self.assertEqual(self.g.paddy.conversions,1);self.assertEqual(len(self.g.mods),1)
        self.assertAlmostEqual(self.g.bank[11],.375*1.10*.25)
        self.runlua('order(buffalo)');self.tick(1.25);self.tick(1.5)
        self.assertAlmostEqual(self.g.bank[11],.375*1.10*.25)

    def test_cancelled_or_destroyed_foundation_never_earns_or_becomes_food(self):
        for mutation in ['registry[501]=nil','paddy.dead=true','paddy.health=0']:
            with self.subTest(mutation=mutation):
                self.setUp();self.tick(0);self.runlua(mutation)
                self.runlua('paddy.incomplete=false;paddy.progress=1')
                self.tick(.25);self.runlua('assign(buffalo)');self.tick(.5);self.tick(.75)
                self.assertIsNone(self.g.paddy.conversions)
                self.assertEqual(len(self.g.mods),0);self.assertEqual(self.g.bank[11],0)

    def test_old_elephant_cannot_supervise_newly_converted_food_deposit(self):
        self.runlua("buffalo.bp='"+PREFIX+"vn_unit_war_elephant_1_vit';paddy.incomplete=false;paddy.progress=1")
        self.tick(0);self.runlua('assign(buffalo)');self.tick(.25);self.tick(.5)
        self.assertEqual(self.g.paddy.conversions,1);self.assertEqual(len(self.g.mods),1)
        self.assertEqual(self.g.bank[11],0)

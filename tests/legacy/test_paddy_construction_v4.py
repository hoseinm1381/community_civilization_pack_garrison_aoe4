"""Completed native foundation conversion; Lua fixtures are not native proof."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX


class PaddyConstructionTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Entity_GetPlayerOwner(e) assert(not e.world);return e.owner end
        function Entity_GetHeading(e) return {x=e.hx or 0,y=0,z=e.hz or 1} end
        function Entity_GetBuildingProgress(e) assert(e.building);return e.progress or 1 end
        function Entity_ConvertBlueprint(e,bp)
            e.bp=bp;e.conversions=(e.conversions or 0)+1
            e.health=450;e.maximum=450
        end
        paddy=building(501,'vn_building_resource_farm2_chi',7)
        paddy.health=270;paddy.maximum=450;paddy.z=12;paddy.hx=1;paddy.hz=0
        ''')
        self.runlua((ROOT/'assets/scar/vietnam/paddy_construction.scar').read_text())

    def update(self):
        self.runlua('VietnamPaddyConstruction_Update(PLAYERS[1],entities)')

    def test_completed_foundation_converts_once_without_healing_or_replacement(self):
        self.update();self.update()
        self.assertEqual(self.g.paddy.bp, PREFIX+'vn_building_resource_farm_chi')
        self.assertEqual(self.g.paddy.conversions,1)
        self.assertEqual(self.g.paddy.id,501)
        self.assertEqual(self.g.paddy.owner,11)
        self.assertEqual(self.g.paddy.x,7);self.assertEqual(self.g.paddy.z,12)
        self.assertEqual(self.g.paddy.hx,1);self.assertEqual(self.g.paddy.hz,0)
        self.assertEqual(self.g.paddy.health,270)
        self.assertTrue(self.has_log('VIETNAM_V5_PADDY_CONVERT'))

    def test_unfinished_cancelled_dead_invalid_world_foreign_and_nonbuilding_do_not_convert(self):
        for mutation in ['paddy.incomplete=true','paddy.progress=.999',
                         'paddy.dead=true','paddy.health=0','registry[501]=nil',
                         'paddy.world=true','paddy.owner=22','paddy.building=false',
                         'paddy.maximum=0',"paddy.bp='house'",
                         'function Player_IsAlive() return false end']:
            with self.subTest(mutation=mutation):
                self.setUp();self.runlua(mutation);self.update()
                self.assertIsNone(self.g.paddy.conversions)

    def test_completed_deposit_is_not_a_construction_target_or_progress_query(self):
        self.runlua("paddy.bp='"+PREFIX+"vn_building_resource_farm_chi';paddy.building=false")
        self.update();self.assertIsNone(self.g.paddy.conversions)

    def test_failed_conversion_does_not_restore_health_or_force_completion(self):
        self.runlua('function Entity_ConvertBlueprint(e,bp) e.health=200 end')
        self.update()
        self.assertEqual(self.g.paddy.health,200)
        self.assertTrue(self.has_log('VIETNAM_V5_PADDY_CONVERT_FAILED'))

    def test_only_foundation_uses_building_api_no_villager_command_polling(self):
        self.runlua('''
        vill=building(601,'vn_unit_villager_1_chi',0);vill.building=false
        function Squad_IsConstructing() error('no villager polling') end
        function Cmd_Stop() error('no stop orders') end
        ''')
        self.update();self.assertEqual(self.g.paddy.conversions,1)

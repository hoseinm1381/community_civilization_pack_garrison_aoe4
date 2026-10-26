"""Scoped Champa Rice modifier lifecycle; native harvest behavior is separate."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX


class PaddyFoodTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua('''
        MAT_Entity=1;MUT_Multiplication=2;mods={};researched={[11]=false,[22]=false}
        function Player_OwnsEntity(p,e) return e.owner==p end
        function Player_HasUpgrade(p,bp)
            assert(bp=='a743d7d1d7534cf78817e29d8ded7366:vn_upgrade_champa_rice_vit')
            return researched[p]
        end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Modifier_Create(kind,name,usage,exclusive,value,arg)
            assert(kind==MAT_Entity and name=='resource_entity_harvest_rate_food')
            assert(usage==MUT_Multiplication and value==1.1 and exclusive==false)
            return {value=value}
        end
        function Modifier_ApplyToEntity(m,e,duration)
            assert(duration==0);m.entity=e;m.active=true;mods[#mods+1]=m;return m
        end
        function Modifier_Remove(m) assert(m.active);m.active=false end
        function countMods() local n=0;for _,m in ipairs(mods) do if m.active then n=n+1 end end;return n end
        paddy=building(501,'vn_building_resource_farm_chi',0)
        ''')
        path=ROOT/'assets/scar/vietnam/paddy_food.scar'
        self.assertTrue(path.exists(),'Scoped Champa food controller not implemented')
        self.runlua(path.read_text())

    def tick(self,player=1,group='entities'):
        self.runlua(f'VietnamPaddyFood_Update(PLAYERS[{player}],{group})')

    def test_only_completed_researched_paddies_and_no_buffalo_required(self):
        self.tick();self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('researched[11]=true;paddy.incomplete=true')
        self.tick();self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('paddy.incomplete=false');self.tick()
        self.assertEqual(self.lua.eval('countMods()'),1)
        self.tick(group='{paddy,paddy}');self.assertEqual(self.lua.eval('#mods'),1)

    def test_remove_on_loss_research_loss_absence_and_cleanup(self):
        for mutation in ['paddy.dead=true','paddy.health=0','paddy.owner=22',
                         'paddy.incomplete=true','registry[501]=nil','researched[11]=false']:
            with self.subTest(mutation=mutation):
                self.runlua('VietnamPaddyFood_Cleanup();paddy.dead=false;paddy.health=100;paddy.owner=11;paddy.progress=1;paddy.incomplete=false;registry[501]=paddy;researched[11]=true')
                self.tick();self.assertEqual(self.lua.eval('countMods()'),1)
                self.runlua(mutation);self.tick();self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('researched[11]=true');self.tick();self.tick(group='{}')
        self.assertEqual(self.lua.eval('countMods()'),0)
        self.tick();self.runlua('VietnamPaddyFood_Cleanup();VietnamPaddyFood_Cleanup()')
        self.assertEqual(self.lua.eval('countMods()'),0)

    def test_capture_replaces_handle_even_new_owner_updates_first(self):
        self.runlua('researched[11]=true;researched[22]=true');self.tick()
        self.runlua('paddy.owner=22');self.tick(player=2)
        self.assertEqual(self.lua.eval('countMods()'),1)
        self.assertFalse(self.lua.eval('mods[1].active'))
        self.tick(player=1);self.assertEqual(self.lua.eval('countMods()'),1)

    def test_no_broad_villager_unrelated_building_or_eliminated_owner_bonus(self):
        self.runlua('researched[11]=true;paddy.bp="'+PREFIX+'vn_building_house_control_chi"')
        self.tick();self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('paddy.bp="'+PREFIX+'vn_building_resource_farm2_chi"');self.tick()
        self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('paddy.bp="'+PREFIX+'vn_building_resource_farm_chi"');self.tick()
        self.assertEqual(self.lua.eval('countMods()'),1)
        self.runlua('function Player_IsAlive() return false end');self.tick()
        self.assertEqual(self.lua.eval('countMods()'),0)

    def test_completed_resource_deposit_does_not_require_building_progress(self):
        self.runlua("researched[11]=true;paddy.progress=0;function Entity_GetBuildingProgress() error('Building-only API') end")
        self.tick()
        self.assertEqual(self.lua.eval('countMods()'),1)

    def test_pending_native_replacement_waits_for_construction_commit(self):
        self.runlua('researched[11]=true;VietnamPaddyConstructionState={replacements={[501]=true}}')
        self.tick();self.assertEqual(self.lua.eval('countMods()'),0)
        self.runlua('VietnamPaddyConstructionState.replacements[501]=nil');self.tick()
        self.assertEqual(self.lua.eval('countMods()'),1)

"""One Pillar's independent timer and shared queue cap; mocked, not native proof."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX


class PagodaBuffaloTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua(r'''
        PITEM_Spawn=1;PITEM_Upgrade=2;spawns={};spawnAttempts=0;failedSpawn=false;deadPlayers={}
        function Player_IsAlive(p) return not deadPlayers[p] end
        function BP_GetSquadBlueprint(n) return n end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_IsValid(id) for _,s in ipairs(squads) do if s.id==id then return true end end;return false end
        function SGroup_ForEachEx(g,callback,spawned,despawned)
            assert(spawned and despawned,'The cap must include living despawned squads')
            for i,s in ipairs(g) do callback(g,i,s) end
        end
        function EGroup_CountSpawned(g)
            local n=0;for _,e in ipairs(g) do if not e.despawned then n=n+1 end end;return n
        end
        function EGroup_GetSpawnedEntityAt(g,index)
            local n=0;for _,e in ipairs(g) do if not e.despawned then n=n+1;if n==index then return e end end end
            error('Bad spawned entity index')
        end
        function Entity_HasProductionQueue(e) return e.queue~=nil end
        function Entity_GetProductionQueueSize(e) return #e.queue end
        function Entity_GetProductionQueueItemType(e,i) assert(i>=0);return e.queue[i+1].kind end
        function Entity_GetProductionQueueItem(e,i) assert(i>=0);return e.queue[i+1].bp end
        function Entity_GetPlayerOwner(e) return e.owner end
        function addBuffalo(owner,dead,despawned)
            local s={id=3000+#squads,owner=owner or 11,bp='''+"'"+PREFIX+"vn_unit_water_buffalo_vit'"+r''',dead=dead,despawned=despawned}
            squads[#squads+1]=s;return s
        end
        function addQueuedBuffalo(e,count)
            e.queue=e.queue or {}
            for i=1,count do e.queue[#e.queue+1]={kind=PITEM_Spawn,bp='''+"'"+PREFIX+"vn_unit_water_buffalo_vit'"+r'''} end
        end
        function Entity_GetStateModelBool(e,n) return e.active~=false end
        function Modify_ProductionSpeed(e,n) e.speed=n;return {e=e} end
        MAT_Entity=1;MUT_Multiplication=1;modifierApplications=0
        function Modifier_Create(application,kind,usage,exclusive,value,target)
            assert(application==MAT_Entity and usage==MUT_Multiplication and not exclusive)
            return {kind=kind,value=value}
        end
        function Modifier_ApplyToEntity(mod,e,duration)
            assert(duration==0);modifierApplications=modifierApplications+1
            e.modifiers=e.modifiers or {};e.modifiers[mod.kind]=mod.value
            return {e=e,kind=mod.kind}
        end
        function Modifier_Remove(h)
            if h.kind then h.e.modifiers[h.kind]=nil else h.e.speed=nil end
        end
        function researchSeconds(e,base)
            return base/(e.speed or 1)/((e.modifiers or {}).entity_upgrade_production_speed_modifier or 1)
        end
        function buffaloSeconds(e)
            return 30/(e.speed or 1)/((e.modifiers or {}).spawn_production_speed_modifier or 1)
        end
        function Entity_CancelProductionQueueItem(e,i) table.remove(e.queue,i+1) end
        function Entity_QueueProductionItemByPBG(e,kind,bp)
            spawnAttempts=spawnAttempts+1
            if failedSpawn then return false end
            e.queue=e.queue or {};e.queue[#e.queue+1]={kind=kind,bp=bp};return true
        end
        ''')
        path=ROOT/'assets/scar/vietnam/pagoda_buffalo.scar'
        self.assertTrue(path.exists(),'One Pillar controller not implemented')
        self.runlua(path.read_text(encoding='utf-8'))
        self.runlua("pagoda=building(701,'vn_building_landmark_age1_vit_one_pilar_pagoda',0);VietnamPagodaBuffalo_Start({[1]='vietnam',[2]='vietnam',[3]='china'})")

    def tick(self, time, player=1, group='entities'):
        self.runlua(f'now={time};VietnamPagodaBuffalo_Update(PLAYERS[{player}],{group},now)')

    def test_queue_single_native_item_and_research_retained(self):
        self.runlua("pagoda.queue={{kind=PITEM_Upgrade,bp='research'}}")
        self.tick(0);self.tick(100)
        self.assertEqual(len(self.g.pagoda.queue),2)
        self.assertEqual(self.g.pagoda.queue[1].bp,'research')
        self.assertIsNone(self.g.pagoda.speed)
        self.assertAlmostEqual(self.lua.eval('buffaloSeconds(pagoda)'),75)
        self.assertEqual(self.lua.eval('researchSeconds(pagoda,30)'),30)
        self.assertEqual(self.lua.eval('researchSeconds(pagoda,45)'),45)
        self.assertEqual(self.g.modifierApplications,1)

    def test_foundation_and_inactive_landmark_do_not_queue(self):
        self.runlua('pagoda.incomplete=true');self.tick(0)
        self.assertIsNone(self.g.pagoda.queue)
        self.runlua('pagoda.incomplete=false;pagoda.active=false');self.tick(1)
        self.assertIsNone(self.g.pagoda.queue)
        self.runlua('pagoda.active=true');self.tick(2)
        self.assertEqual(len(self.g.pagoda.queue),1)

    def test_paid_queues_reserve_fifteenth_slot_and_two_sources_deduplicate(self):
        self.runlua("for i=1,13 do addBuffalo() end;producer=building(702,'ministry',10);addQueuedBuffalo(producer,1);second=building(703,'vn_building_landmark_age1_vit_one_pilar_pagoda',20)")
        self.tick(0,group='{pagoda,pagoda,producer,second}')
        self.assertEqual(len(self.g.pagoda.queue),1)
        self.assertIsNone(self.g.second.queue)
        self.tick(10)
        self.assertEqual(len(self.g.pagoda.queue),1)
        self.assertIsNone(self.g.second.queue)

    def test_cap_retry_and_queue_rejection(self):
        self.runlua('for i=1,15 do addBuffalo() end');self.tick(0)
        self.assertEqual(self.g.spawnAttempts,0)
        self.runlua('squads[1].dead=true;failedSpawn=true');self.tick(1)
        self.assertEqual(self.g.spawnAttempts,1)
        self.runlua('failedSpawn=false');self.tick(2)
        self.assertEqual(len(self.g.pagoda.queue),1)

    def test_killed_between_ticks_full_repair_and_research_preserved(self):
        self.runlua("pagoda.queue={{kind=PITEM_Upgrade,bp='research'}}")
        self.tick(0)
        self.runlua('VietnamPagodaBuffalo_OnKilled({victim=pagoda});pagoda.health=30')
        self.tick(.25)
        self.assertEqual(len(self.g.pagoda.queue),1)
        self.assertIsNone(self.g.pagoda.speed)
        self.assertIsNone(self.lua.eval('(pagoda.modifiers or {}).spawn_production_speed_modifier'))
        self.runlua('pagoda.health=100');self.tick(.5)
        self.assertEqual(len(self.g.pagoda.queue),2)

    def test_capture_and_cleanup_remove_modifiers(self):
        self.tick(0);self.runlua('pagoda.owner=22');self.tick(1)
        self.assertIsNone(self.g.pagoda.speed)
        self.tick(2,player=2)
        self.assertAlmostEqual(self.lua.eval('buffaloSeconds(pagoda)'),75)
        self.assertEqual(self.lua.eval('researchSeconds(pagoda,30)'),30)
        self.runlua('VietnamPagodaBuffalo_Cleanup();VietnamPagodaBuffalo_Cleanup()')
        self.assertIsNone(self.g.pagoda.speed)
        self.assertIsNone(self.lua.eval('(pagoda.modifiers or {}).spawn_production_speed_modifier'))

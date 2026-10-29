import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime


def load(lua, name):
    lua.execute((ROOT/'assets/scar/korea'/(name+'.scar')).read_text(encoding='utf-8-sig'))


class KoreanInitializationTests(unittest.TestCase):
    def setUp(self):
        base = __import__('test_persia_initialization').PersiaInitializationTests()
        base.setUp()
        self.lua = base.lua
        self.lua.execute('''
            function Player_GetRaceName() return env.otherRace and "sultanate" or "chinese_ha_01" end
            function Entity_IsAlive() return true end
            SGroup_CountSpawned=SGroup_Count
            SGroup_GetSpawnedSquadAt=SGroup_GetSquadAt
            Scar_AddInit=function() end
            entities[1].bp="building_town_center_capital_chi_ha_01"
            for i=1,6 do
                local name=i==6 and "unit_official_1_chi_ha_01" or "unit_villager_1_chi_ha_01"
                squads[i].bp=name; squads[i].entity.bp=name
            end
            squads[7].bp="unit_scout_1_chi"; squads[7].entity.bp="unit_scout_1_chi"
        ''')
        for name in ('catalog', 'core', 'blueprints', 'initialization'):
            load(self.lua, name)
        self.g = self.lua.globals()

    def apply(self):
        return self.g.KoreaInitialization_Apply(self.g.player)

    def test_five_villagers_and_official_become_six_villagers(self):
        self.assertEqual(self.apply(), (True, 'applied', True))
        self.assertEqual(self.g.env.mutations, 13)
        self.assertIn('kr_unit_villager_1_chi_ha_01', self.g.squads[6].entity.bp)
        self.assertEqual(self.g.squads[7].bp, 'unit_scout_1_chi')
        self.assertEqual(self.g.env.groups, 0)
        self.assertEqual(self.apply(), (False, 'already-applied', False))

    def test_legacy_six_villager_start_is_also_supported(self):
        self.lua.execute('squads[6].bp="unit_villager_1_chi_ha_01"; squads[6].entity.bp=squads[6].bp')
        self.assertEqual(self.apply(), (True, 'applied', True))

    def test_invalid_start_and_later_age_do_not_mutate(self):
        self.g.env.later = True
        self.assertEqual(self.apply(), (False, 'unsupported-age', False))
        self.g.env.later = False
        self.lua.execute('table.remove(squads,1)')
        self.assertEqual(self.apply(), (False, 'unsupported-starting-army', False))
        self.assertEqual(self.g.env.mutations, 0)

    def test_missing_blueprints_and_wrong_race_are_safe(self):
        self.g.env.missing = True
        self.assertEqual(self.apply(), (False, 'blueprints-unavailable', False))
        self.g.env.otherRace = True
        self.assertEqual(self.apply(), (False, 'ineligible-player', False))
        self.assertEqual(self.g.env.mutations, 0)

    def test_partial_engine_failure_is_reported_and_not_marked_applied(self):
        self.g.env.fail = True
        applied, reason, mutated = self.apply()
        self.assertFalse(applied)
        self.assertTrue(mutated)
        self.assertIn('conversion-error', reason)
        self.assertIsNone(self.g.KoreaInitializationState.applied[1])


class KoreanRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
            env={now=0,money={[1]=1000,[2]=1000},action={[1]=2,[2]=2},queue=true,
                paid=100,handles={},nextHandle=0,offers={},entities={},spawned=0}
            RT_Food=1;RT_Wood=2;RT_Gold=3;RT_Stone=4;RT_Merc_Byz=5;RT_Action=6
            MAT_Upgrade=1;MAT_Entity=2;MAT_EntityType=3;MAT_WeaponType=4;MAT_Weapon=5
            MUT_Multiplication=1;MUT_Addition=2;ITEM_REMOVED=0;ITEM_DEFAULT=1
            ST_ENTITY=1;ST_PLAYER=2;PITEM_Upgrade=1;PITEM_Spawn=2
            KoreaCatalog={ebps={},sbps={},upgrade={},abilities={},weapon={}}
            KoreaResearchCatalog={{ability="a",upgrade="u",foreign=true}}
            PLAYERS={{id=1,index=1,isHuman=true},{id=2,index=2,isHuman=true}}
            function Core_GetPlayersTableEntry(id) return PLAYERS[id] end
            function scartype(v) return type(v)=="table" and ST_ENTITY or ST_PLAYER end
            function World_GetGameTime() return env.now end
            function Player_IsAlive() return true end
            function Player_HasUpgrade() return false end
            function Player_GetResource(id,resource) return resource==RT_Action and env.action[id] or env.money[id] end
            function Player_SetResource(id,resource,n)
                if resource==RT_Action then env.action[id]=n else env.money[id]=n end
            end
            function Player_AddResource(id,resource,n) Player_SetResource(id,resource,Player_GetResource(id,resource)+n) end
            function Player_GetAbilityBPCost() return {merc_byz=env.paid,action=1} end
            function Player_SetAbilityAvailability(id,bp,value) env.offers[id..bp]=value end
            function Player_SetUpgradeAvailability() end
            function BP_GetName(bp) return bp end
            function BP_GetEntityBlueprint(bp) return bp end
            function BP_GetSquadBlueprint(bp) return bp end
            function BP_GetUpgradeBlueprint(bp) return bp end
            function BP_GetAbilityBlueprint(bp) return bp end
            function BP_GetWeaponBlueprint(bp) return bp end
            function Table_GetRandomItem(t) return t[1] end
            function Modifier_Create(app,property,usage,exclusive,value,target)
                return {app=app,property=property,usage=usage,value=value,target=target}
            end
            function Modifier_ApplyToPlayer(mod,id,duration)
                env.nextHandle=env.nextHandle+1
                mod.player=id;mod.active=true;mod.expires=duration>0 and env.now+duration or math.huge
                env.handles[env.nextHandle]=mod;return env.nextHandle
            end
            function Modifier_Remove(handle) env.handles[handle].active=false end
            function Entity_IsValid(id) return id~=999 end
            function Entity_GetID(e) return e.id end
            function Entity_FromID(id) return env.entities[id] end
            function Entity_IsAlive(e) return e.alive~=false end
            function World_OwnsEntity() return false end
            function Entity_GetPlayerOwner(e) return e.owner end
            function Entity_IsUnderConstruction(e) return e.constructing or false end
            function Entity_GetBuildingProgress() return 1 end
            function Entity_GetHealth() return 100 end
            function Entity_GetStateModelBool(e) return e.active~=false end
            function Entity_GetBlueprint(e) return e.bp end
            function Entity_GetPosition() return {x=0,y=0,z=0} end
            function Entity_QueueProductionItemByPBG() return env.queue end
            function Squad_CreateAndSpawnToward() env.spawned=env.spawned+1;return {} end
            function Misc_SetSquadSelectable() end
            function KoreaEffects_Upgrade() end
            function KoreaLandmarks_Research() end
            function KoreaLandmarks_Snapshot() end
            actor={id=100,owner=1};env.entities[100]=actor
        ''')
        for name in ('core', 'research_core', 'research'):
            load(self.lua, name)
        self.lua.execute('''
            p1={id=1,index=1,effects={},decrees={},landmarks={},stoneRewards=0,stoneResearch={}}
            p2={id=2,index=2,effects={},decrees={},landmarks={},stoneRewards=0,stoneResearch={}}
            KoreaState.players[1]=p1;KoreaState.order={1}
            KoreaResearch_Init(p1)
            function fire()
                env.money[1]=env.money[1]-env.paid;env.action[1]=env.action[1]-1
                KoreaResearch_Ability({executer=actor,ability="a"},p1)
            end
        ''')
        self.g = self.lua.globals()

    def test_native_payment_completion_rebates_effective_cost_once(self):
        self.g.p1.observatoryActive = True
        self.g.fire()
        context = self.lua.table_from({'executer': self.g.actor, 'upgrade': 'u'})
        self.g.KoreaResearch_Completed(context)
        self.g.KoreaResearch_Completed(context)
        self.assertEqual(self.g.env.money[1], 915)
        self.assertEqual(self.g.env.action[1], 1)

    def test_queue_failure_returns_paid_literature_and_allowance(self):
        self.g.env.queue = False
        self.g.fire()
        self.assertEqual(self.g.env.money[1], 1000)
        self.assertEqual(self.g.env.action[1], 2)

    def test_death_and_player_context_cancel_refund_once(self):
        self.g.fire()
        self.g.KoreaResearch_EntityLost(100)
        self.g.KoreaResearch_Canceled(self.lua.table_from({'executer': 1, 'upgrade': 'u'}))
        self.assertEqual(self.g.env.money[1], 1000)
        self.assertEqual(self.g.env.action[1], 2)

    def test_unselected_zhu_xi_does_not_receive_korean_events(self):
        load(self.lua, 'lifecycle')
        self.lua.execute('other={id=200,owner=2}')
        self.g.KoreaLifecycle_Ability(self.lua.table_from({'executer': self.g.other, 'ability': 'a'}))
        self.assertEqual(self.g.env.money[2], 1000)
        self.assertIsNone(self.g.KoreaState.players[2])

    def test_overlapping_decrees_remove_exact_handles_and_pause_independently(self):
        load(self.lua, 'effects')
        self.lua.execute('p1.landmarks.hall={};p2.landmarks.hall={}')
        self.g.KoreaEffects_Decree(self.g.p1, self.lua.table_from(['food']))
        self.g.env.now = 10
        self.g.KoreaEffects_Decree(self.g.p2, self.lua.table_from(['wood']))
        self.g.env.now = 20
        self.g.p1.landmarks.hall = None
        self.g.KoreaEffects_Tick(self.g.p1, 20)
        food = [h for h in self.g.env.handles.values() if h.property == 'resource_entity_harvest_rate_food']
        wood = [h for h in self.g.env.handles.values() if h.property == 'resource_entity_harvest_rate_wood']
        self.assertFalse(food[-1].active)
        self.assertTrue(wood[-1].active)
        self.g.p1.landmarks.hall = self.lua.table()
        self.g.env.now = 30
        self.g.KoreaEffects_Tick(self.g.p1, 30)
        food = [h for h in self.g.env.handles.values() if h.property == 'resource_entity_harvest_rate_food']
        self.assertEqual(len(food), 2)
        self.assertEqual(food[-1].value, 1.6)
        self.assertEqual(food[-1].expires, 60)
        self.g.env.now = 60
        self.g.KoreaEffects_Tick(self.g.p1, 60)
        self.assertEqual(len(self.g.p1.decrees), 0)
        self.assertTrue(wood[-1].active)

    def test_observatory_ruin_repair_and_guard_grants_are_idempotent(self):
        load(self.lua, 'landmarks')
        self.lua.execute('''
            function Korea_Entities(player,fn)
                for _,entity in ipairs(env.buildings) do fn(entity) end
            end
            env.buildings={{id=11,owner=1,bp=KoreaLandmarkNames.observatory},
                           {id=12,owner=1,bp=KoreaLandmarkNames.jinju}}
        ''')
        self.g.KoreaLandmarks_Snapshot(self.g.p1)
        self.assertTrue(self.g.p1.observatoryActive)
        self.assertEqual(self.g.p1.research.allowances, 4)
        self.assertEqual(self.g.env.spawned, 8)
        self.g.env.buildings[1].active = False
        self.g.env.buildings[2].active = False
        self.g.KoreaLandmarks_Snapshot(self.g.p1)
        self.assertFalse(self.g.p1.observatoryActive)
        self.g.env.buildings[1].active = True
        self.g.env.buildings[2].active = True
        self.g.KoreaLandmarks_Snapshot(self.g.p1)
        self.assertTrue(self.g.p1.observatoryActive)
        self.assertEqual(self.g.p1.research.allowances, 4)
        self.assertEqual(self.g.env.spawned, 8)

    def test_lifecycle_applies_private_caps_and_cleans_every_registered_resource(self):
        load(self.lua, 'lifecycle')
        self.lua.execute('''
            MAT_Player=6;CT_Vehicle=2;RT_Militia_HRE=7
            env.events={};env.rules={};env.ui=0
            function Player_GetMaxPopulationCap() return 8 end
            function Player_GetCurrentPopulationCap() return 4 end
            function Player_SetResource(id,resource,n)
                if resource==RT_Action then env.action[id]=n
                elseif resource==RT_Militia_HRE then env.militia=n
                else env.money[id]=n end
            end
            function Player_SetStateModelFloat() end
            function KoreaEffects_Start() end
            function KoreaEffects_Damage() end
            function KoreaLandmarks_Snapshot() end
            function Korea_Entities() end
            function KoreaUI_Create() env.ui=env.ui+1 end
            function KoreaUI_Cleanup() env.ui=env.ui-1 end
            function Rule_AddGlobalEvent(callback) env.events[callback]=true end
            function Rule_RemoveGlobalEvent(callback) env.events[callback]=nil end
            function Rule_AddInterval(callback) env.rules[callback]=true end
            function Rule_Remove(callback) env.rules[callback]=nil end
            KoreaInitializationState={applied={}}
            KoreaLifecycle_Start({[1]="korea",[2]="zhu_xi"})
            function count(t) local n=0;for _ in pairs(t) do n=n+1 end;return n end
        ''')
        self.assertEqual(self.g.count(self.g.env.events), 6)
        self.assertEqual(self.g.count(self.g.env.rules), 1)
        self.assertEqual(self.g.env.ui, 1)
        self.assertEqual(self.g.env.militia, 1)
        self.assertIsNone(self.g.KoreaState.players[2])
        self.assertEqual(self.g.env.money[2], 1000)
        caps = {h.property: h.value for h in self.g.env.handles.values() if h.app == 6}
        self.assertEqual(caps['vehicle_cap_player_modifier'], 95)
        self.assertEqual(caps['max_vehicle_cap_player_modifier'], 91)
        self.g.KoreaLifecycle_Cleanup()
        self.g.KoreaLifecycle_Cleanup()
        self.assertEqual(self.g.count(self.g.env.events), 0)
        self.assertEqual(self.g.count(self.g.env.rules), 0)
        self.assertEqual(self.g.env.ui, 0)
        self.assertTrue(all(not h.active for h in self.g.env.handles.values()))

    def test_two_hwacha_barrages_keep_independent_expiry_and_group_ownership(self):
        load(self.lua, 'effects')
        self.lua.execute('''
            KoreaState.debuffs={};KoreaState.barrages={}
            env.groups=0;env.stops={}
            function Modifier_ApplyToEntity(mod,e,duration) return Modifier_ApplyToPlayer(mod,e.owner,duration) end
            function SGroup_CreateUnique() env.groups=env.groups+1;return {} end
            function SGroup_Add(g,s) table.insert(g,s) end
            function SGroup_Destroy() env.groups=env.groups-1 end
            function Entity_GetSquad(e) return e end
            SCMD_Attack=23;SCMD_Stop=22
            function Squad_GetActiveCommand() return SCMD_Attack end
            function LocalCommand_SquadPos() end
            function LocalCommand_Squad(owner,g,command,queued) table.insert(env.stops,{owner,g[1].id}) end
            second={id=200,owner=2};env.entities[200]=second
        ''')
        target = self.lua.table_from({'x': 1, 'y': 0, 'z': 1})
        self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.actor, 'target': target}), self.g.p1, False)
        self.g.env.now = 3
        self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.second, 'target': target}), self.g.p2, False)
        self.g.KoreaEffects_Timers(7)
        self.assertIsNone(self.g.KoreaState.barrages[100])
        self.assertIsNotNone(self.g.KoreaState.barrages[200])
        self.assertEqual(self.g.env.stops[1][1], 1)
        self.g.KoreaEffects_Timers(10)
        self.assertIsNone(self.g.KoreaState.barrages[200])
        self.assertEqual(self.g.env.stops[2][1], 2)
        self.assertEqual(self.g.env.groups, 0)


if __name__ == '__main__':
    unittest.main()

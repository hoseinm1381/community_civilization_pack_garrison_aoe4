import json
import sys
import unittest
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'.tools/python'))
from lupa.lua51 import LuaRuntime
import test_korea_runtime as runtime


class ConditionalLoadingTests(unittest.TestCase):
    def environment(self, roster):
        lua = LuaRuntime(unpack_returned_tuples=True)
        lua.execute('''
            callbacks={};loaded={}
            function Scar_AddInit(f) table.insert(callbacks,f) end
            function Scar_PrecachePrematchResource(name) table.insert(loaded,name) end
            function BP_GetEntityBlueprint(name) return name end
            function BP_GetSquadBlueprint(name) return name end
            function EBP_Exists() return true end
            function SBP_Exists() return true end
            function Player_GetRaceName(id) return id end
            function Game_GetLocalPlayer() error("Local UI must not select loading policy") end
            print=function() end
        ''')
        for file in ('ccp/loading.scar', 'vietnam/prematch_precache.scar',
                     'persia/blueprints.scar', 'korea/blueprints.scar'):
            lua.execute((ROOT/'assets/scar'/file).read_text(encoding='utf-8-sig'))
        # Official core supplies PLAYERS before Scar_AddInit callbacks run.
        lua.execute('PLAYERS='+roster+'; for _,callback in ipairs(callbacks) do callback() end')
        return lua, list(lua.globals().loaded.values())

    def test_unrelated_humans_and_native_ai_load_no_custom_family(self):
        _, loaded = self.environment('{{id="english",isHuman=true},{id="chinese",isHuman=false},'
                                     '{id="sultanate",isHuman=false},{id="chinese_ha_01",isHuman=false}}')
        self.assertEqual(loaded, [])

    def test_each_human_pair_loads_only_its_possible_family(self):
        for race, prefix in [('chinese','vn_'), ('sultanate','ps_'), ('chinese_ha_01','kr_')]:
            with self.subTest(race=race):
                _, loaded = self.environment('{{id="'+race+'",isHuman=true}}')
                private = [n.split(':')[-1] for n in loaded if ':' in n]
                self.assertTrue(private)
                self.assertTrue(all(n.startswith(prefix) for n in private))
                self.assertEqual(len([n for n in loaded if ':' not in n]), 15)

    def test_all_pairs_share_stock_dependencies_once_on_every_client(self):
        roster = '{{id="chinese",isHuman=true},{id="sultanate",isHuman=true},{id="chinese_ha_01",isHuman=true}}'
        _, a = self.environment(roster)
        _, b = self.environment(roster)
        self.assertEqual(a, b)
        self.assertEqual(a.count('projectile_arrow'), 1)
        self.assertEqual({n.split(':')[-1][:3] for n in a if ':' in n}, {'vn_', 'ps_', 'kr_'})

    def test_early_or_incomplete_roster_uses_conservative_full_loading(self):
        for roster in ('nil', '{}', '{{id="english"}}'):
            _, loaded = self.environment(roster)
            self.assertEqual({n.split(':')[-1][:3] for n in loaded if ':' in n}, {'vn_', 'ps_', 'kr_'})

    def test_rdo_cannot_bypass_roster_gates(self):
        root = E.parse(ROOT/'assets/scar/winconditions/VietnamMode.rdo').getroot()
        precache = [x for x in root.iter('DataObject') if x.get('Type') == 'PrecacheList']
        self.assertEqual(len(precache), 1)
        self.assertEqual(precache[0].get('Id'), '12379813733990400066')
        self.assertEqual(len(precache[0].find("DataProperty[@Name='m_precacheItems']")), 0)
        self.assertFalse(any(x.get('Type') in ('EntityPrecacheItem','SquadPrecacheItem') for x in root.iter('DataObject')))


class KoreaNativeContractRepairs(unittest.TestCase):
    def setUp(self):
        base = runtime.KoreanRuntimeTests()
        base.setUp()
        self.lua, self.g = base.lua, base.lua.globals()

    def test_literature_cap_and_byzantine_presentation_are_preserved(self):
        sys.path.insert(0, str(ROOT/'tools'))
        from korea_resource_contract import verify
        self.assertTrue(verify(ROOT))
        resource = E.parse(ROOT/'assets/attrib/instances/resource_type_info/merc_byz.xml').getroot()
        ui = resource.find("group/group[@name='ui']")
        self.assertEqual(ui.find("file[@name='icon_primary']").get('value'), 'resources\\resource_olive_oil')
        self.assertEqual(ui.find("locstring[@name='name']").get('value'), '11244678')
        races = [x.get('value') for x in ui.iter('instance_reference') if x.get('name') == 'race']
        self.assertEqual(races, ['racebps\\byzantine_ha_mac', 'racebps\\chinese_ha_01'])

    def test_seowon_generation_enters_native_storage_and_pauses_on_ruin(self):
        cap = E.parse(ROOT/'assets/attrib/instances/army/standard_mode/normal_chinese_ha_01.xml').getroot()
        self.g.nativeCap = float(cap.find("group/enum_table[@name='resource_max_cap']/float[@name='merc_byz']").get('value'))
        runtime.load(self.lua, 'economy')
        self.lua.execute('''
            env.money[1]=0;env.money[2]=0;env.gold=0;env.groups=0;env.free=0
            p1.seowons={};p1.academyRewards={};p1.dropoffs={}
            p1.nextAcademy=0;p1.nextHangul=0;p1.nextWater=0
            academy={id=300,owner=1,bp="building_landmark_age1_meditation_gardens_control_chi_ha_01"}
            env.entities[300]=academy
            function Korea_Entities(p,callback) callback(academy) end
            function Korea_Squads(p,callback) callback({official=true},{id=301}) end
            function Squad_IsOfType(s,kind) return kind=="official" and s.official or false end
            function Entity_IsBuilding() return true end
            function Entity_IsEBPOfType(bp,kind) return bp==kind end
            function World_DistancePointToPoint() return 0 end
            function EGroup_CreateUnique() env.groups=env.groups+1;return {} end
            function EGroup_Destroy() env.groups=env.groups-1 end
            function World_GetNeutralEntitiesNearPoint(g)
                g[1]={id=400,bp="tree"};g[2]={id=401,bp="tree"}
                g[3]={id=402,bp="forage_bush"};g[4]={id=403,bp="gold"}
            end
            function EGroup_Count(g) return #g end
            function EGroup_GetEntityAt(g,i) return g[i] end
            function Entity_SetStateModelFloat() end
            function Entity_QueueProductionItemByPBG() env.free=env.free+1;return true end
            function Player_AddResource(id,kind,n)
                if kind==RT_Merc_Byz then env.money[id]=math.min(nativeCap,env.money[id]+n)
                elseif kind==RT_Gold then env.gold=env.gold+n end
            end
            function Korea_HasUpgrade(p,name) return env.hangul or false end
            KoreaEconomy_Tick(p1,0)
        ''')
        self.assertAlmostEqual(self.g.env.money[1], 8.15*1.25)
        self.assertEqual(self.g.env.money[2], 0)
        self.assertEqual(self.g.env.free, 1)
        self.g.env.hangul = True
        self.g.KoreaEconomy_Tick(self.g.p1, 6)
        self.assertEqual(self.g.env.gold, 2)
        self.g.KoreaEconomy_Tick(self.g.p1, 15)
        self.assertAlmostEqual(self.g.env.money[1], 8.15*(1.25+1.4))
        saved = self.g.env.money[1]
        self.g.academy.alive = False
        self.g.KoreaEconomy_Tick(self.g.p1, 30)
        self.assertEqual(self.g.env.money[1], saved)
        self.g.academy.alive = True
        self.g.KoreaEconomy_Tick(self.g.p1, 45)
        self.assertAlmostEqual(self.g.env.money[1], saved+8.15*1.4)
        self.assertEqual(self.g.env.free, 1)
        self.assertEqual(self.g.env.groups, 0)

    def test_observatory_retains_four_unspent_choices_with_stock_token_cap(self):
        self.lua.execute('''
            MAT_Player=6;env.actionCap=2
            local create=Modifier_Create
            function Modifier_Create(app,property,...)
                if property=="resource_cap_action_player_modifier" then
                    error("Could not find modifier in code")
                end
                return create(app,property,...)
            end
            local set=Player_SetResource
            function Player_SetResource(id,kind,n)
                if kind==RT_Action then n=math.min(env.actionCap,n) end
                set(id,kind,n)
            end
            KoreaResearch_Observatory(p1);KoreaResearch_Observatory(p1)
        ''')
        self.assertEqual(self.g.env.actionCap, 2)
        self.assertEqual(self.g.env.action[1], 2)
        self.assertEqual(self.g.p1.research.allowances, 4)
        self.assertEqual(self.g.env.action[2], 2)

    def barrage_environment(self):
        runtime.load(self.lua, 'effects')
        self.lua.execute('''
            CMD_AttackForced=20;CMD_Stop=21;SCMD_Stop=22;SCMD_Attack=23
            KoreaState.debuffs={};KoreaState.barrages={};env.groups=0;env.positions={};env.stops={}
            function Modifier_ApplyToEntity(mod,e,duration) return Modifier_ApplyToPlayer(mod,e.owner,duration) end
            function EGroup_CreateUnique() env.groups=env.groups+1;return {} end
            function EGroup_Add(g,e) table.insert(g,e) end
            function EGroup_Destroy() env.groups=env.groups-1 end
            SGroup_CreateUnique=EGroup_CreateUnique;SGroup_Add=EGroup_Add;SGroup_Destroy=EGroup_Destroy
            function Entity_GetSquad(e) return e end
            function Entity_GetActiveCommand(e) return e.command or CMD_AttackForced end
            function Squad_GetActiveCommand(s) return s.command or SCMD_Attack end
            function LocalCommand_EntityPos(owner,g,command,target) table.insert(env.positions,target) end
            LocalCommand_SquadPos=LocalCommand_EntityPos
            function LocalCommand_Entity(owner,g,command) table.insert(env.stops,{owner,g[1].id,command}) end
            LocalCommand_Squad=LocalCommand_Entity
            function Prox_GetRandomPosition() error("Barrage must never retarget randomly") end
            second={id=200,owner=2};env.entities[200]=second
        ''')

    def test_keep_stops_once_without_random_retarget_and_hwacha_is_independent(self):
        self.barrage_environment()
        target = self.lua.table_from({'x': 50, 'y': 0, 'z': 50})
        self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.actor,'target': target}), self.g.p1, True)
        self.g.env.now = 3
        self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.second,'target': target}), self.g.p2, False)
        self.g.KoreaEffects_Timers(6)
        self.assertEqual(len(self.g.env.positions), 2)
        self.assertEqual(len(self.g.env.stops), 1)
        self.assertEqual(self.g.env.stops[1][3], self.g.CMD_Stop)
        self.g.KoreaEffects_Timers(7)
        self.assertIsNone(self.g.KoreaState.barrages[100])
        self.assertIsNotNone(self.g.KoreaState.barrages[200])
        self.assertEqual(len(self.g.env.stops), 1)
        keep_handles = [h for h in self.g.env.handles.values() if h.app == self.g.MAT_Weapon and h.player == 1]
        self.assertEqual(len(keep_handles), 2)
        self.assertTrue(all(not h.active for h in keep_handles))
        self.g.KoreaEffects_Timers(10)
        self.assertEqual(self.g.env.stops[2][3], self.g.SCMD_Stop)
        self.assertEqual(self.g.env.groups, 0)

    def test_destroyed_captured_and_ruined_barrages_release_their_handles(self):
        for state in ('dead','captured','ruined'):
            with self.subTest(state=state):
                self.setUp()
                self.barrage_environment()
                target = self.lua.table_from({'x': 5,'y': 0,'z': 5})
                self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.actor,'target': target}), self.g.p1, True)
                if state == 'dead': self.g.actor.alive = False
                elif state == 'captured': self.g.actor.owner = 2
                else: self.g.actor.active = False
                self.g.KoreaEffects_Timers(1)
                self.assertIsNone(self.g.KoreaState.barrages[100])
                self.assertTrue(all(not h.active for h in self.g.env.handles.values() if h.app == self.g.MAT_Weapon))
                if state in ('dead','captured'): self.assertEqual(len(self.g.env.stops), 0)
                self.assertEqual(self.g.env.groups, 0)

    def test_expiry_does_not_replace_a_new_movement_order(self):
        self.barrage_environment()
        target = self.lua.table_from({'x': 5,'y': 0,'z': 5})
        self.g.KoreaEffects_Barrage(self.lua.table_from({'executer': self.g.actor,'target': target}), self.g.p1, False)
        self.g.actor.command = 999  # A new movement order has superseded attack.
        self.g.KoreaEffects_Timers(7)
        self.assertEqual(len(self.g.env.stops), 0)
        self.assertIsNone(self.g.KoreaState.barrages[100])
        self.assertEqual(self.g.env.groups, 0)


if __name__ == '__main__':
    unittest.main()

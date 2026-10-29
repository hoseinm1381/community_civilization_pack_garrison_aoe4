import json
import sys
import unittest
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime


def load(lua, name):
    lua.execute((ROOT / 'assets/scar/korea' / (name + '.scar')).read_text(encoding='utf-8-sig'))


class ResearchPolicyTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        load(self.lua, 'research_core')
        self.g = self.lua.globals()
        self.core = self.g.KoreaResearchCore
        self.state = self.core.New()

    def test_offers_are_distinct_and_observatory_grants_once(self):
        pool = self.lua.table_from(list('abcdefghij'))
        pick = self.lua.eval('function(n) return n end')
        first = self.core.Offer(self.state, pool, 4, pick)
        extra = self.core.Observatory(self.state, pool, pick)
        self.assertEqual(len(first), 4)
        self.assertEqual(len(extra), 4)
        self.assertEqual(len(set(self.state.offers.values())), 8)
        self.assertEqual(self.state.allowances, 4)
        self.assertEqual(len(self.core.Observatory(self.state, pool, pick)), 0)
        self.assertEqual(self.state.allowances, 4)

    def test_small_offer_pool_has_no_nil_or_duplicate(self):
        self.core.Offer(self.state, self.lua.table_from(['a', 'b']), 4, self.lua.eval('function() return 1 end'))
        self.assertEqual(len(self.state.offers), 2)

    def begin(self, amount=200, foreign=True):
        return self.core.Begin(self.state, 'u', self.lua.table_from({'merc_byz': amount, 'action': int(foreign)}), foreign, 99, 'ability')

    def test_completion_refunds_effective_paid_cost_once(self):
        self.assertTrue(self.begin(150))
        costs, transaction = self.core.Settle(self.state, 'u', True, True)
        self.assertEqual(costs.merc_byz, 22.5)
        self.assertIsNone(costs.action)
        self.assertEqual(self.state.allowances, 1)
        self.assertIsNone(self.core.Settle(self.state, 'u', True, True))
        self.assertFalse(self.begin())

    def test_cancel_refunds_once_and_restores_allowance(self):
        self.begin()
        costs, _ = self.core.Settle(self.state, 'u', False, False)
        self.assertEqual(costs.merc_byz, 200)
        self.assertEqual(costs.action, 1)
        self.assertEqual(self.state.allowances, 2)
        self.assertIsNone(self.core.Settle(self.state, 'u', False, False))
        self.assertTrue(self.begin())

    def test_no_rebate_for_free_research_or_ruined_observatory(self):
        self.begin(0)
        costs, _ = self.core.Settle(self.state, 'u', True, True)
        self.assertEqual(costs.merc_byz, 0)
        state = self.core.New()
        self.core.Begin(state, 'v', self.lua.table_from({'merc_byz': 300}), False, 10, 'a')
        costs, _ = self.core.Settle(state, 'v', True, False)
        self.assertEqual(costs.merc_byz, 0)

    def test_players_and_pending_research_are_independent(self):
        second = self.core.New()
        self.begin()
        self.assertFalse(self.begin())
        self.assertTrue(self.core.Begin(second, 'u', self.lua.table_from({'merc_byz': 500}), True, 2, 'a'))
        self.core.Settle(self.state, 'u', False, False)
        self.assertEqual(second.pending.u.paid.merc_byz, 500)
        self.assertEqual(second.allowances, 1)

    def test_income_preserves_proximity_bonus_and_defense_values(self):
        self.assertEqual(self.core.SeowonIncome(10, 2, False, 2, 1), 19)
        self.assertEqual(self.core.SeowonIncome(10, 2, True, 2, 1), 22)


class ThreePairSelectionTests(unittest.TestCase):
    def setUp(self):
        base = __import__('test_persia_mode').ModePairTests()
        base.setUp()
        self.lua = base.lua
        self.lua.execute('''
            PLAYERS={{id=11,index=1,isHuman=true},{id=22,index=2,isHuman=true},
                     {id=44,index=3,isHuman=true},{id=33,index=4,isHuman=false}}
            function Player_GetRaceName(id)
                if id==11 then return "chinese" elseif id==22 then return "sultanate" else return "chinese_ha_01" end
            end
            env.kr=0
            function KoreaInitialization_Apply()
                env.kr=env.kr+1
                if env.koreaFail then return false,"injected",env.partial end
                return true,"applied",true
            end
        ''')
        self.g = self.lua.globals()

    def choose(self, korea='korea'):
        self.g.VietnamMode_NetChoose(11, 'vietnam')
        self.g.VietnamMode_NetChoose(22, 'persia')
        self.g.VietnamMode_NetChoose(44, korea)
        self.g.VietnamMode_Tick()

    def test_three_pairs_resolve_together_and_keep_ai_original(self):
        self.g.VietnamMode_OnInit()
        self.assertEqual(self.g.VietnamModeState.selection.deadline, 30)
        self.assertIsNone(self.g.VietnamModeState.selection.players[4])
        self.choose()
        self.assertEqual(self.g.env.vn, 1)
        self.assertEqual(self.g.env.ps, 1)
        self.assertEqual(self.g.env.kr, 1)
        self.assertEqual(self.g.env.kcivs[3], 'korea')
        self.assertFalse(self.g.VietnamModeState.held)
        self.assertTrue(self.g.env.ai[33])

    def test_timeout_and_explicit_original_keep_zhu_xi(self):
        self.g.VietnamMode_OnInit()
        self.g.env.clock = 30
        self.g.VietnamMode_Tick()
        self.assertEqual(self.g.VietnamModeState.civilizations[3], 'zhu_xi')
        self.assertEqual(self.g.env.kr, 0)

    def test_korea_missing_does_not_disable_other_pairs(self):
        self.lua.execute('KoreaBlueprints_Available=function() return false end')
        self.g.VietnamMode_OnInit()
        self.assertIsNone(self.g.VietnamModeState.selection.players[3])
        self.assertIsNotNone(self.g.VietnamModeState.selection.players[1])
        self.assertIsNotNone(self.g.VietnamModeState.selection.players[2])

    def test_wrong_pair_ai_and_repeated_messages_are_rejected(self):
        self.g.VietnamMode_OnInit()
        self.g.VietnamMode_NetChoose(44, 'persia')
        self.g.VietnamMode_NetChoose(33, 'korea')
        self.assertIsNone(self.g.VietnamModeState.selection.players[3].choice)
        self.choose('zhu_xi')
        self.g.VietnamMode_NetChoose(44, 'korea')
        self.assertEqual(self.g.env.kr, 0)

    def test_preflight_and_partial_failure_are_distinguished(self):
        self.g.VietnamMode_OnInit()
        self.g.env.koreaFail = True
        self.choose()
        self.assertEqual(self.g.VietnamModeState.civilizations[3], 'zhu_xi')
        self.assertFalse(self.g.VietnamModeState.held)
        self.assertIsNone(self.g.env.network['VietnamMode_NetChoose'])

    def test_disconnect_does_not_convert_dropped_player(self):
        self.g.VietnamMode_OnInit()
        self.g.VietnamSelectionCore.Drop(self.g.VietnamModeState.selection, 3)
        self.choose()
        self.assertEqual(self.g.env.kr, 0)

    def test_partial_korea_conversion_never_claims_unchanged_zhu_xi(self):
        self.g.VietnamMode_OnInit()
        self.g.env.koreaFail = True
        self.g.env.partial = True
        self.choose()
        self.assertEqual(self.g.VietnamModeState.civilizations[3], 'initialization_failed')
        self.assertFalse(self.g.VietnamModeState.held)
        self.assertTrue(self.g.env.ai[33])

    def test_all_korean_initializers_run_once_after_successful_selection(self):
        self.g.VietnamMode_OnInit()
        self.choose()
        self.g.VietnamMode_Tick()
        self.g.VietnamMode_NetChoose(44, 'korea')
        self.assertEqual(self.g.env.kr, 1)

    def test_two_korean_humans_resolve_in_the_shared_window(self):
        self.lua.execute('table.insert(PLAYERS,{id=55,index=5,isHuman=true})')
        self.g.VietnamMode_OnInit()
        self.choose()
        self.assertEqual(self.g.env.kr, 0, 'Resolution waits for the remaining human')
        self.g.VietnamMode_NetChoose(55, 'korea')
        self.g.VietnamMode_Tick()
        self.assertEqual(self.g.env.kr, 2)
        self.assertEqual(self.g.env.kcivs[3], 'korea')
        self.assertEqual(self.g.env.kcivs[5], 'korea')


class KoreaSourceTests(unittest.TestCase):
    def test_private_data_and_only_approved_shared_resource_exceptions(self):
        data = json.loads((ROOT/'docs/korea-import.json').read_text())
        self.assertEqual(len(data['instances']), 378)
        self.assertEqual(data['research_abilities'], 91)
        self.assertEqual(len(set(r['pbg_id'] for r in data['instances'])), 378)
        for row in data['instances']:
            self.assertIn('\\korea\\kr_', row['private'])
        sys.path.insert(0, str(ROOT/'tools'))
        from korea_resource_contract import verify
        self.assertTrue(verify(ROOT))

    def test_all_korean_scar_parses_in_lua51(self):
        lua = LuaRuntime(unpack_returned_tuples=True)
        compile_ = lua.eval('function(code,name) local f,err=loadstring(code,name); return f~=nil,err end')
        for path in (ROOT/'assets/scar/korea').glob('*.scar'):
            ok, error = compile_(path.read_text(encoding='utf-8-sig'), str(path))
            self.assertTrue(ok, error)

    def test_official_observers_are_never_filtered_or_destroyed(self):
        code = (ROOT/'assets/scar/korea/core.scar').read_text()
        function = code.split('function Korea_Squads')[1].split('function Korea_HasUpgrade')[0]
        self.assertNotIn('SGroup_Filter(', function)
        self.assertNotIn('SGroup_Destroy(', function)


if __name__ == '__main__':
    unittest.main()

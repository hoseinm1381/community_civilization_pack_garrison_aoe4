"""Regress the reported inflated build times and native Observatory failure."""
import json
import sys
import unittest
import xml.etree.ElementTree as E
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from korea_resource_contract import semantic_digest
import test_korea_runtime as runtime


class ConstructionRepairTests(unittest.TestCase):
    def test_only_construction_seconds_change_in_all_27_definitions(self):
        rows=json.loads((ROOT/'docs/korea-construction.json').read_text())['changes']
        self.assertEqual(len(rows),27)
        for row in rows:
            with self.subTest(blueprint=row['blueprint']):
                tree=E.parse(ROOT/row['file']).getroot()
                node=tree.find(row['xpath'])
                self.assertEqual(node.get('value'),row['after'])
                node.set('value',row['before'])
                self.assertEqual(semantic_digest(tree),row['before_semantic_sha256'])

    def test_landmark_roles_and_custom_academy_times(self):
        base=ROOT/'assets/attrib/instances/ebps/korea'
        expected={
            'building_landmark_age1_prefecture_chi_ha_01':190,
            'building_landmark_age2_shaolin_temple_control_chi_ha_01':220,
            'building_landmark_age2_white_deer_grotto_control_chi_ha_01':220,
            'building_landmark_age3_library_chi_ha_01':250,
            'building_landmark_age3_temple_of_the_sun_control_chi_ha_01':250,
            'building_landmark_age1_meditation_gardens_control_chi_ha_01_main':190,
            'building_landmark_age1_meditation_gardens_control_chi_ha_01':30,
            'building_dynasty_pagoda_control_chi_ha_01':30}
        for name,seconds in expected.items():
            tree=E.parse(base/('kr_'+name+'.xml')).getroot()
            self.assertEqual(float(tree.find(".//group[@name='time_cost']/float[@name='time_seconds']").get('value')),seconds,name)


class StockCappedAllowanceTests(unittest.TestCase):
    def setUp(self):
        env=runtime.KoreanRuntimeTests();env.setUp()
        self.lua,self.g=env.lua,env.lua.globals()
        self.lua.execute('''
            local set=Player_SetResource
            function Player_SetResource(id,kind,n)
                if kind==RT_Action then n=math.min(2,n) end
                set(id,kind,n)
            end
            -- Reproduce the engine rejection instead of accepting every name.
            local create=Modifier_Create
            function Modifier_Create(app,property,...)
                if property=="resource_cap_action_player_modifier" then
                    error("Could not find modifier in code")
                end
                return create(app,property,...)
            end
            KoreaResearchCatalog={}
            for i=1,10 do
                table.insert(KoreaResearchCatalog,{ability="a"..i,upgrade="u"..i,foreign=true})
            end
            KoreaForeignPool={};KoreaResearchRoutes={}
            KoreaResearch_Init(p1);KoreaResearch_Init(p2)
            function buy(p,n)
                if env.action[p.id]<1 then return false end
                env.action[p.id]=env.action[p.id]-1
                env.money[p.id]=env.money[p.id]-env.paid
                local e={id=100+p.id,owner=p.id};env.entities[e.id]=e
                KoreaResearch_Ability({executer=e,ability="a"..n},p)
                return true
            end
        ''')

    def test_actual_previous_observatory_function_reproduces_engine_rejection(self):
        self.lua.execute((ROOT/'tests/fixtures/korea/observatory_before_repair.scar').read_text())
        with self.assertRaisesRegex(Exception,'Could not find modifier in code'):
            self.g.KoreaResearch_Observatory(self.g.p1)

    def test_four_distinct_purchases_can_be_pending_and_fifth_is_blocked(self):
        self.g.KoreaResearch_Observatory(self.g.p1)
        self.g.KoreaResearch_Observatory(self.g.p1)
        self.assertEqual(self.g.p1.research.allowances,4)
        for i in range(1,5):
            self.assertTrue(self.g.buy(self.g.p1,i))
            self.assertEqual(self.g.p1.research.allowances,4-i)
            self.assertEqual(self.g.env.action[1],min(2,4-i))
        self.assertFalse(self.g.buy(self.g.p1,5))
        self.assertEqual(self.g.env.money[1],600)
        self.assertEqual(self.g.p2.research.allowances,2)
        self.assertEqual(self.g.env.action[2],2)

    def test_cancellation_returns_one_choice_and_repair_never_repeats_reward(self):
        self.g.KoreaResearch_Observatory(self.g.p1)
        self.g.buy(self.g.p1,1)
        self.g.KoreaResearch_Settle(self.g.p1,'u1',False)
        self.g.KoreaResearch_Settle(self.g.p1,'u1',False)
        self.g.KoreaResearch_Observatory(self.g.p1)
        self.assertEqual(self.g.p1.research.allowances,4)
        self.assertEqual(self.g.env.money[1],1000)
        for i in range(1,5):
            self.assertTrue(self.g.buy(self.g.p1,i))
        self.assertFalse(self.g.buy(self.g.p1,5))

    def test_two_korean_players_keep_independent_entitlements(self):
        self.g.KoreaResearch_Observatory(self.g.p1)
        self.g.buy(self.g.p1,1)
        self.g.buy(self.g.p2,1)
        self.g.KoreaResearch_Observatory(self.g.p2)
        self.assertEqual(self.g.p1.research.allowances,3)
        self.assertEqual(self.g.p2.research.allowances,3)
        self.g.buy(self.g.p1,2)
        self.assertEqual(self.g.p2.research.allowances,3)


if __name__=='__main__':unittest.main()

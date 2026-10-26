"""Conversion/receiver regressions. Lua fixtures do not prove native stealth."""
import unittest
from test_engine_adapter import FIXTURE, ROOT, LuaRuntime


class StartingStealthTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute(FIXTURE)
        self.lua.execute('''
        function BP_GetAbilityBlueprint(n) return n end
        function Entity_HasAbility(e,a) return e.abilities and e.abilities[a]==true or false end
        function Entity_AddAbility(e,a)
          assert(e.squad.bp==privateVillager, 'receiver must follow BOTH conversions')
          e.abilities=e.abilities or {};e.abilities[a]=true;e.adds=(e.adds or 0)+1
        end
        function Entity_SetStateModelBool(e,k,v) e.flags=e.flags or {};e.flags[k]=v end
        privateVillager='a743d7d1d7534cf78817e29d8ded7366:vn_unit_villager_1_chi'
        stealth='a743d7d1d7534cf78817e29d8ded7366:vn_activate_stealth_forvills_vit'
        squads={};starting={}
        for i=1,6 do
          local e={id=400+i,owner=11,bp='unit_villager_1_chi'}
          local s={owner=11,bp='unit_villager_1_chi',entity=e};e.squad=s
          entityRegistry[e.id]=e;squads[#squads+1]=s;starting[i]=e
        end
        local e={id=410,owner=11,bp='unit_scout_1_chi'}
        entityRegistry[e.id]=e;squads[#squads+1]={owner=11,bp='unit_scout_1_chi',entity=e}
        ''')
        self.source = (ROOT/'assets/scar/vietnam/initialization.scar').read_text()
        self.lua.execute(self.source)
        self.g = self.lua.globals()

    def assert_receivers(self, expected_adds):
        self.assertTrue(self.g.VietnamInitialization_Apply(self.g.PLAYERS[1]))
        for i in range(1, 7):
            e = self.g.starting[i]
            self.assertIsNotNone(e.abilities, f'starting Villager {i} lacks the receiver binding')
            self.assertTrue(e.abilities[self.g.stealth])
            self.assertEqual(e.adds or 0, expected_adds)
            self.assertIsNotNone(e.flags, f'starting Villager {i} lacks initialized eligibility')
            self.assertFalse(e.flags['is_in_stealth_aura_mal'])
        self.assertEqual(len(self.g.conversions), 15)

    def test_all_six_receive_missing_ability_after_entity_and_squad_conversion(self):
        self.assert_receivers(1)

    def test_conversion_that_retains_native_binding_does_not_recreate_it(self):
        self.lua.execute('''
        local original=Entity_ConvertBlueprint
        function Entity_ConvertBlueprint(e,bp)
          original(e,bp)
          if bp==privateVillager then e.abilities={[stealth]=true} end
        end
        ''')
        self.assert_receivers(0)

    def test_squad_conversion_can_clear_entity_binding_before_guard(self):
        self.lua.execute('''
        local originalEntity=Entity_ConvertBlueprint
        function Entity_ConvertBlueprint(e,bp)
          originalEntity(e,bp)
          if bp==privateVillager then e.abilities={[stealth]=true} end
        end
        local originalSquad=Squad_ConvertBlueprint
        function Squad_ConvertBlueprint(s,bp)
          originalSquad(s,bp)
          if bp==privateVillager then s.entity.abilities={} end
        end
        ''')
        self.assert_receivers(1)

    def test_rejected_starting_army_does_not_grant_or_convert(self):
        self.lua.execute('table.remove(squads,1)')
        self.assertFalse(self.g.VietnamInitialization_Apply(self.g.PLAYERS[1]))
        self.assertEqual(len(self.g.conversions), 0)
        for i in range(1, 7):
            self.assertIsNone(self.g.starting[i].abilities)


if __name__ == '__main__':
    unittest.main()

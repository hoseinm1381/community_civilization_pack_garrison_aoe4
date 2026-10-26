"""Real Lua regressions; engine fixtures are not native gameplay proof."""
import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua53 import LuaRuntime
SOURCE=ROOT/'assets/scar/vietnam/flooded_citadel.scar'

class FloodedTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
        function import(x) end
        probes=0; speed=4.5;bad=false;modified=nil
        function Entity_GetID(e) return e.id or 5 end
        function Entity_IsValid(id) return true end
        function Entity_IsAlive(e) return e.alive~=false end
        function Entity_GetHealth(e) return e.health or 100 end
        function Entity_IsInHold(e) return e.hold==true end
        function Entity_IsBuilding(e) return e.building==true end
        function Entity_IsOfType(e,t) return e.kind==t end
        function Entity_GetBlueprint(e) return e.bp end
        function BP_GetName(bp) return bp end
        function BP_GetEntityBPDefaultSpeed(bp, m, player)
            probes=probes+1;modified=m
            if bad then error('Entity BP did not have moving_ext!') end
            return speed
        end
        player={id=2}
        ''')
        self.eligible=self.lua.execute(SOURCE.read_text(encoding='utf-8')+'\nreturn eligible')

    def entity(self,bp='unit_villager_1_chi',**kw):
        return self.lua.table_from(dict(bp=bp,**kw))

    def test_nonmoving_visual_never_reaches_fatal_probe(self):
        self.lua.globals().bad=True
        self.assertFalse(self.eligible(self.entity('unit_trade_camel_abb_ha_01_viz'),self.lua.globals().player))
        self.assertEqual(self.lua.globals().probes,0)

    def test_persian_mobile_units_are_admitted(self):
        for name in ('ps_unit_villager_1_sul','ps_unit_scout_1_sul','ps_unit_zamburak_persia'):
            self.assertTrue(self.eligible(self.entity('b7fcea91257b408fb9e8ae4d8bc402e1:'+name),self.lua.globals().player),name)

    def test_unknown_blueprint_fails_closed(self):
        self.lua.globals().bad=True
        self.assertFalse(self.eligible(self.entity('foreign_or_visual_actor'),self.lua.globals().player))
        self.assertEqual(self.lua.globals().probes,0)

    def test_removed_inherited_movement_is_not_a_speed_target(self):
        self.lua.globals().bad=True
        self.assertFalse(self.eligible(self.entity('trader_abb_viz'),self.lua.globals().player))
        self.assertEqual(self.lua.globals().probes,0)

    def test_emplacement_actor_is_not_a_speed_target(self):
        self.lua.globals().bad=True
        self.assertFalse(self.eligible(self.entity('b7fcea91257b408fb9e8ae4d8bc402e1:vn_wpn_range_barbican_handcannon_chi'),self.lua.globals().player))
        self.assertEqual(self.lua.globals().probes,0)

    def test_land_unit_uses_unmodified_speed_and_caches(self):
        e=self.entity();p=self.lua.globals().player
        self.assertTrue(self.eligible(e,p));self.assertTrue(self.eligible(e,p))
        self.assertEqual(self.lua.globals().probes,1)
        self.assertFalse(self.lua.globals().modified)

    def test_private_skirmisher_is_covered(self):
        self.assertTrue(self.eligible(self.entity('b7fcea91257b408fb9e8ae4d8bc402e1:vn_unit_skirmisher_2_vit'),self.lua.globals().player))

    def test_private_voice_derived_unit_is_covered(self):
        self.assertTrue(self.eligible(self.entity('b7fcea91257b408fb9e8ae4d8bc402e1:vn084_e_unit_culverin_4_chi'),self.lua.globals().player))

    def test_zero_speed_is_excluded_and_cached(self):
        self.lua.globals().speed=0;e=self.entity();p=self.lua.globals().player
        self.assertFalse(self.eligible(e,p));self.assertFalse(self.eligible(e,p))
        self.assertEqual(self.lua.globals().probes,1)

    def test_existing_exclusions_do_not_probe(self):
        for props in (dict(alive=False),dict(health=0),dict(hold=True),dict(building=True),dict(kind='naval_unit'),dict(kind='deep_water_fish'),dict(kind='shore_fish')):
            self.assertFalse(self.eligible(self.entity(**props),self.lua.globals().player))
        self.assertEqual(self.lua.globals().probes,0)

    def test_strength_range_and_no_catch_and_continue(self):
        s=SOURCE.read_text(encoding='utf-8')
        self.assertIn('local fieldRange = 8 * 4',s)
        self.assertIn('MUT_Multiplication, false, 0.7',s)
        self.assertNotIn('pcall(',s)

if __name__=='__main__':unittest.main()

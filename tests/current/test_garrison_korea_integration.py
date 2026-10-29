"""Garrison preservation and Korea coexistence beyond the carried Normal suite."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))


class GarrisonKoreaIntegrationTests(unittest.TestCase):
    def test_existing_garrison_assets_and_korean_behavior_are_preserved(self):
        from verify_korea_garrison import verify
        self.assertEqual(verify()['changed_existing_assets'],5)

    def test_resolved_three_pair_choices_reach_existing_vietnam_voice_hook(self):
        from test_korea import ThreePairSelectionTests
        base=ThreePairSelectionTests();base.setUp()
        base.g.VietnamMode_OnInit();base.choose()
        self.assertEqual(base.g.env.voiceCivs[1],'vietnam')
        self.assertEqual(base.g.env.voiceCivs[2],'persia')
        self.assertEqual(base.g.env.voiceCivs[3],'korea')
        self.assertFalse(base.g.VietnamModeState.held)

    def test_korean_movers_are_safe_flooded_citadel_targets(self):
        from test_garrison_mobility import FloodedTests
        base=FloodedTests();base.setUp()
        for name in ('kr_unit_archer_2_chi_ha_01','kr_unit_villager_1_chi_ha_01'):
            self.assertTrue(base.eligible(base.entity('b7fcea91257b408fb9e8ae4d8bc402e1:'+name),base.lua.globals().player))
        self.assertFalse(base.eligible(base.entity('b7fcea91257b408fb9e8ae4d8bc402e1:kr_building_dynasty_pagoda_control_chi_ha_01'),base.lua.globals().player))


if __name__=='__main__':unittest.main()

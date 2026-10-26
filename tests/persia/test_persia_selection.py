import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / '.tools/python'))
from lupa.lua51 import LuaRuntime


class PairSelectionTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT / 'assets/scar/vietnam/selection_core.scar').read_text())
        self.core = self.lua.globals().VietnamSelectionCore
        self.state = self.core.New(self.lua.table_from([1, 2, 3, 4]), 10, 30,
                                   self.lua.table_from({1: 'china', 2: 'delhi', 3: 'delhi', 4: 'china'}))

    def test_pairs_reject_cross_pair_and_unknown_choices(self):
        self.assertFalse(self.core.Choose(self.state, 1, 'persia', 11))
        self.assertFalse(self.core.Choose(self.state, 2, 'vietnam', 11))
        self.assertFalse(self.core.Choose(self.state, 2, 'china', 11))
        self.assertFalse(self.core.Choose(self.state, 9, 'persia', 11))
        self.assertTrue(self.core.Choose(self.state, 2, 'persia', 11))
        self.assertFalse(self.core.Choose(self.state, 2, 'delhi', 12))
        self.assertTrue(self.core.Choose(self.state, 1, 'vietnam', 12))

    def test_timeout_and_disconnect_keep_each_original(self):
        self.core.Drop(self.state, 2)
        self.assertEqual(self.state.players[2].choice, 'delhi')
        self.assertFalse(self.core.Choose(self.state, 2, 'persia', 12))
        self.core.Choose(self.state, 1, 'vietnam', 12)
        self.assertFalse(self.core.Tick(self.state, 39.9))
        self.assertTrue(self.core.Tick(self.state, 40))
        self.assertEqual(self.state.players[1].choice, 'vietnam')
        self.assertEqual(self.state.players[3].choice, 'delhi')
        self.assertEqual(self.state.players[4].choice, 'china')

    def test_deadline_and_closed_reject_persia(self):
        self.assertFalse(self.core.Choose(self.state, 2, 'persia', 40))
        self.core.Close(self.state)
        self.assertFalse(self.core.Choose(self.state, 3, 'persia', 12))


if __name__ == '__main__':
    unittest.main()

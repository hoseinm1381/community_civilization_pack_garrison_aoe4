import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
try:
    import lupa.lua51
except ModuleNotFoundError:
    sys.path.insert(0, str(ROOT / '.tools' / 'python'))
from lupa.lua51 import LuaRuntime


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.lua = LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute((ROOT / 'assets/scar/vietnam/selection_core.scar').read_text())
        self.core = self.lua.globals().VietnamSelectionCore

    def state(self, players=(1, 2), start=0):
        return self.core.New(self.lua.table_from(players), start, 30)

    def test_no_eligible_players_starts_without_countdown(self):
        self.assertTrue(self.core.IsReady(self.state(())))

    def test_player_can_only_choose_their_own_slot(self):
        s = self.state()
        self.assertTrue(self.core.Choose(s, 1, 'vietnam', 5))
        self.assertEqual(s.players[1].choice, 'vietnam')
        self.assertIsNone(s.players[2].choice)
        self.assertFalse(self.core.Choose(s, 3, 'vietnam', 5))
        self.assertFalse(self.core.Choose(s, 2, '1,vietnam', 5))

    def test_choice_cannot_be_changed_or_repeated(self):
        s = self.state()
        self.assertTrue(self.core.Choose(s, 1, 'china', 1))
        self.assertFalse(self.core.Choose(s, 1, 'vietnam', 2))
        self.assertFalse(self.core.Choose(s, 1, 'china', 2))
        self.assertEqual(s.players[1].choice, 'china')

    def test_timeout_defaults_only_unanswered_players_to_china(self):
        s = self.state()
        self.core.Choose(s, 1, 'vietnam', 2)
        self.core.Tick(s, 29.99)
        self.assertFalse(self.core.IsReady(s))
        self.core.Tick(s, 30)
        self.assertTrue(self.core.IsReady(s))
        self.assertEqual(s.players[1].choice, 'vietnam')
        self.assertEqual(s.players[2].choice, 'china')

    def test_input_at_deadline_is_rejected_before_periodic_tick(self):
        s = self.state()
        self.assertFalse(self.core.Choose(s, 1, 'vietnam', 30))
        self.core.Tick(s, 30)
        self.assertEqual(s.players[1].choice, 'china')

    def test_all_choices_finish_early(self):
        s = self.state()
        self.core.Choose(s, 1, 'china', 1)
        self.core.Choose(s, 2, 'vietnam', 2)
        self.assertTrue(self.core.IsReady(s))

    def test_disconnect_resolves_slot_without_waiting_for_deadline(self):
        s = self.state()
        self.core.Choose(s, 1, 'vietnam', 1)
        self.core.Drop(s, 2)
        self.assertTrue(self.core.IsReady(s))
        self.assertEqual(s.players[2].choice, 'china')
        self.assertTrue(s.players[2].dropped)
        self.assertFalse(self.core.Choose(s, 2, 'vietnam', 2))

    def test_countdown_uses_shared_start_time(self):
        s = self.state(start=11)
        self.core.Tick(s, 40)
        self.assertFalse(self.core.IsReady(s))
        self.core.Tick(s, 41)
        self.assertTrue(self.core.IsReady(s))

    def test_closed_selection_ignores_late_network_input(self):
        s = self.state()
        self.core.Close(s)
        self.assertFalse(self.core.Choose(s, 1, 'vietnam', 1))
        self.assertFalse(self.core.Tick(s, 31))
        self.assertIsNone(s.players[1].choice)


if __name__ == '__main__':
    unittest.main()

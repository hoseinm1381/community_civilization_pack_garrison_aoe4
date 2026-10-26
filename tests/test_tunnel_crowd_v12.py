"""Formation collision offsets at entrance, not a native pathfinding test."""
from test_tunnel_v9 import TunnelV9Tests
import unittest

class TunnelCrowdV12(TunnelV9Tests):
    def crowd(self,offset):
        self.runlua('autoArrive=false;for i=2,35 do addTraveler(2000+i) end')
        self.request(','.join(str(2000+i) for i in range(1,36)))
        # Entrance fixture is centered at 0, half-width 4. Units remain usable
        # around that entrance instead of teleporting to a fictitious edge.
        self.runlua(f'for _,squad in ipairs(squads) do squad.pos={{x=0,y=0,z=4+{offset}}} end')

    def test_all_35_load_with_collision_offsets_seven_metres_from_edge(self):
        self.crowd(7);self.step(.25);self.step(3.25)
        self.assertEqual(self.g.departures,35);self.assertEqual(self.g.moveCount,35)
        self.complete();self.assertEqual(self.g.tempGroups,0)

    def test_eight_metre_boundary_is_inclusive(self):
        self.crowd(8);self.step(.25);self.step(3.25)
        self.assertEqual(self.g.departures,35)

    def test_outside_eight_metres_never_loads_or_loses_units(self):
        self.crowd(8.01);self.step(.25);self.step(3.25);self.step(15.25)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.tempGroups,0)
        self.assertEqual(self.g.moveCount,35)

    def test_leaving_acceptance_restarts_continuous_loading_timer(self):
        self.crowd(7);self.step(.25);self.step(2)
        self.runlua('for _,squad in ipairs(squads) do squad.pos.z=13 end')
        self.step(2.25)
        self.runlua('for _,squad in ipairs(squads) do squad.pos.z=11 end')
        self.step(2.5);self.step(5.25);self.assertEqual(self.g.departures,0)
        self.step(5.5);self.assertEqual(self.g.departures,35)

def load_tests(loader,tests,pattern):
    return unittest.TestSuite(TunnelCrowdV12(n) for n in TunnelCrowdV12.__dict__ if n.startswith('test_'))

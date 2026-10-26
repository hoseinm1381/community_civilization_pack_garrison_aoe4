"""Regression for the reported respawn-at-entrance engine boundary.

The engine double deliberately does NOT make Squad_Spawn a teleport. It also
rejects free-position queries on despawned squads, matching the lifecycle used
by the official map-monsters source. These tests are not native game proof.
"""
import zipfile
import test_tunnel_v7 as v7
from test_runtime_repairs import ROOT


class TunnelV8Tests(v7.TunnelV7Tests):
    def setUp(self):
        super().setUp()
        self.runlua('''
        spawnAttempts=0;positionChanges=0;teleportBlocked=false;freeQueriesHidden=0
        function Squad_Spawn(s,p,kind)
            assert(s.despawned and kind=='')
            s.despawned=false;spawnAttempts=spawnAttempts+1
            -- Reproduce the reported result: original member positions survive.
        end
        function Squad_TryFindClosestFreePosition(s,p)
            if s.despawned then freeQueriesHidden=freeQueriesHidden+1;return s.pos end
            return p
        end
        function Squad_SetPosition(s,p,toward)
            assert(not s.despawned)
            positionChanges=positionChanges+1
            if not teleportBlocked then s.pos={x=p.x,y=p.y,z=p.z};arrivals=arrivals+1 end
        end
        ''')

    def test_original_squad_is_explicitly_relocated_after_respawn(self):
        self.request();self.step(3.1);self.step(6.1)
        self.assertEqual(self.g.freeQueriesHidden,0)
        self.assertEqual(self.g.positionChanges,1)
        self.assertGreater(self.g.s.pos.x,32)
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.id,2001)
        self.assertEqual(self.g.s.health,45)

    def test_failed_relocation_never_claims_destination_or_drops_record(self):
        self.request();self.step(3.1)
        self.runlua('teleportBlocked=true')
        self.step(6.1)
        self.assertFalse(self.has_log('boundary=arrival'))
        self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])
        self.runlua('teleportBlocked=false');self.step(6.5)
        self.assertGreater(self.g.s.pos.x,32)
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_solver_fallback_to_origin_is_rejected_as_exit(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_TryFindClosestFreePosition(s,p) return s.pos end')
        self.step(6.1)
        self.assertEqual(self.g.positionChanges,0)
        self.assertFalse(self.has_log('boundary=arrival'))
        self.assertTrue(self.g.s.despawned)

    def test_unspawned_result_does_not_query_live_position(self):
        self.request();self.step(3.1)
        self.runlua('function Squad_Spawn(s,p,k) spawnAttempts=spawnAttempts+1 end')
        self.step(6.1)
        self.assertEqual(self.g.freeQueriesHidden,0)
        self.assertEqual(self.g.positionChanges,0)
        self.assertTrue(self.g.s.despawned)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_cooldown_objective_counts_from_cast_even_during_travel(self):
        self.runlua('function Obj_SetCounterTimerSeconds(o,n) lastCounter=n end')
        self.request();self.step(3.1)
        self.assertEqual(self.g.lastCounter,27)

    def test_actual_v7_snapshot_reproduces_false_destination_success(self):
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v8_20261023/before.zip') as z:
            old=z.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig')
        self.runlua(old)
        self.runlua("VietnamTunnels_Start({[1]='vietnam'});VietnamTunnelsState.players[1].graph=VietnamTunnelCore.Build({n1,n2,n3})")
        self.request();self.step(3.1);self.step(6.1)
        self.assertLess(self.g.s.pos.x,0)
        self.assertEqual(self.g.freeQueriesHidden,1)
        self.assertTrue(self.has_log('boundary=arrival'))


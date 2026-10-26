"""Failure presentation against the real controller; native UI remains a match gate."""
import unittest
import re
import zipfile
import test_tunnel_v9 as v9


def simulation_source(source):
    """Remove only notification helper/call sites, then compare actual frozen code."""
    source = re.sub(r'local warningText=\{.*?(?=local function playerState|function VietnamTunnels_OnTravelCommand)', '', source, flags=re.S)
    source = re.sub(r'if sameOwner\(Game_GetLocalPlayer\(\),r.owner\) then UIWarning_Show\("[^"\n]*"\) end', '', source)
    source = re.sub(r'if finished then warn\([^\n]*?\) end', '', source)
    source = re.sub(r'warn\([^\n]*?\)', '', source)
    source = re.sub(r'--[^\n]*', '', source)
    return re.sub(r'[\s;]', '', source)


class TunnelNotificationsV10Tests(v9.TunnelV9Tests):
    def messages(self):
        return [self.g.warnings[i] for i in range(1, len(self.g.warnings) + 1)]

    def test_replay_rejection_is_silent_but_keeps_cooldown(self):
        self.runlua('function UI_IsReplay() return true end')
        self.cast(x=9999)
        self.assertEqual(self.messages(), [])
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown, 30)

    def test_pending_new_order_has_specific_notification_and_keeps_order(self):
        self.cast()
        self.runlua('callbacks[2001]({})')
        self.step(.1)
        self.assertEqual(self.messages(), ['Tunnel cancelled by a new order.'])
        self.assertEqual(self.g.moveCount, 0)
        self.assertEqual(self.g.stopCount, 0)

    def test_destroyed_target_uses_readable_message(self):
        self.runlua('registry[3].dead=true')
        self.cast()
        self.assertEqual(self.messages(), ['Tunnel cancelled: the chosen building was destroyed.'])

    def test_dead_traveler_notifies_once_without_spawning(self):
        self.request()
        self.runlua('s.dead=true')
        self.step(.2); self.step(.4)
        self.assertEqual(self.messages(), ['Tunnel cancelled: the unit was lost.'])
        self.assertEqual(self.g.spawnAttempts, 0)

    def test_converted_traveler_notifies_original_owner_once(self):
        self.request(); self.step(3.1)
        self.runlua('s.owner=22')
        self.complete()
        self.assertEqual(self.messages(), ['Tunnel cancelled: the unit changed owner.'])
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.owner, 22)

    def test_converted_traveler_does_not_warn_new_owner(self):
        self.request(); self.step(3.1)
        self.runlua('s.owner=22;localPlayer=22')
        self.complete()
        self.assertEqual(self.messages(), [])

    def test_recovery_notifications_are_suppressed_in_replay(self):
        self.request(); self.step(3.1)
        self.runlua('function UI_IsReplay() return true end;teleportBlocked=true')
        self.step(6.1); self.complete()
        self.assertEqual(self.messages(), [])
        self.assertFalse(self.g.s.despawned)

    def test_native_spawn_refusal_warns_once_for_whole_selected_group(self):
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        self.request(','.join(str(2000+i) for i in range(1,36)))
        self.step(3.1)
        self.runlua('function Squad_Spawn(s,p,k) spawnAttempts=spawnAttempts+1 end')
        self.step(6.1); self.complete()
        self.assertEqual(len(self.messages()), 1)
        self.assertIn('recovery', self.messages()[0])
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_alternating_reject_reasons_do_not_repeat_same_warning_in_one_tick(self):
        self.cast(x=9999)
        self.cast(x=48)
        self.cast(x=9999)
        self.assertEqual(len(self.messages()), 2)

    def test_repeated_cooldown_commands_are_limited_then_reported_again(self):
        self.request()
        self.cast(); self.step(.25); self.cast(); self.step(.5); self.cast()
        self.assertEqual(len(self.messages()), 1)
        self.step(2.5); self.cast()
        self.assertEqual(len(self.messages()), 2)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown, 30)

    def test_successful_journey_has_no_warning(self):
        self.request(); self.step(3.1); self.step(6.1); self.complete()
        self.assertEqual(self.messages(), [])

    def test_owner_handle_wrappers_still_receive_one_group_notification(self):
        self.runlua('function Game_GetLocalPlayer() return {id=11} end')
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        self.cast(','.join(str(2000+i) for i in range(1,36)), x=9999)
        self.assertEqual(len(self.messages()), 1)

    def test_simulation_source_matches_frozen_working_v9_after_presentation_removal(self):
        with zipfile.ZipFile(v9.ROOT / 'work/vietnam_redesign/runtime_v10_20261023/before.zip') as archive:
            before = archive.read('assets/scar/vietnam/tunnels.scar').decode('utf-8-sig')
        after = (v9.ROOT / 'assets/scar/vietnam/tunnels.scar').read_text(encoding='utf-8-sig')
        self.assertEqual(simulation_source(before), simulation_source(after))

    def test_visible_recovery_reports_final_position_once(self):
        self.request(); self.step(3.1)
        self.runlua('''function Squad_Spawn(s,p,k)
            spawnAttempts=spawnAttempts+1
            pendingEngine[#pendingEngine+1]=function() s.despawned=false;s.pos={x=999,y=0,z=999} end
        end
        teleportBlocked=true''')
        self.step(6.1); self.complete()
        self.assertEqual(self.messages(), [
            'Tunnel exit blocked. Returning the unit to its entrance.',
            'Tunnel cancelled: the unit is visible and available at its current position.',
        ])
        self.assertEqual(self.g.s.pos.x, 999)
        self.assertFalse(self.g.s.despawned)

    def test_replay_spawn_failure_is_silent_but_retries_original(self):
        self.request(); self.step(3.1)
        self.runlua('function UI_IsReplay() return true end;function Squad_Spawn(s,p,k) spawnAttempts=spawnAttempts+1 end')
        self.step(6.1); self.complete()
        self.assertEqual(self.messages(), [])
        self.assertGreater(self.g.spawnAttempts, 3)
        self.assertIsNotNone(self.g.VietnamTunnelsState.players[1].records[2001])

    def test_destroyed_exit_announces_return_once(self):
        self.request(); self.step(3.1)
        self.runlua('registry[3].dead=true;VietnamTunnels_OnEntityKilled({victim=registry[3]})')
        self.step(6.1); self.complete()
        self.assertEqual(self.messages(), ['Tunnel exit lost. Returning the unit to its entrance.'])
        self.assertFalse(self.g.s.despawned)
        self.assertLess(self.g.s.pos.x, 0)


if __name__ == '__main__':
    unittest.main()

"""Execute real Lua routing with deterministic game API fixtures, no game proof."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/release_084'))
import test_dispatcher as fixture


class ChatterTests(unittest.TestCase):
    def setUp(self):
        fixture.DispatcherTests.setUp(self)
        target=ROOT/'tools/release_085/voices.scar'
        if target.exists():self.lua.execute(target.read_text(encoding='utf-8'))

    def test_selection_and_orders_share_five_seconds_across_actors(self):
        self.lua.execute('''
        local a=add(1);local b=add(2);selection={a}
        VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;selection={b};VietnamVoice_Tick();assert(#played==1)
        now=4.99;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[2]);assert(#played==1)
        now=5;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[2]);assert(played[2]=='attack.wav')
        now=9.99;selection={a};VietnamVoice_Tick();assert(#played==2)
        now=10;selection={b};VietnamVoice_Tick();assert(#played==3)
        ''')

    def test_repeated_land_movement_waits_eight_seconds(self):
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        local r=VietnamVoiceState.actors[1]
        now=5;VietnamVoice_OnCommand({command=SCMD_Move},r);assert(played[2]=='move.wav')
        now=12.99;VietnamVoice_OnCommand({command=SCMD_Patrol},r);assert(#played==2)
        now=13;VietnamVoice_OnCommand({command=SCMD_Move},r);assert(#played==3)
        ''')

    def test_naval_sail_uses_same_movement_limit(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:unit'].role='NAVAL_FISH'
        VietnamVoiceBank.clips.NAVAL_FISH={A2={select={{'crew',.5}},sail={{'sail',.5}}}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        local r=VietnamVoiceState.actors[1]
        now=5;VietnamVoice_OnCommand({command=SCMD_Move},r);assert(played[2]=='sail')
        now=12;VietnamVoice_OnCommand({command=SCMD_Move},r);assert(#played==2)
        now=13;VietnamVoice_OnCommand({command=SCMD_Move},r);assert(#played==3)
        ''')

    def test_under_attack_fifteen_seconds_and_efforts_independent(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:unit'].stock_speaker='soldier'
        VietnamVoiceBank.stock_efforts={soldier={pain_light={{'pain',.5}},pain_heavy={{'pain',.5}},death={{'death',.5}}}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;a.hp=99;VietnamVoice_Tick();assert(played[2]=='pain' and played[3]=='hurt.wav')
        now=3;a.hp=98;VietnamVoice_Tick();now=5;a.hp=97;VietnamVoice_Tick()
        local n=0;for _,p in ipairs(played) do if p=='hurt.wav' then n=n+1 end end;assert(n==1)
        now=15;a.hp=96;VietnamVoice_Tick();now=16;a.hp=95;VietnamVoice_Tick()
        n=0;for _,p in ipairs(played) do if p=='hurt.wav' then n=n+1 end end;assert(n==2)
        now=16.2;VietnamVoice_OnKilled({},VietnamVoiceState.actors[1]);assert(played[#played]=='death')
        ''')

    def test_order_activity_echo_suppressed_even_after_clip_finishes(self):
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=5;VietnamVoice_OnCommand({command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==2)
        now=10.5;a.moving=true;VietnamVoice_Tick();assert(#played==2)
        ''')

    def test_suppressed_order_does_not_echo_as_delayed_activity(self):
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[1])
        now=6;a.attacking=true;VietnamVoice_Tick();assert(#played==1)
        ''')

    def test_build_after_long_travel_does_not_echo(self):
        self.lua.execute('''
        VietnamVoiceBank.clips.INFANTRY.A2.build={{'build.wav',.5}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=5;VietnamVoice_OnCommand({command=SCMD_BuildStructure},VietnamVoiceState.actors[1])
        now=14;a.building=true;VietnamVoice_Tick();assert(#played==2)
        ''')

    def test_gather_command_suppresses_travel_and_delayed_resource_reply(self):
        self.lua.execute('''
        VietnamVoiceBank.clips.INFANTRY.A2.acknowledge={{'ack',.5}}
        VietnamVoiceBank.clips.INFANTRY.A2.wood={{'wood',.5}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=5;VietnamVoice_OnCommand({command=SCMD_Gather},VietnamVoiceState.actors[1])
        now=10.5;a.moving=true;VietnamVoice_Tick();assert(#played==2)
        now=20;a.moving=false;a.resource=RT_Wood;VietnamVoice_Tick();assert(#played==2)
        ''')

    def test_generic_right_click_acknowledgements_use_eight_second_gate(self):
        self.lua.execute('''
        VietnamVoiceBank.clips.INFANTRY.A2.acknowledge={{'ack',.5}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        local r=VietnamVoiceState.actors[1]
        now=5;VietnamVoice_OnCommand({command=SCMD_DefaultAction},r);assert(#played==2)
        now=10;VietnamVoice_OnCommand({command=SCMD_DefaultAction},r);assert(#played==2)
        now=13;VietnamVoice_OnCommand({command=SCMD_DefaultAction},r);assert(#played==3)
        ''')

    def test_restart_resets_cooldowns(self):
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        VietnamVoice_Stop();VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick();assert(#played==2)
        ''')

    def test_stock_efforts_still_play_during_long_dialogue(self):
        fixture.DispatcherTests.test_stock_heavy_light_and_death_are_admitted_during_spoken_dialogue(self)

    def test_wildlife_is_not_voiced(self):
        fixture.DispatcherTests.test_wildlife_never_calls_player_owner(self)

    def test_ownership_and_teardown_remove_handlers(self):
        fixture.DispatcherTests.test_ownership_change_and_teardown_remove_handlers(self)

    def test_recycled_dead_handle_cannot_speak(self):
        fixture.DispatcherTests.test_recycled_id_before_death_callback_does_not_play_for_new_actor(self)

    def test_failed_audio_does_not_consume_reply_budget(self):
        self.lua.execute('''
        local first=true
        Garrison.audio.forMod=function() return {session=function() end,stop=function() end,pulse=function() end,
          play=function(p) if first then first=false;return false end;table.insert(played,p);return true end} end
        ''')
        self.lua.execute((ROOT/'tools/release_085/voices.scar').read_text(encoding='utf-8'))
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick();assert(#played==0)
        now=.1;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[1]);assert(played[1]=='attack.wav')
        ''')


if __name__=='__main__':unittest.main()

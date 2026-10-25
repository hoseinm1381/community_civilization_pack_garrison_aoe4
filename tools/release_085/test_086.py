"""0.8.6 per-unit cooldowns; real Lua dispatcher with existing game fixtures."""
from pathlib import Path
import unittest
import test_chatter as previous
ROOT=Path(__file__).resolve().parents[2]


class UnitChatterTests(previous.ChatterTests):
    def setUp(self):
        super().setUp()
        path=ROOT/'tools/release_085/voices_086.scar'
        if path.exists():self.lua.execute(path.read_text(encoding='utf-8'))

    def test_selection_and_orders_share_five_seconds_across_actors(self):
        # Replace the obsolete global-gate expectation with independent actors.
        self.lua.execute('''
        local clips=VietnamVoiceBank.clips.INFANTRY
        VietnamVoiceBank.clips.SCOUT=clips;VietnamVoiceBank.clips.CIV_M=clips
        VietnamVoiceBank.units.scout={role='SCOUT',age=2,private=true}
        VietnamVoiceBank.units.worker={role='CIV_M',age=2,private=true}
        local a=add(1,false,1,'scout');local b=add(2,false,1,'worker');selection={a}
        VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick();assert(#played==1)
        now=1;selection={b};VietnamVoice_Tick();assert(#played==2)
        now=2;selection={a};VietnamVoice_Tick();assert(#played==2)
        now=4.99;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[1]);assert(#played==2)
        now=5;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[1]);assert(#played==3)
        now=6;selection={b};VietnamVoice_Tick();assert(#played==4)
        ''')

    def test_two_units_of_same_role_also_have_separate_timers(self):
        self.lua.execute('''
        local a=add(1);local b=add(2);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;selection={b};VietnamVoice_Tick();assert(#played==2)
        now=2;selection={a};VietnamVoice_Tick();assert(#played==2)
        ''')

    def test_shared_clip_gate_prevents_overlapping_unit_replies(self):
        self.lua.execute('''
        local a=add(1);local b=add(2);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=.2;selection={b};VietnamVoice_Tick();assert(#played==1)
        now=.7;VietnamVoice_OnCommand({command=SCMD_Attack},VietnamVoiceState.actors[2]);assert(#played==2)
        ''')

    def test_movement_gate_belongs_to_the_individual_unit(self):
        self.lua.execute('''
        local a=add(1);local b=add(2);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=5;VietnamVoice_OnCommand({command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==2)
        VietnamVoiceState.leader=2;now=6;VietnamVoice_OnCommand({command=SCMD_Move},VietnamVoiceState.actors[2]);assert(#played==3)
        VietnamVoiceState.leader=1;now=12.99;VietnamVoice_OnCommand({command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==3)
        now=13;VietnamVoice_OnCommand({command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==4)
        ''')

    def test_under_attack_gate_belongs_to_the_individual_unit(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:unit'].stock_speaker='soldier'
        VietnamVoiceBank.stock_efforts={soldier={pain_light={{'pain',.1}},pain_heavy={{'pain',.1}},death={{'death',.1}}}}
        local a=add(1);local b=add(2);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;a.hp=99;VietnamVoice_Tick()
        now=2;b.hp=99;VietnamVoice_Tick()
        local n=0;for _,p in ipairs(played) do if p=='hurt.wav' then n=n+1 end end;assert(n==2)
        now=3;a.hp=98;VietnamVoice_Tick();now=4;a.hp=97;VietnamVoice_Tick()
        n=0;for _,p in ipairs(played) do if p=='hurt.wav' then n=n+1 end end;assert(n==2)
        ''')

    def test_blueprint_age_refresh_does_not_reset_cooldown(self):
        self.lua.execute('''
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=1;VietnamVoice_Tick();selection={};VietnamVoice_Tick();selection={a};VietnamVoice_Tick();assert(#played==1)
        ''')


if __name__=='__main__':unittest.main()

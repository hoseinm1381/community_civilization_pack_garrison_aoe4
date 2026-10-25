"""Offline lifecycle regressions. Mocks do not qualify native playback or MP."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'.tools/python'))
from lupa.lua53 import LuaRuntime


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.lua=LuaRuntime(unpack_returned_tuples=True)
        self.lua.execute('''
        function import(x) end
        now=0;played={};removed=0;registered=0;worldOwnerCalls=0
        SCMD_Move=1;SCMD_Patrol=2;SCMD_Attack=3;SCMD_StationaryAttack=4;SCMD_AttackMove=5
        SCMD_Stop=6;SCMD_HoldPosition=7;SCMD_BuildStructure=8;SCMD_Gather=9;SCMD_Trade=10
        SCMD_Load=11;SCMD_Retreat=12;SCMD_Ability=13;SCMD_Unload=14
        SCMD_DefaultAction=15
        GE_SquadCommandIssued=20;GE_SquadKilled=21;GE_LocalPlayerChanged=22
        RT_Wood=1;RT_Gold=2;RT_Stone=3;RT_Food=4
        PLAYERS={{id={id=1},index=1,isHuman=true}};localPlayer={id=1};selection={};roster={}
        function Game_GetLocalPlayer() return localPlayer end
        function Player_GetID(p) return p.id end
        function Player_GetSquads(p) return roster end
        function Player_HasUpgrade(p,bp) return false end
        function BP_GetUpgradeBlueprint(n) return n end
        function BP_GetName(bp) return bp.name end
        function World_GetGameTime() return now end
        function Camera_GetCurrentTargetPos() return {x=0,z=0} end
        function Squad_GetID(s) return s.id end
        function Squad_IsValid(id) return roster[id]~=nil end
        function Squad_FromID(id) return roster[id] end
        function Squad_IsAlive(s) return not s.dead end
        function World_OwnsSquad(s) return s.world==true end
        function Squad_GetPlayerOwner(s) assert(not s.world);worldOwnerCalls=worldOwnerCalls+1;return {id=s.owner} end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_GetPosition(s) return {x=0,z=0} end
        function Squad_GetHealth(s) return s.hp end
        function Squad_IsFemale(s) return s.female==true end
        function Squad_IsConstructing(s) return s.building==true end
        function Squad_IsGatheringResourceType(s,r) return s.resource==r end
        function Squad_IsAttacking(s,t) return s.attacking==true end
        function Squad_IsMoving(s) return s.moving==true end
        function SGroup_CreateUnique() return {} end
        function SGroup_Destroy(g) end
        function SGroup_CountSpawned(g) return #g end
        function SGroup_GetSpawnedSquadAt(g,i) return g[i] end
        function Misc_GetSelectedSquads(g) for k in pairs(g) do g[k]=nil end;for i,s in ipairs(selection) do g[i]=s end end
        function Rule_AddSquadEvent(...) registered=registered+1 end
        function Rule_RemoveSquadEvent(...) removed=removed+1 end
        function Rule_AddInterval(...) end;function Rule_Remove(...) end
        function Rule_AddGlobalEvent(...) end;function Rule_RemoveGlobalEvent(...) end
        Garrison={audio={forMod=function(key) assert(key=='community_civilization_pack');return {
          session=function() return true end,stop=function() end,pulse=function() end,
          play=function(path,x,z,gain) table.insert(played,path);return true end} end}}
        local clips={select={{'one.wav',.5},{'two.wav',.5}},move={{'move.wav',.5}},
          attack={{'attack.wav',.5}},under_attack={{'hurt.wav',.5}},death={{'death.wav',.5}}}
        VietnamVoiceBank={units={['owner:unit']={role='INFANTRY',age=2,private=true}},
          clips={INFANTRY={A2=clips}},complete=true}
        function add(id,world,owner,bp)
          local s={id=id,world=world,owner=owner or 1,bp={name=bp or 'owner:unit'},hp=100}
          roster[id]=s;return s
        end
        ''')
        self.lua.execute((ROOT/'tools/release_084/templates/voices.scar').read_text())

    def test_wildlife_never_calls_player_owner(self):
        self.lua.execute('local w=add(1,true);selection={w};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();assert(worldOwnerCalls==0 and #played==0)')

    def test_stock_death_uses_explicit_female_speaker_without_custom_effort(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:unit'].female_role='INFANTRY_F'
        VietnamVoiceBank.units['owner:unit'].stock_speaker='manatarms'
        VietnamVoiceBank.units['owner:unit'].stock_female_speaker='villagerfemale'
        VietnamVoiceBank.clips.INFANTRY_F={A2={select={{'female-select.ogg',.5}}}}
        VietnamVoiceBank.stock_efforts={manatarms={death={{'male-stock.ogg',.5}}},
          villagerfemale={death={{'female-stock.ogg',.5}}}}
        local a=add(1);a.female=true;selection={a}
        VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        local old=VietnamVoiceState.actors[1];roster[1]=nil;a.dead=true;now=2
        VietnamVoice_OnKilled({},old);assert(played[2]=='female-stock.ogg')
        ''')

    def test_stock_heavy_light_and_death_are_admitted_during_spoken_dialogue(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:unit'].stock_speaker='manatarms'
        VietnamVoiceBank.clips.INFANTRY.A2.select={{'long-dialogue.ogg',5}}
        VietnamVoiceBank.stock_efforts={manatarms={pain_light={{'stock-light.ogg',.2}},
          pain_heavy={{'stock-heavy.ogg',.3}},death={{'stock-death.ogg',.4}}}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        now=.25;a.hp=70;VietnamVoice_Tick();assert(played[2]=='stock-heavy.ogg')
        now=1.25;a.hp=69;VietnamVoice_Tick();assert(played[3]=='stock-light.ogg')
        local old=VietnamVoiceState.actors[1];roster[1]=nil;a.dead=true;now=1.5
        VietnamVoice_OnKilled({},old);assert(played[4]=='stock-death.ogg')
        assert(VietnamVoiceState.busyUntil>=5)
        ''')

    def test_selection_is_edge_triggered_and_replies_do_not_repeat_immediately(self):
        self.lua.execute('local a=add(1);selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();assert(#played==1);now=1;VietnamVoice_Tick();assert(#played==1);selection={};VietnamVoice_Tick();selection={a};VietnamVoice_Tick();assert(#played==2 and played[1]~=played[2])')

    def test_mixed_group_has_one_stable_responder_and_busy_gate(self):
        self.lua.execute('local a=add(1);local b=add(2);selection={b,a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();assert(#played==1);VietnamVoice_OnCommand({squad=a,command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==1);now=1;VietnamVoice_OnCommand({squad=b,command=SCMD_Move},VietnamVoiceState.actors[2]);assert(#played==1);VietnamVoice_OnCommand({squad=a,command=SCMD_Move},VietnamVoiceState.actors[1]);assert(#played==2)')

    def test_foreign_namespace_is_not_admitted(self):
        self.lua.execute('local a=add(1,false,1,"other:unit");selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();assert(#played==0 and registered==0)')

    def test_ownership_change_and_teardown_remove_handlers(self):
        self.lua.execute('local a=add(1);selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();a.owner=2;now=2;VietnamVoice_Tick();assert(VietnamVoiceState.actors[1]==nil);VietnamVoice_Stop();assert(not VietnamVoiceState.running and removed==2)')

    def test_killed_callback_uses_cached_data_and_ignores_stale_recycled_id(self):
        self.lua.execute('local a=add(1);selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();local old=VietnamVoiceState.actors[1];roster[1]=nil;a.dead=true;now=1;VietnamVoice_OnKilled({},old);assert(played[2]=="death.wav");add(1);VietnamVoice_OnKilled({},old);assert(#played==2)')

    def test_recycled_id_before_death_callback_does_not_play_for_new_actor(self):
        self.lua.execute('local a=add(1);selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();local old=VietnamVoiceState.actors[1];a.dead=true;add(1);now=2;VietnamVoice_OnKilled({},old);assert(#played==1)')

    def test_female_player_age_bank_changes_after_advancing_age(self):
        self.lua.execute('''
        VietnamVoiceBank.units['owner:scout']={role='SCOUT',female_role='SCOUT_F',private=true}
        VietnamVoiceBank.clips.SCOUT_F={A1={select={{'female1.wav',.5}}},A4={select={{'female4.wav',.5}}}}
        age4=false;function Player_HasUpgrade(p,bp) return age4 and bp=='imperial_age' end
        local a=add(1,false,1,'owner:scout');a.female=true;selection={a}
        VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick();assert(played[1]=='female1.wav')
        age4=true;now=2;selection={};VietnamVoice_Tick();selection={a};VietnamVoice_Tick()
        assert(played[2]=='female4.wav')
        ''')

    def test_fixed_blueprint_tier_ignores_higher_player_age(self):
        self.lua.execute('function Player_HasUpgrade(p,bp) return true end;local a=add(1);selection={a};VietnamVoice_Start({[1]="vietnam"});VietnamVoice_Tick();assert(played[1]=="one.wav")')

    def test_shared_stock_naval_admission_and_move_event(self):
        self.lua.execute('''
        VietnamVoiceBank.units.ship={role='NAVAL_FISH',age=1,private=false}
        VietnamVoiceBank.clips.NAVAL_FISH={A1={select={{'crew.wav',.5}},sail={{'sail.wav',.5}}}}
        local a=add(1,false,1,'ship');selection={a}
        VietnamVoice_Start({[1]='other'});VietnamVoice_Tick();assert(#played==0)
        VietnamVoice_Stop();VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick();assert(played[1]=='crew.wav')
        now=2;VietnamVoice_OnCommand({squad=a,command=SCMD_Move},VietnamVoiceState.actors[1]);assert(played[2]=='sail.wav')
        ''')

    def test_default_orders_use_generic_ack_without_guessing_target_and_respect_busy_gate(self):
        self.lua.execute('''
        VietnamVoiceBank.clips.INFANTRY.A2.acknowledge={{'ack-one.wav',.5},{'ack-two.wav',.5}}
        local a=add(1);selection={a};VietnamVoice_Start({[1]='vietnam'});VietnamVoice_Tick()
        local r=VietnamVoiceState.actors[1];now=1
        VietnamVoice_OnCommand({squad=a,command=SCMD_DefaultAction},r);assert(played[2]=='ack-one.wav')
        now=1.1;VietnamVoice_OnCommand({squad=a,command=SCMD_DefaultAction},r);assert(#played==2)
        now=2;VietnamVoice_OnCommand({squad=a,command=SCMD_DefaultAction},r);assert(played[3]=='ack-two.wav')
        ''')


if __name__=='__main__':unittest.main()

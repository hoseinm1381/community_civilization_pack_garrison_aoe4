"""Reusable original-squad journey fixture, independent of retired modal tests."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX

class TunnelNativeFixture(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua((ROOT/'assets/scar/vietnam/tunnel_core.scar').read_text())
        self.runlua('''
        tick=100;autoArrive=true;departures=0;arrivals=0;moveCount=0;stopCount=0;callbacks={};entityCallbacks={};tempGroups=0
        function World_GetGameTicks() return tick end
        function Squad_GetID(s) return s.id end
        function Squad_IsValid(id) for _,s in ipairs(squads) do if s.id==id then return true end end;return false end
        function Squad_IsAlive(s) return not s.dead end
        function Squad_GetPlayerOwner(s) return s.owner end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_GetFirstEntity(s) return s.entity end
        function Squad_GetPosition(s) assert(not s.despawned);return s.pos end
        function Squad_IsInHoldEntity(s) return s.held==true end
        function Squad_IsInHoldSquad(s) return false end
        function Squad_HasAbility(s,a) return s.ability==true end
        function Squad_AddAbility(s,a) s.ability=true end
        function Squad_RemoveAbility(s,a) s.ability=false end
        function Entity_IsOfType(e,t) return e.types and e.types[t]==true end
        function Entity_GetPlayerOwner(e) return e.owner or 11 end
        function Entity_GetStateModelBool(e,k) return e.active~=false end
        function Entity_GetHeading(e) return {x=0,z=1} end
        function SGroup_ForEachEx(g,f,a,b) for i,s in ipairs(g) do f(g,i,s) end end
        function Player_GetSquads(p) local g={};for _,s in ipairs(squads) do if s.owner==p then g[#g+1]=s end end;return g end
        function SGroup_CreateUniqueWithPrefix(p) tempGroups=tempGroups+1;return {} end
        function SGroup_Add(g,s) g[#g+1]=s end
        function SGroup_Destroy(g) tempGroups=tempGroups-1 end
        function SGroup_CountSpawned(g) local n=0;for _,s in ipairs(g) do if not s.despawned then n=n+1 end end;return n end
        function SGroup_GetSpawnedSquadAt(g,i) return g[i] end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        function Squad_DeSpawn(s) assert(not s.despawned);s.despawned=true;departures=departures+1 end
        function Squad_Spawn(s,p,kind) assert(s.despawned and kind=='');s.despawned=false;s.pos=p;arrivals=arrivals+1 end
        function Squad_TryFindClosestFreePosition(s,p) return p end
        function Cmd_Move(g,p) moveCount=moveCount+1;if autoArrive then g[1].pos=p end end
        function Cmd_Stop(g) stopCount=stopCount+1 end
        function requireNamedRule(f)
            for name,value in pairs(_G) do if value==f then return end end
            error('Adding unnamed function as rule')
        end
        function Rule_AddSquadEvent(f,s,event,data)
            requireNamedRule(f);callbacks[s.id]=function(context) return f(context,data) end
        end
        function Rule_RemoveSquadEvent(f,s) callbacks[s.id]=nil end
        function Rule_AddEntityEvent(f,e,event,data)
            requireNamedRule(f);entityCallbacks[e.id]=function(context) return f(context,data) end
        end
        function Rule_RemoveEntityEvent(f,e) entityCallbacks[e.id]=nil end
        function Core_GetPlayersTableEntry(id) for _,p in ipairs(PLAYERS) do if p.id==id then return p end end end
        function Obj_Create(...) return 1 end
        function Obj_SetState(...) end;function Obj_SetVisible(...) end;function Obj_SetTitle(...) end
        function Obj_SetCounterType(...) end;function Obj_SetCounterTimerSeconds(...) end;function Obj_Delete(...) end
        function Loc_GetString(s) return s end;function Loc_Empty() return '' end
        function BP_GetSquadBlueprint(s) return s end
        function addTraveler(id,x)
            local s={id=id,owner=11,ability=true,pos={x=x or -8,y=0,z=0},health=45,bp='combat'}
            s.entity={id=id+1000,types={}};registry[s.entity.id]=s.entity;squads[#squads+1]=s;return s
        end
        GE_SquadCommandIssued=9;DT_INFO_DEFAULT='InfoObjectiveDataTemplate';OT_Information=9;OS_Incomplete=1
        COUNTER_None=0;COUNTER_TimerDecreasing=2;R_ALLY=1
        function HintPoint_Add(e,visible,text,height,action,icon,priority,fow)
            hints=hints or {};hints[e.id]={fow=fow};return e.id
        end
        function HintPoint_Remove(id) hints[id]=nil end
        relationship=2;vision=false
        function Player_ObserveRelationship(a,b) return relationship end
        function Player_CanSeeEntity(p,e) return vision end
        ''')
        p=ROOT/'assets/scar/vietnam/tunnels.scar'
        self.assertTrue(p.exists(),'Tunnel controller not implemented')
        self.runlua(p.read_text())
        self.runlua('''
        VietnamTunnels_Start({[1]='vietnam',[2]='vietnam'})
        n1={id=1,x=0,z=0,hx=4,hz=4,root=true,reach=16};n2={id=2,x=24,z=0,hx=4,hz=4,reach=16};n3={id=3,x=48,z=0,hx=4,hz=4,reach=16}
        VietnamTunnelsState.players[1].graph=VietnamTunnelCore.Build({n1,n2,n3})
        -- A graph node is a live owned building, not just an integer accepted
        -- by a permissive mock. Simulation must recheck current ownership.
        for _,node in ipairs({n1,n2,n3}) do building(node.id,'tunnel_fixture',node.x,11) end
        s=addTraveler(2001)
        ''')


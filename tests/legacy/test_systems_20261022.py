"""Behavior checks for the approved systems; native scheduling/placement remain game gates."""
from test_runtime_repairs import RuntimeFixture, ROOT, PREFIX
import xml.etree.ElementTree as ET
from pathlib import Path
import zipfile


class GeometryTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        p=ROOT/'assets/scar/vietnam/tunnel_core.scar'
        self.assertTrue(p.exists(), 'New tunnel core not implemented')
        self.runlua(p.read_text(encoding='utf-8'))
        self.runlua('''
        function node(id,x,z,root,hx,hz,heading,reach)
          return {id=id,x=x,z=z,hx=hx or 4,hz=hz or 4,heading=heading or 0,root=root,reach=reach or 4}
        end
        ''')

    def test_edge_range_not_center_distance_or_two_overlapping_radii(self):
        self.runlua('a=node(1,0,0,true);b=node(2,12,0);c=node(3,24.01,0);g=VietnamTunnelCore.Build({a,b,c})')
        self.assertEqual(self.g.a.component,self.g.b.component)
        self.assertIsNone(self.g.c.component)

    def test_disconnected_cycle_does_not_generate_its_own_network(self):
        self.runlua('a=node(1,0,0,true);b=node(2,100,0);c=node(3,120,0);g=VietnamTunnelCore.Build({a,b,c})')
        self.assertIsNone(self.g.b.component)

    def test_multiple_tc_roots_merge_without_native_placement_restriction(self):
        self.runlua('a=node(5,0,0,true,4,4,0,8);b=node(2,16,0,true,4,4,0,8);g=VietnamTunnelCore.Build({a,b})')
        self.assertEqual(self.g.a.component,2)
        self.assertEqual(self.g.b.component,2)

    def test_rotated_footprint_distance_and_closest_point(self):
        self.runlua('a=node(1,0,0,true,8,2,math.pi/2);d,p=VietnamTunnelCore.PointDistance(a,0,10)')
        self.assertAlmostEqual(self.g.d,2)
        self.assertAlmostEqual(self.g.p.z,8)

    def test_crossed_thin_rectangles_overlap_even_without_contained_corners(self):
        self.runlua('a=node(1,0,0,true,8,1);b=node(2,0,0,false,8,1,math.pi/2);d=VietnamTunnelCore.Gap(a,b)')
        self.assertAlmostEqual(self.g.d,0)

    def test_nearest_entrance_ties_are_stable_and_destination_component_only(self):
        self.runlua('a=node(4,-20,0,true);b=node(2,20,0,true);g=VietnamTunnelCore.Build({a,b});chosen=VietnamTunnelCore.Nearest(g,2,0,0)')
        self.assertEqual(self.g.chosen.id,2)


class HeadquartersTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua((ROOT/'assets/scar/vietnam/tunnel_core.scar').read_text(encoding='utf-8'))
        self.runlua('''
        function Entity_GetPlayerOwner(e) return e.owner or 11 end
        function Entity_SetStateModelBool(e,k,v) e.flags=e.flags or {};e.flags[k]=v end
        function Entity_GetStateModelBool(e,k)
          if k=='landmark_active' then return e.active~=false end
          return e.flags and e.flags[k]==true or false
        end
        function Entity_IsDoingAbility(e,a) return e.doing==true end
        function Entity_HasAbility(e,a) return e.hasAbility==true end
        function Entity_AddAbility(e,a) e.hasAbility=true;e.added=(e.added or 0)+1 end
        function Entity_RemoveAbility(e,a) e.hasAbility=false;e.removed=(e.removed or 0)+1 end
        function Entity_StopAbility(e,a,early) e.stopped=(e.stopped or 0)+1;e.doing=false end
        function Player_GetAllEntities(p) return entities end
        function Entity_GetHeading(e) return {x=0,z=1} end
        function Entity_GetPosition(e) return {x=e.x or 0,y=0,z=e.z or 0} end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        ''')
        self.runlua((ROOT/'assets/scar/vietnam/landmarks.scar').read_text(encoding='utf-8'))
        self.runlua("hq=building(91,'vn_building_landmark_age2_headquarter_vit',0);hq.owner=11;v=building(92,'vn_unit_villager_1_chi',0);v.building=false;v.owner=11;v.x=39")

    def tick(self):self.runlua('VietnamLandmarks_Update(PLAYERS[1],entities)')

    def test_automatic_coverage_uses_footprint_edge_and_exact_economic_receivers(self):
        self.tick()
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal'])
        self.runlua('v.x=40.1;v.doing=true');self.tick()
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertIsNone(self.g.v.stopped)
        self.assertTrue(self.g.v.hasAbility)
        self.assertIsNone(self.g.v.removed)

    def test_other_owners_are_not_covered(self):
        self.runlua('v.owner=22');self.tick()
        self.assertIsNone(self.g.v.flags)

    def test_native_stealth_receiver_persists_without_recreation_through_exit_and_reentry(self):
        self.runlua('v.x=100');self.tick();self.assertIsNone(self.g.v.added)
        self.runlua('v.x=30;now=4');self.tick();self.assertEqual(self.g.v.added,1)
        self.runlua('now=33.75');self.tick();self.assertEqual(self.g.v.added,1)
        self.runlua('now=95');self.tick();self.assertEqual(self.g.v.added,1)
        self.runlua('v.x=100');self.tick();self.assertTrue(self.g.v.hasAbility)
        self.assertIsNone(self.g.v.removed)
        self.runlua('v.x=30');self.tick();self.assertEqual(self.g.v.added,1)
        self.assertIsNone(self.g.v.stopped)

    def test_trained_villager_static_binding_is_never_stopped_or_recreated_on_entry(self):
        self.runlua('v.hasAbility=true;v.doing=true')
        self.tick();self.tick()
        self.assertIsNone(self.g.v.added)
        self.assertIsNone(self.g.v.stopped)
        self.assertIsNone(self.g.v.removed)

    def test_missing_receiver_after_an_upgrade_is_repaired_without_removing_other_bindings(self):
        self.tick();self.runlua("v.bp='a743d7d1d7534cf78817e29d8ded7366:vn_unit_villager_3_chi';v.hasAbility=false")
        self.tick();self.assertEqual(self.g.v.added,2)
        self.assertIsNone(self.g.v.removed)

    def test_receiver_capture_reassigns_coverage_owner_before_old_owner_cleanup(self):
        self.tick()
        self.runlua("v.owner=22;other=building(93,'vn_building_landmark_age2_headquarter_vit',0);other.owner=22;VietnamLandmarks_Update(PLAYERS[2],entities)")
        self.tick()
        self.assertEqual(self.g.VietnamLandmarksState.targets[92].owner,2)
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertIsNone(self.g.v.stopped)

    def test_headquarters_capture_disables_old_owner_coverage(self):
        self.tick();self.runlua('hq.owner=22');self.tick()
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertTrue(self.g.v.hasAbility)

    def test_departure_changes_eligibility_without_abrupt_passive_stop(self):
        self.tick();self.runlua('v.x=100;v.doing=false');self.tick()
        self.assertIsNone(self.g.v.stopped)
        self.assertTrue(self.g.v.hasAbility)
        self.assertIsNone(self.g.v.removed)

    def test_blueprint_conversion_does_not_write_foreign_state_schema(self):
        self.tick();self.runlua("v.bp='foreign';v.flags=nil;v.hasAbility=false")
        self.tick();self.assertIsNone(self.g.v.flags)

    def test_ruin_partial_and_full_repair(self):
        self.tick();self.runlua('hq.active=false;hq.dead=true;hq.health=0');self.tick()
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.runlua('hq.active=true;hq.dead=false;hq.health=50;hq.maximum=100');self.tick()
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.runlua('hq.health=100');self.tick()
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal'])

    def test_cleanup_is_idempotent_and_preserves_receiver_binding(self):
        self.tick();self.runlua('v.doing=true;VietnamLandmarks_Cleanup();VietnamLandmarks_Cleanup()')
        self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])
        self.assertIsNone(self.g.v.stopped)
        self.assertTrue(self.g.v.hasAbility)
        self.assertIsNone(self.g.v.removed)

    def test_death_and_fast_partial_repair_between_ticks_stays_disabled(self):
        self.tick()
        self.runlua('VietnamLandmarks_OnEntityKilled({victim=hq});hq.health=50;hq.active=true')
        self.tick();self.assertFalse(self.g.v.flags['is_in_stealth_aura_mal'])

    def test_another_operational_headquarters_preserves_union_of_coverage(self):
        self.runlua("other=building(93,'vn_building_landmark_age2_headquarter_vit',0);other.owner=11")
        self.tick();self.runlua('hq.dead=true;hq.health=0;v.doing=true');self.tick()
        self.assertTrue(self.g.v.flags['is_in_stealth_aura_mal']);self.assertIsNone(self.g.v.stopped)


class GardenTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua(r'''
        PITEM_Spawn=1;royals={};queued=0;grants=0;pop=0;popcap=200;CT_Personnel=1
        function Player_GetCurrentPopulation(p,kind) return pop end
        function Player_GetCurrentPopulationCap(p,kind) return popcap end
        function BP_GetSquadBlueprint(n) return n end
        function SGroup_ForEachEx(g,f,a,b) for i,s in ipairs(g) do f(g,i,s) end end
        function Player_GetSquads(p) return royals end
        function Squad_GetBlueprint(s) return s.bp end
        function Squad_IsAlive(s) return not s.dead end
        function Squad_IsValid(s) return s~=nil end
        function Squad_GetID(s) return s.id end
        function Squad_CreateAndSpawnToward(bp,p,count,pos,toward)
          grants=grants+1;local s={id=grants,bp=bp};royals[#royals+1]=s;pop=pop+3;return s
        end
        function Entity_HasProductionQueue(e) return true end
        function Entity_GetProductionQueueSize(e) return #(e.queue or {}) end
        function Entity_GetProductionQueueItemType(e,i) return PITEM_Spawn end
        function Entity_GetProductionQueueItem(e,i) return e.queue[i+1] end
        function Entity_QueueProductionItemByPBG(e,kind,bp)
          if pop+3>popcap then return false end
          e.queue=e.queue or {};e.queue[#e.queue+1]=bp;queued=queued+1;return true
        end
        function Entity_CancelProductionQueueItem(e,i) table.remove(e.queue,i+1) end
        function Entity_GetPlayerOwner(e) return e.owner or 11 end
        function Entity_GetStateModelBool(e,k) return e.active~=false end
        function EGroup_CountSpawned(g) return #g end
        function EGroup_GetSpawnedEntityAt(g,i) return g[i] end
        ''')
        p=ROOT/'assets/scar/vietnam/garden.scar';self.assertTrue(p.exists(),'Garden lifecycle not implemented')
        self.runlua(p.read_text(encoding='utf-8'))
        self.runlua("garden=building(700,'vn_building_landmark_age3_imperial_garden_vit',0);garden.owner=11;VietnamGarden_Start({[1]='vietnam'})")

    def tick(self):self.runlua('VietnamGarden_Update(PLAYERS[1],entities)')

    def test_initial_grant_then_one_native_queue_after_death(self):
        self.tick();self.tick();self.assertEqual(self.g.grants,1)
        self.runlua('royals[1].dead=true;pop=0');self.tick();self.tick()
        self.assertEqual(self.g.queued,1)
        self.assertEqual(len(self.g.garden.queue),1)

    def test_foundation_and_full_population_do_not_bypass_native_population(self):
        self.runlua('garden.incomplete=true');self.tick();self.assertEqual(self.g.grants,0)
        self.runlua('garden.incomplete=false;pop=200');self.tick();self.assertEqual(self.g.grants,0)
        self.runlua('pop=197');self.tick();self.assertEqual(self.g.grants,1)

    def test_destruction_cancels_only_royal_queue_and_repair_never_regrants(self):
        self.tick();self.runlua('royals[1].dead=true;pop=0');self.tick()
        self.runlua('garden.active=false;garden.dead=true;garden.health=0');self.tick()
        self.assertEqual(len(self.g.garden.queue),0)
        self.runlua('garden.active=true;garden.dead=false;garden.health=50');self.tick()
        self.assertEqual(self.g.queued,1)
        self.runlua('garden.health=100');self.tick()
        self.assertEqual(self.g.grants,1)
        self.assertEqual(self.g.queued,2)

    def test_two_gardens_and_foreign_royal_cannot_duplicate(self):
        self.runlua("other=building(701,'vn_building_landmark_age3_new_imperial_garden',0);other.owner=11")
        self.tick();self.assertEqual(self.g.grants,1)
        self.tick();self.assertEqual(self.g.queued,0)

    def test_death_before_first_observation_then_fast_repair_queues_replacement(self):
        self.runlua('VietnamGarden_OnEntityKilled({victim=garden});garden.health=100')
        self.tick();self.assertEqual(self.g.grants,0);self.assertEqual(self.g.queued,1)

    def test_unrelated_queue_is_not_cancelled(self):
        self.tick();self.runlua('royals[1].dead=true;pop=0');self.tick()
        self.runlua("garden.queue[#garden.queue+1]='unrelated';VietnamGarden_OnEntityKilled({victim=garden})")
        self.assertEqual(len(self.g.garden.queue),1);self.assertEqual(self.g.garden.queue[1],'unrelated')


class SystemsTuningTests(RuntimeFixture):
    def test_user_native_receiver_bindings_are_preserved_exactly(self):
        before=ROOT/'work/vietnam_redesign/runtime_v5_20261023/before.zip'
        for key in ('vn_unit_villager_1_chi','vn_unit_villager_3_chi','vn_unit_trade_cart_chi'):
            p=next((ROOT/'assets/attrib/instances/ebps').rglob(key+'.xml'))
            t=ET.parse(p).getroot()
            with zipfile.ZipFile(before) as snapshot:
                baseline=ET.fromstring(snapshot.read(p.relative_to(ROOT).as_posix()))
            def bindings(tree):
                return [dict(n.attrib) for n in tree.iter('instance_reference')
                        if n.get('value','').endswith('\\vn_activate_stealth_forvills_vit')]
            self.assertEqual(bindings(t),bindings(baseline))
        source=(ROOT/'assets/scar/vietnam/landmarks.scar').read_text()
        self.assertNotIn('Entity_RemoveAbility',source)

    def test_receiver_gate_is_the_only_change_to_working_user_ability(self):
        p=ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
        with zipfile.ZipFile(ROOT/'work/vietnam_redesign/runtime_v5_20261023/before.zip') as snapshot:
            before=ET.fromstring(snapshot.read(p.relative_to(ROOT).as_posix()))
        current=ET.parse(p).getroot()
        gate=current.find('.//list[@name="requirements"]')
        self.assertEqual(len(gate),1)
        required=gate[0]
        self.assertEqual(required.get('value'),r'requirements\required_statemodelbool')
        self.assertEqual(required.get('List.ItemID'),'1073741853')
        expected={'key':'is_in_stealth_aura_mal','data_source_type':'entity_datasource',
                  'default_value':'False','compare_to_value':'True','reason':'usage','ui_name':'0'}
        self.assertEqual({n.get('name'):n.get('value') for n in required},expected)
        def canonical(node):
            return (node.tag,tuple(sorted(node.attrib.items())),tuple(canonical(c) for c in node))
        for tree in (before,current):
            tree.find('.//list[@name="requirements"]').clear()
        self.assertEqual(canonical(current),canonical(before))

    def test_gardens_declare_one_hidden_native_free_royal_spawn_item(self):
        for key in ('vn_building_landmark_age3_imperial_garden_vit','vn_building_landmark_age3_new_imperial_garden'):
            p=next((ROOT/'assets/attrib/instances/ebps').rglob(key+'.xml'))
            t=ET.parse(p).getroot()
            for queue in t.findall('.//template_reference[@value="ebpextensions\\spawner_ext"]/list[@name="spawn_items"]'):
                items=list(queue)
                self.assertEqual(len(items),1)
                self.assertTrue(items[0].find('instance_reference[@name="squad"]').get('value').endswith('_free'))
                self.assertEqual(items[0].find('bool[@name="can_be_cancelled"]').get('value'),'False')
                self.assertEqual(items[0].find('instance_reference[@name="hotkey_binding"]').get('value'),'')
                self.assertTrue(all(n.get('value')=='-1' for n in items[0].findall('group[@name="ui_position"]/int')))

    def test_economic_schema_declares_all_native_stealth_action_state(self):
        expected={'is_in_stealth_aura_mal':('bool','False'),
                  'is_toggled_stealth':('bool','False'),
                  'stealth_ended_local_knowledge':('bool','False'),
                  'stealth_start_time_in_ticks':('int','0')}
        for role,parent in [('villager','villager'),('trader','trade_cart')]:
            tree=ET.parse(ROOT/f'assets/attrib/instances/statemodel_schema/vietnam/vn_headquarters_{role}.xml').getroot()
            self.assertEqual(tree.find('./instance_reference').get('value'),f'statemodel_schema\\units\\{parent}')
            actual={}
            for prop in tree.findall('.//template_reference'):
                key=prop.find('./enum');default=prop.find('./bool') if prop.find('./bool') is not None else prop.find('./int')
                if key is not None:actual[key.get('value')]=(default.tag,default.get('value'))
            self.assertEqual(actual,expected)

    def test_free_royal_has_three_population_and_100_second_training(self):
        for category,field,value in [('sbps','personnel_pop','0'),('ebps','personnel_pop','3'),('ebps','time_seconds','100')]:
            p=next((ROOT/'assets/attrib/instances'/category).rglob('vn_unit_war_elephant_handcannon_4_vit_free.xml'))
            t=ET.parse(p).getroot()
            self.assertEqual(t.find(f'.//float[@name="{field}"]').get('value'),value)

    def test_native_automatic_receiver_is_not_a_squad_button(self):
        p=ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml'
        t=ET.parse(p).getroot()
        self.assertEqual(t.find('.//bool[@name="disable_when_active"]').get('value'),'False')
        self.assertEqual(t.find('.//float[@name="recharge_time"]').get('value'),'0')
        self.assertEqual(t.find('.//bool[@name="can_queue_passive_ability"]').get('value'),'False')
        self.assertIsNotNone(t.find('.//enum[@name="key"][@value="is_in_stealth_aura_mal"]'))
        self.assertEqual(t.find('.//state_tree_node[@name="entity_tree"]').get('value'),
                         r'activate_stealth_mal\Master\Defer_EnableStealth\EnableStealth')

    def test_old_shinobi_teleport_action_is_disconnected(self):
        t=ET.parse(ROOT/'assets/attrib/instances/abilities/vietnam/vn_vietnam_unit_mov_vit.xml').getroot()
        self.assertEqual(t.find('.//state_tree_node[@name="ability_activate_deferred_tree"]').get('value'),'')


class TunnelJourneyTests(RuntimeFixture):
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

    def request(self,ids='2001',dest=3):self.runlua(f"VietnamTunnels_NetRequest(11,'{dest};{ids}')")
    def step(self,t):self.runlua(f'now={t};tick=101+math.floor(now*8);VietnamTunnels_Step(now,tick)')

    def test_same_tick_unlimited_batch_and_later_tick_rejected(self):
        self.runlua('for i=2,35 do addTraveler(2000+i) end')
        self.request(','.join(str(2000+i) for i in range(1,31)))
        self.request(','.join(str(2000+i) for i in range(31,36)),dest=2)
        self.step(.1)
        self.assertEqual(self.g.moveCount,35)
        self.runlua('late=addTraveler(2100)');self.request('2100')
        self.step(.2);self.assertEqual(self.g.moveCount,35)

    def test_loading_travel_unload_and_first_arrival_cooldown_preserve_identity(self):
        self.request();self.step(.1);self.step(3.1)
        self.assertTrue(self.g.s.despawned)
        self.step(5.1);self.assertTrue(self.g.s.despawned)
        self.step(6.1)
        self.assertFalse(self.g.s.despawned)
        self.assertEqual(self.g.s.id,2001);self.assertEqual(self.g.s.health,45)
        self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,36.1)
        self.assertEqual(self.g.moveCount,1);self.assertEqual(self.g.tempGroups,0)

    def test_player_move_cancels_without_reissuing_or_stopping_player_order(self):
        self.request();self.step(.1)
        self.runlua('callbacks[2001]({});s.pos={x=-100,y=0,z=0}')
        self.step(10)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.moveCount,1)
        self.assertEqual(self.g.s.pos.x,-100);self.assertEqual(self.g.tempGroups,0)
        self.assertEqual(self.g.stopCount,0)

    def test_manual_move_while_pending_is_not_overwritten_at_admission(self):
        self.request();self.runlua('callbacks[2001]({});s.pos={x=-100,y=0,z=0}')
        self.step(.1);self.step(4)
        self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.stopCount,0)
        self.assertEqual(self.g.departures,0);self.assertIsNone(self.g.callbacks[2001])

    def test_expired_pending_observer_is_removed_and_cleanup_is_idempotent(self):
        self.request();self.assertIsNotNone(self.g.callbacks[2001]);self.step(16)
        self.assertIsNone(self.g.callbacks[2001]);self.request()
        self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.callbacks[2001])

    def test_unreachable_entrance_times_out_without_despawn(self):
        self.runlua('autoArrive=false;s.pos={x=-1000,y=0,z=0}')
        self.request();self.step(.1);self.step(15.2)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.tempGroups,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,0)
        self.assertEqual(self.g.stopCount,1)

    def test_deadline_is_measured_from_activation_not_later_admission(self):
        self.request();self.step(13);self.step(16)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.tempGroups,0)
        self.assertEqual(self.g.stopCount,1)

    def test_expired_request_is_not_ordered_after_delayed_admission(self):
        self.request();self.step(16)
        self.assertEqual(self.g.moveCount,0);self.assertEqual(self.g.tempGroups,0)

    def test_exit_destroyed_before_departure_stops_owned_approach(self):
        self.request();self.step(.1)
        self.runlua('VietnamTunnels_OnEntityKilled({victim={id=3}})');self.step(1)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.stopCount,1)

    def test_exit_loss_returns_same_squad_and_does_not_start_cooldown(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('VietnamTunnelsState.players[1].graph.byID[3]=nil')
        self.step(6.1)
        self.assertFalse(self.g.s.despawned);self.assertEqual(self.g.s.id,2001)
        self.assertLess(self.g.s.pos.x,0)
        self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,0)

    def test_entrance_loss_or_relay_disconnection_does_not_stop_existing_transit(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('VietnamTunnelsState.players[1].graph.byID[1]=nil;n3.component=nil')
        self.step(6.1)
        self.assertEqual(self.g.arrivals,1);self.assertEqual(self.g.s.pos.x,48)

    def test_cleanup_returns_in_transit_and_removes_observers(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('VietnamTunnels_Cleanup();VietnamTunnels_Cleanup()')
        self.assertFalse(self.g.s.despawned);self.assertEqual(self.g.tempGroups,0)

    def test_forged_other_owner_or_economy_unit_is_rejected(self):
        self.runlua("s.owner=22;v=addTraveler(2002);v.entity.types.villager=true")
        self.request('2001,2002');self.step(.1)
        self.assertEqual(self.g.moveCount,0)

    def test_trade_cart_siege_naval_and_buffalo_are_excluded(self):
        self.runlua("s.entity.types.trade_cart=true;a=addTraveler(2002);a.entity.types.siege=true;b=addTraveler(2003);b.entity.types.naval_unit=true;c=addTraveler(2004);c.bp='"+PREFIX+"vn_unit_water_buffalo_vit'")
        self.request('2001,2002,2003,2004');self.step(.1);self.assertEqual(self.g.moveCount,0)

    def test_conversion_before_departure_cancels_and_preserves_new_owner(self):
        self.request();self.step(.1);self.runlua('s.owner=22');self.step(3.1)
        self.assertEqual(self.g.departures,0);self.assertEqual(self.g.s.owner,22)

    def test_fast_exit_repair_does_not_rescue_a_destroyed_destination(self):
        self.request();self.step(.1);self.step(3.1)
        self.runlua('VietnamTunnels_OnEntityKilled({victim={id=3}})')
        self.step(6.1)
        self.assertLess(self.g.s.pos.x,0);self.assertEqual(self.g.VietnamTunnelsState.players[1].cooldown,0)

    def test_later_arrivals_do_not_extend_first_arrival_cooldown(self):
        self.runlua('other=addTraveler(2002)');self.request('2001',2);self.request('2002',3)
        self.step(.1);self.step(3.1);self.step(5.1)
        self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,35.1)
        self.step(6.1);self.assertAlmostEqual(self.g.VietnamTunnelsState.players[1].cooldown,35.1)

    def test_destinations_follow_ordinary_vision_for_enemies(self):
        self.runlua("target=building(3,'target',0);localPlayer=22")
        self.request();self.step(.1);self.runlua('VietnamTunnels_UpdateUI()')
        self.assertIsNone(self.g.hints)
        self.runlua('vision=true;VietnamTunnels_UpdateUI()');self.assertFalse(self.g.hints[3].fow)
        self.runlua('vision=false;VietnamTunnels_UpdateUI()');self.assertIsNone(self.g.hints[3])

    def test_allies_can_see_destination_without_revealing_terrain(self):
        self.runlua("target=building(3,'target',0);localPlayer=22;relationship=R_ALLY")
        self.request();self.step(.1);self.runlua('VietnamTunnels_UpdateUI()')
        self.assertTrue(self.g.hints[3].fow)

    def test_modal_command_snapshots_selection_and_networks_owned_ids(self):
        self.runlua("TP_Position=1;TP_Cancelled=2;selected={s};target=building(3,'target',0);hovered=target")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position);selected={}")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.assertIsNone(self.g.sentMessage)
        self.runlua("entityCallbacks[3001]({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'})")
        self.assertEqual(self.g.sentMessage,'3;2001');self.step(.25)
        self.assertEqual(self.g.moveCount,1)

    def test_named_selection_callbacks_route_each_squad_and_keep_manual_cancellation(self):
        self.runlua("TP_Position=1;TP_Cancelled=2;other=addTraveler(2002);selected={s,other};target=building(3,'target',0);hovered=target")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.runlua("entityCallbacks[3001]({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'});callbacks[2001]({})")
        self.assertIsNone(self.g.sentMessage)
        self.runlua("entityCallbacks[3002]({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'})")
        self.assertEqual(self.g.sentMessage,'3;2002')
        self.step(.25)
        self.assertEqual(self.g.moveCount,1)
        self.assertIsNone(self.g.entityCallbacks[3001]);self.assertIsNone(self.g.entityCallbacks[3002])

    def test_stale_named_selection_callback_cannot_complete_a_replacement_selection(self):
        self.runlua("TP_Position=1;TP_Cancelled=2;selected={s};target=building(3,'target',0);hovered=target")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position);oldCallback=entityCallbacks[3001]")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Position)")
        self.runlua("VietnamTunnels_AbilityPhase('"+PREFIX+"vn_vietnam_unit_mov_vit',TP_Issued)")
        self.runlua("oldCallback({ability='"+PREFIX+"vn_vietnam_unit_mov_vit'})")
        self.assertIsNone(self.g.sentMessage)
        self.runlua('VietnamTunnels_Cleanup()')
        self.assertIsNone(self.g.entityCallbacks[3001]);self.assertIsNone(self.g.callbacks[2001])

    def test_graph_adapter_rejects_foundations_and_ruins_until_fully_repaired(self):
        self.runlua('''
        VietnamTunnelBuildings={test_tc={hx=4,hz=4,axis=true,root=true},test_landmark={hx=4,hz=4,axis=true}}
        tc=building(10,'test_tc',0);tc.owner=11
        lm=building(11,'test_landmark',0);lm.owner=11;lm.x=12;lm.types={landmark=true};lm.incomplete=true
        VietnamTunnels_Update(PLAYERS[1],entities)
        ''')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].graph.byID[11])
        self.runlua('lm.incomplete=false;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertEqual(self.g.VietnamTunnelsState.players[1].graph.byID[11].component,10)
        self.runlua('VietnamTunnels_OnEntityKilled({victim=lm});lm.health=50;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].graph.byID[11])
        self.runlua('lm.health=100;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertEqual(self.g.VietnamTunnelsState.players[1].graph.byID[11].component,10)

    def test_graph_checks_building_class_before_construction_queries(self):
        self.runlua('''
        VietnamTunnelBuildings={test_tc={hx=4,hz=4,axis=true,root=true}}
        tc=building(10,'test_tc',0);tc.owner=11
        unit=building(11,'test_tc',0);unit.owner=11;unit.building=false
        function Entity_IsUnderConstruction(e) assert(e.building);return false end
        function Entity_GetBuildingProgress(e) assert(e.building);return 1 end
        VietnamTunnels_Update(PLAYERS[1],entities)
        ''')
        self.assertIsNone(self.g.VietnamTunnelsState.players[1].graph.byID[11])

    def test_dynamic_ability_is_removed_on_conversion_and_cleanup(self):
        self.runlua('VietnamTunnelBuildings={};s.ability=false;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertTrue(self.g.s.ability)
        self.runlua('s.owner=22;VietnamTunnels_Update(PLAYERS[1],entities)')
        self.assertFalse(self.g.s.ability)
        self.runlua('s.owner=11;VietnamTunnels_Update(PLAYERS[1],entities);VietnamTunnels_Cleanup()')
        self.assertFalse(self.g.s.ability)

"""Empty Gardens native-event controller under mocked APIs; no runtime claim."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import unittest,xml.etree.ElementTree as E
from test_runtime_repairs import RuntimeFixture,ROOT,PREFIX
NAME='vn_upgrade_empty_gardens_vit'
A=ROOT/'assets/attrib/instances'

class EmptyGardensSourceTests(unittest.TestCase):
    def test_research_cost_age_shared_completion_and_ministry_links(self):
        p=A/'upgrade/vietnam'/(NAME+'.xml');self.assertTrue(current_path(p).exists(),'Research not implemented')
        t=parse_current_xml(p).getroot();b=t.find('group');c=b.find('group[@name="time_cost"]')
        self.assertEqual([c.find('enum_table/float[@name="'+k+'"]').get('value') for k in ['food','wood','gold','stone']],['0','50','150','0'])
        self.assertEqual(c.find('float[@name="time_seconds"]').get('value'),'30')
        self.assertEqual(b.find('enum[@name="owner_type"]').get('value'),'player')
        self.assertEqual(b.find('float[@name="global_max_limit"]').get('value'),'1')
        req=b.find('list[@name="requirements"]');self.assertEqual(len(req),2)
        self.assertEqual(req[0].find('instance_reference').get('value'),r'upgrade\dev\ages\castle_age')
        self.assertEqual(req[1].find('instance_reference').get('value'),'upgrade\\vietnam\\'+NAME)
        self.assertEqual(req[1].find('bool[@name="include_queued"]').get('value'),'True')
        self.assertEqual(req[1].find('bool[@name="include_completed"]').get('value'),'True')
        self.assertEqual(req[1].find('bool[@name="is_present"]').get('value'),'False')
        self.assertEqual(b.find('instance_reference[@name="hotkey_binding"]').get('value'),'')
        self.assertFalse(any(x.get('value') for x in b.findall('group[@name="state_tree_references"]//state_tree_node')))
        ministry=parse_current_xml(A/'ebps/vietnam/vn_building_econ_food_control_chi.xml').getroot()
        for scope in [ministry,*ministry.findall('variant')]:
            table=scope.find('list/template_reference[@value="ebpextensions\\upgrade_ext"]/list')
            self.assertEqual(sum(n.get('value')=='upgrade\\vietnam\\'+NAME for n in table),1)

class EmptyGardensBehaviorTests(RuntimeFixture):
    def setUp(self):
        super().setUp()
        self.runlua("function World_GetPlayerIndex(p) if type(p)=='table' then return p.index end;for _,v in ipairs(PLAYERS) do if v.id==p then return v.index end end;return -1 end")
        p=ROOT/'assets/scar/vietnam/empty_gardens.scar';self.assertTrue(current_path(p).exists(),'Controller not implemented')
        self.runlua('''
        RT_Food=1;RT_Wood=2;RT_Gold=3;RT_Stone=4;RES_RefundOnDeath=7;GE_EntityKilled=8
        refunds={};costs={};listeners=0;removedListeners=0;hasResearch={[11]=true,[22]=true}
        function Rule_AddGlobalEvent(f,event) assert(event==GE_EntityKilled);listeners=listeners+1 end
        function Rule_RemoveGlobalEvent(f) removedListeners=removedListeners+1 end
        function Player_HasUpgrade(p,u) return hasResearch[p]==true end
        function BP_GetEntityBPCost(bp) return costs[bp] or {food=0,wood=0,gold=0,stone=0} end
        function Player_GetEntityBPCost() error('Modified cost must not be queried') end
        function Player_AddResource(p,r,v) refunds[#refunds+1]={p=p,r=r,v=v} end
        function total(p,r) local n=0;for _,v in ipairs(refunds) do if v.p==p and (r==nil or v.r==r) then n=n+v.v end end;return n end
        ''')
        self.runlua(current_path(p).read_text(encoding='utf-8'))
        self.runlua("house=building(601,'vn_building_house_control_chi',0);costs[house.bp]={food=0,wood=50,gold=0,stone=0};VietnamEmptyGardens_Start({[1]='vietnam',[2]='china'})")

    def kill(self,entity='house',owner=11,killer='nil'):
        self.runlua('VietnamEmptyGardens_OnEntityKilled({victim='+entity+',victimOwner='+str(owner)+',killer='+killer+'})')

    def test_enemy_destruction_manual_deletion_fractional_and_duplicate_delivery(self):
        self.runlua('house.dead=true;house.health=0')
        self.kill(killer='{}');self.kill();self.assertEqual(self.lua.eval('total(11)'),12.5)
        self.runlua("other=building(602,'vn_building_house_control_chi',0)")
        self.kill('other');self.assertEqual(self.lua.eval('total(11)'),25)

    def test_four_resources_listed_cost_not_discounted_or_upgrade_cost(self):
        self.runlua('costs[house.bp]={food=100,wood=200,gold=300,stone=400};house.paidCost=1;house.upgradeCost=10000')
        self.kill()
        self.assertEqual([self.lua.eval('total(11,'+str(k)+')') for k in range(1,5)],[25,50,75,100])

    def test_fortified_hideout_refunds_base_construction_only_and_free_trap_zero(self):
        self.runlua("house.bp='"+PREFIX+"vn_building_defense_outpost_chi_fortified';costs[house.bp]={wood=50,food=0,gold=0,stone=0};house.upgradeCost={wood=50,stone=50}")
        self.kill();self.assertEqual(self.lua.eval('total(11)'),12.5)
        self.runlua("trap=building(603,'vn_building_bambo_outpost_chi_passable',0)");self.kill('trap')
        self.assertEqual(self.lua.eval('total(11)'),12.5)

    def test_landmarks_wonders_and_units_excluded(self):
        self.runlua("house.types={landmark=true}");self.kill();self.assertEqual(self.lua.eval('total(11)'),0)
        self.runlua("w=building(602,'wonder',0);w.types={wonder=true};costs[w.bp]={wood=3000}");self.kill('w')
        self.runlua('u=unit(603,0);u.bp=house.bp');self.kill('u');self.assertEqual(self.lua.eval('total(11)'),0)

    def test_incomplete_cancel_and_pre_research_death_never_pay_retroactively(self):
        self.runlua('house.incomplete=true;house.progress=0.5');self.kill();self.assertEqual(self.lua.eval('total(11)'),0)
        self.runlua("old=building(602,'vn_building_house_control_chi',0);hasResearch[11]=false");self.kill('old')
        self.runlua('hasResearch[11]=true');self.kill('old');self.assertEqual(self.lua.eval('total(11)'),0)

    def test_owner_isolation_and_defeated_world_missing_owner_ignored(self):
        self.kill(owner=22);self.kill(owner=99);self.assertEqual(self.lua.eval('total(11)'),0)
        self.runlua('VietnamEmptyGardens_OnEntityKilled({victim=house});function Player_IsAlive() return false end')
        self.kill();self.assertEqual(self.lua.eval('total(11)'),0)

    def test_event_owner_wrapper_is_resolved_by_index(self):
        self.runlua('VietnamEmptyGardens_OnEntityKilled({victim=house,victimOwner={index=1}})')
        self.assertEqual(self.lua.eval('total(11)'),12.5)

    def test_registration_is_once_and_cleanup_removes_listener_and_blocks_refund(self):
        self.runlua("VietnamEmptyGardens_Start({[1]='vietnam'});VietnamEmptyGardens_Cleanup();VietnamEmptyGardens_Cleanup()")
        self.assertEqual(self.g.listeners,1);self.assertEqual(self.g.removedListeners,1)
        self.kill();self.assertEqual(self.lua.eval('total(11)'),0)

if __name__=='__main__':unittest.main()

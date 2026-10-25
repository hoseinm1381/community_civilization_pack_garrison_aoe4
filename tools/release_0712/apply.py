"""Build exact 0712 edits from frozen 0711; no historical source is overwritten."""
import copy,re,zipfile,xml.etree.ElementTree as E
from common import *

def expected_changes():
    changes={}
    with zipfile.ZipFile(OUT/'baseline/source.zip') as z:
        def text(p):return z.read(p).decode('utf-8-sig').replace('\r\n','\n')
        for age in (2,3,4):
            p=f'assets/attrib/instances/weapon/vietnam/vn_weapon_skirmisher_{age}_vit.xml';s=text(p)
            assert s.count('<float name="wind_up" value="0.25"')==1
            assert s.count('value="1.375"')==2
            changes[p]=s.replace('<float name="wind_up" value="0.25"','<float name="wind_up" value="0.5"').replace('value="1.375"','value="1.125"')
        p='assets/scar/vietnam/presentation.scar';s=text(p)
        anchor='local function collect(player)'
        helper='''-- Player handles can be distinct wrappers for the same native player ID.
local function localPlayerEntry()
    local localPlayer = Game_GetLocalPlayer()
    if localPlayer == nil then return nil end
    local id = Player_GetID(localPlayer)
    for _, player in ipairs(PLAYERS) do
        if Player_GetID(player.id) == id then return player end
    end
    return nil
end

'''
        s=s.replace(anchor,helper+anchor,1)
        s=s.replace('Core_GetPlayersTableEntry(Game_GetLocalPlayer())','localPlayerEntry()')
        s=s.replace('    Misc_SelectSquad(target.squad, true)','    Misc_SelectSquad(target.squad, true)\n    Camera_FocusOnPosition(Squad_GetPosition(target.squad))',1)
        s=s.replace('model.vietnam_buffalo_cycle = nil','model.vietnam_buffalo_cycle = nil\n        model.vietnam_buffalo_can_cycle = false')
        s=s.replace('                model.vietnam_buffalo_cycle = hud.command','                model.vietnam_buffalo_cycle = hud.command\n                model.vietnam_buffalo_can_cycle = model.vietnam_buffalo_count > 0',1)
        changes[p]=s
        p='assets/ui/resources/hudresources.xaml';s=text(p);a=s.index('    <DataTemplate x:Key="VietnamBuffaloCounter"');before,custom=s[:a],s[a:]
        a=custom.index('                <Button.IsEnabled>');b=custom.index('                </Button.IsEnabled>',a)+len('                </Button.IsEnabled>')
        custom=custom[:a]+'''                <Button.IsEnabled><Binding Path="LocalPlayer.ScarModel[vietnam_buffalo_can_cycle]" /></Button.IsEnabled>'''+custom[b:]
        custom=custom.replace('                Command="{Binding LocalPlayer.ScarModel[vietnam_buffalo_cycle]}"',
            '                IsHitTestVisible="True" Background="Transparent"\n                Command="{Binding LocalPlayer.ScarModel[vietnam_buffalo_cycle]}"',1)
        custom=custom.replace('Width="14" Height="14" Background="#9020281B" BorderBrush="#A8B79B6D" BorderThickness="1" CornerRadius="7" Opacity="0.65"',
            'Width="48" Height="48" Background="#D020281B" BorderBrush="#E7C66F" BorderThickness="2" CornerRadius="24" Opacity="0.95"')
        custom=custom.replace('<Image Width="10" Height="10"','<Image Width="40" Height="40"')
        changes[p]=before+custom
        p='assets/ui/hud/pages/cardinalhudpage.xaml';s=text(p)
        assert s.count('Content="{Binding TagData}" Margin="0,-18,0,0"')==1
        changes[p]=s.replace('Content="{Binding TagData}" Margin="0,-18,0,0"','Content="{Binding TagData}" Margin="0,-52,0,0"',1)
        p='assets/scar/vietnam/tunnels.scar';s=text(p)
        s=s.replace('-- Select identity across ALL owned buildings before checking support,\n-- completion or connectivity. Never jump over the closest invalid building.',
            '-- Snap ground clicks within 8m of a footprint edge to the nearest eligible\n-- completed, owned, connected building. Invalid neighbours cannot steal clicks.')
        s=s.replace('local best,distance=nil,math.huge;local unknown=false','local best,distance=nil,math.huge;local unknown=false\n    local rejected,rejectedDistance=nil,math.huge',1)
        old='''                if gap<=8 and (gap<distance-0.000001 or (math.abs(gap-distance)<=0.000001 and (best==nil or id<best))) then
                    best,distance=id,gap
                end'''
        new='''                if gap<=8.000001 then
                    local status=targetStatus(s,id)
                    if status==nil then
                        if gap<distance-0.000001 or (math.abs(gap-distance)<=0.000001 and (best==nil or id<best)) then
                            best,distance=id,gap
                        end
                    elseif gap<rejectedDistance then
                        rejected,rejectedDistance=status,gap
                    end
                end'''
        assert old in s;s=s.replace(old,new,1)
        s=s.replace('    if unknown then return nil,"unknown-building-footprint" end',
            '    if best~=nil then return best,nil end\n    if rejected~=nil then return nil,rejected end\n    if unknown then return nil,"unknown-building-footprint" end',1)
        s=s.replace('Tunnel cancelled: choose a point within 8 metres of an owned building.',
            'Tunnel cancelled: choose ground within 8 metres of the edge of an owned, completed, connected building.')
        changes[p]=s
        p='assets/scar/vietnam/tunnel_buildings.scar';s=text(p)
        changes[p]=re.sub(r'reach=(\d+)',lambda m:'reach='+str(int(m[1])+2),s)
        byfile={}
        for row in read(OUT/'range-inventory.json')['rows']:byfile.setdefault(row['key'],[]).append(row)
        for key,rows in byfile.items():
            p='assets/attrib/instances/'+key.replace('\\','/')+'.xml';root=E.fromstring(z.read(p))
            for row in rows:
                scope=root if row['variant']=='default' else root.find("variant[@name='"+row['variant']+"']")
                assert scope is not None
                exts=scope.find("list[@name='extensions']")
                if exts is None:exts=E.SubElement(scope,'list',name='extensions')
                ext=next((n for n in exts if n.get('value')=='ebpextensions\\district_generator_ext'),None)
                if ext is None:
                    attrs=dict(row['extension']);attrs.pop('List.ListAction',None)
                    attrs['List.ParentItemID']=attrs['List.ItemID'];ext=E.SubElement(exts,'template_reference',attrs)
                field=ext.find("float[@name='range_metres']")
                if field is None:field=E.SubElement(ext,'float',name='range_metres')
                field.set('value',format(row['after'],'g'));field.set('overrideParent','True')
            E.indent(root,space='\t');changes[p]=E.tostring(root,encoding='unicode',xml_declaration=False)
            changes[p]="<?xml version='1.0' encoding='utf-8'?>\n"+changes[p]
    return changes

def main():
    guard();changes=expected_changes()
    original=read(OUT/'baseline/source-hashes.json')
    for name,s in changes.items():
        p=ROOT/name
        previous=read(OUT/'patch-receipt.json')['changes'] if (OUT/'patch-receipt.json').exists() else {}
        assert sha(p)==original[str(p)] or sha(p)==previous.get(name) or p.read_text(encoding='utf-8-sig')==s,('Unowned edits',name)
    for name,s in changes.items():(ROOT/name).write_text(s,encoding='utf-8',newline='\n')
    write(OUT/'patch-receipt.json',{'changes':{p:sha(ROOT/p) for p in changes},'authorized_extra_actual_influence_metres':2,
        'skirmisher_windup_delta':0.25,'skirmisher_reload_delta':-0.25,'marker_pixels':48,'destination_allowance_from_footprint_edge_metres':8})
    print('PATCHED',len(changes),'files')

if __name__=='__main__':main()

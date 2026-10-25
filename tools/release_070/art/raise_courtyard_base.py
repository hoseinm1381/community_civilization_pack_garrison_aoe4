"""Add terrain-supported, genuinely recessed compound bases to new revisions."""
from pathlib import Path
import bpy,json
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
def raised_base(source_name,new_name,bounds,holes,depth,export_z_shift,export_scale,slug,water_or_pit_floor):
    if bpy.data.collections.get(new_name):raise RuntimeError('Preserve prior revision')
    source=bpy.data.collections[source_name];c=bpy.data.collections.new(new_name);bpy.context.scene.collection.children.link(c)
    parts={}
    for old in source.objects:
        o=old.copy();o.data=old.data.copy();o.name=new_name+'_garrison_part_'+old.name[-4:];c.objects.link(o);parts[int(old.name[-4:])]=o
    x0,x1,y0,y1=bounds;xs=sorted({x0,x1,*(x for h in holes for x in h[:2])});ys=sorted({y0,y1,*(y for h in holes for y in h[2:])})
    panels=[]
    for a,b in zip(xs,xs[1:]):
        for cc,d in zip(ys,ys[1:]):
            if any(h[0]<(a+b)/2<h[1] and h[2]<(cc+d)/2<h[3] for h in holes):continue
            panels.append((a,b,cc,d))
    for index in (0,2):
        o=parts[index];old=o.data;vertices=[tuple(v.co) for v in old.vertices];faces=[tuple(p.vertices) for p in old.polygons]
        old_uv={l.name:[tuple(v.uv) for v in l.data] for l in old.uv_layers}
        old_color=[tuple(v.color) for v in old.color_attributes['CCP070_Color'].data]
        oldloops=len(old.loops)
        for a,b,cc,d in panels:
            start=len(vertices);vertices.extend([(a,cc,-depth),(b,cc,-depth),(a,d,-depth),(b,d,-depth),(a,cc,0),(b,cc,0),(a,d,0),(b,d,0)])
            faces.extend(tuple(start+i for i in f) for f in ((0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)))
        new=bpy.data.meshes.new(o.name+'_RaisedBase');new.from_pydata(vertices,[],faces);new.update();new.materials.clear()
        for m in old.materials:new.materials.append(m)
        for name,values in old_uv.items():
            layer=new.uv_layers.new(name=name)
            for i,u in enumerate(values):layer.data[i].uv=u
            for i in range(oldloops,len(new.loops)):
                v=new.vertices[new.loops[i].vertex_index].co
                layer.data[i].uv=(.005+(v.x*.07%1)*.24,.005+(v.y*.07%1)*.49)
        color=new.color_attributes.new(name='CCP070_Color',type='BYTE_COLOR',domain='CORNER')
        for i,v in enumerate(old_color):color.data[i].color=v
        for i in range(oldloops,len(new.loops)):color.data[i].color=(.40,.38,.30,1)
        o.data=new
    for old in source.objects:old.hide_set(True);old.hide_render=True
    for i,o in parts.items():o.hide_set(i in (2,3));o.hide_render=i in (2,3)
    result={'schema':'ccp-070-raised-recess-base/v1','source':source_name,'revision':new_name,'base_panels':len(panels),
            'base_parts':[0,2],'actual_holes':holes,'source_base_bottom':-depth,'source_base_top':0,
            'export_scale':export_scale,'export_z_shift':export_z_shift,
            'world_base_bottom':-depth*export_scale+export_z_shift,'world_base_top':export_z_shift,
            'world_recess_floor':water_or_pit_floor*export_scale+export_z_shift,
            'terrain_excavation':False,'native_stamp_vertical_translation':0,'native_gameplay_changed':False,
            'roof_and_uv_geometry_preserved':True}
    assert result['world_base_bottom']<0 and result['world_recess_floor']>0,result
    (OUT/(slug+'-terrain-base.json')).write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result));return result

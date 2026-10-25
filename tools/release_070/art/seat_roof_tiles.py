"""Create a new detailed revision with tile pans seated on measured hip roofs.

Each pan is a discrete 12-vertex, 10-quad closed module. Its curved cross-section
and UVs are retained; its bottom follows the actual supporting roof surface.
Old editable revisions are preserved. Execute only through Blender MCP.
"""
from pathlib import Path
import bpy,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
def seat(source_name,new_name,base_name,offset,slug):
    if bpy.data.collections.get(new_name):raise RuntimeError('Preserve existing revision')
    source=bpy.data.collections[source_name];base=bpy.data.collections[base_name];origin=Vector(offset)
    trees=[]
    for o in base.objects:
        if o.type=='MESH' and ('roof' in o.name.lower() or o.get('stock_geometry_unchanged')):
            trees.append((o.name,BVHTree.FromPolygons([o.matrix_world@v.co-origin for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons])))
    if not trees:raise RuntimeError('No exact roof reference')
    c=bpy.data.collections.new(new_name);bpy.context.scene.collection.children.link(c)
    parts={}
    for o in source.objects:
        clone=o.copy();clone.data=o.data.copy();clone.name=new_name+'_garrison_part_'+o.name[-4:];c.objects.link(clone);parts[int(o.name[-4:])]=clone
    assert set(parts)==set(range(7))
    me=parts[4].data;parent=list(range(len(me.vertices)))
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for edge in me.edges:
        a,b=map(find,edge.vertices);parent[b]=a
    components={}
    for i in range(len(parent)):components.setdefault(find(i),[]).append(i)
    component_faces={}
    for p in me.polygons:component_faces.setdefault(find(p.vertices[0]),[]).append(p)
    changed=0;unseated=[];max_delta=0;proof=[]
    for root,comp in components.items():
        faces=component_faces.get(root,[])
        if len(comp)!=12 or len(faces)!=10 or any(len(p.vertices)!=4 for p in faces):continue
        coords=[me.vertices[i].co.copy() for i in comp];x=sum(v.x for v in coords)/12;y=sum(v.y for v in coords)/12;z=min(v.z for v in coords)
        hits=[]
        for name,t in trees:
            hit=t.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),100)[0]
            if hit is not None:hits.append((abs(z-hit.z),name,t))
        if not hits:unseated.append({'component':root,'reason':'No supporting roof at center'});continue
        target=[];name=''
        # Overlapping upper/lower tiers can both hit the center. Select the
        # nearest roof that supports the COMPLETE pan, not only its center.
        for _,candidate,tree in sorted(hits,key=lambda row:row[0]):
            positions=[]
            for old in coords:
                hit=tree.ray_cast(Vector((old.x,old.y,40)),Vector((0,0,-1)),100)[0]
                if hit is None:break
                positions.append(Vector((old.x,old.y,hit.z+.004+(old.z-z))))
            if len(positions)==12:target=positions;name=candidate;break
        if len(target)!=12:unseated.append({'component':root,'reason':'No roof supports complete pan'});continue
        for index,old,new in zip(comp,coords,target):
            max_delta=max(max_delta,abs(old.z-new.z));me.vertices[index].co=new
        changed+=1
        proof.append({'component':root,'support':name,'bottom_contact_offset':.004})
    me.update()
    for o in source.objects:o.hide_set(True);o.hide_render=True
    for i,o in parts.items():o.hide_set(i in (2,3));o.hide_render=i in (2,3)
    result={'schema':'ccp-070-roof-seated-source/v1','source':source_name,'revision':new_name,'tiles_seated':changed,
            'unseated':unseated,'maximum_z_correction':max_delta,'per_pan_support':proof,
            'healthy_parts':[0,1,4,5,6],'heavy_damage_parts':[0,3],'ruins_parts':[2],
            'uvs_unchanged':True,'vertex_count_unchanged':True,'native_cook':False,'native_render':False}
    (OUT/(slug+'-roof-seated.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='per_pan_support'}))
    if unseated:raise RuntimeError('Retain diagnostic revision; unresolved tile supports')
    return result

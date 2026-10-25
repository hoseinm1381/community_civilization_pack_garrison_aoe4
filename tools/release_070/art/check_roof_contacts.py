"""Read-only tile seating probe against approved roof surfaces, via MCP."""
import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
OUT=Path('F:/aoe_4_temp/Community_civilization_pack_garrison_temp/output/release_070/art/detail')
def probe(collection_name,base_name,offset,slug):
    source=bpy.data.collections[collection_name];base=bpy.data.collections[base_name];origin=Vector(offset)
    roofs=[]
    for o in base.objects:
        if o.type=='MESH' and 'roof' in o.name.lower():
            roofs.append(BVHTree.FromPolygons([o.matrix_world@v.co-origin for v in o.data.vertices],[list(p.vertices) for p in o.data.polygons]))
    obj=next(o for o in source.objects if o.name.endswith('garrison_part_0004'));me=obj.data
    parent=list(range(len(me.vertices)))
    def find(a):
        while parent[a]!=a:parent[a]=parent[parent[a]];a=parent[a]
        return a
    for edge in me.edges:
        a,b=map(find,edge.vertices);parent[b]=a
    components={}
    for i in range(len(parent)):components.setdefault(find(i),[]).append(i)
    gaps=[]
    for comp in components.values():
        if len(comp)!=12:continue
        vs=[me.vertices[i].co for i in comp];x=sum(v.x for v in vs)/12;y=sum(v.y for v in vs)/12
        z=min(v.z for v in vs)
        hits=[tree.ray_cast(Vector((x,y,40)),Vector((0,0,-1)),100)[0] for tree in roofs]
        heights=[v.z for v in hits if v is not None]
        if heights:gaps.append(z-min(heights,key=lambda h:abs(z-h)))
    report={'schema':'ccp-070-roof-seating-probe/v1','asset':slug,'tile_candidates':len(gaps),'max_gap':max(gaps) if gaps else None,
            'min_gap':min(gaps) if gaps else None,'gaps_above_0_10':sum(g>.1 for g in gaps),'gaps_below_minus_0_10':sum(g<-.1 for g in gaps),
            'limits':'12-vertex connected components are tile candidates; measure only against original blockout roof surfaces, not native engine.'}
    (OUT/(slug+'-roof-seating.json')).write_text(json.dumps(report,indent=2));print(json.dumps(report))

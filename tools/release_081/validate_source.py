"""Independent saved-master checks; no source writes or shader substitutions."""
import bpy,sys,math,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from common import *
guard();revision=sys.argv[sys.argv.index('--')+1]
receipt=read(OUT/'art/buffalo'/revision/'export.json')
assert sha(receipt['source'])==receipt['source_sha256']
assert receipt['files']=={p.name:sha(p) for p in Path(receipt['export']).iterdir() if p.is_file()}
bpy.ops.wm.open_mainfile(filepath=receipt['source']);rig=bpy.data.objects['081_Native_cattle_45'];expected=receipt['donor_contract']
assert [b.name for b in rig.data.bones]==[b['name'] for b in expected['bones']]
source=ROOT/'art/authoring/release_0710/buffalo/r1/model.blend'
with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=[n for n in a.objects if 'Armature' in n]
old=next(o for o in b.objects if o.type=='ARMATURE')
bind_delta=max(abs(a-b) for bone in rig.data.bones for row1,row2 in zip(bone.matrix_local,old.data.bones[bone.name].matrix_local) for a,b in zip(row1,row2));assert bind_delta==0
checks=[]
for level,cap in ((1,20000),(2,10000),(3,5000)):
    o=bpy.data.objects['body_lod'+str(level)];assert len(o.data.polygons)<=cap
    assert all(len(p.vertices)==3 and p.area>1e-12 for p in o.data.polygons)
    assert all(math.isfinite(x) for v in o.data.vertices for x in v.co)
    assert len(o.data.uv_layers)==1 and len(o.data.materials)==1
    assert o.data.materials[0].name=='lod'+str(level),'Native material name must match .material definition exactly'
    for v in o.data.vertices:
        ws=[g.weight for g in v.groups if g.weight>1e-8]
        assert 1<=len(ws)<=4 and abs(sum(ws)-1)<1e-5
    checks.append({'LOD':level,'triangles':len(o.data.polygons),'weighted_vertices':len(o.data.vertices)})
# Sample the actual UVs against the owner-mask tile. Only the cloth is assigned it.
mask_regions=[]
component_names={c['name'] for c in receipt['components']}
for o in bpy.context.scene.objects:
    if o.type!='MESH' or o.name not in component_names:continue
    masked=any(.25<=x.uv.x<.5 and .25<=x.uv.y<.5 for x in o.data.uv_layers.active.data)
    if masked:
        assert o.name=='081_Padded_saddlecloth',o.name
        mask_regions.append(o.name)
assert mask_regions==['081_Padded_saddlecloth']
assert all(im.size[:]==(2048,2048) for im in bpy.data.images if im.name.startswith('081_') and im.name!='081_pattern.001')
write(OUT/'art/buffalo'/revision/'source-validation.json',{'passed':True,'lods':checks,'native_bones':45,'bind_matrix_max_delta':bind_delta,'only_player_masked_component':mask_regions,'contacts':receipt['contacts'],'native_playback_tested':False})
print('SOURCE_CHECKS_PASSED',checks)

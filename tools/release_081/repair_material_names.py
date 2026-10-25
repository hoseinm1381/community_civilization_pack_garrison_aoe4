"""Identity-only native material repair; retain all geometry, UVs and weights."""
import bpy,sys,shutil,hashlib,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from common import *
sys.path.append(str(ROOT/'tools/release_079'))
from export_pilot import addon
guard();old=read(OUT/'art/buffalo/r5/export.json');a=ART/'buffalo/r6';e=EXPORT/'buffalo/r6'
assert not a.exists() and not e.exists();a.mkdir(parents=True);shutil.copytree(EXPORT/'buffalo/r5',e)
bpy.ops.wm.open_mainfile(filepath=old['source']);rig=bpy.data.objects['081_Native_cattle_45'];lods=[bpy.data.objects['body_lod'+str(i)] for i in (1,2,3)]
def fingerprint(o):
    return hashlib.sha256(json.dumps({'v':[list(v.co) for v in o.data.vertices],'f':[list(p.vertices) for p in o.data.polygons],'uv':[list(uv.uv) for uv in o.data.uv_layers.active.data],'weights':[[[o.vertex_groups[g.group].name,g.weight] for g in v.groups] for v in o.data.vertices]}).encode()).hexdigest()
before=[fingerprint(o) for o in lods];changes=[]
for i,obj in enumerate(lods,1):
    target='lod'+str(i);mat=obj.data.materials[0]
    collision=bpy.data.materials.get(target)
    if collision and collision!=mat:collision.name='Unexported_'+target
    changes.append([mat.name,target]);mat.name=target
    assert mat.name==target
addon('unit_export').export_unit_model(rig,lods,e/'model.fbx',addon('unit_export').skeleton_records(rig),three_lods=False)
assert before==[fingerprint(o) for o in lods]
for name in ('albedo','normal','roughness','metalness','pattern'):
    im=bpy.data.images['081_'+name];im.filepath_raw=str(e/(name+'.png'));im.pack();im.use_fake_user=True
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(a/'model.blend'))
old.update(revision='r6',source=str(a/'model.blend'),source_sha256=sha(a/'model.blend'),export=str(e),files={p.name:sha(p) for p in e.iterdir()},material_identity_fix=changes,geometry_uv_weights_preservation_sha256=before)
write(OUT/'art/buffalo/r6/export.json',old);print('MATERIAL_IDENTITIES_REPAIRED',changes)

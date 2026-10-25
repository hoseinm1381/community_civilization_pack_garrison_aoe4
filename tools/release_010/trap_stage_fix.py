"""Change only saved trap stage metadata; retain approved art and its contact proof."""
import bpy, sys, json, hashlib
from pathlib import Path
from array import array

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).resolve().parent))
sys.path.insert(0,r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from trap_art_runner import validate, export_building, write
from garrison import building_project
from garrison.model_preflight_ui import require_valid

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
def objects(): return [bpy.data.objects[n] for n in ['Trap_00_earth_brush','Trap_01_hardwood']]
def art_fingerprint():
    rows=[]
    for obj in objects():
        mesh=obj.data
        assert not obj.modifiers
        rows.append({'name':obj.name,'matrix':[list(r) for r in obj.matrix_world],
            'vertices':[list(v.co) for v in mesh.vertices],
            'edges':[list(e.vertices) for e in mesh.edges],
            'polygons':[(list(p.vertices),p.material_index,p.use_smooth) for p in mesh.polygons],
            'uv':{u.name:[list(v.uv) for v in u.data] for u in mesh.uv_layers},
            'materials':[m.name for m in mesh.materials]})
    materials=[]
    for material in sorted({m for o in objects() for m in o.data.materials},key=lambda m:m.name):
        nodes=[]
        for node in material.node_tree.nodes:
            inputs=[]
            for socket in node.inputs:
                if hasattr(socket,'default_value'):
                    value=socket.default_value
                    try: value=list(value)
                    except TypeError: pass
                    if not isinstance(value,(str,int,float,bool,list,type(None))): value=str(value)
                    inputs.append((socket.name,value))
            nodes.append((node.name,node.bl_idname,inputs,getattr(getattr(node,'image',None),'name',None)))
        materials.append((material.name,nodes,[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in material.node_tree.links]))
    images=[]
    for image in sorted(bpy.data.images,key=lambda i:i.name):
        if not image.has_data: continue
        pixels=array('f',[0])*len(image.pixels); image.pixels.foreach_get(pixels)
        images.append((image.name,list(image.size),image.colorspace_settings.name,hashlib.sha256(pixels.tobytes()).hexdigest()))
    return {'geometry_uv_transforms':digest(rows),'materials':digest(materials),'packed_images':digest(images)}

name=sys.argv[sys.argv.index('--')+1]
assert name in ['stake_thicket','stake_fan']
source=ROOT/'art/authoring/traps_010'/name
export=ROOT/'art/exports/traps_010'/name
output=ROOT/'output/release_010/traps'/name
blend=source/(name+'.blend')
bpy.ops.wm.open_mainfile(filepath=str(blend))
before=art_fingerprint()
before_hashes={str(p.relative_to(ROOT)):sha(p) for directory in [source,export] for p in directory.iterdir() if p.is_file()}
check=json.loads((output/'validation.json').read_text())
write(output/'validation-before-stage-correction.json',check)
assert check['construction_stages']==[0,5]
assert all(c['passes'] for c in check['contacts'])
assert [o[building_project.STAGE_PROPERTY] for o in objects()]==[0,5]
# Reproduce the actual supported stage contract before correcting saved metadata.
try:
    building_project.parts([{'name':o.name,'first_stage':o.get(building_project.STAGE_PROPERTY)} for o in objects()],'english-house')
except (ValueError,RuntimeError) as exc:
    rejection=str(exc)
else:
    raise AssertionError('Expected original stage5 to be refused by installed Garrison')
objects()[1][building_project.STAGE_PROPERTY]=20
stage_rows=building_project.parts([{'name':o.name,'first_stage':o.get(building_project.STAGE_PROPERTY)} for o in objects()],'english-house')
fresh_geometry=validate(objects())
assert fresh_geometry==check['geometry']
preflight=require_valid(objects(),bpy.context)
assert preflight['ok'] and not preflight['findings']
manifest=export_building(objects(),export,building_project.SCHEMA)
assert art_fingerprint()==before
# Retain earlier .blend1 rollback rather than replacing it with an automatic backup.
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
assert art_fingerprint()==before
assert [o[building_project.STAGE_PROPERTY] for o in objects()]==[0,20]
for directory in [source,export]:
    for p in directory.glob('*.png'): assert sha(p)==before_hashes[str(p.relative_to(ROOT))]
check.update({'construction_stages':[0,20],'garrison_preflight':preflight,
    'stage_correction':'Source property5 ->20 only; geometry/material/UV/transform/packed-image fingerprints preserved across export/save/reload. Existing contacts remain valid for identical geometry.'})
write(output/'validation.json',check)
write(output/'manifest.json',{'name':name,'source_blend':str(blend),'building':manifest,'files':{p.name:sha(p) for p in export.iterdir() if p.is_file()}})
write(output/'stage-correction.json',{'schema':'ccp.trap-stage-correction/v1','name':name,
    'original_stage_rejection':rejection,'before_stages':[0,5],'after_stages':[0,20],
    'validated_parts':stage_rows,'before_files':before_hashes,'art_fingerprints':before,
    'art_unchanged':True,'saved_source_verified':True,'contact_count':len(check['contacts']),
    'contacts_preserved_for_identical_geometry':True,'native_cook':'not run','gameplay_edits':False})
print('TRAP_STAGE_CORRECTION_COMPLETE '+name)

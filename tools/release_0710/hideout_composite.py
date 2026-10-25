"""Final stamp-transform compound preview; retained native tower plus new shelter."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/release_020'))
from model_ministry_farm_hideout_runner import render_views,write
variant=sys.argv[sys.argv.index('--')+1]
native=ROOT/'art/authoring/buildings_020/hideout'/variant/('Vietnam_Hideout_'+variant+'.blend')
new=ROOT/'art/authoring/release_0710/hideout'/('shelter_'+variant)/('shelter_'+variant+'.blend')
old=ROOT/'art/authoring/buildings_020/hideout'/('shelter_'+variant)/('shelter_'+variant+'.blend')
out=ROOT/'output/release_0710/hideout'/('compound-'+variant+'-grounded')
trans=json.loads((ROOT/'output/release_0710/hideout/stamp-transforms.json').read_text());rows=[x for x in trans if x['variant']==variant]
assert rows[0]['visuals'][0]['transform']==[0,1,0,0,0,0,0,1,1,1]
assert rows[1]['visuals'][0]['transform']==[0,0,0,1,0,0,0,1,1,1]
bpy.ops.wm.open_mainfile(filepath=str(native))
base=[o for o in bpy.context.scene.objects if o.type=='MESH'];native_bounds=[]
for o in base:
 world=o.matrix_world.copy();o.parent=None;o.matrix_world=Matrix.Rotation(math.pi,4,'Z')@world
 withmesh=[o.matrix_world@v.co for v in o.data.vertices];native_bounds.extend(withmesh)
with bpy.data.libraries.load(str(new),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('Shelter_')]
added=b.objects;assert len(added)==2
for o in added:bpy.context.scene.collection.objects.link(o)
def bounds(objects):
 points=[o.matrix_world@v.co for o in objects for v in o.data.vertices]
 return {'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]}
new_bounds=bounds(added)
with bpy.data.libraries.load(str(old),link=False) as (a,b):b.objects=[n for n in a.objects if n.startswith('Shelter_')]
oldobjs=b.objects;old_bounds=bounds(oldobjs)
for o in oldobjs:bpy.data.objects.remove(o,do_unlink=True)
# New supports stay inside old canopy envelope; no functional stamp translation.
write(out/'bounds-diagnostic.json',{'new':new_bounds,'old':old_bounds,'tower':bounds(base)})
assert all(new_bounds['min'][i]>=old_bounds['min'][i]-.05 and new_bounds['max'][i]<=old_bounds['max'][i]+.05 for i in [0,1])
assert new_bounds['min'][2]>=-.001 and abs(new_bounds['min'][2]-old_bounds['min'][2])<=.031
# Native object origin is ground Z0. Retained donor buried foundation reaches -1.93m.
# A preview-only opaque ground plane hides underground donor geometry; never exported.
from model_ministry_farm_hideout_runner import box
mat=bpy.data.materials.new('Preview ground only');mat.diffuse_color=(.24,.29,.17,1)
plane=box('PREVIEW_ONLY_GROUND',(0,0,-.06),(12,12,.12),mat,'earth')
render_views(base+added,out)
bpy.data.objects.remove(plane,do_unlink=True)
write(out/'proof.json',{'variant':variant,'old_shelter_bounds':old_bounds,'new_shelter_bounds':new_bounds,'horizontal_envelope_expansion_at_most_5cm':True,'ground_seating_change_at_most_3cm':True,'stamp_transforms':rows,'native_game_quaternion_y_180_converted_to_blender_z_180':True,'native_ground_plane_z':0,'ground_evidence':'both native stamp translations exactly zero; native source retains z<=0 foundation while original shelter starts z0.02','preview_ground_only_not_exported':True,'source_only_native_match_unverified':True})


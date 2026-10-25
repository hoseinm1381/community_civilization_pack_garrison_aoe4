"""Reproducible 040 healthy/ruined landmark sets; run in owned background Blender."""
import bpy
import hashlib
import json
import math
import random
import shutil
import sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage
check_storage(ROOT,configuration(ROOT))
sys.path.insert(0,str(ROOT/'tools/release_020'))
from model_ministry_farm_hideout_runner import box,mesh,faceted_vessel,join_stage,validate,export_building,write
sys.path.insert(0,r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material

NAME=sys.argv[sys.argv.index('--')+1]
assert NAME in ('pho_minh','one_pillar') and bpy.app.background
SOURCE=ROOT/'art/authoring/landmarks_040'/NAME
EXPORT=ROOT/'art/exports/landmarks_040'/(NAME+'_combined')
OUT=ROOT/'output/release_040/landmarks'/NAME
for path in (SOURCE,EXPORT,OUT):path.mkdir(parents=True,exist_ok=True)
old=ROOT/'art/authoring/landmarks_030'/NAME
old_hash=hashlib.sha256((old/(NAME+'.blend')).read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(old/(NAME+'.blend')))
healthy=sorted([o for o in bpy.context.scene.objects if o.type=='MESH'],key=lambda o:o['garrison_building_first_stage'])
assert len(healthy)==2
MAT=healthy[0].data.materials[0]
for name in ('albedo','normal','roughness','metalness'):
    shutil.copyfile(old/(name+'.png'),SOURCE/(name+'.png'))
    shutil.copyfile(old/(name+'.png'),EXPORT/(name+'.png'))
for image in bpy.data.images:
    if image.source=='FILE':
        for name in ('albedo','normal','roughness','metalness'):
            if name in image.name.lower():image.filepath=str(SOURCE/(name+'.png'));image.reload()
scale=2.5 if NAME=='one_pillar' else 1.0
original_bounds={o.name:[[min(v.co[i] for v in o.data.vertices) for i in range(3)],
                              [max(v.co[i] for v in o.data.vertices) for i in range(3)]] for o in healthy}
for o in healthy:
    o.name=o.name.replace('030','040')
    for v in o.data.vertices:v.co*=scale
    o.data.update()

ruins=[];contacts=[];rng=random.Random(4041 if NAME=='pho_minh' else 4042)
def add(o):ruins.append(o);return o
def block(name,c,size,tile):return add(box('CCP040_R_'+name,c,size,MAT,tile))
def rubble(name,x,y,r,h,tile='brick'):
    n=7;phase=rng.random()*math.tau
    points=[]
    for level in (0,1):
        for i in range(n):
            angle=phase+i*math.tau/n;rad=r*(.78+rng.random()*.22)
            points.append((x+math.cos(angle)*rad,y+math.sin(angle)*rad,
                           .025 if not level else h*(.65+rng.random()*.35)))
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]
    faces.extend((i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n))
    return add(mesh('CCP040_R_'+name,points,faces,MAT,tile))
if NAME=='pho_minh':
    # Continuous court/plinth provides readable ground remains; fractured tower is low.
    block('court',(0,0,.045),(6.8,6.8,.09),'earth')
    block('stone_plinth',(0,-.05,.18),(2.65,2.65,.27),'plaster')
    block('fractured_lower_tower',(0,-.05,.64),(1.94,1.94,.66),'brick')
    # Deliberate asymmetric wall stumps preserve a recognizable square tower base.
    for label,x,y,w,d,h in (('north',0,.83,1.94,.20,.68),('west',-.87,-.05,.20,1.56,.44),
                           ('east',.87,.15,.20,1.16,.26)):
        block('stump_'+label,(x,y,.97+h/2),(w,d,h),'brick')
    contacts.append({'interface':'tower stump to lower body','gap':0.0,'pass':True})
    for i in range(56):
        a=rng.random()*math.tau;rad=rng.uniform(.95,2.8)
        rubble('brick_scatter_'+str(i),math.cos(a)*rad,math.sin(a)*rad,
               rng.uniform(.09,.28),rng.uniform(.10,.34),'brick' if i%4 else 'plaster')
    # Fallen cornice sections lie on the court, not floating finished tiers.
    for i,(x,y,rot) in enumerate(((-1.7,-1.0,.4),(1.7,.6,-.6),(.1,-1.9,.16))):
        o=block('fallen_cornice_'+str(i),(x,y,.18),(.95,.38,.30),'brick');o.rotation_euler.z=rot
    for i in range(8):
        x=-1.4+i*.4;o=block('rear_hall_beam_'+str(i),(x,2.32,.13),(.13,1.15,.20),'timber')
        o.rotation_euler.z=.1*(i%3-1)
else:
    block('court',(0,0,.045),(6.8,6.8,.09),'earth')
    block('pond_bed',(0,0,.14),(4.45,4.45,.18),'water')
    for label,c,s in (('south',(0,-2.30,.23),(4.9,.30,.27)),('north',(0,2.30,.23),(4.9,.30,.27)),
                       ('west',(-2.30,0,.23),(.30,4.35,.27)),('east',(2.30,0,.23),(.30,4.35,.27))):
        block('pond_coping_'+label,c,s,'plaster')
    add(faceted_vessel('CCP040_R_broken_column',(0,0,.23),[(0,.44),(.76,.44),(.90,.37)],MAT,'plaster',16))
    contacts.append({'interface':'broken column to pond bed','gap':0.0,'pass':True})
    for i in range(18):
        a=i*math.tau/18;rad=1.05+(i%3)*.32
        o=block('fallen_shrine_timber_'+str(i),(math.cos(a)*rad,math.sin(a)*rad,.32),
                (.15,rng.uniform(.6,1.2),.18),'timber');o.rotation_euler.z=a
    for i in range(48):
        a=rng.random()*math.tau;rad=rng.uniform(.55,2.5)
        rubble('roof_tile_'+str(i),math.cos(a)*rad,math.sin(a)*rad,
               rng.uniform(.08,.19),rng.uniform(.27,.43),'tile')
    # Low stair and broken approach remain distinct from the pond.
    for i in range(4):block('broken_stair_'+str(i),(0,-2.8+i*.22,.08+i*.055),(.86,.23,.14+i*.11),'plaster')
    for o in ruins:
        for v in o.data.vertices:v.co*=scale
        o.data.update()
ruin=join_stage(ruins,'CCP040_'+NAME+'_ruins',0)
ruin['garrison_building_profile']='english-house'
objects=healthy+[ruin]
for o in objects:
    bpy.context.view_layer.objects.active=o;o.select_set(True)
    bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    o.select_set(False)
checks=validate(objects)
preflight=require_valid(objects,bpy.context);assert preflight['ok'],preflight
adopt_material(MAT)
manifest=export_building(objects,EXPORT)
assert manifest['parts'][2]['name']=='garrison_part_0002'
bounds=lambda os:{'min':[min((o.matrix_world@v.co)[i] for o in os for v in o.data.vertices) for i in range(3)],
                  'max':[max((o.matrix_world@v.co)[i] for o in os for v in o.data.vertices) for i in range(3)]}
ruin.hide_render=True;ruin.hide_set(True)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))

def previews(label,visible):
    for o in objects:o.hide_render=o not in visible
    pts=[o.matrix_world@v.co for o in visible for v in o.data.vertices]
    lo=Vector([min(v[i] for v in pts) for i in range(3)]);hi=Vector([max(v[i] for v in pts) for i in range(3)])
    center=(lo+hi)/2;size=max(hi-lo);scene=bpy.context.scene
    nodes=MAT.node_tree.nodes;links=MAT.node_tree.links
    output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');original=output.inputs['Surface'].links[0].from_socket
    albedo=next(n for n in nodes if n.type=='TEX_IMAGE' and 'albedo' in n.image.name.lower())
    diffuse=nodes.new('ShaderNodeBsdfDiffuse');links.new(albedo.outputs['Color'],diffuse.inputs['Color']);links.new(diffuse.outputs[0],output.inputs['Surface'])
    scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.max_bounces=2
    scene.render.resolution_x=900;scene.render.resolution_y=750;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.8
    helpers=[]
    for key,vec,power in [('key',(.8,-.8,1.6),9),('fill',(-.6,-.8,.65),5)]:
        data=bpy.data.lights.new('CCP040 '+key,'AREA');o=bpy.data.objects.new('CCP040 '+key,data)
        scene.collection.objects.link(o);o.location=center+Vector(vec)*size;data.energy=size*size*power;data.size=size*1.2;helpers.append(o)
    cam=bpy.data.objects.new('CCP040 preview',bpy.data.cameras.new('CCP040 preview'));scene.collection.objects.link(cam)
    cam.data.type='ORTHO';cam.data.ortho_scale=size*1.5;scene.camera=cam
    for view,vec in [('iso',(1,-1,.8)),('front',(0,-1,.2)),('back',(0,1,.2)),('left',(-1,0,.2)),('right',(1,0,.2)),('top',(0,0,1)),('bottom',(0,0,-1))]:
        cam.location=center+Vector(vec).normalized()*size*2;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(label+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
    scene.camera=None
    for o in helpers+[cam]:bpy.data.objects.remove(o,do_unlink=True)
    links.new(original,output.inputs['Surface']);nodes.remove(diffuse)
previews('healthy',healthy);previews('ruins',[ruin])
write(OUT/'validation.json',{'name':NAME,'healthy_scale':scale,'healthy_bounds':bounds(healthy),'ruin_bounds':bounds([ruin]),
    'geometry':checks,'contacts':contacts,'garrison_preflight':preflight,'ruin_part':'garrison_part_0002',
    'visibility_contract':'integration must select part0002 only for native life_cycle_state=ruins',
    'native_match':'not run','old_source_sha256':old_hash,'old_source_unchanged':hashlib.sha256((old/(NAME+'.blend')).read_bytes()).hexdigest()==old_hash})
write(OUT/'handoff.json',{'name':NAME,'source_blend':str(SOURCE/(NAME+'.blend')),'source_blend_sha256':hashlib.sha256((SOURCE/(NAME+'.blend')).read_bytes()).hexdigest(),
    'export_directory':str(EXPORT),'export_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in EXPORT.iterdir() if p.is_file()},
    'building':manifest,'healthy_scale':scale,'ruin_parts':['garrison_part_0002'],'healthy_bounds':bounds(healthy),'ruin_bounds':bounds([ruin]),
    'triangles':sum(c['triangles'] for c in checks),'validation':str(OUT/'validation.json'),'previews':[str(p) for p in OUT.glob('*.png')]})
print('CCP040_LANDMARK_COMPLETE '+NAME)

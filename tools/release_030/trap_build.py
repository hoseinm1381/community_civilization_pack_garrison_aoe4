"""Deterministic shallow, concealed traps; no black rim or black cavity atlas."""
import bpy, sys, math, random, json, shutil, hashlib
from pathlib import Path
from mathutils import Vector
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from common import guarded
from trap_art_runner import mesh, join_parts, validate, render, export_building, write
guarded()
sys.path.insert(0, str(Path.home()/'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com'))
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
from garrison import building_project
NAME = sys.argv[sys.argv.index('--')+1]
assert NAME in ('stake_thicket', 'stake_fan')
assert bpy.app.background and not bpy.data.filepath
WIDTH = 6.4 if NAME == 'stake_thicket' else 20.8
SCALE = .75 if NAME == 'stake_thicket' else .25
SOURCE = ROOT/'art/authoring/traps_030'/NAME
EXPORT = ROOT/'art/exports/traps_030'/NAME
OUTPUT = ROOT/'output/release_030/traps'/NAME
for p in (SOURCE, EXPORT, OUTPUT): p.mkdir(parents=True, exist_ok=True)
for o in list(bpy.context.scene.objects): bpy.data.objects.remove(o, do_unlink=True)
random.seed(3001 if NAME == 'stake_thicket' else 3002)

def atlas():
    size=1024; yy,xx=np.mgrid[0:size,0:size]; rng=np.random.default_rng(30301)
    noise=rng.random((size,size))-.5
    broad=np.sin(xx*.043+np.sin(yy*.027)*2)*.025+np.cos(yy*.063)*.014
    color=np.ones((size,size,4),dtype=np.float32)
    soil=(xx>=512)&(yy<512); leaves=(xx>=512)&(yy>=512)
    grain=np.sin(xx*.25+np.sin(yy*.025)*2)*.025+noise*.035
    for c,v in enumerate((.40,.34,.205)): color[:,:,c]=v+grain
    for c,v in enumerate((.39,.365,.245)): color[:,:,c][soil]=v+noise[soil]*.085+broad[soil]
    for c,v in enumerate((.355,.365,.23)): color[:,:,c][leaves]=v+noise[leaves]*.08+broad[leaves]
    # Fine straw, gravel and vein marks; no painted black AO or dark border.
    for i in range(210):
        x=int(rng.integers(524,1004)); y=int(rng.integers(16,1004)); r=int(rng.integers(1,5))
        patch=(xx-x)**2+(yy-y)**2<r*r
        for c,v in enumerate((.56,.49,.33)): color[:,:,c][patch]=v
    al=bpy.data.images.new('CCP030_Concealed_Earth_Leaf_Atlas',width=size,height=size,alpha=False)
    al.pixels.foreach_set(np.clip(color,0,1).ravel()); al.filepath_raw=str(SOURCE/'albedo.png'); al.file_format='PNG'; al.save(); al.pack()
    mat=bpy.data.materials.new('CCP030_trap_earth_leaf'); mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF')
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image=al; mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    for channel in ('normal','roughness','metalness'):
        a=np.ones((size,size,4),dtype=np.float32)
        if channel=='normal':
            a[:,:,0]=.5+noise*.07; a[:,:,1]=.5+np.sin(xx*.26)*.025; a[:,:,2]=.997
        elif channel=='roughness':
            for c in range(3): a[:,:,c]=.83+noise*.12
        else: a[:,:,:3]=0
        im=bpy.data.images.new('CCP030_Trap_'+channel,width=size,height=size,alpha=False); im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel()); im.filepath_raw=str(SOURCE/(channel+'.png')); im.file_format='PNG'; im.save(); im.pack()
        t=mat.node_tree.nodes.new('ShaderNodeTexImage'); t.image=im
        if channel=='normal':
            nm=mat.node_tree.nodes.new('ShaderNodeNormalMap'); mat.node_tree.links.new(t.outputs['Color'],nm.inputs['Color']); mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
        else: mat.node_tree.links.new(t.outputs['Color'],bs.inputs['Roughness' if channel=='roughness' else 'Metallic'])
    for f in SOURCE.glob('*.png'): shutil.copy2(f,EXPORT/f.name)
    return mat

MAT=atlas(); ground=[]; detail=[]; contacts=[]

def box(label, center, size, kind='wood', angle=0):
    x,y,z=center; a,b,c=[s/2 for s in size]; co=[]
    for X,Y,Z in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]:
        co.append((x+X*math.cos(angle)-Y*math.sin(angle),y+X*math.sin(angle)+Y*math.cos(angle),z+Z))
    return mesh(label,co,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],MAT,kind)

def outline(a):
    r=1+.065*math.sin(a*3+.3)+.04*math.sin(a*7)
    if NAME=='stake_thicket': return 2.5*r*math.cos(a),1.87*r*math.sin(a)
    # Rounded, ragged rectangular outline, distinct from the oval trap.
    return 2.5*r*math.copysign(abs(math.cos(a))**.62,math.cos(a)),1.68*r*math.copysign(abs(math.sin(a))**.62,math.sin(a))

# One low closed substrate with an earth-coloured surface; no raised ring.
n=40; outer=[outline(i*math.tau/n) for i in range(n)]
vs=[(x,y,.002) for x,y in outer]+[(x,y,.022) for x,y in outer]
fs=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
ground.append(mesh('CCP030_low_soil_substrate',vs,fs,MAT,'earth'))

# Radial overlapping cover patches meet the ground at an irregular edge.
# Two small interrupted sectors show only earth-shaded recesses and short stakes.
holes={8,9,23} if NAME=='stake_thicket' else {14,15,16}
for i in range(n):
    a=i*math.tau/n; b=(i+1)*math.tau/n
    x1,y1=outer[i]; x2,y2=outer[(i+1)%n]
    # Leave a small interior opening; the perimeter remains pale earth/leaf cover.
    inner=.32 if i in holes else .02
    top=.032
    pts=[(x1*inner,y1*inner,top),(x1*.91,y1*.91,.028),(x2*.91,y2*.91,.028),(x2*inner,y2*inner,top)]
    pts += [(x,y,.018) for x,y,z in pts]
    faces=[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)]
    detail.append(mesh('CCP030_leaf_soil_cover_%02d'%i,pts,faces,MAT,'earth'))
    contacts.append({'part':'cover_%02d'%i,'substrate_top':.022,'cover_bottom':.018,'overlap':.004,'passes':True})

# Broken bamboo woven underneath the cover, with only ragged tips exposed.
for i in range(11):
    y=-1.26+i*.25
    length=3.4 if abs(y)<1 else 2.7
    detail.append(box('CCP030_buried_weft_%02d'%i,(0,y,.035),(length,.032,.025),'wood',.05 if NAME=='stake_thicket' else -.10))
for i in range(7):
    x=-1.05+i*.35
    detail.append(box('CCP030_buried_warp_%02d'%i,(x,0,.045),(.028,2.6,.025),'wood'))

# Stakes are seated in the substrate and mostly hidden by the cover.
for i,theta in enumerate([8.5,9,23.5] if NAME=='stake_thicket' else [14.5,15,16]):
    a=theta*math.tau/n; x,y=.39*math.cos(a),.32*math.sin(a); sides=6; r=.038; base=.018; h=.115
    verts=[(x+r*math.cos(k*math.tau/sides),y+r*math.sin(k*math.tau/sides),base) for k in range(sides)]+[(x+.025,y,base+h)]
    faces=[tuple(reversed(range(sides)))]+[(k,(k+1)%sides,sides) for k in range(sides)]
    detail.append(mesh('CCP030_revealed_stake_%02d'%i,verts,faces,MAT))
    contacts.append({'part':'stake_%02d'%i,'base':base,'substrate_top':.022,'overlap':.004,'passes':True})

# Scattered irregular leaves overlap cover and extend beyond the substrate edge.
for i in range(74):
    a=random.uniform(0,math.tau); rr=random.uniform(.12,1.02); ox,oy=outline(a); x,y=ox*rr,oy*rr
    z=.035 if rr>.9 else .079
    ang=random.uniform(0,math.tau); u=Vector((math.cos(ang),math.sin(ang),0)); v=Vector((-u.y,u.x,0)); c=Vector((x,y,z))
    half=random.uniform(.07,.19); spread=half*.36
    pts=[c-u*half,c+v*spread,c+u*half,c-v*spread,c+Vector((0,0,.014)),c-Vector((0,0,.012))]
    detail.append(mesh('CCP030_leaf_%03d'%i,[tuple(p) for p in pts],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],MAT,'leaf' if i%4 else 'earth'))

objects=[join_parts(ground,'CCP030_00_ground_cover_base',0),join_parts(detail,'CCP030_01_concealed_stakes_cover',20)]
low=[min(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]
high=[max(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]
factor=WIDTH/(high[0]-low[0]); center=Vector(((low[0]+high[0])/2,(low[1]+high[1])/2,0))
for o in objects:
    for v in o.data.vertices: v.co=(v.co-center)*factor
    o['garrison_building_profile']='english-house'
checks=validate(objects); preflight=require_valid(objects,bpy.context); assert preflight['ok'],preflight
adopt_material(MAT)
col=bpy.data.collections.new('CCP030 '+NAME); bpy.context.scene.collection.children.link(col)
for k,v in {'garrison_asset_container':True,'garrison_asset_id':NAME,'garrison_namespace':'community_civilization_pack','garrison_display_name':NAME,'garrison_qualified_id':'community_civilization_pack:'+NAME,'garrison_archetype':'building','garrison_building_profile':'english-house','garrison_building_integration':'script'}.items(): col[k]=v
for o in objects:
    col.objects.link(o)
    for old in tuple(o.users_collection):
        if old!=col: old.objects.unlink(o)
bounds={'min':[min(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]}
assert bounds['min'][2]>=0 and bounds['max'][2]*SCALE<.2
write(OUTPUT/'validation.json',{'name':NAME,'bounds':bounds,'geometry':checks,'garrison_preflight':preflight,'contacts':contacts,'contact_scale':factor,'source_width':WIDTH,'preserved_animator_scale':SCALE,'world_height':bounds['max'][2]*SCALE,'construction_stages':[0,20],'no_gameplay_changes':True,'no_black_rim':True,'no_black_cavity':True,'albedo_rgb_min':float(np.min(np.asarray(next(n.image for n in MAT.node_tree.nodes if n.type=='TEX_IMAGE').pixels[:]).reshape(-1,4)[:,:3])),'opening_sectors':sorted(holes),'cover_sector_count':n,'no_cook':True})
manifest=export_building(objects,EXPORT,building_project.SCHEMA)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))
render(objects,OUTPUT,WIDTH)
write(OUTPUT/'manifest.json',{'name':NAME,'building':manifest,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in EXPORT.iterdir() if p.is_file()}})
print('TRAP030_COMPLETE '+NAME)

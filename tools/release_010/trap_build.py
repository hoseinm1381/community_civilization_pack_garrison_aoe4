"""Scratch game-art recipe. No gameplay, native bindings, or mechanical design."""
import bpy, sys, math, random, json, hashlib, shutil
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from trap_art_runner import mesh, join_parts, validate, render, export_building, write

ROOT=Path(__file__).resolve().parents[2]
ARGS=sys.argv[sys.argv.index('--')+1:]
NAME=ARGS[0] if ARGS else 'stake_thicket'
WIDTH=float(ARGS[1]) if len(ARGS)>1 else 6.4
SCHEMA=ARGS[2] if len(ARGS)>2 else 'garrison.building-source/v1'
SOURCE=ROOT/'art/authoring/traps_010'/NAME
EXPORT=ROOT/'art/exports/traps_010'/NAME
OUTPUT=ROOT/'output/release_010/traps'/NAME
for p in (SOURCE,EXPORT,OUTPUT): p.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
random.seed(3401 if NAME=='stake_thicket' else 3402)

def atlas():
    import numpy as np
    size=512; yy,xx=np.mgrid[0:size,0:size]; rng=np.random.default_rng(3411)
    noise=rng.random((size,size))-.5
    color=np.zeros((size,size,4),dtype=np.float32); color[:,:,3]=1
    warp=np.sin(yy*.023)*1.6
    knots=np.zeros_like(xx,dtype=float)
    for cx,cy in [(39,108),(105,340),(198,215),(221,445),(150,65)]:
        d=((xx-cx)/9)**2+((yy-cy)/27)**2
        warp+=np.exp(-d)*7; knots-=np.exp(-d)*.055
    grain=np.sin(xx*.30+warp)*.025+np.sin(xx*.73+yy*.009)*.012+noise*.025+knots
    broad=np.sin(xx*.065)*.022
    for i,c in enumerate((.205,.148,.084)): color[:,:,i]=c+grain+broad
    woodcut=(xx>=256)&(xx<384)
    rad=np.sqrt(((xx-320)*1.1)**2+((yy-256)*.63)**2)
    rings=np.sin(rad*.30+np.sin(yy*.04))*.019
    cracks=np.where((abs(np.sin(np.arctan2(yy-256,xx-320)*5+.4))<.035)&(rad>30),-.065,0)
    earth=(xx>=384)&(yy<256); leaf=(xx>=384)&(yy>=256)
    for i,c in enumerate((.30,.213,.123)): color[:,:,i][woodcut]=c+rings[woodcut]+noise[woodcut]*.04+cracks[woodcut]
    for i,c in enumerate((.222,.184,.112)): color[:,:,i][earth]=c+noise[earth]*.06
    for i,c in enumerate((.135,.175,.061)): color[:,:,i][leaf]=c+noise[leaf]*.045+np.sin(xx*.12)[leaf]*.017
    image=bpy.data.images.new('Trap_DarkHardwood_Atlas',width=size,height=size,alpha=True); image.pixels.foreach_set(color.ravel()); image.filepath_raw=str(SOURCE/'albedo.png'); image.file_format='PNG'; image.save(); image.pack()
    mat=bpy.data.materials.new('trap_neutral_atlas'); mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF'); bsdf.inputs['Roughness'].default_value=.9
    node=mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image=image; mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    shutil.copy2(SOURCE/'albedo.png',EXPORT/'albedo.png')
    for name,color_value in [('normal',(.5,.5,1,1)),('roughness',(.9,.9,.9,1)),('metalness',(0,0,0,1))]:
        image=bpy.data.images.new('Trap_'+name,width=16,height=16,alpha=False); image.generated_color=color_value; image.colorspace_settings.name='Non-Color'; image.filepath_raw=str(SOURCE/(name+'.png')); image.file_format='PNG'; image.save(); image.pack(); shutil.copy2(SOURCE/(name+'.png'),EXPORT/(name+'.png'))
    return mat
MAT=atlas()
ground=[]; wood=[]; contacts=[]

def earth_patch():
    n=26; verts=[]; contour=[]
    for i in range(n):
        a=i*math.tau/n; contour.append(1+.10*math.sin(a*3+.4)+.06*math.sin(a*5)+random.uniform(-.07,.07))
    for z,shrink in [(0,1),(.08,.87)]:
        for i in range(n):
            a=i*math.tau/n; r=contour[i]; zz=z if z==0 else z+.022*math.sin(a*4+.6)
            verts.append((math.cos(a)*2.65*r*shrink,math.sin(a)*2.05*r*shrink,zz))
    verts.append((-.13,.06,.095))
    faces=[tuple(reversed(range(n)))]+[(n+i,n+(i+1)%n,n*2) for i in range(n)]
    faces += [(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    ground.append(mesh('Earth_contact_lens',verts,faces,MAT,'earth'))

def stake(index,x,y,h,leanx,leany,r):
    # Thick faceted hardwood silhouette; base intersects the earth lens.
    n=8; verts=[]; base=.018; radial=[random.uniform(.83,1.14) for k in range(n)]
    phase=random.uniform(0,math.tau); bow=random.uniform(-.11,.11)
    for fraction,rr in [(0,r*1.12),(.32,r*.99),(.65,r*.88),(.81,r*.53)]:
        for k in range(n):
            angle=k*math.tau/n+phase; jitter=radial[k]
            zz=base+h*fraction+(random.uniform(-.04,.04)*h if fraction>0 else 0)
            verts.append((x+leanx*fraction+bow*math.sin(fraction*math.pi)+math.cos(angle)*rr*jitter,y+leany*fraction+math.sin(angle)*rr*jitter,zz))
    verts.append((x+leanx+random.uniform(-.45,.45)*r,y+leany+random.uniform(-.45,.45)*r,base+h))
    faces=[tuple(reversed(range(n)))]
    for ring in range(3): faces += [(ring*n+k,ring*n+(k+1)%n,(ring+1)*n+(k+1)%n,(ring+1)*n+k) for k in range(n)]
    faces += [(n*3+k,n*3+(k+1)%n,n*4) for k in range(n)]
    obj=mesh(f'Hardwood_{index:02}',verts,faces,MAT)
    # End-grain on the broad cut planes, longitudinal grain on shaft.
    uv=obj.data.uv_layers.active
    for poly in list(obj.data.polygons)[-n:]:
        for j,li in enumerate(poly.loop_indices): uv.data[li].uv=[(.54,.1),(.71,.1),(.625,.9)][j]
    wood.append(obj)
    hit,location,normal,face=ground[0].ray_cast(Vector((x,y,3)),Vector((0,0,-1)))
    assert hit and location.z>base
    contacts.append({'name':obj.name,'base_z':base,'earth_top_z':location.z,'embed':location.z-base,'passes':hit and base<location.z})

def leaf(index,x,y):
    # Sparse curved, folded solid leaves in low irregular clumps.
    for k in range(3):
        a=random.uniform(0,math.tau); length=random.uniform(.24,.44); width=random.uniform(.04,.07); rise=random.uniform(.08,.18)
        t=Vector((math.cos(a),math.sin(a),0)); side=Vector((-math.sin(a),math.cos(a),0)); anchor=Vector((x,y,.045))
        v=[anchor,anchor+t*length*.45+side*width+Vector((0,0,rise*.65)),anchor+t*length+Vector((0,0,rise*.55)),anchor+t*length*.45-side*width+Vector((0,0,rise*.65)),anchor+t*length*.45+Vector((0,0,rise)),anchor+t*length*.45+Vector((0,0,rise*.60))]
        faces=[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)]
        ground.append(mesh(f'Foliage_{index:02}_{k}',v,faces,MAT,'leaf'))

earth_patch()
if NAME=='stake_thicket':
    # Compact broken crescent silhouette, low at the outer tips.
    positions=[(-1.75,-.50,.60),(-1.2,-.75,.88),(-.55,-.80,1.05),(.1,-.75,1.20),(.8,-.63,.99),(1.45,-.30,.68),(-1.4,.25,.87),(-.72,.05,1.35),(.0,.10,1.55),(.72,.25,1.25),(1.3,.48,.84),(-.58,.83,1.10),(.12,.95,.96),(.8,.92,.68)]
    for i,(x,y,h) in enumerate(positions): stake(i,x,y,h,random.uniform(-.25,.28),random.uniform(-.20,.24),random.uniform(.14,.20))
    for i in range(8): leaf(i,random.uniform(-1.9,1.9),random.uniform(-1.2,1.3))
else:
    # Broad asymmetric fan silhouette with a shallow central brush cap.
    positions=[(-1.8,-.35,.67),(-1.26,-.7,.80),(-.67,-.87,.67),(.05,-.90,.73),(.75,-.76,.70),(1.40,-.5,.76),(1.90,.0,.65),(-1.6,.4,.70),(-1.05,.65,.88),(-.38,.70,.92),(.35,.80,.78),(1.08,.61,.88),(1.65,.48,.64),(-.83,.08,.81),(.85,.04,.76)]
    for i,(x,y,h) in enumerate(positions):
        length=math.sqrt(x*x+y*y) or 1
        stake(i,x,y,h,x/length*.33,y/length*.30,random.uniform(.17,.225))
    for i in range(13): leaf(i,random.uniform(-1.6,1.6),random.uniform(-1.0,1.05))

objects=[join_parts(ground,'Trap_00_earth_brush',0),join_parts(wood,'Trap_01_hardwood',20)]
# Parameterize authoring width only; native binding transforms remain integration-owned.
extent=max(v.co.x for o in objects for v in o.data.vertices)-min(v.co.x for o in objects for v in o.data.vertices)
factor=WIDTH/extent
center=Vector(((min(v.co.x for o in objects for v in o.data.vertices)+max(v.co.x for o in objects for v in o.data.vertices))/2,(min(v.co.y for o in objects for v in o.data.vertices)+max(v.co.y for o in objects for v in o.data.vertices))/2,0))
for obj in objects:
    for v in obj.data.vertices: v.co=(v.co-center)*factor
    obj['garrison_building_profile']='english-house'
checks=validate(objects)
collection=bpy.data.collections.new('GARRISON · '+NAME.replace('_',' ').title()); bpy.context.scene.collection.children.link(collection)
for key,value in {'garrison_asset_container':True,'garrison_asset_id':NAME,'garrison_namespace':'community_civilization_pack','garrison_display_name':NAME.replace('_',' ').title(),'garrison_qualified_id':'community_civilization_pack:'+NAME,'garrison_archetype':'building','garrison_building_profile':'english-house','garrison_building_integration':'script'}.items(): collection[key]=value
for obj in objects:
    collection.objects.link(obj)
    for previous in tuple(obj.users_collection):
        if previous!=collection: previous.objects.unlink(obj)
sys.path.insert(0,r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
from garrison import building_project
garrison_check=require_valid(objects,bpy.context)
adopt_material(MAT)
assert SCHEMA==building_project.SCHEMA
bounds={'min':[min(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]}
report={'schema':'ccp.trap-art-validation/v1','name':NAME,'requested_width':WIDTH,'bounds':bounds,'geometry':checks,'garrison_preflight':garrison_check,'contacts':contacts,'contact_scale':factor,'art_interpretation':'Scratch digital infantry-trap composition; medieval Bach Dang timber motif only, not a reconstructed historical device.','reference':'https://whc.unesco.org/document/211490','native_gameplay_edited':False,'owner_colour':'Neutral opaque atlas; native owner flags and visual markers retained by integration.','construction_stages':[0,20],'native_cook':'not run'}
write(OUTPUT/'validation.json',report)
manifest=export_building(objects,EXPORT,SCHEMA)
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))
render(objects,OUTPUT,WIDTH)
write(OUTPUT/'manifest.json',{'name':NAME,'source_blend':str(SOURCE/(NAME+'.blend')),'building':manifest,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in EXPORT.iterdir() if p.is_file()}})
print('TRAP_ART_COMPLETE '+NAME)

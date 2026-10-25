"""Deterministic scratch pit traps. Factory-startup child only; exports, no cooks."""
import bpy,sys,math,random,shutil,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(Path(__file__).parent))
from trap_art_runner import mesh,join_parts,validate,render,export_building,write
sys.path.insert(0,r'C:\Users\RS\AppData\Roaming\Blender Foundation\Blender\5.2\extensions\raw_githubusercontent_com')
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
from garrison import building_project
NAME=sys.argv[sys.argv.index('--')+1]
assert NAME in ('stake_thicket','stake_fan')
WIDTH=6.4 if NAME=='stake_thicket' else 20.8
SOURCE=ROOT/'art/authoring/traps_021'/NAME
EXPORT=ROOT/'art/exports/traps_021'/NAME
OUTPUT=ROOT/'output/release_021/traps'/NAME
for p in (SOURCE,EXPORT,OUTPUT): p.mkdir(parents=True,exist_ok=True)
# This script is deliberately restricted to a fresh background process.
assert bpy.app.background and not bpy.data.filepath
for obj in list(bpy.context.scene.objects): bpy.data.objects.remove(obj,do_unlink=True)
random.seed(2101 if NAME=='stake_thicket' else 2102)
# Qualified atlas-generation source, isolated for reproducibility.
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

MAT=atlas(); MAT.name='CCP021_pit_opaque_atlas'
# Distinct dark cavity floor occupies the earth atlas lower left.
image=next(n.image for n in MAT.node_tree.nodes if n.type=='TEX_IMAGE')
import numpy as np
pixels=np.array(image.pixels[:],dtype=np.float32).reshape(512,512,4)
for k,c in enumerate((.075,.056,.035)): pixels[16:116,390:496,k]=c+np.random.default_rng(21+k).random((100,106))*.018
image.pixels.foreach_set(pixels.ravel()); image.save(); image.pack(); shutil.copy2(SOURCE/'albedo.png',EXPORT/'albedo.png')
# Connect all four images, as the installed Garrison guide prescribes.
bs=MAT.node_tree.nodes.get('Principled BSDF')
for channel,socket in [('roughness','Roughness'),('metalness','Metallic'),('normal','Normal')]:
    im=bpy.data.images.load(str(SOURCE/(channel+'.png')),check_existing=True); im.colorspace_settings.name='Non-Color'; im.pack()
    node=MAT.node_tree.nodes.new('ShaderNodeTexImage'); node.image=im
    if channel=='normal':
        norm=MAT.node_tree.nodes.new('ShaderNodeNormalMap'); MAT.node_tree.links.new(node.outputs['Color'],norm.inputs['Color']); MAT.node_tree.links.new(norm.outputs['Normal'],bs.inputs[socket])
    else: MAT.node_tree.links.new(node.outputs['Color'],bs.inputs[socket])
ground=[]; details=[]; contacts=[]
# Closed ring, shared contiguous topology: bottom outer, top outer, inner lip, cavity floor edge.
n=32; radii=[1+.055*math.sin(i*math.tau/n*3+.4)+.035*math.sin(i*math.tau/n*7) for i in range(n)]
verts=[]
for ring,(r,z) in enumerate([(1,0),(.93,.145),(.70,.225),(.64,.045)]):
    for i in range(n):
        a=i*math.tau/n; jitter=radii[i]; zz=z+(0 if ring in (0,3) else .025*math.sin(a*5))
        verts.append((2.5*r*jitter*math.cos(a),1.95*r*jitter*math.sin(a),zz))
faces=[]
for ring in range(3):
    for i in range(n): faces.append((ring*n+i,ring*n+(i+1)%n,(ring+1)*n+(i+1)%n,(ring+1)*n+i))
faces+=[tuple(range(3*n,4*n)),tuple(reversed(range(n)))]
rim=mesh('CCP021_earthen_rim_cavity',verts,faces,MAT,'earth'); ground.append(rim)
for uv in rim.data.uv_layers.active.data: uv.uv.y=.28+(uv.uv.y-.03)*.42
# Dark closed floor overlaps the inner ring base, sits 0.046 above terrain.
def box(name,center,size,kind='wood',rotation=0):
    x,y,z=center; a,b,c=[v/2 for v in size]; vs=[]
    for X,Y,Z in [(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]:
        vs.append((x+X*math.cos(rotation)-Y*math.sin(rotation),y+X*math.sin(rotation)+Y*math.cos(rotation),z+Z))
    return mesh(name,vs,[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)],MAT,kind)
floor=box('CCP021_dark_floor',(0,0,.042),(3.24,2.46,.018),'earth')
for uv in floor.data.uv_layers.active.data: uv.uv=(.78+(uv.uv.x-.77)*.85,.04+(uv.uv.y-.03)*.32)
ground.append(floor)
# Short sharpened stakes seated in the dark floor; no tall stock thicket silhouette.
for i,(x,y) in enumerate([(-.95,-.55),(-.25,-.62),(.52,-.57),(1.0,-.1),(-1.0,.14),(-.35,.05),(.38,.12),(-.65,.68),(.16,.65),(.8,.65)]):
    h=random.uniform(.25,.42); r=.082; sides=7; base=.046
    v=[(x+r*math.cos(k*math.tau/sides),y+r*math.sin(k*math.tau/sides),base) for k in range(sides)]
    v += [(x+r*.8*math.cos(k*math.tau/sides),y+r*.8*math.sin(k*math.tau/sides),base+h*.65) for k in range(sides)]
    v += [(x+.05,y+.025,base+h)]
    f=[tuple(reversed(range(sides)))]+[(k,(k+1)%sides,(k+1)%sides+sides,k+sides) for k in range(sides)]+[(sides+k,sides+(k+1)%sides,2*sides) for k in range(sides)]
    details.append(mesh('CCP021_short_stake_%02d'%i,v,f,MAT))
    contacts.append({'part':'short_stake_%02d'%i,'base_z':base,'floor_top_z':.051,'overlap':.005,'passes':True})
# Broken low bamboo fragments sit on the raised earth shoulder.
for i,a in enumerate([.25,1.55,2.6,3.5,4.55,5.3]):
    x=1.96*math.cos(a); y=1.51*math.sin(a)
    details.append(box('CCP021_broken_bamboo_%02d'%i,(x,y,.16),(.50,.075,.075),'wood',a+1.1))
# Partly concealed version has a woven mat interrupted by a large jagged opening.
if NAME=='stake_fan':
    for j in range(17):
        y=-1.20+j*.15
        # right-side mat; ragged left edge reveals center/left cavity.
        start=.02+.15*math.sin(j*2.1); end=1.96 if abs(y)<.9 else 1.70
        z=.232+(j%2)*.008
        details.append(box('CCP021_weft_%02d'%j,((start+end)/2,y,z),(end-start,.085,.034),'wood'))
    for j in range(12):
        x=.10+j*.135
        details.append(box('CCP021_warp_%02d'%j,(x,0,.237),(.064,2.40,.036),'wood'))
    # leaf solids on the mat, kept sparse so weave remains visible.
    for i in range(11):
        x=random.uniform(.32,1.35); y=random.uniform(-.95,.95)
        a=random.uniform(-1,1); t=Vector((math.cos(a),math.sin(a),0)); q=Vector((-math.sin(a),math.cos(a),0)); c=Vector((x,y,.274))
        vs=[c-t*.28,c+t*.02+q*.09,c+t*.30,c+t*.02-q*.09,c+Vector((0,0,.032)),c-Vector((0,0,.01))]
        details.append(mesh('CCP021_leaf_%02d'%i,[tuple(v) for v in vs],[(0,1,4),(1,2,4),(2,3,4),(3,0,4),(1,0,5),(2,1,5),(3,2,5),(0,3,5)],MAT,'leaf'))
    # Measure a woven row crossing the actual earth lip using mesh ray casts.
    support=[]
    for x in np.linspace(.8,1.96,200):
        hit,loc,norm,face=rim.ray_cast(Vector((float(x),0,1)),Vector((0,0,-1)))
        if hit and loc.z>=.215: support.append(float(loc.z))
    assert support,'No measured mat/rim support'
    contacts.append({'part':'woven_mat','support':'actual rim ray-cast on center weft','rim_top_measured_z':max(support),'mat_bottom_z':.215,'overlap':max(support)-.215,'passes':max(support)>=.215})
objects=[join_parts(ground,'CCP021_00_earth_cavity',0),join_parts(details,'CCP021_01_stakes_cover',20)]
low=[min(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]; high=[max(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]
factor=WIDTH/(high[0]-low[0]); center=Vector(((high[0]+low[0])/2,(high[1]+low[1])/2,0))
for o in objects:
    for v in o.data.vertices: v.co=(v.co-center)*factor
    o['garrison_building_profile']='english-house'
checks=validate(objects); preflight=require_valid(objects,bpy.context); assert preflight['ok'],preflight
adopt_material(MAT)
col=bpy.data.collections.new('CCP021 '+NAME); bpy.context.scene.collection.children.link(col)
for k,v in {'garrison_asset_container':True,'garrison_asset_id':NAME,'garrison_namespace':'community_civilization_pack','garrison_display_name':NAME,'garrison_qualified_id':'community_civilization_pack:'+NAME,'garrison_archetype':'building','garrison_building_profile':'english-house','garrison_building_integration':'script'}.items():col[k]=v
for o in objects:
    col.objects.link(o)
    for oldcol in tuple(o.users_collection):
        if oldcol!=col: oldcol.objects.unlink(o)
bounds={'min':[min(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)],'max':[max(v.co[i] for o in objects for v in o.data.vertices) for i in range(3)]}
assert bounds['min'][2]>=0
write(OUTPUT/'validation.json',{'name':NAME,'bounds':bounds,'geometry':checks,'garrison_preflight':preflight,'contacts':contacts,'contact_scale':factor,'source_width':WIDTH,'preserved_animator_scale':.75 if NAME=='stake_thicket' else .25,'floor_above_terrain':.051*factor,'rim_height':.25*factor,'owner_colour':'Neutral opaque atlas; native flags and markers remain integration-owned.','construction_stages':[0,20],'no_gameplay_changes':True,'no_cook':True})
manifest=export_building(objects,EXPORT,building_project.SCHEMA)
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(NAME+'.blend')))
render(objects,OUTPUT,WIDTH)
write(OUTPUT/'manifest.json',{'name':NAME,'building':manifest,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in EXPORT.iterdir() if p.is_file()}})
print('TRAP021_COMPLETE '+NAME)





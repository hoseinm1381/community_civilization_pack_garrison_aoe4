"""Owned Ministry 021 refinement; run in serialized factory-startup Blender.

Retains the qualified 020 geometry generator/export route, with 021 outputs only.
Actual stock worker elephant LOD1 is frozen from its decoded standing bind pose.
"""
import bpy, bmesh, json, math, os, sys, hashlib, importlib.util
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration, check_storage
CFG=configuration(ROOT);check_storage(ROOT,CFG)
EXT=Path(CFG['garrison_extension'])
sys.path.insert(0,str(EXT))
spec=importlib.util.spec_from_file_location('garrison_shared',str(EXT/'garrison_shared.cp313-win_amd64.pyd'))
shared=importlib.util.module_from_spec(spec);sys.modules['garrison_shared']=shared;spec.loader.exec_module(shared)
sys.path.insert(0,str(EXT.parent));import garrison
sys.modules['garrison.garrison_shared']=shared;garrison.register()
sys.path.insert(0,str(ROOT/'tools/release_020'))
original=ROOT/'tools/release_020/model_ministry_farm_hideout.py'
code=original.read_text().split('notes = ministry()')[0]
code=code.replace('buildings_020','buildings_021').replace('output/release_020/ministry_farm_hideout','output/release_021')
# Preserve original __file__ root calculation while rewriting only owned paths.
namespace={'__file__':str(original),'__name__':'ccp021_ministry_geometry'}
argv=sys.argv;sys.argv=[str(original),'--','ministry']
exec(compile(code,str(original),'exec'),namespace);sys.argv=argv
globals().update({k:v for k,v in namespace.items() if not k.startswith('__')})
notes=ministry()
original_geometry=validate(base+superstructure)
# Preserve full-size hall/wing architecture and relocate it to the compound rear.
# The former miniature yard is superseded, retained separately in draft-single.
retired=('Packed_yard_base','Yard_post','Yard_long_rail','Yard_west_rail','Stone_water_trough','Trough_water')
for parts in (base,superstructure):
    for o in list(parts):
        if o.name.startswith(retired):parts.remove(o);bpy.data.objects.remove(o,do_unlink=True)
        else:
            for v in o.data.vertices:v.co.y+=2.0
contacts[:]=[c for c in contacts if c['interface'] not in ('yard posts/earth','water trough/earth')]
# The broad exterior yard uses two pens around a clear 2.2m central lane.
# Closed shallow terrain meshes sit on ground, rather than elevated platforms.
def yard_patch(label,x0,x1,y0,y1):
    perimeter=[(x0+.13,y0),(x1-.15,y0),(x1,y0+.18),(x1,y1-.14),
               (x1-.18,y1),(x0+.15,y1),(x0,y1-.17),(x0,y0+.19)]
    verts=[(x,y,z) for z in (0,.08) for x,y in perimeter]
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    add(mesh(label,verts,faces,MAT,'earth'),0)
yard_patch('Exterior_west_elephant_yard',-7.50,-1.25,-7.45,-.60)
yard_patch('Exterior_east_elephant_yard',1.25,7.50,-7.45,-4.52)
add(box('Central_open_ground_path',(0,-3.65,.018),(2.20,7.30,.036),MAT,'earth'),0)
def rail_run(label,a,b):
    length=math.dist(a,b);count=math.ceil(length/2.2)
    points=[(a[0]+(b[0]-a[0])*i/count,a[1]+(b[1]-a[1])*i/count) for i in range(count+1)]
    for i,(x,y) in enumerate(points):
        add(box(f'{label}_post_{i}',(x,y,.78),(.16,.16,1.48),MAT,'timber'))
        contacts.append({'interface':f'{label} post{i}/ground','signed_gap':.04-.08})
    for i,(a,b) in enumerate(zip(points,points[1:])):
        for z in (.66,1.20):beam(f'{label}_rail_{i}_{z}',(a[0],a[1],z),(b[0],b[1],z),.12)
for label,x0,x1,y0,y1 in (('West',-7.42,-1.34,-7.35,-.69),('East',1.34,7.42,-7.35,-4.60)):
    outer=x0 if label=='West' else x1
    rail_run(label+'_outer',(outer,y0),(outer,y1))
    rail_run(label+'_front',(x0,y0),(x1,y0))
    rail_run(label+'_rear',(x0,y1),(x1,y1))
    # Inner edges leave a broad side gate into the central production lane.
    rail_run(label+'_inner_front',(x1 if label=='West' else x0,y0),(x1 if label=='West' else x0,y0+1.55))
    rail_run(label+'_inner_rear',(x1 if label=='West' else x0,y1-1.25),(x1 if label=='West' else x0,y1))
add(box('Yard_water_trough',(7.15,-6.00,.20),(.35,1.65,.30),MAT,'brick'))
add(box('Yard_trough_water',(7.15,-6.00,.355),(.19,1.48,.025),MAT,'water'))
contacts.append({'interface':'yard trough/earth','signed_gap':-.03})

donor_path=next((ROOT/'output/release_021/ministry/stock_elephant').rglob('decoded-static.json'))
donor=json.loads(donor_path.read_text())
assert donor['rig_projection']['status']=='complete'
group=next(g for g in donor['geometry']['groups'] if g['name']=='geo_tug_elephant_worker_age1' and g['group_index']==0)
assert group['preview_material']=='tug_elephant_lod1'
positions=np.asarray(group['positions'],dtype=float)
# The stock rest pose has all four legs below its body and the trunk down;
# freeze its geometry directly, preserving every native triangle and UV seam.
lo=positions.min(0);hi=positions.max(0);scale=1.0
foot_region=(np.abs(positions[:,0])>.3)&(np.abs(positions[:,1])<2)
sole=float(positions[foot_region,2].min())
# The stock bind trunk points 0.24m below its soles. A gentle pose-only lift of
# its terminal section lets the retained stock feet and trunk seat on the yard.
tip_lift=sole-float(positions[:,2].min())
factor=np.clip((-positions[:,1]-2.0)/1.2,0,1)
factor=factor*factor*(3-2*factor)
positions[:,2]+=tip_lift*factor*np.clip((1.15-positions[:,2])/.8,0,1)
positions[:,0]-=(lo[0]+hi[0])/2
positions[:,1]-=(lo[1]+hi[1])/2
positions[:,2]=(positions[:,2]-sole)+.08
elephant_objects=[];elephant_records=[]
for index,(cx,cy,yaw) in enumerate(((-4.40,-6.00,88),(-4.40,-2.35,92),(4.20,-6.00,88))):
    angle=math.radians(yaw);p=positions.copy()
    p[:,0]=positions[:,0]*math.cos(angle)-positions[:,1]*math.sin(angle)+cx
    p[:,1]=positions[:,0]*math.sin(angle)+positions[:,1]*math.cos(angle)+cy
    data=bpy.data.meshes.new(f'Stock_worker_elephant_{index+1}_standing_static')
    data.from_pydata(p.tolist(),[],group['triangles']);data.update()
    elephant=bpy.data.objects.new(data.name,data);bpy.context.scene.collection.objects.link(elephant)
    uv=data.uv_layers.new(name='UVMap');uvs=group['uv_layers']['UVMap']
    for poly in data.polygons:
        poly.use_smooth=True
        for li in poly.loop_indices:
            u,v=uvs[data.loops[li].vertex_index];uv.data[li].uv=(u%1,v%1)
    data.materials.append(MAT);superstructure.append(elephant);elephant_objects.append(elephant)
    bounds={'minimum':p.min(0).tolist(),'maximum':p.max(0).tolist()}
    assert max(abs(bounds[k][0]) for k in bounds)<7.50,bounds
    assert bounds['minimum'][1]>-7.35 and bounds['maximum'][1]<-.60,bounds
    assert bounds['maximum'][0]<-1.1 or bounds['minimum'][0]>1.1,bounds
    elephant_records.append({'index':index+1,'center':[cx,cy],'yaw_degrees':yaw,'bounds_before_shift':bounds,
        'sole_gap':float(p[foot_region,2].min()-.08),'stock_scale':1.0})
    contacts.append({'interface':f'elephant {index+1} hoof/yard','signed_gap':float(p[foot_region,2].min()-.08)})
# Exact unchanged stock benches are incorporated as keep-out boxes, not moved.
bench_rows=json.loads((ROOT/'output/release_020/inventory/native-graph.json').read_text())['stamps']['economy_ministry']['visuals']
bench_clearance=[]
for b in [r for r in bench_rows if r['model'].endswith('/stone_bench')]:
    t=b['transform'];bx,bz=t[4],t[6]
    bench_min=[bx-.787,bz-.264];bench_max=[bx+.787,bz+.264]
    for e in elephant_records:
        bounds=e['bounds_before_shift'];emin=[bounds['minimum'][0],bounds['minimum'][1]+.0693049793243408];emax=[bounds['maximum'][0],bounds['maximum'][1]+.0693049793243408]
        separation=max(bench_min[0]-emax[0],emin[0]-bench_max[0],bench_min[1]-emax[1],emin[1]-bench_max[1])
        assert separation>.10,(b,e,separation)
        bench_clearance.append({'bench_translation':[bx,bz],'elephant':e['index'],'aabb_separation_m':separation})

# A single shared atlas follows the qualified construction exporter contract.
# Left half: original 8 building swatches with weathered surface detail; right:
# stock worker elephant albedo with original UVs. No player-colour is baked in.
N=1024
old=bpy.data.images.load(str(source/'albedo.png'),check_existing=False);old.scale(N,N)
pixels=np.array(old.pixels[:],dtype=np.float32).reshape(N,N,4)
stockbuilding_path=next((ROOT/'art/stock_cache/buildings_020/barracks_tc/barracks/age01').rglob('decoded-static.json'))
stockbuilding=json.loads(stockbuilding_path.read_text())
surface_sources=[]
for tile,needle in ((1,'str_wood_chi_generic_02_alb'),(3,'str_plaster_cob_01_alb')):
    t=next(t for m in stockbuilding['material']['materials'] for t in m['textures'] if needle in t.get('texture_name',''))
    img=bpy.data.images.load(t['projection_path'],check_existing=False);img.scale(256,512)
    sample=np.array(img.pixels[:],dtype=np.float32).reshape(512,256,4)
    col,row=tile%4,tile//4;sl=np.s_[row*512:(row+1)*512,col*256:(col+1)*256]
    if tile==1:
        # Borrow chipped stock timber texture without carrying its red lacquer.
        luminance=sample[:,:,:3]@np.array([.2126,.7152,.0722])
        mean=max(float(luminance.mean()),.001)
        tint=pixels[sl+(slice(0,3),)].mean(axis=(0,1))
        sample[:,:,:3]=np.clip((luminance/mean)[:,:,None]*tint,0,1)
    pixels[sl+(slice(0,3),)]=.55*pixels[sl+(slice(0,3),)]+.45*sample[:,:,:3]
    import shutil
    refdir=source/'donor';refdir.mkdir(exist_ok=True)
    ref=refdir/(needle+'.dds');shutil.copy2(t['projection_path'],ref)
    surface_sources.append({'stock_texture':t['texture_name'],'retained_source':str(ref),'sha256':sha(ref)})
yy,xx=np.mgrid[:N,:N];rng=np.random.default_rng(21021)
noise=rng.normal(0,.012,(N,N));height=np.zeros((N,N),float)
rough=np.full((N,N),.84)
for i in range(8):
    col,row=i%4,i//4;sl=np.s_[row*512:(row+1)*512,col*256:(col+1)*256]
    x=xx[sl]-col*256;y=yy[sl]-row*512
    grime=np.zeros(x.shape)
    if i==3:
        # Vertical rain tracks, damp foot and irregular lime-plaster mottling.
        streak=(np.sin(x*.19+np.sin(x*.033)*2)>.65)*.045*(.4+.6*y/512)
        grime=streak+.085*np.exp(-y/90)+.026*np.sin(x*.052+np.sin(y*.028))
        height[sl]=noise[sl]*.15;rough[sl]=.88+noise[sl]
    elif i==1:
        grain=np.sin(x*.29+np.sin(y*.016)*1.6)+.35*np.sin(x*.87+y*.008)
        grime=.019*grain+.015*np.cos(y*.045);height[sl]=grain*.12;rough[sl]=.74+.10*np.sin(x*.051)**2
    elif i==2:
        channel=np.sin(x*.74+((y//22)%2)*.8)
        grime=.024*channel+.023*(y%22<3)+.02*np.sin(x*.043+y*.019)
        height[sl]=channel*.24+(y%22<3)*-.20;rough[sl]=.77+.10*np.sin(x*.043+y*.021)**2
    elif i in (0,4):
        grime=.025*np.sin(x*.11+y*.17)+noise[sl];height[sl]=noise[sl]*.9;rough[sl]=.9+noise[sl]*2
    else:grime=noise[sl]
    pixels[sl+(slice(0,3),)]=np.clip(pixels[sl+(slice(0,3),)]-grime[:,:,None],0,1)
albedo=next(t for m in donor['material']['materials'] if m['name']=='tug_elephant_lod1' for t in m['textures'] if t['name']=='albedoTexture')
import shutil
shutil.copy2(albedo['projection_path'],source/'donor/stock-worker-elephant-albedo.dds')
write(source/'donor/stock-worker-elephant-lod1.json',{'group':group,'donor_manifest_sha256':sha(donor_path),
    'logical_path':donor['request']['logical_path'],'stock_albedo_resource':albedo['logical_path']})
stock=bpy.data.images.load(albedo['projection_path'],check_existing=False);stock.scale(N,N)
stockpixels=np.array(stock.pixels[:],dtype=np.float32).reshape(N,N,4)
rgba=np.concatenate([pixels,stockpixels],axis=1)
rgba[:,:,3]=1
def image_map(label,arr,noncolor=False):
    image=bpy.data.images.new('CCP_021_ministry_'+label,width=2*N,height=N,alpha=True)
    if noncolor:image.colorspace_settings.name='Non-Color'
    image.pixels.foreach_set(arr.astype(np.float32).ravel())
    image.filepath_raw=str(source/(label+'.png'));image.file_format='PNG';image.save();image.pack()
    import shutil;shutil.copy2(source/(label+'.png'),target/(label+'.png'))
    return image
alb=image_map('albedo',rgba)
gx,gy=np.gradient(height);normal=np.ones((N,2*N,4),dtype=np.float32)
normal[:,:,:3]=(.5,.5,1);normal[:,:N,0]=.5-gy*.32;normal[:,:N,1]=.5-gx*.32
norm=image_map('normal',normal,True)
r=np.ones_like(rgba);r[:,:N,:3]=np.clip(rough,.60,.98)[:,:,None];r[:,N:,:3]=.87
rou=image_map('roughness',r,True)
metal=np.ones_like(rgba);metal[:,:,:3]=0;image_map('metalness',metal,True)
for o in base+superstructure:
    for item in o.data.uv_layers.active.data:item.uv.x=item.uv.x*.5+(.5 if o in elephant_objects else 0)
nodes=MAT.node_tree.nodes;links=MAT.node_tree.links;shader=nodes.get('Principled BSDF')
for node in list(nodes):
    if node.type=='TEX_IMAGE':nodes.remove(node)
for image,socket in ((alb,'Base Color'),(rou,'Roughness')):
    node=nodes.new('ShaderNodeTexImage');node.image=image;links.new(node.outputs['Color'],shader.inputs[socket])
node=nodes.new('ShaderNodeTexImage');node.image=norm
normalnode=nodes.new('ShaderNodeNormalMap');normalnode.inputs['Strength'].default_value=.40
links.new(node.outputs['Color'],normalnode.inputs['Color']);links.new(normalnode.outputs['Normal'],shader.inputs['Normal'])
notes['trunk_terminal_pose_lift_native_m']=tip_lift
# Preserve the seven required orthographic/isometric views while using bounded
# review renders. Geometry, materials and exports are unaffected by sample count.
import inspect
render_code=inspect.getsource(render_views).replace('"CYCLES"','"BLENDER_EEVEE"').replace('samples = 12','samples = 4').replace('resolution_x = 900','resolution_x = 640').replace('resolution_y = 750','resolution_y = 540')
exec(compile(render_code,'021_ministry_review_views','exec'),render_views.__globals__)
render_views=render_views.__globals__['render_views']
notes.update({'stock_elephants':{'donor':donor['request'],'uniform_scale':scale,'count':3,'instances':elephant_records,
    'pose':'stock decoded standing geometry; terminal trunk gently raised to sole plane, frozen static without skeleton or entity',
    'access':'two exterior pens;2.2m central path, open side gates, origin clear'},
    'ground_footprint':'16x16 user-approved compound; placement source change owned by integration agent',
    'architectural_shift_source_y_m':2.0,
    'surface_refinement':'rain-streaked dirty lime plaster, wood grain, fired-tile channels, roughness and tangent normal variation',
    'geometry_only_blender_y_shift_m':-1.812,'principal_stamp_transform_unchanged':True})
for o in base+superstructure:
    for v in o.data.vertices:v.co.y-=1.812
all_vertices=[v.co for o in base+superstructure for v in o.data.vertices]
world_bounds={'minimum':[min(v.x for v in all_vertices),min(v.z for v in all_vertices),min(v.y for v in all_vertices)+1.8813049793243408],
              'maximum':[max(v.x for v in all_vertices),max(v.z for v in all_vertices),max(v.y for v in all_vertices)+1.8813049793243408]}
# Garrison cooked X=-Blender X and Z=-Blender Y; native yaw reverses both.
assert all(abs(world_bounds[k][i])<=7.75 for k in world_bounds for i in (0,2)),world_bounds
assert max(c['signed_gap'] for c in contacts)<=1e-6,contacts
notes['expected_world_bounds_m']=world_bounds
objects=[join_stage(base,'Ministry_00_foundation',0),join_stage(superstructure,'Ministry_20_superstructure',20)]
for o in objects:o['garrison_building_profile']='english-house'
from garrison.model_preflight_ui import require_valid
from garrison.material_adoption import adopt_material
preflight=require_valid(objects,bpy.context);assert preflight['ok'] is True;adopt_material(MAT)
export_building(objects,target)
bpy.ops.file.pack_all();bpy.context.preferences.filepaths.save_version=0
blend=source/'ministry.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
render_views(objects,out)
report={'schema':'ccp.021-ministry-art/v1','asset':'ministry','status':'authored','source':str(blend),
    'source_sha256':sha(blend),'export':str(target),'export_files':{p.name:sha(p) for p in target.iterdir() if p.is_file()},
    'donor_manifest':str(donor_path),'donor_manifest_sha256':sha(donor_path),
    'generator_dependencies':{str(p):sha(p) for p in (original,ROOT/'tools/release_020/model_ministry_farm_hideout_runner.py',Path(__file__))},
    'before_020_preview':str(ROOT/'output/release_020/ministry_farm_hideout/ministry/iso.png'),
    'stock_building_surface_sources':surface_sources,
    'donor_resource_hashes':{k:v.get('sha256') for k,v in donor['resources'].items() if isinstance(v,dict) and 'sha256' in v},
    'garrison_preflight':preflight,'original_closed_building_geometry':original_geometry,'contact_checks':contacts,
    'native_bench_clearance_checks':bench_clearance,
    'notes':notes,'construction_stages':[0,20],'native_cook':'parent-owned pending','native_match':'not run',
    'material_validation':{'one_material':all(len(o.data.materials)==1 for o in objects),'atlas_size':[2048,1024],
        'roughness_range':[float(np.clip(rough,.60,.98).min()),float(np.clip(rough,.60,.98).max())],'normal_nonflat':bool(np.std(normal[:,:N,0])>.001),
        'stock_elephant_albedo_resource':albedo['logical_path']},
    'previews':{p.name:{'path':str(p),'sha256':sha(p)} for p in out.glob('*.png')}}
write(out/'handoff.json',report);write(ROOT/'art/recipes/release_021/ministry-source.json',report)
print('CCP_021_MINISTRY_READY',flush=True)

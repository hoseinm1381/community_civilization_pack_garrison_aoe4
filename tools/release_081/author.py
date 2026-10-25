"""Deterministic staged buffalo construction; old masters never overwritten.

Anatomy: long low head, high broad withers, tapered loin, strong articulated legs.
Units follow the native cattle rig. Nose-to-rump/withers-height ~= 1.85;
body width/height ~= .48. Gear anchors derive from the same torso profile.
"""
import sys,math,random
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent))
from common import *
sys.path.append(str(ROOT/'tools/release_079'))
from mesh_workshop import Workshop,uv_tile
from author_units import weights
from export_pilot import addon
from rig_contract import rig_text

REV=sys.argv[sys.argv.index('--')+2] if '--' in sys.argv and len(sys.argv)>sys.argv.index('--')+2 else 'r1'
T=[]
RINGS=[(1.22,1.32,.035,.06),(1.10,1.32,.25,.32),(.88,1.30,.33,.38),(.58,1.27,.375,.43),(.25,1.25,.40,.46),(-.05,1.28,.39,.46),(-.32,1.33,.38,.43),(-.53,1.33,.32,.38),(-.72,1.25,.23,.30)]
def torso(y):
    for a,b in zip(RINGS,RINGS[1:]):
        if b[0]<=y<=a[0]:
            t=(a[0]-y)/(a[0]-b[0]);return tuple(a[k]*(1-t)+b[k]*t for k in (1,2,3))
    raise ValueError('Outside pad anchor surface')
def surface(y,theta,offset=0):
    z,rx,rz=torso(y);return (math.sin(theta)*(rx+offset),y,z+math.cos(theta)*(rz+offset))
def atlas(folder):
    folder.mkdir(parents=True,exist_ok=True)
    colors=[(145,130,112),(156,145,119),(88,76,64),(19,17,14),(163,128,75),(205,195,169),(120,82,42),(176,150,101),(56,50,43),(170,151,124),(80,83,81),(63,56,47),(125,100,85),(218,190,135),(107,90,70),(212,200,172)]
    size=2048;n=512;yy,xx=np.mgrid[0:n,0:n];rng=np.random.default_rng(810)
    arrays={k:np.zeros((size,size,4),np.float32) for k in ('albedo','normal','roughness','metalness','pattern')}
    arrays['normal'][:]=(.5,.5,1,1)
    for t,c in enumerate(colors):
        noise=rng.normal(0,1,(n,n));height=noise*.0015
        detail=noise*.006
        if t in (0,2,9,14):
            detail+=.011*np.sin(yy*.075+np.sin(xx*.018)*1.4)+.005*np.sin(xx*.4+yy*.9)
            # Irregular short hair strands; no evenly spaced carved ridges.
            for _ in range(3100):
                x=int(rng.integers(4,n-10));y=int(rng.integers(4,n-16));length=int(rng.integers(3,11))
                for k in range(length):
                    detail[y+k,x+k//4]-=.022*(1-k/length);height[y+k,x+k//4]+=.003
        elif t==4:
            detail+=.032*np.sin(xx*math.pi/12)*np.cos(yy*math.pi/12);height+=.014*np.sin(xx*math.pi/12)*np.cos(yy*math.pi/12)
        elif t in (5,7,13):
            detail+=.008*np.sin(xx*math.pi/2)+.008*np.sin(yy*math.pi/2);height+=.002*np.sin(xx*math.pi/2)*np.sin(yy*math.pi/2)
        elif t==6:detail+=.028*np.sin(xx*.035+np.sin(yy*.011)*2)
        elif t in (1,11):detail+=.015*np.sin(yy*.22)+.007*np.sin(xx*.019)
        rgb=np.clip(np.array(c)[None,None,:]/255+detail[:,:,None],0,1)
        linear=np.where(rgb<=.04045,rgb/12.92,((rgb+.055)/1.055)**2.4)
        region=np.s_[t//4*n:(t//4+1)*n,t%4*n:(t%4+1)*n]
        arrays['albedo'][region][:,:,:3]=linear
        rough=.86 if t in (0,2,9,14) else .76
        if t in (1,8,11):rough=.64
        if t==3:rough=.27
        if t==10:rough=.58
        arrays['roughness'][region][:,:,:3]=np.clip(rough+noise[:,:,None]*.018,0,1)
        arrays['metalness'][region][:,:,:3]=.72 if t==10 else 0
        arrays['pattern'][region][:,:,0]=1 if t==5 else 0
        dy,dx=np.gradient(height);arrays['normal'][region][:,:,0]=.5-dx*.8;arrays['normal'][region][:,:,1]=.5-dy*.8
    images={}
    for name,pixels in arrays.items():
        pixels[:,:,3]=1;im=bpy.data.images.new('081_'+name,width=size,height=size,alpha=True)
        if name!='albedo':im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save();im.pack();im.use_fake_user=True;images[name]=im
    mat=bpy.data.materials.new('lod1');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Specular IOR Level'].default_value=.25
    for name,slot in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images[name];mat.node_tree.links.new(tex.outputs['Color'],bs.inputs[slot])
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=images['normal'];nm=mat.node_tree.nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.45;mat.node_tree.links.new(tex.outputs['Color'],nm.inputs['Color']);mat.node_tree.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    return mat
def init():
    # Append only the official unchanged armature; none of the old visible mesh.
    source=ROOT/'art/authoring/release_0710/buffalo/r1/model.blend'
    for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
    with bpy.data.libraries.load(str(source),link=False) as (a,b):b.objects=[n for n in a.objects if 'Armature' in n]
    rig=next(o for o in b.objects if o.type=='ARMATURE');bpy.context.scene.collection.objects.link(rig);rig.animation_data_clear();rig.data.pose_position='REST'
    rig.name='081_Native_cattle_45';rig.hide_render=True
    return rig
def anatomy(w):
    rows=[((0,y,z),rx,rz) for y,z,rx,rz in RINGS]
    ws=[{'root_m':1},{'root_m':1},{'root_m':.85,'spine1_m':.15},{'root_m':.35,'spine1_m':.65},{'spine1_m':1},{'spine1_m':.4,'chest_m':.6},{'chest_m':1},{'chest_m':1},{'chest_m':.7,'neck_m':.3}]
    w.loft('081_Ribcage_hip_withers',rows,0,ws,32,'y',3)
    head=[(-.58,1.27,.255,.29),(-.78,1.23,.255,.30),(-.98,1.27,.23,.30),(-1.16,1.30,.24,.27),(-1.30,1.24,.225,.245),(-1.45,1.13,.195,.19),(-1.60,1.02,.18,.145),(-1.74,.97,.225,.12),(-1.84,.97,.20,.10)]
    hw=[{'chest_m':.8,'neck_m':.2},{'neck_m':1},{'neck1_m':.8,'head_m':.2}]+[{'head_m':1}]*6
    w.loft('081_Neck_brow_muzzle',[((0,y,z),rx,rz) for y,z,rx,rz in head],0,hw,32,'y',3)
    w.loft('081_Throat',[((0,y,z),rx,rz) for y,z,rx,rz in [(-.59,1.03,.20,.22),(-.8,1.00,.20,.225),(-1.03,1.06,.15,.18),(-1.3,1.04,.13,.10)]],0,[{'chest_m':1},{'neck_m':1},{'neck1_m':1},{'head_m':1}],24,'y',3)
    main=[o.name for o in w.parts]
    for side,sign in [('l',1),('r',-1)]:
        for front in (True,False):
            ns=([n+side for n in ('frontrump_','fronthip_','frontknee_','frontankle_','fronttoes_')] if front else [n+side for n in ('backhip_','backknee_','backankle_','backtoes3_')])
            pts=[w.bone(n) for n in ns];pts[-1].z=.115
            rs=[.205,.155,.113,.080,.087] if front else [.25,.17,.105,.09]
            # Broad fleshy upper leg, shaped knee, tapered cannon and fetlock.
            name='081_'+('Foreleg_' if front else 'Hindleg_')+side
            w.path(name,pts,rs,0,[{n:1} for n in ns],20,4);main.append(name)
        # Muscular scapula seated within ribcage, not a floating oval patch.
        p=w.bone('frontrump_'+side);name='081_Shoulder_'+side
        w.oval(name,(sign*.245,p.y+.13,1.28),(.20,.29,.36),0,'chest_m',20,12);main.append(name)
        name='081_Haunch_'+side
        w.oval(name,(sign*.19,.86,1.24),(.225,.30,.35),0,'backhip_'+side,20,12);main.append(name)
    obj=w.weld_hide(main,8300,voxel=.018);obj.name='081_Continuous_anatomy'
    bpy.context.view_layer.objects.active=obj
    smooth=obj.modifiers.new('Anatomical surface flow','SMOOTH');smooth.factor=.65;smooth.iterations=5
    bpy.ops.object.modifier_apply(modifier=smooth.name)
    # Native donor skin silhouette is the only retained geometric reference.
    return obj
def details(w):
    from mathutils.bvhtree import BVHTree
    skin=bpy.data.objects['081_Continuous_anatomy']
    bvh=BVHTree.FromPolygons([v.co for v in skin.data.vertices],[tuple(p.vertices) for p in skin.data.polygons])
    def skin_side(sign,y,z):
        hit,normal,index,distance=bvh.ray_cast(Vector((sign*2,y,z)),Vector((-sign,0,0)))
        assert hit is not None,('Missing face anchor',sign,y,z)
        return hit.x
    for side,sign in [('l',1),('r',-1)]:
        for front in (True,False):
            bone=('fronttoes_' if front else 'backtoes3_')+side;p=w.bone(bone)
            for split in (-1,1):
                w.loft('081_Cloven_hoof_'+side+str(front)+str(split),[((p.x+split*.043,p.y-.065,.016),.039,.101),((p.x+split*.043,p.y-.062,.05),.043,.112),((p.x+split*.04,p.y-.023,.15),.042,.075)],8,bone,12,subdiv=2)
        points=[(sign*x,y,z) for x,y,z in [(.18,-1.16,1.48),(.31,-1.12,1.50),(.46,-1.02,1.51),(.61,-.87,1.55),(.75,-.65,1.63),(.81,-.44,1.74),(.78,-.29,1.85),(.68,-.23,1.91)]]
        w.loft('081_Sweeping_horn_'+side,[(p,r,r*.65) for p,r in zip(points,[.106,.103,.088,.068,.049,.031,.014,.001])],1,'head_m',14,'path',2)
        # Actual ear bone anchors avoid the old detached low ears.
        p=w.bone('ear_'+side);end=w.bone('earend_'+side)
        w.loft('081_Leaf_ear_'+side,[(p,.045,.028),(p.lerp(end,.48)+Vector((0,.005,-.025)),.092,.034),(end+Vector((sign*.065,.015,-.035)),.056,.018),(end+Vector((sign*.10,.015,-.035)),.001,.001)],0,[{'ear_'+side:1},{'ear_'+side:.45,'ear1_'+side:.55},{'ear1_'+side:1},{'ear1_'+side:1}],12,'path',2)
        w.path('081_Inner_ear_'+side,[p+Vector((0,-.022,-.004)),p.lerp(end,.65)+Vector((0,-.027,-.015)),end+Vector((sign*.035,-.005,-.02))],[.012,.035,.005],12,'ear_'+side,8,2)
        # Small dark eyes, sculpted brow and subtle tear duct, no cartoon whites.
        x=skin_side(sign,-1.36,1.28)
        w.oval('081_Eye_'+side,(x+sign*.006,-1.36,1.28),(.015,.026,.019),3,'head_m',14,8)
        brow=[(skin_side(sign,y,z)+sign*.003,y,z) for y,z in [(-1.43,1.31),(-1.36,1.32),(-1.30,1.32)]]
        w.path('081_Brow_'+side,brow,[.010,.015,.007],0,'head_m',10,2)
        T.append({'interface':'eye inner surface to facial skin','side':sign,'skin_surface_x':x,'eye_inner_x':x-sign*.009,'intentional_overlap':.009})
        w.oval('081_Nostril_'+side,(sign*.125,-1.862,1.01),(.035,.009,.019),3,'head_m',14,6)
        w.path('081_Lip_'+side,[(sign*.01,-1.843,.916),(sign*.12,-1.833,.913),(sign*.20,-1.77,.926)],[.004,.006,.003],2,'jaw_m',8,2)
    # Darker muzzle surface follows the actual broad nose, seated into its skin.
    w.loft('081_Muzzle',[( (0,-1.76,.973),.222,.111),((0,-1.84,.972),.195,.094),((0,-1.865,.972),.15,.07)],2,'head_m',24,'y',2)
    ns=['tail'+str(i)+'_m' for i in range(5)];pts=[w.bone(n) for n in ns]
    w.path('081_Tail',pts,[.034,.029,.023,.018,.012],0,[{n:1} for n in ns],12,3)
    w.oval('081_Tail_tuft',pts[-1]+Vector((0,.035,-.035)),(.045,.07,.11),14,ns[-1],14,8)
    body=bpy.data.objects['081_Continuous_anatomy'];rng=random.Random(81)
    candidates=[v for v in body.data.vertices if v.co.z>1.1 and v.normal.z>.20 and -.65<v.co.y<1.05]
    for index,v in enumerate(rng.sample(candidates,min(95,len(candidates)))):
        n=v.normal.normalized();base=v.co-n*.001;t=n.cross(Vector((0,1,0))).normalized();tip=base+n*rng.uniform(.009,.020)+Vector((0,.009,0))
        ws={body.vertex_groups[g.group].name:g.weight for g in v.groups}
        w.mesh('081_Fur_'+str(index),[base+t*.004,base-t*.004,tip,base+n*.001],[(0,1,2),(0,3,1),(0,2,3),(1,3,2)],[(.2,.2)]*4,[ws]*4,14)
def shell(w,name,ymin,ymax,theta0,theta1,tile,offset=.012,ny=9,nt=22):
    vs=[];uv=[];ws=[];faces=[]
    for j in range(ny):
        y=ymin+(ymax-ymin)*j/(ny-1)
        for i in range(nt):
            theta=theta0+(theta1-theta0)*i/(nt-1);vs.append(surface(y,theta,offset));uv.append((i/(nt-1),j/(ny-1)));ws.append({'spine1_m':.8,'chest_m':.2})
    for j in range(ny-1):
        for i in range(nt-1):
            a=j*nt+i;faces.append((a,a+1,a+nt+1,a+nt))
    return w.mesh(name,vs,faces,uv,ws,tile)
def gear(w):
    before=len(w.parts)
    shell(w,'081_Padded_saddlecloth',-.29,.64,-1.88,1.88,5,.022)
    # Narrow woven border exactly follows the cloth's outer edges.
    for y in (-.29,.64):w.path('081_Cloth_border_'+str(y),[surface(y,-1.88+i*3.76/24,.027) for i in range(25)],[.010]*25,13,'spine1_m',6,1)
    for sign in (-1,1):w.path('081_Lower_cloth_border_'+str(sign),[surface(-.29+i*.93/12,sign*1.88,.027) for i in range(13)],[.01]*13,13,'spine1_m',6,1)
    for y in (-.16,.46):
        shell(w,'081_Pack_girth_'+str(y),y-.028,y+.028,-2.65,2.65,6,.038,ny=2,nt=28)
    # Two compact closed woven panniers; inward face seats against saddlecloth.
    for sign in (-1,1):
        x=sign*.495;y=.16;z=1.39
        rows=[((x,y,z-.18),.105,.20),((x,y,z-.12),.14,.235),((x,y,z+.12),.15,.25),((x,y,z+.18),.14,.235)]
        basket=w.loft('081_Woven_basket_'+str(sign),rows,4,'spine1_m',16,subdiv=2)
        for zz in (z-.14,z-.07,z,z+.07,z+.16):
            w.path('081_Basket_welt_'+str(sign)+str(zz),[(x+.149*math.cos(i*math.tau/16),y+.247*math.sin(i*math.tau/16),zz) for i in range(17)],[.009]*17,7,'spine1_m',6,1)
        for yy in (-.16,.48):
            # Ropes cross the basket and attach to the upper pack straps.
            w.path('081_Basket_lashing_'+str(sign)+str(yy),[(sign*.13,yy,torso(yy)[0]+torso(yy)[2]+.065),(sign*.39,yy,1.64),(sign*.61,yy,1.57),(sign*.62,yy,1.24),(sign*.46,yy,1.19)],[.012]*5,7,'spine1_m',7,2)
        T.append({'interface':'basket inner face to cloth','side':sign,'nominal_inner_x':abs(x)-.15,'cloth_x_at_midheight':.39,'intentional_overlap':.045})
    # One hoe: handle rests on two rope cradles on top of the pad.
    top=surface(.16,0,.065)[2]
    w.path('081_Wooden_hoe_handle',[(-.11,-.44,top+.015),(-.11,.83,top+.015)],[.025,.023],6,'spine1_m',10,5)
    # Broad, angled forged hoe blade joined through a wooden socket.
    w.mesh('081_Hoe_blade',[(-.13,.70,top+.015),(-.09,.70,top+.015),(.18,.70,top-.14),(.18,.89,top-.14),(-.13,.89,top+.015)],[(0,1,2,3,4)],[(0,0),(1,0),(1,1),(0,1),(0,.5)],[{'spine1_m':1}]*5,10)
    for y in (-.16,.46):
        w.path('081_Hoe_tie_'+str(y),[(-.18,y,top-.005),(-.145,y,top+.045),(-.08,y,top+.05),(-.05,y,top-.005)],[.011]*4,7,'spine1_m',7,2)
        T.append({'interface':'hoe handle to rope cradle','y':y,'handle_bottom':top-.010,'cradle_contact':top-.005,'intentional_overlap':.005})
    for o in w.parts[before:]:o['081_gear']=True
def join_copy(objects,name):
    bpy.ops.object.select_all(action='DESELECT');copies=[]
    for o in objects:
        c=o.copy();c.data=o.data.copy();bpy.context.scene.collection.objects.link(c);c.hide_set(False);c.select_set(True);copies.append(c)
    bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();bpy.context.object.name=name;return bpy.context.object
def save(path):
    path.parent.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0
    for im in list(bpy.data.images):
        if im.users==0 and not im.name.startswith('081_'):bpy.data.images.remove(im)
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
def export(w,rig,art,exp):
    contract=read(ROOT/'output/release_0710/buffalo/art/buffalo/r1/export.json')['donor_contract']
    for o in w.parts:
        assert all(math.isfinite(c) for v in o.data.vertices for c in v.co)
    unladen=join_copy([o for o in w.parts if not o.get('081_gear')],'081_Unladen_master');unladen.hide_set(True);unladen.hide_render=True
    body=join_copy(w.parts,'body_lod1');weights(body,contract,1)
    count=sum(len(p.vertices)-2 for p in body.data.polygons)
    if count>19500:
        bpy.context.view_layer.objects.active=body;d=body.modifiers.new('Game surface budget','DECIMATE');d.ratio=19450/count;bpy.ops.object.modifier_apply(modifier=d.name)
    lods=[body]
    for level,cap in ((2,9800),(3,4800)):
        obj=body.copy();obj.data=body.data.copy();obj.name='body_lod'+str(level);bpy.context.scene.collection.objects.link(obj);bpy.context.view_layer.objects.active=obj
        d=obj.modifiers.new('LOD budget','DECIMATE');d.ratio=min(1,cap/sum(len(p.vertices)-2 for p in obj.data.polygons));bpy.ops.object.modifier_apply(modifier=d.name);weights(obj,contract,level)
        mat=w.mat.copy();mat.name='lod'+str(level);obj.data.materials.clear();obj.data.materials.append(mat);lods.append(obj)
    for obj in lods:
        bpy.context.view_layer.objects.active=obj;t=obj.modifiers.new('Explicit triangles','TRIANGULATE');bpy.ops.object.modifier_apply(modifier=t.name)
    rig.animation_data_clear();rig.data.pose_position='REST'
    addon('unit_export').export_unit_model(rig,lods,exp/'model.fbx',addon('unit_export').skeleton_records(rig),three_lods=False)
    (exp/'model.rig').write_text(rig_text(contract),encoding='utf-8')
    for o in w.parts+lods[1:]:o.hide_set(True);o.hide_render=True
    body.hide_set(False);body.hide_render=False
    components=[{'name':o.name,'triangles':sum(len(p.vertices)-2 for p in o.data.polygons),'gear':bool(o.get('081_gear'))} for o in w.parts]
    save(art/'model.blend')
    counts=[len(o.data.polygons) for o in lods];assert all(n<=cap for n,cap in zip(counts,(20000,10000,5000)))
    write(OUT/'art/buffalo'/REV/'export.json',{'family':'buffalo','revision':REV,'source':str(art/'model.blend'),'source_sha256':sha(art/'model.blend'),'export':str(exp),'files':{p.name:sha(p) for p in exp.iterdir() if p.is_file()},'lod_triangles':counts,'donor_contract':contract,'components':components,'texture_size':2048,'native_acceptance':False,'contacts':T,'new_geometry':True})
    print('081_EXPORTED',counts)
def main():
    guard();phase=sys.argv[sys.argv.index('--')+1];art=ART/'buffalo'/REV;exp=EXPORT/'buffalo'/REV
    if phase=='anatomy':
        if (art/'anatomy.blend').exists():raise FileExistsError('Immutable checkpoint')
        rig=init();mat=atlas(exp);w=Workshop(rig,mat);anatomy(w);save(art/'anatomy.blend')
    else:
        bpy.ops.wm.open_mainfile(filepath=str(art/'anatomy.blend'));rig=bpy.data.objects['081_Native_cattle_45'];mat=bpy.data.materials['lod1'];w=Workshop(rig,mat);w.parts=[bpy.data.objects['081_Continuous_anatomy']]
        details(w);save(art/'detailed.blend');gear(w);export(w,rig,art,exp)
if __name__=='__main__':main()

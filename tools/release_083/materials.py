"""One 2048 atlas with dedicated charts, native owner mask and PBR inputs."""
import bpy,numpy as np,math
from mesh import charts
def atlas(folder,age,donor_images):
    size=2048;maps={k:np.ones((size,size,4),np.float32) for k in ['albedo','normal','roughness','metalness','pattern']}
    maps['normal'][:]=(.5,.5,1,1);maps['metalness'][:]=(0,0,0,1);maps['pattern'][:]=(0,0,0,1)
    rng=np.random.default_rng(830)
    palette={'tunic':(211,204,186),'sleeve_l':(211,204,186),'sleeve_r':(211,204,186),'headcloth':(210,203,185),
       'trousers_l':(61,70,73),'trousers_r':(61,70,73),'linen':(167,158,129),'leather':(81,57,39),'iron':(112,125,131),'brass':(156,124,61),'armour':(87,103,112),'wood':(135,100,57),'dark':(33,33,29),'skin':(209,168,132),'neck':(202,165,132)}
    for name,(x,y,w,h) in charts().items():
        x0,y0,nx,ny=round(x*size),round(y*size),round(w*size),round(h*size);v,u=np.mgrid[0:ny,0:nx];u=u/(nx-1);v=v/(ny-1)
        weave=.008*np.sin(u*nx*math.pi)*np.sin(v*ny*math.pi);noise=rng.normal(0,.002,(ny,nx))
        shade=np.ones((ny,nx));height=np.zeros((ny,nx))
        if name=='tunic':
            folds=np.sin(u*math.tau*9+.35*np.sin(v*math.tau))*.5+np.sin(u*math.tau*5-v*2)*.25
            height=folds*(.20+.8*np.sin(v*math.pi)**2);shade+=height*.09
            # Waist compression and two stitched hem lines; no directional light bake.
            shade-=.09*np.exp(-((v-.42)/.025)**2)
            shade-=.11*(np.exp(-((v-.045)/.003)**2)+np.exp(-((v-.065)/.002)**2))
        elif name.startswith('sleeve'):
            height=.4*np.sin(v*24+u*3)*(np.sin(v*math.pi)**2);shade+=height*.065
            shade-=.09*np.exp(-((v-.1)/.012)**2)
        elif name.startswith('trousers'):
            height=.4*np.sin(u*math.tau*7+v*2);shade+=height*.1
        elif name=='linen':
            height=.025*np.sin((v*6+u*.5)*math.tau);shade+=height*.08
        elif name=='leather':
            shade+=rng.normal(0,.018,(ny,nx));shade+=.10*(np.abs(u-.5)*2)**12
            if age>=3:
                seams=np.exp(-(np.sin((u*7+v*3)*math.pi)/.09)**2)+np.exp(-(np.sin((u*7-v*3)*math.pi)/.09)**2)
                shade-=seams*.055;height-=seams*.025
        elif name in ['iron','brass','armour']:
            height=.03*np.sin(u*nx*.12)+noise;shade+=.13*(np.abs(u-.5)*2)**8
            shade-=.08*(np.abs(v-.5)*2)**16
        elif name=='wood':
            height=np.sin(u*nx*.12+np.sin(v*5)*2)*.2;shade+=height*.15
        color=np.clip(np.array(palette[name])/255*shade[:,:,None]+weave[:,:,None]+noise[:,:,None],0,1)
        linear=np.where(color<=.04045,color/12.92,((color+.055)/1.055)**2.4)
        region=np.s_[y0:y0+ny,x0:x0+nx];maps['albedo'][region][:,:,:3]=linear
        dy,dx=np.gradient(height+weave*.15);normal=maps['normal'][region];normal[:,:,0]=np.clip(.5-dx*5,.2,.8);normal[:,:,1]=np.clip(.5-dy*5,.2,.8)
        rough=.84 if name.startswith(('tunic','sleeve','trousers')) or name in ['headcloth','linen'] else .7
        if name in ['iron','brass','armour']:rough=.43;maps['metalness'][region][:,:,:3]=.85 if name!='armour' else .65
        maps['roughness'][region][:,:,:3]=np.clip(rough+noise[:,:,None],0,1)
        if name in ['tunic','sleeve_l','sleeve_r','headcloth']:maps['pattern'][region][:,:,0]=1
    # Copy official head/hand painted features, bake a warm light skin tint.
    donor=donor_images['albedo'];raw=np.empty(len(donor.pixels),np.float32);donor.pixels.foreach_get(raw);raw=raw.reshape(donor.size[1],donor.size[0],4)
    yy=np.minimum((np.arange(1024)/1024*raw.shape[0]).astype(int),raw.shape[0]-1);xx=np.minimum((np.arange(1024)/1024*raw.shape[1]).astype(int),raw.shape[1]-1)
    skin=raw[yy[:,None],xx[None,:]].copy();lum=skin[:,:,:3].mean(2)
    # Native base faces are neutral; retain painted dark brows, eyes and creases.
    tint=np.array([.70,.455,.29]);skin[:,:,:3]=np.clip(lum[:,:,None]*2.1*tint,0,1)
    maps['albedo'][1024:2048,1024:2048]=skin;maps['roughness'][1024:2048,1024:2048,:3]=.69
    images={}
    for name,a in maps.items():
        im=bpy.data.images.new('083_'+name,width=size,height=size,alpha=True)
        if name!='albedo':im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save();im.pack();images[name]=im
    mat=bpy.data.materials.new('lod1');mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    tex={}
    for name in maps:
        node=nodes.new('ShaderNodeTexImage');node.name='083 '+name;node.image=images[name];tex[name]=node
    owner=nodes.new('ShaderNodeRGB');owner.name='OWNER PREVIEW';owner.outputs[0].default_value=(.025,.18,.65,1)
    mult=nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;links.new(tex['albedo'].outputs['Color'],mult.inputs[1]);links.new(owner.outputs[0],mult.inputs[2])
    separate=nodes.new('ShaderNodeSeparateColor');separate.mode='RGB';links.new(tex['pattern'].outputs['Color'],separate.inputs[0])
    mix=nodes.new('ShaderNodeMixRGB');links.new(separate.outputs['Red'],mix.inputs[0]);links.new(tex['albedo'].outputs['Color'],mix.inputs[1]);links.new(mult.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
    links.new(tex['roughness'].outputs['Color'],bs.inputs['Roughness']);links.new(tex['metalness'].outputs['Color'],bs.inputs['Metallic'])
    nm=nodes.new('ShaderNodeNormalMap');links.new(tex['normal'].outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    nodes.active=tex['albedo'];return mat,images

"""Reusable procedural surface construction, skinning and authored atlas helpers."""
import math
import bpy,bmesh
from mathutils import Vector
import numpy as np
TAU=math.tau

def uv_tile(tile,u,v):return ((tile%4+.025+.95*u)/4,(tile//4+.025+.95*v)/4)

class Workshop:
    def __init__(self,rig,material):self.rig=rig;self.mat=material;self.parts=[]
    def bone(self,n):return self.rig.data.bones[n].head_local.copy()
    def mesh(self,name,vertices,faces,uvs,weights,tile):
        data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);data.materials.append(self.mat)
        uv=data.uv_layers.new(name='UVMap')
        for p in data.polygons:
            p.use_smooth=True
            for li in p.loop_indices:uv.data[li].uv=uv_tile(tile,*uvs[data.loops[li].vertex_index])
        if self.rig:
            for i,ws in enumerate(weights):
                total=sum(ws.values())
                assert total>0,(name,i)
                for n,w in ws.items():
                    assert n in self.rig.data.bones,n
                    (obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([i],w/total,'REPLACE')
            mod=obj.modifiers.new('Native skin','ARMATURE');mod.object=self.rig;obj.parent=self.rig
        obj['079_component']=name;obj['079_tile']=tile;self.parts.append(obj);return obj
    def loft(self,name,rows,tile,bones,sides=24,axis='z',subdiv=1,ripple=0,caps=True):
        # Rows: (center, first radius, second radius). Interpolate rings and weights.
        if isinstance(bones,str):bones=[{bones:1} for _ in rows]
        if bones is None:bones=[{} for _ in rows]
        rr=[];ww=[]
        for k in range(len(rows)-1):
            for j in range(subdiv):
                t=j/subdiv;a,b=rows[k],rows[k+1]
                rr.append((Vector(a[0]).lerp(Vector(b[0]),t),a[1]*(1-t)+b[1]*t,a[2]*(1-t)+b[2]*t))
                ww.append({n:bones[k].get(n,0)*(1-t)+bones[k+1].get(n,0)*t for n in bones[k].keys()|bones[k+1].keys()})
        rr.append((Vector(rows[-1][0]),*rows[-1][1:]));ww.append(bones[-1])
        vs=[];us=[];weights=[];faces=[]
        for k,(c,ra,rb) in enumerate(rr):
            if axis=='z':a,b=Vector((1,0,0)),Vector((0,1,0))
            elif axis=='y':a,b=Vector((1,0,0)),Vector((0,0,1))
            else:
                tangent=rr[min(k+1,len(rr)-1)][0]-rr[max(k-1,0)][0]
                tangent.normalize();ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0))
                a=tangent.cross(ref).normalized();b=tangent.cross(a).normalized()
            for i in range(sides):
                q=TAU*i/sides;wr=1+ripple*math.sin(q*7+k*.72)*math.sin(math.pi*k/(len(rr)-1))
                vs.append(c+a*(ra*math.cos(q)*wr)+b*(rb*math.sin(q)*wr));us.append((i/sides,k/(len(rr)-1)));weights.append(ww[k])
        for k in range(len(rr)-1):
            for i in range(sides):j=(i+1)%sides;faces.append((k*sides+i,k*sides+j,(k+1)*sides+j,(k+1)*sides+i))
        if caps:faces.extend([tuple(reversed(range(sides))),tuple((len(rr)-1)*sides+i for i in range(sides))])
        return self.mesh(name,vs,faces,us,weights,tile)
    def path(self,name,points,radii,tile,bones,sides=16,subdiv=2):
        return self.loft(name,[(p,r,r*.9) for p,r in zip(points,radii)],tile,bones,sides,'path',subdiv)
    def oval(self,name,center,scale,tile,bone,sides=24,rings=12):
        rows=[]
        for i in range(rings+1):
            angle=math.pi*(.008+.984*i/rings)
            rows.append(((center[0],center[1],center[2]-scale[2]*math.cos(angle)),max(.0005,scale[0]*math.sin(angle)),max(.0005,scale[1]*math.sin(angle))))
        return self.loft(name,rows,tile,bone,sides)
    def weld_hide(self,names,target=10000):
        from mathutils.kdtree import KDTree
        objects=[o for o in self.parts if o.name in names];samples=[]
        for o in objects:
            for v in o.data.vertices:samples.append((v.co.copy(),{o.vertex_groups[g.group].name:g.weight for g in v.groups}))
        tree=KDTree(len(samples))
        for i,(v,w) in enumerate(samples):tree.insert(v,i)
        tree.balance();bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True);self.parts.remove(o)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();obj=bpy.context.object;obj.name='079_Continuous_anatomy'
        obj.modifiers.clear();obj.data.remesh_voxel_size=.024;bpy.ops.object.voxel_remesh()
        sm=obj.modifiers.new('Joint surface relaxation','SMOOTH');sm.factor=.65;sm.iterations=3;bpy.ops.object.modifier_apply(modifier=sm.name)
        tris=sum(len(p.vertices)-2 for p in obj.data.polygons)
        dec=obj.modifiers.new('Anatomical game surface','DECIMATE');dec.ratio=min(1,target/tris);bpy.ops.object.modifier_apply(modifier=dec.name)
        obj.vertex_groups.clear()
        for v in obj.data.vertices:
            ws={}
            for co,i,dist in tree.find_n(v.co,6):
                for n,w in samples[i][1].items():ws[n]=ws.get(n,0)+w/(dist+.008)**3
            ws=dict(sorted(ws.items(),key=lambda p:p[1],reverse=True)[:4]);total=sum(ws.values())
            for n,w in ws.items():(obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([v.index],w/total,'REPLACE')
        uv=obj.data.uv_layers.active or obj.data.uv_layers.new(name='UVMap')
        for p in obj.data.polygons:
            p.use_smooth=True
            for li in p.loop_indices:
                v=obj.data.vertices[obj.data.loops[li].vertex_index].co;uv.data[li].uv=uv_tile(0,max(0,min(1,(v.y+1.9)/3.3)),max(0,min(1,v.z/1.9)))
        mod=obj.modifiers.new('Native skin','ARMATURE');mod.object=self.rig;obj.parent=self.rig
        self.parts.append(obj);return obj

def make_atlas(folder):
    colors=[(80,84,86),(133,126,108),(46,40,35),(16,13,11),(182,165,124),(48,66,74),(210,164,126),(29,24,20),(113,75,44),(146,46,36),(112,125,129),(168,130,67),(128,91,48),(150,88,75),(219,211,186),(192,167,111)]
    size=2048;tile=512;yy,xx=np.mgrid[0:tile,0:tile];rng=np.random.default_rng(790)
    albedo=np.zeros((size,size,4),np.float32);normal=np.empty_like(albedo);normal[:]=(.5,.5,1,1)
    rough=np.zeros_like(albedo);metal=np.zeros_like(albedo);pattern=np.zeros_like(albedo)
    for t,c in enumerate(colors):
        noise=rng.normal(0,1,(tile,tile));detail=noise*.006
        if t==0:detail+=.012*np.sin(xx*.045+np.sin(yy*.02)*3)*np.sin(yy*.075)+.003*np.sin(xx*.8)
        elif t==1:detail+=.02*np.sin(yy*.22)+.004*np.sin(xx*.025)
        elif t in (4,5,9,15):detail+=.009*np.cos(xx*math.pi/2)+.009*np.cos(yy*math.pi/2)
        elif t==8:detail+=.006*np.sin(xx*.5)*np.sin(yy*.4)
        elif t==12:detail+=.014*np.sin(xx*.08+np.sin(yy*.017)*2)
        elif t==6:detail*=.25
        srgb=np.clip(np.array(c)[None,None,:]/255+detail[:,:,None],0,1)
        linear=np.where(srgb<=.04045,srgb/12.92,((srgb+.055)/1.055)**2.4)
        y=t//4*tile;x=t%4*tile;region=np.s_[y:y+tile,x:x+tile]
        albedo[region][:,:,:3]=linear;albedo[region][:,:,3]=1
        rough[region][:,:,:3]=.74 if t not in (3,10,11,14) else .32
        metal[region][:,:,:3]=.82 if t in (10,11) else 0
        pattern[region][:,:,0]=1 if t==9 else 0
        dy,dx=np.gradient(detail);normal[region][:,:,0]=np.clip(.5-dx*.8,0,1);normal[region][:,:,1]=np.clip(.5-dy*.8,0,1)
    for a in (rough,metal,pattern):a[:,:,3]=1
    images={}
    for name,a in [('albedo',albedo),('normal',normal),('roughness',rough),('metalness',metal),('pattern',pattern)]:
        im=bpy.data.images.new('079_'+name,width=size,height=size,alpha=True)
        if name!='albedo':im.colorspace_settings.name='Non-Color'
        im.pixels.foreach_set(a.ravel());im.filepath_raw=str(folder/(name+'.png'));im.file_format='PNG';im.save();images[name]=im
    mat=bpy.data.materials.new('lod1');mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
    for name,slot in [('albedo','Base Color'),('roughness','Roughness'),('metalness','Metallic')]:
        tex=nodes.new('ShaderNodeTexImage');tex.image=images[name];links.new(tex.outputs['Color'],bs.inputs[slot])
    tex=nodes.new('ShaderNodeTexImage');tex.image=images['normal'];nm=nodes.new('ShaderNodeNormalMap');links.new(tex.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],bs.inputs['Normal'])
    return mat

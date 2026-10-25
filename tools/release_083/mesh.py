"""Deterministic, UV-charted skinned surface construction."""
import bpy,bmesh,math
from mathutils import Vector
class Builder:
    def __init__(self,rig,material):self.rig=rig;self.material=material;self.parts=[];self.contacts=[]
    def bone(self,n):return self.rig.data.bones[n].head_local.copy()
    def mesh(self,name,vertices,faces,uvs,weights,chart,tag):
        data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update()
        bm=bmesh.new();bm.from_mesh(data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free()
        obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj);obj.data.materials.append(self.material)
        uv=obj.data.uv_layers.new(name='UVMap');x,y,w,h=chart
        for p in data.polygons:
            p.use_smooth=tag not in ['plate','blade','sole']
            for li in p.loop_indices:
                u,v=uvs[data.loops[li].vertex_index];uv.data[li].uv=(x+w*u,y+h*v) if tag=='skin' else (x+w*(.015+.97*u),y+h*(.015+.97*v))
        if self.rig:
            for i,ws in enumerate(weights):
                total=sum(ws.values());assert total>0,(name,i)
                for n,weight in ws.items():
                    if weight>1e-8:(obj.vertex_groups.get(n) or obj.vertex_groups.new(name=n)).add([i],weight/total,'REPLACE')
            obj.parent=self.rig;mod=obj.modifiers.new('Native skin','ARMATURE');mod.object=self.rig
        obj['083_component']=name;obj['083_surface']=tag;self.parts.append(obj);return obj
    def loft(self,name,rows,weights,chart,tag='cloth',sides=24,fold=0,axis='z',caps=True):
        if isinstance(weights,str):weights=[{weights:1} for _ in rows]
        if weights is None:weights=[{} for _ in rows]
        vertices=[];uvs=[];groups=[];faces=[]
        for k,(center,rx,ry) in enumerate(rows):
            c=Vector(center)
            if axis=='z':a,b=Vector((1,0,0)),Vector((0,1,0))
            else:
                tangent=(Vector(rows[min(k+1,len(rows)-1)][0])-Vector(rows[max(0,k-1)][0])).normalized()
                ref=Vector((0,1,0)) if abs(tangent.y)<.9 else Vector((1,0,0));a=tangent.cross(ref).normalized();b=tangent.cross(a).normalized()
            for i in range(sides+1):
                t=i/sides;q=t*math.tau;profile=1+fold*(math.sin(q*9+k*.26)*.6+math.sin(q*5-k*.37)*.4)
                vertices.append(c+a*(rx*math.cos(q)*profile)+b*(ry*math.sin(q)*profile));uvs.append((t,k/(len(rows)-1)));groups.append(weights[k])
        for k in range(len(rows)-1):
            for i in range(sides):
                a=k*(sides+1)+i;b=a+sides+1;faces.append((a,a+1,b+1,b))
        if caps:faces.extend([tuple(reversed(range(sides))),tuple((len(rows)-1)*(sides+1)+i for i in range(sides))])
        return self.mesh(name,vertices,faces,uvs,groups,chart,tag)
    def ribbon(self,name,centers,widths,bone,chart,tag='trim',normal=(0,-1,0)):
        vs=[];uvs=[];faces=[];n=Vector(normal)
        for i,(point,width) in enumerate(zip(centers,widths)):
            tangent=Vector(centers[min(i+1,len(centers)-1)])-Vector(centers[max(0,i-1)]);across=tangent.cross(n).normalized()
            for j in [-1,1]:vs.append(Vector(point)+across*width*.5*j);uvs.append(((j+1)/2,i/(len(centers)-1)))
        for i in range(len(centers)-1):faces.extend([(i*2,i*2+1,i*2+3,i*2+2),(i*2+2,i*2+3,i*2+1,i*2)])
        return self.mesh(name,vs,faces,uvs,[{bone:1} for _ in vs] if bone else [{} for _ in vs],chart,tag)

def charts():
    return {'tunic':(0,0,.5,.5),'sleeve_l':(.5,0,.25,.25),'sleeve_r':(.75,0,.25,.25),
    'trousers_l':(0,.5,.25,.125),'trousers_r':(.25,.5,.25,.125),'neck':(0,.625,.5,.125),'skin':(.5,.5,.5,.5),
    'linen':(0,.75,.25,.25),'leather':(.25,.75,.25,.25),'iron':(.5,.25,.125,.125),
    'brass':(.625,.25,.125,.125),'headcloth':(.75,.25,.25,.125),'armour':(.5,.375,.25,.125),'wood':(.75,.375,.125,.125),'dark':(.875,.375,.125,.125)}

"""Read-only UV tile audit for 0.3.0 landmark blends."""
import bpy
import json
import sys
from collections import Counter

name=sys.argv[sys.argv.index('--')+1]
threshold=4.2 if name=='one_pillar' else 2.0
rows=[]
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    uv=obj.data.uv_layers.active.data
    for poly in obj.data.polygons:
        center=sum(obj.data.vertices[obj.data.loops[i].vertex_index].co.z for i in poly.loop_indices)/len(poly.loop_indices)
        if center<threshold:continue
        xy=[tuple(uv[i].uv) for i in poly.loop_indices]
        rows.append((center,min(u for u,v in xy),max(u for u,v in xy),min(v for u,v in xy),max(v for u,v in xy)))
print('UV_PROBE',name,'sampled',len(rows),'u_quartiles',dict(Counter(int(((a+b)/2)*4) for _,a,b,_,_ in rows)),
      'v_halves',dict(Counter(int(((a+b)/2)*2) for _,_,_,a,b in rows)))
print('UV_EXTREMES',json.dumps(sorted(rows,key=lambda a:a[1])[:5]+sorted(rows,key=lambda a:a[2])[-5:]))
for mat in bpy.data.materials:
    if not mat.name.startswith('CCP030'):continue
    print('MAT',mat.name,'nodes',[(n.name,n.type,getattr(getattr(n,'image',None),'name',None)) for n in mat.node_tree.nodes],
          'links',[(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in mat.node_tree.links])
for image in bpy.data.images:
    if 'albedo' not in image.name:continue
    samples=[]
    for u,v in ((.62,.2),(.55,.2),(.70,.3),(.1,.8)):
        ix=int(u*image.size[0]);iy=int(v*image.size[1]);k=4*(iy*image.size[0]+ix)
        samples.append((u,v,tuple(image.pixels[k:k+4])))
    print('IMAGE_SAMPLES',image.name,samples)
for obj in bpy.data.objects:
    if obj.type=='MESH':print('MATERIAL_INDICES',obj.name,dict(Counter(p.material_index for p in obj.data.polygons)),
                              'UV_LAYERS',[(u.name,u.active_render) for u in obj.data.uv_layers])
for obj in bpy.data.objects:
    if obj.type!='MESH':continue
    uv=obj.data.uv_layers.active.data
    for lo,hi in ((.15,.17),(4.34,5.42)):
        selected=[]
        for poly in obj.data.polygons:
            z=sum(obj.data.vertices[obj.data.loops[i].vertex_index].co.z for i in poly.loop_indices)/len(poly.loop_indices)
            if not lo<=z<=hi or poly.normal.z<.3:continue
            selected.append((z,poly.center.x,poly.center.y,tuple(uv[poly.loop_start].uv)))
        if selected:print('UV_BAND',obj.name,lo,hi,'n',len(selected),'tiles',dict(Counter((int(u*4),int(v*2)) for _,_,_,(u,v) in selected)),
                          'first',selected[:5])

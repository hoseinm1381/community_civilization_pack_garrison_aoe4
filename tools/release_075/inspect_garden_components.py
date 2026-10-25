import bpy,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/buildings_070/architecture-final-r4.blend'))
c=bpy.data.collections['CCP070_Imperial_Garden_Detailed_r4']
o=next(o for o in c.objects if o.name.endswith('0005'))
m=o.data
parent=list(range(len(m.vertices)))
def root(i):
 while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
 return i
for e in m.edges:
 a,b=map(root,e.vertices);parent[a]=b
parts={}
for v in m.vertices:parts.setdefault(root(v.index),[]).append(v.index)
rows=[]
for ids in parts.values():
 pts=[m.vertices[i].co for i in ids];s=set(ids);faces=[p for p in m.polygons if p.vertices[0] in s]
 uv=[m.uv_layers.active.data[i].uv for p in faces for i in p.loop_indices]
 rows.append(dict(vertices=len(ids),polygons=len(faces),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],uv_center=[sum(v[i] for v in uv)/len(uv) for i in range(2)]))
out=ROOT/'output/release_075/inspection/garden-components.json';out.write_text(json.dumps(rows,indent=2))
print('COMPONENTS',len(rows))
for r in rows:
 if r['bounds'][1][2]>.7: print(r)

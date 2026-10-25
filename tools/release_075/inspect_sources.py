"""Background Blender inspection; never saves or changes historical files."""
import bpy, json, math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_075/inspection'
OUT.mkdir(parents=True,exist_ok=True)
ITEMS={
 'garden':('art/authoring/buildings_070/architecture-final-r4.blend','CCP070_Imperial_Garden_Detailed_r4'),
 'foundry':('art/authoring/buildings_070/architecture-final-r4.blend','CCP070_Trung_Foundries_Detailed_r3'),
 'citadel':('art/authoring/castle_next/landmarks/imperial_citadel/imperial_citadel.blend',None),
 'hq':('art/authoring/castle_next/landmarks/resistance_hq/resistance_hq.blend',None),
 'ministry':('art/authoring/buildings_021/ministry/ministry.blend',None),
 'pho_minh':('art/authoring/landmarks_040/pho_minh/pho_minh.blend',None),
 'one_pillar':('art/authoring/landmarks_040/one_pillar/one_pillar.blend',None)}
for key,(rel,col) in ITEMS.items():
 bpy.ops.wm.open_mainfile(filepath=str(ROOT/rel))
 objects=bpy.data.collections[col].all_objects if col else bpy.context.scene.objects
 rows=[]
 for o in objects:
  if o.type!='MESH':continue
  o.data.calc_loop_triangles()
  pts=[o.matrix_world@Vector(p) for p in o.bound_box]
  rows.append(dict(name=o.name,vertices=len(o.data.vertices),triangles=len(o.data.loop_triangles),
   hidden_render=o.hide_render,hidden_view=o.hide_viewport,
   location=list(o.location),scale=list(o.scale),
   bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],
   materials=[m.name if m else None for m in o.data.materials],
   modifiers=[m.type for m in o.modifiers],uv_layers=[u.name for u in o.data.uv_layers]))
 images=[dict(name=i.name,path=bpy.path.abspath(i.filepath),packed=bool(i.packed_file)) for i in bpy.data.images if i.source=='FILE']
 (OUT/(key+'.json')).write_text(json.dumps(dict(source=rel,collection=col,objects=rows,images=images),indent=2))
 print('INSPECT',key,len(rows),sum(r['triangles'] for r in rows),flush=True)

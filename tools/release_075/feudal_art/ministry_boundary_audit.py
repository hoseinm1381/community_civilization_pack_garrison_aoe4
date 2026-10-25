"""Read-only inherited open-surface exception; no welding or repair."""
import bpy,bmesh,json,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def digest(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],[tuple(u.uv) for u in o.data.uv_layers.active.data])).encode()).hexdigest()
def stats(o):
 bm=bmesh.new();bm.from_mesh(o.data)
 r={'name':o.name,'vertices':len(bm.verts),'non_manifold_edges':sum(not e.is_manifold for e in bm.edges),'boundary_edges':sum(e.is_boundary for e in bm.edges),'degenerate_faces':sum(f.calc_area()<1e-9 for f in bm.faces),'geometry_uv_digest':digest(o)}
 bm.free();return r
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/buildings_021/ministry/ministry.blend'))
old={o.name:stats(o) for o in bpy.context.scene.objects if o.type=='MESH'}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_075/ministry/r3/ministry.blend'))
current={o.name:stats(o) for o in bpy.context.scene.objects if o.type=='MESH'}
preserved={k:old[k]==current[k] for k in old};assert all(preserved.values())
new=[v for k,v in current.items() if k not in old]
assert all(v['non_manifold_edges']==0 and v['degenerate_faces']==0 for v in new)
receipt=json.loads((ROOT/'output/release_075/art/ministry/r3/receipt.json').read_text())
assert sum(r['non_manifold_edges'] for r in receipt['geometry'])==sum(r['non_manifold_edges'] for r in old.values())
result={'scope':'Ministry r3 only','accepted_warning':'open_surface','original_objects':old,'original_objects_exact':preserved,'new_component_count':len(new),'new_non_manifold_edges':sum(x['non_manifold_edges'] for x in new),'new_degenerate_faces':sum(x['degenerate_faces'] for x in new),'old_boundary_edges':sum(x['boundary_edges'] for x in old.values()),'old_non_manifold_edges':sum(x['non_manifold_edges'] for x in old.values()),'export_non_manifold_edges':sum(x['non_manifold_edges'] for x in receipt['geometry']),'all_new_closed':True,'reason':'Preserved approved static stock elephant vertex splits; new architectural components are watertight. No blanket warning suppression.'}
(ROOT/'output/release_075/art/ministry/r3/preflight-exception.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))

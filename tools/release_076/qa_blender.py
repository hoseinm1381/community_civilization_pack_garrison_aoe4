"""Independent saved-source checks. Does not modify the source blend."""
import sys,math
from pathlib import Path
import bpy,bmesh
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
def main(selection):
 reports={}
 for family,revision in selection.items():
  p=ART/family/revision/'model.blend';before=sha(p);bpy.ops.wm.open_mainfile(filepath=str(p))
  meshes=[bpy.data.objects.get('body_lod'+str(i)) for i in (1,2,3)];assert all(meshes)
  report={'source_sha256':before,'lods':[]}
  for obj in meshes:
   bm=bmesh.new();bm.from_mesh(obj.data)
   assert all(v.co.length<20 and all(math.isfinite(x) for x in v.co) for v in bm.verts)
   assert not any(f.calc_area()<1e-10 for f in bm.faces)
   boundary=sum(not e.is_manifold for e in bm.edges);bm.free()
   assert boundary==0,(family,obj.name,'nonmanifold',boundary)
   assert obj.data.uv_layers.active and len(obj.data.materials)==1
   rig=next((m.object for m in obj.modifiers if m.type=='ARMATURE'),None)
   max_error=0;max_influences=0
   if rig:
    for v in obj.data.vertices:
     assert v.groups,(family,'unweighted',v.index)
     max_error=max(max_error,abs(sum(g.weight for g in v.groups)-1));max_influences=max(max_influences,len(v.groups))
     assert all(obj.vertex_groups[g.group].name in rig.data.bones for g in v.groups)
    assert max_error<1e-5 and max_influences<=4,(family,max_error,max_influences)
   report['lods'].append({'mesh':obj.name,'triangles':sum(len(p.vertices)-2 for p in obj.data.polygons),'nonmanifold_edges':boundary,'max_weight_sum_error':max_error,'max_influences':max_influences})
  if family=='buffalo':
   rig=next(m.object for m in meshes[0].modifiers if m.type=='ARMATURE');poses=[]
   for frame in (1,31,61,91,121):
    bpy.context.scene.frame_set(frame);poses.append({b.name:[list(r) for r in b.matrix_basis] for b in rig.pose.bones})
   assert poses[0]==poses[-1] or max(abs(poses[0][n][i][j]-poses[-1][n][i][j]) for n in poses[0] for i in range(4) for j in range(4))<1e-6
   assert all(p['root_m']==poses[0]['root_m'] for p in poses)
   report['animation']={'loop_endpoints_match':True,'root_stationary':True,'native_playback':False}
  assert sha(p)==before
  reports[family]=report
 write(OUT/'source-qa.json',{'status':'passed','families':reports,'native_motion_review':'unverified','native_acceptance':False})
 print('SOURCE_QA_PASSED',len(reports))
if __name__=='__main__':main(read(sys.argv[sys.argv.index('--')+1]))

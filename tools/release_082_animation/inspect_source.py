import bpy,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,CFG)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'art/authoring/release_081/buffalo/r6/model.blend'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
report={'rig':rig.name,'keys':list(rig.keys()),'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'length':b.length,'matrix':[list(r) for r in b.matrix_local],'parent':b.parent.name if b.parent else None} for b in rig.data.bones}}
(ROOT/'output/release_082_animation/source-inspection.json').write_text(json.dumps(report,indent=2))
print('SOURCE_INSPECTED')

"""Preview native Hideout plus visual-only shelter at the intended shared origin.

No blend is saved and no native binding is modified. This is a fit check only.
"""
import bpy
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from model_ministry_farm_hideout_runner import render_views,write

ROOT=Path(__file__).resolve().parents[2]
variant=sys.argv[sys.argv.index("--")+1]
assert variant in ("default","stone")
native=ROOT/"art/authoring/buildings_020/hideout"/variant/("Vietnam_Hideout_"+variant+".blend")
added=ROOT/"art/authoring/buildings_020/hideout"/("shelter_"+variant)/("shelter_"+variant+".blend")
target=ROOT/"output/release_020/ministry_farm_hideout/hideout/composite"/variant
assert native.is_file() and added.is_file()
bpy.ops.wm.open_mainfile(filepath=str(native))
before={o.name for o in bpy.context.scene.objects}
with bpy.data.libraries.load(str(added),link=False) as (data_from,data_to):
    data_to.objects=[name for name in data_from.objects if name.startswith("Shelter_")]
assert data_to.objects
for obj in data_to.objects:
    bpy.context.scene.collection.objects.link(obj)
for obj in bpy.context.scene.objects:
    if obj.type!="MESH":continue
    if obj.name in before:obj.color=(.75,.73,.68,1)
    else:obj.color=(.40,.25,.14,1)
render_views([o for o in bpy.context.scene.objects if o.type=="MESH"],target)
write(target/"context.json",{"schema":"ccp.020-hideout-composite-preview/v1",
    "variant":variant,"native_blend":str(native),"supplement_blend":str(added),
    "shared_origin":True,"native_binding":"not modified","composite_is_native_proof":False})
print("CCP_020_COMPOSITE_READY",variant,flush=True)

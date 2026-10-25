"""Close girth loops and give cloth/hoe native-safe thickness before final export."""
import bpy,sys,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from common import *
import author
guard();old=read(OUT/'art/buffalo/r4/export.json');art=ART/'buffalo/r5';exp=EXPORT/'buffalo/r5'
assert not (art/'model.blend').exists();art.mkdir(parents=True,exist_ok=True);exp.mkdir(parents=True,exist_ok=True)
for name in ('albedo','normal','roughness','metalness','pattern'):shutil.copyfile(EXPORT/f'buffalo/r4/{name}.png',exp/(name+'.png'))
bpy.ops.wm.open_mainfile(filepath=old['source']);rig=bpy.data.objects['081_Native_cattle_45'];mat=bpy.data.materials['lod1']
names=[r['name'] for r in old['components']];w=author.Workshop(rig,mat);w.parts=[bpy.data.objects[n] for n in names]
for o in list(bpy.data.objects):
    if o.name in ('body_lod1','body_lod2','body_lod3','081_Unladen_master'):bpy.data.objects.remove(o,do_unlink=True)
for material in list(bpy.data.materials):
    if material.users==0:bpy.data.materials.remove(material)
for o in w.parts:
    if o.name.startswith('081_Pack_girth_'):
        for v in o.data.vertices:
            i=v.index%28;v.co=author.surface(v.co.y,-math.pi+math.tau*i/27,.038)
        for j in range(2):assert (o.data.vertices[j*28].co-o.data.vertices[j*28+27].co).length<1e-6
    if o.name=='081_Hoe_blade' or o.name=='081_Padded_saddlecloth' or o.name.startswith('081_Pack_girth_'):
        bpy.context.view_layer.objects.active=o;o.hide_set(False)
        mod=o.modifiers.new('Physical thickness','SOLIDIFY');mod.thickness=.010 if o.name=='081_Hoe_blade' else .006;mod.offset=0
        bpy.ops.object.modifier_apply(modifier=mod.name)
for name in ('albedo','normal','roughness','metalness','pattern'):
    im=bpy.data.images['081_'+name];im.filepath_raw=str(exp/(name+'.png'));im.pack();im.use_fake_user=True
author.REV='r5';author.T=old['contacts']+[{'interface':'girth underside seam','maximum_gap':1e-6,'verified':True},{'interface':'hoe blade solid thickness','thickness':.010,'verified':True}]
author.export(w,rig,art,exp)

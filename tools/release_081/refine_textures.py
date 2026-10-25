"""Keep approved r3 shape; darken lower-leg fur via the skin tile's height UV."""
import bpy,sys,shutil,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from common import *
guard();old=read(OUT/'art/buffalo/r3/export.json');art=ART/'buffalo/r4';exp=EXPORT/'buffalo/r4'
assert not (art/'model.blend').exists() and not (OUT/'art/buffalo/r4/export.json').exists()
art.mkdir(parents=True,exist_ok=True);shutil.copytree(EXPORT/'buffalo/r3',exp,dirs_exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=old['source'])
im=bpy.data.images['081_albedo'];w,h=im.size;pixels=np.array(im.pixels[:],dtype=np.float32).reshape(h,w,4)
height=np.linspace(0,1,512)[:,None];t=np.clip((height-.10)/.30,0,1);brightness=.45+.55*t*t*(3-2*t)
pixels[:512,:512,:3]*=brightness[:,:,None]
im.pixels.foreach_set(pixels.ravel());im.filepath_raw=str(exp/'albedo.png');im.file_format='PNG';im.save();im.pack()
for name in ('normal','roughness','metalness','pattern'):
    image=bpy.data.images.get('081_'+name)
    if image is None:
        image=bpy.data.images.load(str(exp/(name+'.png')),check_existing=False);image.name='081_'+name;image.colorspace_settings.name='Non-Color'
    image.filepath_raw=str(exp/(name+'.png'));image.pack();image.use_fake_user=True
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(art/'model.blend'))
old.update(revision='r4',source=str(art/'model.blend'),source_sha256=sha(art/'model.blend'),export=str(exp),files={p.name:sha(p) for p in exp.iterdir()},refinement='Lower-leg fur gradient in existing skin tile UV height; identical r3 geometry/skeleton/gear.')
write(OUT/'art/buffalo/r4/export.json',old);print('081_FUR_REFINED')

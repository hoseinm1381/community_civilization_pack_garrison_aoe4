"""Read image/library dependencies without loading geometry or saving scenes."""
from pathlib import Path
import sys,json,argparse,os
import bpy
p=argparse.ArgumentParser();p.add_argument('--config',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);cfg=json.loads(a.config.read_text());missing=[];external=0;packed=0
def resolve(value,blend):
 raw=str(blend.parent/value[2:]) if value.startswith('//') else value;raw=os.path.normpath(raw).replace('\\','/').removeprefix('//?/')
 for old in sorted((s.replace('\\','/') for s in (cfg['candidate_root'],cfg['permanent_root'],cfg['source_root'])),key=len,reverse=True):
  if raw.lower().startswith(old.lower().rstrip('/')+'/'):
   key='source/'+raw[len(old.rstrip('/'))+1:]
   return key,key in cfg['virtual_files']
 return raw,False
for i,name in enumerate(cfg['blends'],1):
 path=Path(name)
 with bpy.data.libraries.load(name,link=False) as (data,target):target.images=data.images
 for im in target.images:
  if im is None:continue
  if im.packed_file or im.source in ('GENERATED','VIEWER') or not im.filepath:packed+=1
  else:
   external+=1;key,available=resolve(im.filepath,path)
   if not available:missing.append({'blend':name,'image':im.name,'original':im.filepath,'resolved':key})
  bpy.data.images.remove(im)
 if i%25==0:print('CURRENT_BLENDS_CHECKED',i,'missing',len(missing),flush=True)
report={'status':'passed' if not missing else 'failed','Blender_masters':len(cfg['blends']),'packed_or_generated_images':packed,'external_images_checked_against_promoted_store':external,'missing':missing,'geometry_loaded_or_scenes_saved':False}
(a.config.parent/'blend-verification.json').write_text(json.dumps(report,indent=2)+'\n')
if missing:raise RuntimeError('Unresolved current image dependencies; inspect blend-verification.json')
print('CURRENT_BLEND_CLOSURE_PASS',len(cfg['blends']),flush=True)

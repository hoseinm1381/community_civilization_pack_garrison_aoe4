"""Prepare private Garrison surface variants; no native cook or gameplay edits."""
import hashlib, io, json, math, os, struct, subprocess
from pathlib import Path
from PIL import Image
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
EXT=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
CORE=EXT/'bin/core/garrison-core.exe'
PROJECT=ROOT/'output/release_010/houses/library/Mods/community_civilization_pack'
ART=ROOT/'art/authoring/houses_010'
TEX=ART/'textures';TEX.mkdir(exist_ok=True)
PREVIEW=ART/'preview-projections';PREVIEW.mkdir(exist_ok=True)
OUT=ROOT/'output/release_010/houses'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(label,args):
 p=subprocess.run([str(CORE),*map(str,args)],capture_output=True,text=True,encoding='utf8')
 (OUT/(label+'.log')).write_text(p.stdout+p.stderr)
 assert p.returncode==0,(label,p.stderr)

def png(t):
 src=Path(t['projection']['path']);dest=PREVIEW/(t['source']['sha256']+'.png')
 if not dest.exists():
  raw=bytearray(src.read_bytes())
  if raw[84:88]==b'DX10':
   fmt=struct.unpack_from('<I',raw,128)[0]
   if fmt in (72,75,78):struct.pack_into('<I',raw,128,fmt-1)
  Image.open(io.BytesIO(raw)).save(dest)
 return dest

def surface(src,dest,kind,age):
 im=Image.open(src).convert('RGBA');w,h=im.size
 palette={'straw':(174,145,91),'bamboo':(127,101,58),'timber':(92,59,32),'tile':(113,77,55) if age==2 else (139,83,56) if age==3 else (78,75,68),'brick':(133,87,63),'earth':(130,111,80),'plaster':(185,165,126)}
 base=palette[kind]
 arr=np.asarray(im).copy();y,x=np.mgrid[:h,:w];lum=np.sum(arr[:,:,:3]*np.array([.2126,.7152,.0722]),axis=2)/255
 if kind=='straw':gain=(.82+.13*lum+.10*np.sin(x*1.7)+.07*np.sin(x*.35+y*.006)+.07*((x*7919+y*104729)%103)/102)*np.where(y%max(8,h//8)<2,.78,1)
 elif kind=='bamboo':gain=.75+.18*lum+.08*np.sin(x*.22)+np.where(y%max(6,h//6)<2,.05,0)
 else:gain=.72+.40*lum
 arr[:,:,:3]=np.clip(np.rint(gain[:,:,None]*np.array(base)),0,255).astype('uint8');im=Image.fromarray(arr)
 im.save(dest)
 return {'image':str(dest),'sha256':sha(dest),'kind':kind,'source_png_sha256':sha(src),'dimensions':list(im.size)}

report={'schema':'ccp.houses-material-variants/v1','status':'running','project':str(PROJECT),'models':[],'preview_projections':{},'owner_mask_policy':'Do not alter maskTex*, debug/owner albedo, team sources, or options/owner parameters. Texture and neutral surface colour only.'}
for age in range(1,5):
 source=next((ROOT/f'art/stock_cache/houses_010/age{age:02}').rglob('decoded-static.json'));d=json.loads(source.read_text())
 for t in d['textures']:report['preview_projections'][t['projection']['path']]=str(png(t))
 mats=[]
 for mi,m in enumerate(x for x in d['material']['materials'] if not x['name'].endswith('_collection')):
  # Each carrier compiles a full native model; integration chooses its matching
  # material block by native name, retaining all original collection semantics.
  carrier=f'vn_house_age{age:02}'+('' if m['name']=='roof' else '_'+m['name'])
  current=json.loads((PROJECT/'mod-project.json').read_text())
  if carrier not in [v['name'] for v in current.get('model_variants',[])]:run('variant-'+carrier,['mod-project','variant','--project',PROJECT,'--source',d['request']['logical_path'][:-4],'--name',carrier])
  edits=[]
  for t in [t for b in m['blocks'] for t in b.get('textures',[]) if t['name'].startswith('albedoTex') and t['name']!='albedoTexCharred']:
   path=t['logical_path'].lower();kind=None
   if '/debug/' in path or 'team' in path:continue
   if '/shingle/' in path:kind='straw' if age==1 else 'tile'
   elif '/wood/' in path:kind='bamboo' if age==1 else 'timber'
   elif '/plaster/' in path:kind='bamboo' if age==1 else 'plaster'
   elif '/stone/' in path:kind='earth' if age==1 else 'brick'
   elif '/trim/' in path and age==1:kind='timber'
   if kind is None:continue
   match=next(x for x in d['textures'] if x.get('texture_name')==t.get('texture_name'))
   dest=TEX/f'age{age:02}_{m["name"]}_{t["name"]}_{kind}.png';meta=surface(png(match),dest,kind,age)
   run(carrier+'-'+t['name'],['mod-project','variant-set','--project',PROJECT,'--name',carrier,'--slot',t['name'],'--image',dest])
   edits.append({'slot':t['name'],'source_logical_path':t['logical_path'],**meta})
   if kind=='straw':
    # Packed structure normal: R emissive, G normal Y, B AO, A normal X.
    normal=dest.with_name(dest.stem+'_packed_normal.png');Image.new('RGBA',Image.open(dest).size,(0,128,235,128)).save(normal)
    nslot='normalMap'+t['name'].removeprefix('albedoTex')
    run(carrier+'-'+nslot,['mod-project','variant-set','--project',PROJECT,'--name',carrier,'--slot',nslot,'--image',normal]);edits.append({'slot':nslot,'image':str(normal),'sha256':sha(normal),'kind':'straw packed normal','source_logical_path':'generated flat normal with donor AO semantics'})
  mats.append({'name':m['name'],'carrier':carrier,'textures':edits,'native_collection_material':m['name']+'_collection'})
 report['models'].append({'age':age,'name':f'vn_house_age{age:02}','source':d['request']['logical_path'],'materials':mats})
 (OUT/'materials-ready.json').write_text(json.dumps(report,indent=2))
 print('HOUSE_MATERIAL_READY',age,flush=True)
report['status']='ready_for_serial_native_cook'
(OUT/'materials-ready.json').write_text(json.dumps(report,indent=2))
(ROOT/'art/recipes/release_010/houses-materials.json').write_text(json.dumps(report,indent=2))

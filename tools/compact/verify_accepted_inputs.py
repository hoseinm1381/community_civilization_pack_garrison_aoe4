"""Verify current art inputs and materialize only Blender masters for read-only QA."""
from pathlib import Path
import argparse,json,sys
import portable
from store import write_json,file_sha,check_text
def main():
 p=argparse.ArgumentParser();p.add_argument('--destination',type=Path,required=True);a=p.parse_args();dest=a.destination.resolve()
 if dest.exists():raise FileExistsError('Previous input audit preserved')
 dest.mkdir(parents=True);r=portable.reader();keys=r.doc['milestone']['editable_input_keys'];blends=[]
 for i,key in enumerate(keys,1):
  data=r.read(key);check_text(key,data)
  if key.endswith('.blend'):
   path=dest/key;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);blends.append(str(path))
  if i%500==0:print('CURRENT_ART_INPUTS_VERIFIED',i,len(keys),flush=True)
 write_json(dest/'audit-config.json',{'blends':blends,'virtual_files':{k:v['sha256'] for k,v in r.doc['files'].items()},'source_root':str(dest/'source'),'candidate_root':'F:/aoe_4_temp/Temp_before_github_push','permanent_root':str(portable.ROOT)})
 write_json(dest/'input-verification.json',{'status':'passed','current_art_input_files':len(keys),'bytes':sum(r.doc['files'][k]['bytes'] for k in keys),'Blender_masters':len(blends),'all_from_promoted_store':True})
 r.close();print('CURRENT_ART_INPUTS_PASS',len(keys),len(blends),flush=True)
if __name__=='__main__':main()

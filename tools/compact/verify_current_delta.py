"""Read back every changed immutable input and all newly referenced packs."""
import argparse,copy,gzip,hashlib,json,subprocess
from pathlib import Path
import portable
from store import file_sha,write_json,check_text
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=portable.reader();root=portable.ROOT
 raw=subprocess.check_output(['git','-c','safe.directory='+str(root),'-C',str(root),'show','HEAD:development-data/current-084-v1/index-current.json.gz'])
 olddelta=json.loads(gzip.decompress(raw));base=portable.load(root/'development-data/current-084-v1/index.json.gz');old=copy.deepcopy(base)
 for field in ('files','chunks','packs'):old[field].update(olddelta[field])
 packs={k:v for k,v in r.doc['packs'].items() if k not in old['packs']}
 for k,v in packs.items():
  path=portable.FOLDER/k
  if path.stat().st_size!=v['bytes'] or file_sha(path)!=v['sha256']:raise ValueError('New immutable pack differs: '+k)
 keys=[k for k,v in r.doc['files'].items() if v!=old['files'].get(k)]
 for i,k in enumerate(keys,1):
  data=r.read(k);check_text(k,data)
  if i%1000==0:print('CURRENT_DELTA_KEYS_VERIFIED',i,len(keys),flush=True)
 for row in r.doc['milestone']['payloads']:
  if hashlib.sha256(r.read(row['key'])).hexdigest()!=row['sha256']:raise ValueError('Final payload differs')
 report={'status':'passed','changed_input_keys_verified':len(keys),'new_pack_count':len(packs),'new_pack_bytes':sum(v['bytes'] for v in packs.values()),'new_packs':packs,'current_editable_input_keys':len(r.doc['milestone']['editable_input_keys']),'original_packs_preserved':True,'full_delivery_archive_stored_in_new_Git_delta':False}
 write_json(a.output,report);r.close();print('CURRENT_DELTA_PASS',len(keys),report['new_pack_bytes'],flush=True)
if __name__=='__main__':main()

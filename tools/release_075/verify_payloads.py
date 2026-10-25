"""Re-read isolated payloads and prove exact native owner preservation."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2];CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import relic_chunky as rc,model_variants as mv
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
base=Path(CFG['external_root'])/'staging/r74/v1/readback'
rows=[]
for receipt in sorted((ROOT/'output/release_075/payloads').glob('*/receipt.json')):
 data=json.loads(receipt.read_text());members={m['member']:m for m in data['members']}
 for member,m in members.items():
  p=Path(m['file']);assert sha(p)==m['sha256']
  if member.endswith('.rgm'):
   a=rc.parse((base/member).read_bytes()).roots[0];b=rc.parse(p.read_bytes()).roots[0]
   assert [(x.tag,x.name,x.version) for x in a.children]==[(x.tag,x.name,x.version) for x in b.children]
   changes=[x.tag.decode() for x,y in zip(a.children,b.children) if x.payload!=y.payload]
   assert changes==['MSCL'],(member,changes)
   owner=member[:-4]+'.rgo';assert owner not in members
   rows.append({'member':member,'changed_chunks':changes,'selectors_markers_other_chunks_exact':True,'native_rgo_sha256':sha(base/owner)})
  elif member.endswith('.rrmaterial'):
   descriptors=[]
   for mat in rc.parse(p.read_bytes()).roots:
    if mat.tag!=b'GMat':continue
    descriptors += [c.payload[4:].decode() for c in mat.children if c.tag==b'MatD']
    one=rc.pack_document([rc.pack_chunk(mat.kind,mat.tag,mat.payload,name=mat.name,version=mat.version)])
    for val in mv.material_slots(one)['textures'].values():
     if isinstance(val,str) and val.startswith('art\\'):assert val.replace('\\','/') in members,(member,val)
   assert descriptors==['object','object_collection'],descriptors
report={'status':'passed_for_available_payloads','families':[json.loads(p.read_text())['family'] for p in sorted((ROOT/'output/release_075/payloads').glob('*/receipt.json'))],'models':rows,'runtime':'unverified','scope':'Only completed payload receipts; does not imply seven-building completion'}
(ROOT/'output/release_075/payload-verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

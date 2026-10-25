"""Refresh seven-building consumer evidence against verified 0.7.4 readback."""
from pathlib import Path
import hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text(encoding='utf-8'))
OUT=ROOT/'output/release_075/inspection'
BACK=Path(CFG['external_root'])/'staging/r74/v1/readback'
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
proof=json.loads((ROOT/'output/release_074/verification-v1.json').read_text())
assert all(sha(BACK/k)==v for k,v in proof['member_sha256'].items()),'074 readback drift'
audit=ROOT/'output/asset_audit_073'
actors=json.loads((audit/'actors.json').read_text(encoding='utf-8'))
old=json.loads((ROOT/'output/release_073/verification-v1.json').read_text())
stems={
 'garden':'art/scenario/cc070/garden/model',
 'foundry':'art/scenario/cc070/foundry/model',
 'citadel':'art/scenario/cccastle/imperial_citadel/model',
 'hq':'art/scenario/cccastle/resistance_hq/model',
 'ministry':'art/scenario/cc020/economy_ministry/model',
 'pho_minh':'art/scenario/cc040/pho_minh/model',
 'one_pillar':'art/scenario/cc040/one_pillar/model'}
rows={}
for family,stem in stems.items():
 consumers=[a for a in actors if stem in a['custom_models'] or any(stem in v for v in a['variants'].values())]
 assert consumers,family
 for a in consumers:assert old['member_sha256'][a['member']]==proof['member_sha256'][a['member']]
 variants=sorted({m for a in consumers for values in a['variants'].values() for m in values})
 stamp_members=[]
 for member in proof['member_sha256']:
  if not member.startswith('art/stamps/') or not member.endswith('.bin'):continue
  raw=(BACK/member).read_bytes().lower().replace(b'\\',b'/')
  if any(model.encode() in raw for model in variants):stamp_members.append(member)
 media=[member for member in proof['member_sha256'] if any(member.startswith(s.rsplit('/',1)[0]+'/') for s in variants)]
 assert all(old['member_sha256'].get(k)==proof['member_sha256'][k] for k in media+stamp_members)
 rows[family]={'body_model':stem,'all_variant_models':variants,'consumers':consumers,'private_stamps':stamp_members,'media_members':media}
result={'schema':'ccp075-current-consumer-inventory/v1','baseline_sga_sha256':proof['sga_sha256'],'all_074_readback_hashes_verified':len(proof['member_sha256']),'families':rows,'boundary':'073 graph reused only where current packaged actor/media/stamp bytes are proven identical; full official parent resolution remains a separate check'}
(OUT/'current-consumers.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({k:{'actors':len(v['consumers']),'models':v['all_variant_models'],'stamps':v['private_stamps']} for k,v in rows.items()},indent=2))

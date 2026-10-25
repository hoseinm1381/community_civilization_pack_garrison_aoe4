import sys,zipfile,hashlib,json
from pathlib import Path
from common import *
sys.path.insert(0,str(ROOT/'tools/release_073'))
from check_identity import check
guard();base=ROOT/'output/release_076/delivery/final-v1';proof=read(base/'delivery-proof.json');archive=base/'community_civilization_pack.sga'
assert sha(archive)==proof['sga_sha256']=='65b7e601df5d649be90e0dc8f7a1b28812ef5482e65cddbad1d3a83c860e56fc'
check(ROOT,archive);before=read(base/'verification.json');payload=read(OUT/'payloads/ministry-v1/receipt.json');cook=read(OUT/'cooks/ministry-v1/receipt.json')
assert sha(cook['archive'])==cook['archive_sha256']
source=read(OUT/'art/receipt.json');assert sha(source['source'])==source['source_sha256']
for n,h in source['export_hashes'].items():assert sha(ROOT/'art/exports/release_077/ministry/r1'/n)==h
assert all(m['all_model_chunks_except_MSCL_exact'] and m['selector_bytes_exact'] for m in payload['models'])
out=OUT/'delivery/final-v1';assert not out.exists();out.mkdir(parents=True)
mapping={m['member']:m for m in payload['members']}
for m in mapping.values():assert sha(m['file'])==m['sha256']
allowed={s+e for s in read(ROOT/'output/release_075/inspection/current-consumers.json')['families']['ministry']['all_variant_models'] for e in ('.rgm','.rrgeom','.rrmaterial')}
assert all(m in allowed or m.startswith('art/scenario/cc077/ministry/') and m.endswith('.rrtex') for m in mapping)
lst=out/'members.txt';lst.write_text('\n'.join(m+'='+v['file'] for m,v in sorted(mapping.items()))+'\n')
final=out/'community_civilization_pack.sga'
run('assemble',[CFG['archive_tool'],'set-members',archive,lst,final,'--alias','data'],out/'logs');check(ROOT,final)
listing=json.loads(run('list',[CFG['archive_tool'],'list',final,'--verify'],out/'logs'));mounts={m['path']:m['toc'] for m in listing['members']}
expected=dict(before['member_sha256']);expected.update({k:v['sha256'] for k,v in mapping.items()})
assert set(expected)==set(mounts);assert all(mounts[k]==v for k,v in before['mounts'].items())
back=out/'readback';run('readback',[CFG['archive_tool'],'extract',final,back,'--filter',''],out/'logs')
actual={p.relative_to(back).as_posix():sha(p) for p in back.rglob('*') if p.is_file()};assert actual==expected
for p,h in read(ROOT/'output/release_076/source-freeze.json').items():assert sha(p)==h
for p,h in read(ROOT/'output/release_075/baseline/normal.json').items():assert sha(ROOT.parent/'Community_civilization_pack_normal'/p)==h
manifest=read(base/'garrison.json');manifest['members'][0]['sha256']=sha(final);manifest['details'].update(version='0.7.7',summary='Economic Ministry yard elephants replaced with three water buffalo.',description='Includes 0.7.6. Replaces only the Ministry decorative elephants with static copies of the new water buffalo. Gameplay, building lifecycle, flags and all other assets preserved.',changelog='Three decorative Ministry elephants replaced with water buffalo. Native appearance acceptance pending.')
write(out/'garrison.json',manifest)
changed=sorted(k for k,v in before['member_sha256'].items() if expected[k]!=v);added=sorted(set(expected)-set(before['member_sha256']))
evidence={'version':'0.7.7','baseline_sga_sha256':sha(archive),'sga_sha256':sha(final),'changed_members':changed,'added_members':added,'unchanged_members':len(before['member_sha256'])-len(changed),'mounts':mounts,'member_sha256':actual,'native_tested':False,'gameplay_unchanged':True,'buffalo_count':3,'source_receipt_sha256':sha(OUT/'art/receipt.json'),'payload_receipt_sha256':sha(OUT/'payloads/ministry-v1/receipt.json')}
write(out/'verification.json',evidence)
package=out/'community_civilization_pack-0.7.7.zip'
with zipfile.ZipFile(package,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 z.write(out/'garrison.json','garrison.json');z.write(final,final.name);z.writestr('START-HERE.txt','Community Civilization Pack 0.7.7\nCredits: hosein81 and chilly5\nImport into Garrison, select both Game Mode and Tuning Pack, then China and Vietnam. Ministry yard now contains three static water buffalo. Native appearance, construction, destruction and repair should be checked. Keep 0.7.6 for rollback.\n')
with zipfile.ZipFile(package) as z:
 assert z.testzip() is None and sum(Path(n).name=='garrison.json' for n in z.namelist())==1
 assert hashlib.sha256(z.read(final.name)).hexdigest()==sha(final)
 assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.7'
assert sha(archive)==proof['sga_sha256'] and sha(proof['zip'])==proof['zip_sha256']
write(out/'delivery-proof.json',{'zip':str(package),'zip_sha256':sha(package),'sga_sha256':sha(final),'verified':True,'installed':False})
print('DELIVERY_VERIFIED',str(package),len(changed),len(added))

from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent));from buffalo_runner import *
sys.path.insert(0,CFG['garrison_extension']);from garrison_shared import relic_chunky as rc
from rig_contract import read_contract,validate_contract
base=ROOT/'output/release_079/delivery/final-v1/readback';cook=OUT/'cooks/fur1';rows=[]
receipt=read(cook/'receipt.json');export=read(OUT/'art/buffalo/r1/export.json');proof=read(cook/'decoded-proof.json')['buffalo'];assert not proof['blockers'] and not proof['missing_textures'];assert sha(receipt['archive'])==receipt['archive_sha256']
assert sha(export['source'])==export['source_sha256'];assert all(sha(Path(export['export'])/n)==h for n,h in export['files'].items())
root='art/scenario/garrison/cc076/buffalo';old=(base/root/'model.rgm').read_bytes();new=(cook/'readback'/root/'model.rgm').read_bytes()
a=rc.parse(old).roots[0].children;b=rc.parse(new).roots[0].children
assert [(x.tag,x.name,x.version) for x in a]==[(x.tag,x.name,x.version) for x in b]
assert all(x.payload==y.payload for x,y in zip(a,b) if x.tag!=b'SKMS')
validate_contract(read_contract(new),export['donor_contract'])
for p in (cook/'readback'/root).iterdir():
 if p.suffix=='.rgo' or not p.is_file():continue
 member=root+'/'+p.name
 if (base/member).exists() and sha(base/member)==sha(p):continue
 rows.append({'member':member,'file':str(p),'sha256':sha(p),'toc':'data'})
ministry=read(OUT/'payloads/ministry-fur1/receipt.json')
for row in ministry['members']:
 assert sha(row['file'])==row['sha256']
 if row['before_sha256']==row['sha256']:continue
 rows.append({k:row[k] for k in ('member','file','sha256')}|{'toc':'data'})
checks=[OUT/'source-preservation.json',OUT/'art/buffalo/r1/export.json',OUT/'art/ministry/r1/receipt.json',cook/'receipt.json',cook/'decoded-proof.json',cook/'partition-proof.json',OUT/'cooks/ministry-fur1/receipt.json',OUT/'payloads/ministry-fur1/receipt.json',OUT/'rig-regressions.log']
write(OUT/'payload.json',{'status':'fresh_cooked_media_verified_native_unverified','members':rows,'proof_files':{str(p):sha(p) for p in checks},'buffalo_all_non_SKMS_chunks_exact':True,'buffalo_rgo_preserved_sha256':sha(base/root/'model.rgo'),'source_review':'Seven buffalo views and Ministry isometric reviewed; sparse short hairs retain silhouette. Native appearance unverified.','native_game_verified':False,'baseline_sga_sha256':read(ROOT/'output/release_079/delivery/final-v1/verification.json')['sga_sha256']})
write(RECIPES/'rebuild.json',{'author':'tools/release_0710/buffalo_author.py','ministry':'tools/release_0710/buffalo_ministry.py','runner':'tools/release_0710/buffalo_runner.py','native_cook_label':'fur1','ministry_cook':'tools/release_0710/buffalo_cook_ministry.py ministry --label fur1 --revision r1','assembly':'tools/release_0710/buffalo_assemble_ministry.py ministry --label fur1','required_python_for_garrison_modules':CFG['blender_python'],'retained_baselines':['art/authoring/release_079/buffalo/r3','art/authoring/release_079/ministry/r1']})
print('VERIFIED_PAYLOAD_MEMBERS',len(rows))

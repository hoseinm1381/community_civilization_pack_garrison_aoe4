from common import *
guard();dest=OUT/'baseline';dest.mkdir(parents=True,exist_ok=False)
assert sha(BASE/'community_civilization_pack.sga')==EXPECTED
sys.path.insert(0,str(ROOT/'tools/release_073'));from check_identity import check
check(ROOT,BASE/'community_civilization_pack.sga')
listing=json.loads(run('baseline-list',[CFG['archive_tool'],'list',BASE/'community_civilization_pack.sga','--verify'],dest))
freeze=read(BASE/'verification.json');assert {m['path'] for m in listing['members']}==set(freeze['member_sha256'])
write(dest/'archive.json',{'archive':str(BASE/'community_civilization_pack.sga'),'sha256':EXPECTED,'zip':str(BASE/'community_civilization_pack-0.8.2-pilot.2.zip'),'zip_sha256':sha(BASE/'community_civilization_pack-0.8.2-pilot.2.zip'),'members':freeze['member_sha256'],'mounts':{m['path']:m['toc'] for m in listing['members']}})
write(dest/'protected.json',{str(p):sha(p) for base in [ROOT/'art/authoring/release_079',ROOT/'art/exports/release_079',ROOT/'art/authoring/release_081',ROOT/'art/authoring/release_082_animation'] for p in base.rglob('*') if p.is_file()})
write(dest/'normal.json',read(ROOT/'output/release_081/baseline/normal.json'))
assert all(sha(p)==h for p,h in read(dest/'normal.json').items())
readback=ROOT/'output/release_081/delivery/final-v1/readback'
for family in [f'{kind}{age}' for kind in ['skirmisher','javelin','projectile'] for age in [2,3,4]]:
    path=readback/f'art/scenario/garrison/cc076/{family}/model.rgo'
    assert sha(path)==freeze['member_sha256'][f'art/scenario/garrison/cc076/{family}/model.rgo']
print('083_BASELINE_FROZEN',len(freeze['member_sha256']))

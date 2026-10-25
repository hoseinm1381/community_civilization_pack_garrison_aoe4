"""Prepare a one-variable rig-partition recook of existing custom geometry."""
import shutil
from common import *
from rig_contract import read_contract,rig_text

guard()
assert sha(OUT/'baseline/community_civilization_pack.sga')==EXPECTED
donors=read(ROOT/'output/release_076/donors.json')
RECIPES.mkdir(parents=True,exist_ok=True)
rules=ROOT/'art/recipes/release_076/art-burn-rules.xml'
shutil.copyfile(rules,RECIPES/rules.name)
write(OUT/'donors.json',donors)
selection={}
for family in ('buffalo','skirmisher2','skirmisher3','skirmisher4'):
    old=ROOT/'art/exports/release_076'/family/'r3';dest=EXPORT/family/'pilot-r1'
    if dest.exists():raise FileExistsError(dest)
    shutil.copytree(old,dest)
    d=read(donors[family]['manifest']);contract=read_contract(Path(d['skeleton']['source']).read_bytes())
    (dest/'model.rig').write_text(rig_text(contract),encoding='utf-8')
    unchanged={p.name:sha(p) for p in old.iterdir() if p.is_file() and p.name!='model.rig'}
    assert all(sha(dest/n)==h for n,h in unchanged.items())
    receipt=read(ROOT/'output/release_076/art'/family/'r3/export.json')
    receipt.update(revision='pilot-r1',export=str(dest),files={p.name:sha(p) for p in dest.iterdir() if p.is_file()},purpose='animation partition repair pilot; old art retained to isolate variable',unchanged_export_files=unchanged,donor_contract=contract)
    write(OUT/'art'/family/'pilot-r1/export.json',receipt)
    selection[family]='pilot-r1'
write(RECIPES/'pilot-selection.json',selection)
print('PILOT_EXPORTS_PREPARED',len(selection))

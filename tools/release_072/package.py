"""Package only a successfully read-back 0.7.2 assembly."""
from freeze import *
import argparse
def package(label):
    proof=json.loads((OUT/('assembly-'+label+'.json')).read_text());assert proof['passed']
    delivery=OUT/'delivery';sga=delivery/'community_civilization_pack.sga';assert sha(sga)==proof['sga_sha256']
    with zipfile.ZipFile(ROOT/'output/release_071/delivery/community_civilization_pack-0.7.1.zip')as z:
        assert z.testzip()is None;manifest=json.loads(z.read('garrison.json'))
    manifest['details'].update(version='0.7.2',name='Community Civilization Pack',author='hosein81 and chilly5',summary='Current Vietnam gameplay with preserved custom Garrison buildings, units and equipment.',changelog='Ports normal v12 gameplay, Buffalo/Paddy repairs and crowded tunnel entrance allowance; preserves existing custom art. Native match acceptance pending.')
    assert len(manifest['members'])==1
    manifest['members'][0].update(path=sga.name,sha256=sha(sga))
    evidence={'schema':'ccp.release072.evidence/v1','version':'0.7.2','credits':'hosein81 and chilly5','sga_sha256':sha(sga),'gameplay':'normal runtime v12','custom_media_preserved_members':proof['old_art_members_preserved'],'native_build_completed':True,'native_archive_readback_verified':True,'native_import_tested':False,'native_match_tested':False,'save_load_tested':False,'multiplayer_tested':False}
    start='''Community Civilization Pack 0.7.2
Credits: hosein81 and chilly5

Close Age of Empires IV and import this ZIP through Garrison. Enable the pack,
then select Community Civilization Pack as BOTH Game Mode and Tuning Pack.
Select China in the lobby, then choose Vietnam at match start. Start a fresh
match; existing 0.7.1 saves are not qualified for this gameplay update.

This release ports the complete normal v12 gameplay and preserves existing
custom buildings, unit bodies and equipment. No new art or voices are included.
Expected log revision: 20261023-runtime-v12-garrison-072.

Focused native checks:
- Check custom buildings/units at every available age; stock visuals stay stock.
- Check construction, damage, destruction, persistent landmark ruins and repair.
- Check Water Buffalo speed (0.875 tiles/s), Supervise hotkey E and Paddy Wood.
- Check the Town Center diamond is absent and influence display is smaller.
- Tunnel 35-50 eligible units once from a spread formation; verify arrivals,
  cancellation, recovery and cooldown. Loading allowance is 8m from the edge.
- Check multiplayer and save/load separately; these are not validated here.

Completed Content Editor build and archive/package verification do not establish
in-game appearance or behavior. Reimport the preserved 0.7.1 ZIP to roll back;
the development workspace also retains the exact original 0.7.0 rollback.
'''
    dump(delivery/'garrison.json',manifest)
    target=delivery/'community_civilization_pack-0.7.2.zip'
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
        z.writestr('garrison.json',json.dumps(manifest,indent=2)+'\n');z.write(sga,sga.name);z.writestr('START-HERE.txt',start);z.writestr('EVIDENCE.json',json.dumps(evidence,indent=2)+'\n')
    with zipfile.ZipFile(target)as z:
        assert z.testzip()is None
        assert set(z.namelist())=={'garrison.json',sga.name,'START-HERE.txt','EVIDENCE.json'}
        assert sum(Path(n).name.lower()=='garrison.json'for n in z.namelist())==1
        assert hashlib.sha256(z.read(sga.name)).hexdigest()==manifest['members'][0]['sha256']
        assert json.loads(z.read('garrison.json'))['details']['version']=='0.7.2'
    dump(OUT/'delivery-proof.json',dict(evidence,package_verified=True,zip_sha256=sha(target),zip_bytes=target.stat().st_size,assembly_label=label))
    print(json.dumps({'package':str(target),'zip_sha256':sha(target),'bytes':target.stat().st_size}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--label',required=True);a=p.parse_args();package(a.label)

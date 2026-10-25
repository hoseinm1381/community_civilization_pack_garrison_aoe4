"""Qualify isolated source structure materials before changing landmark media."""
from __future__ import annotations
import json,re,shutil,sys,subprocess
from pathlib import Path
from common import CFG,OUT,WORK,CORE,ARCH,ART_EDITOR,guarded,read,write,sha,run_logged
from cook import asset_inputs,exclusive_native,material
from native_support import rc,mv
from owner_colour import prepare_project,decode_material,structure_parameters

def qualify(label):
    guarded()
    assert re.fullmatch(r'r[a-z0-9-]{2,15}',label)
    pointer=read(OUT/'cook/landmarks-pointer.json')
    inputs=read(pointer['inputs']);project=Path(inputs['project'])
    prepared=OUT/'owner-colour/owner-colour-prepare.json'
    candidate=read(prepared) if prepared.exists() else None
    if not candidate or candidate.get('candidate_revision')!=4 or candidate['source_project']!=str(project.resolve()) or candidate['source_project_config_sha256']!=sha(project/'mod-project.json'):
        candidate=prepare_project(project,asset_inputs('landmarks'))
    source=Path(candidate['candidate_project'])
    assert sha(source/'mod-project.json')==candidate['candidate_project_config_sha256']
    for building in read(source/'mod-project.json')['buildings']:
        for member,digest in building['files'].items():assert sha(source/'project/source'/member)==digest
    short=Path(CFG['external_root'])/'c'/('ccnext-owner-'+label)
    assert not short.exists();shutil.copytree(source,short,ignore=shutil.ignore_patterns('.garrison.lock'))
    burnfile=short/'project/source/_default.burnproj'
    burn=burnfile.read_text(encoding='utf-8-sig')
    def select(match):
        rule=match[0]
        burner=re.search(r'<Burner>(.*?)</Burner>',rule)
        enabled=bool(burner and any(word in burner[1] for word in ('Material','Texture')))
        return re.sub(r'<IsEnabled>(?:true|false)</IsEnabled>',f'<IsEnabled>{str(enabled).lower()}</IsEnabled>',rule)
    burnfile.write_text(re.sub(r'<BurnRule>.*?</BurnRule>',select,burn,flags=re.S),encoding='utf-8')
    source_files={p.relative_to(short/'project/source').as_posix():sha(p) for p in (short/'project/source').rglob('*') if p.is_file()}
    root=OUT/'owner-colour'/label
    write(root/'input-freeze.json',{'files':source_files,'candidate':candidate,'short_project':str(short)})
    with exclusive_native():
        run_logged('owner-colour-'+label,[CORE,'essence','build-mod','--editor',ART_EDITOR,
                   '--mod',next((short/'project').glob('*.aoe4mod')),'--run-root',root/'run','--timeout','300'],timeout=360)
    state=read(root/'run/run.json');assert state['status']=='succeeded' and state['exit_code']==0
    archives=list((root/'run/output').rglob('*.sga'));assert len(archives)==1
    archive=archives[0];back=root/'readback'
    run_logged('owner-colour-'+label+'-readback',[ARCH,'unpack',archive,'--output',back])
    return finish(label)

def finish(label):
    root=OUT/'owner-colour'/label
    frozen=read(root/'input-freeze.json');candidate=frozen['candidate']
    short=Path(frozen['short_project']);source_files=frozen['files']
    state=read(root/'run/run.json');assert state['status']=='succeeded' and state['exit_code']==0
    archives=list((root/'run/output').rglob('*.sga'));assert len(archives)==1
    archive=archives[0];back=root/'readback'
    reports=[]
    for asset in candidate['assets']:
        base=f"art/scenario/garrison/community_castle_next_landmarks/buildings/{asset['key']}/model"
        original=back/(base+'.rrmaterial')
        raw=mv.rewrite_material(original.read_bytes(),{},structure_parameters())
        path=root/'variants'/(asset['key']+'.rrmaterial');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        decoded=decode_material(path)
        assert {m['shader_descriptor'] for m in decoded['materials']}=={'structure','structure_collection'}
        entry=next(m for m in decoded['materials'] if m['shader_descriptor']=='structure')
        slots=entry['texture_slots'];assert slots.get('maskTex5') not in (None,'','__default'),entry
        assert 'albedoTex' in slots and 'normalMap' in slots and 'metalTex' in slots,entry
        strength=entry['parameters'].get('secondaryMaskStrength567')
        assert strength and strength['type']=='Float4' and all(abs(float(a)-b)<1e-6 for a,b in zip(strength['values'],[0,.57,0,0])),strength
        print('OWNER_NATIVE_MATERIAL',asset['key'],json.dumps(entry),flush=True)
        mask=slots['maskTex5'].replace('\\','/').lower()
        if not mask.endswith('.rrtex'):mask+='.rrtex'
        assert (back/mask).is_file(),mask
        reports.append({'key':asset['key'],'material':str(path),'material_sha256':sha(path),
                        'original_native_material':str(original),'original_native_sha256':sha(original),
                        'decoded':entry,'mask':mask,'mask_sha256':sha(back/mask),'strength567':strength})
    assert source_files=={p.relative_to(short/'project/source').as_posix():sha(p) for p in (short/'project/source').rglob('*') if p.is_file()}
    value={'status':'passed_native_material_cook_pending_application','archive':str(archive),
           'sha256':sha(archive),'readback':str(back),'reports':reports,'candidate':candidate,
           'native_match':'not tested'}
    write(root/'qualification.json',value)
    print('OWNER_NATIVE_QUALIFIED',label,len(reports));return value

if __name__=='__main__':
    if sys.argv[1]=='finish':finish(sys.argv[2])
    else:qualify(sys.argv[1])

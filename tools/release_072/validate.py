"""Static checks, CSV/RDO identities and imported-source semantic parity."""
from freeze import *
import subprocess,csv,io,xml.etree.ElementTree as E
STAGE=Path(CFG['external_root'])/'staging/r72/ported-source'
def main():
    reports=[];skill=Path.home()/'.codex/skills/aoe4-game-mode-skill'
    for p in sorted((STAGE/'assets/scar').rglob('*')):
        if p.suffix not in ('.scar','.rdo'):continue
        proc=subprocess.run([sys.executable,str(skill/'scripts/validate_scar.py'),str(p),'--project-root',str(STAGE)],capture_output=True,text=True,encoding='utf-8',errors='replace')
        reports.append({'file':p.relative_to(STAGE).as_posix(),'exit':proc.returncode,'output':proc.stdout+proc.stderr})
    dump(OUT/'scar-static.json',reports);assert all(x['exit']==0 for x in reports),'Static errors; inspect scar-static.json'
    p=STAGE/'assets/locdb/community_civilization_pack_en.csv'
    rows=list(csv.reader(io.StringIO(p.read_text(encoding='utf-8-sig'),newline='')));assert all(len(x)==len(rows[0])for x in rows)
    ids=[x[0]for x in rows[1:]];assert len(set(ids))==len(ids);assert all(x.isdigit()for x in ids)
    for p in (STAGE/'assets').rglob('*.rdo'):
        root=E.parse(p).getroot();seen=[]
        for o in root.iter('DataObject'):
            if o.get('Id'):seen.append(o.get('Id'))
            if o.get('Type')=='util::ReflectLocString':
                values={x.get('Name'):x.get('Value')for x in o.findall('DataProperty')}
                assert values.get('m_locStringKey')in ids
                assert [values.get('m_modPart'+str(i))for i in range(4)]==['3086805649','1083123067','1303308473','3775054987']
        assert len(set(seen))==len(seen),'RDO duplicate object identity'
    print(json.dumps({'scar_rdo_files_checked':len(reports),'locale_rows':len(ids),'status':'passed'}))
if __name__=='__main__':main()

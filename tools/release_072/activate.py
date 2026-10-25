"""Activate only the verified staged sources, preserving full 0.7.1 recovery."""
from port import *
def main():
    freeze();receipt=json.loads((OUT/'source-port.json').read_text());expected=receipt['staged_hashes']
    for name,v in expected.items():assert sha(STAGE/name)==v,name
    before=json.loads((OUT/'freeze/garrison.json').read_text())
    for name,v in before.items():assert sha(ROOT/name)==v,'Concurrent Garrison edit: '+name
    source={name:v for name,v in expected.items()if name.startswith('assets/')}
    for name in before:
        if not name.startswith('assets/')or name in source:continue
        target=(ROOT/name).resolve();assert target.is_relative_to((ROOT/'assets').resolve());target.unlink()
    for name in source:
        target=ROOT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((STAGE/name).read_bytes())
    cfg=json.loads((ROOT/'workspace.json').read_text());cfg['version']='0.7.2';dump(ROOT/'workspace.json',cfg)
    assert {p.relative_to(ROOT).as_posix():sha(p)for p in files(ROOT/'assets')}==source
    dump(OUT/'activation.json',{'passed':True,'assets':source,'removed_old_paths':[k for k in before if k.startswith('assets/')and k not in source],'recovery':'output/release_072/freeze/garrison.zip','normal_unchanged':True})
    print('Activated',len(source),'verified source assets; old source recoverable in freeze/garrison.zip')
if __name__=='__main__':main()

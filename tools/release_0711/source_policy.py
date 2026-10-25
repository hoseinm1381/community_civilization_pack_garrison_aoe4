"""0711 changes presentation only; tuning, art and gameplay are byte-preserved."""
import zipfile
from common import *
from patch import CHANGED,transforms

def main():
    guard();original={Path(p).relative_to(ROOT).as_posix():h for p,h in read(OUT/'baseline/source-hashes.json').items()}
    current={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    for p in (ROOT/'workspace.json',ROOT/CFG['project_file']):current[p.relative_to(ROOT).as_posix()]=sha(p)
    assert not (original.keys()-current.keys())
    changed={p for p in original if original[p]!=current[p]}
    assert changed==set(CHANGED),changed
    added=set(current)-set(original)
    assert added=={'assets/scar/vietnam/presentation_data.scar','assets/scar/vietnam/presentation_badges.scar'},added
    with zipfile.ZipFile(OUT/'baseline/source.zip') as z:
        for p in changed:
            assert (ROOT/p).read_text(encoding='utf-8-sig')==transforms(p,z.read(p).decode('utf-8-sig').replace('\r\n','\n')),p
    for file in ('normal-hashes.json','protected-0710-inputs.json'):
        assert all(sha(p)==h for p,h in read(OUT/'baseline'/file).items()),file
    cap=read(OUT/'cap-source.json');assert sha(cap['source'])==cap['sha256']
    write(OUT/'source-policy.json',{'passed':True,'changed':sorted(changed),'added':sorted(added),'current_hashes':current,
        'all_tuning_and_art_byte_preserved':True,'normal_and_0710_preserved':True,
        'paddy_changes':'local presentation function only; onscreen visibility and private tag routing flag',
        'all_other_paddy_gameplay_exact':True})
    print('SOURCE_POLICY_PASSED',len(changed),len(added))

if __name__=='__main__':main()

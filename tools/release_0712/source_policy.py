"""Reject every source change outside the exact authorized 0712 transforms."""
from common import *
from apply import expected_changes

def main():
    guard();old={Path(p).relative_to(ROOT).as_posix():h for p,h in read(OUT/'baseline/source-hashes.json').items()}
    now={p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'assets').rglob('*') if p.is_file()}
    for p in (ROOT/'workspace.json',ROOT/CFG['project_file']):now[p.relative_to(ROOT).as_posix()]=sha(p)
    assert now.keys()==old.keys(),'Unexpected added/deleted source'
    changed={p for p in now if now[p]!=old[p]};expected=expected_changes()
    assert changed==expected.keys(),changed^expected.keys()
    assert all((ROOT/p).read_text(encoding='utf-8-sig')==s for p,s in expected.items())
    for name in ('normal-hashes.json','protected-0711-inputs.json'):
        assert all(sha(p)==h for p,h in read(OUT/'baseline'/name).items()),name
    write(OUT/'source-policy.json',{'passed':True,'changed':sorted(changed),'added':[],
        'current_hashes':now,'normal_and_prior_inputs_preserved':True,
        'authorization':'Original 0712 request plus actual influence +2m and 8m ground-click destination clarification'})
    print('SOURCE_POLICY_PASSED',len(changed))

if __name__=='__main__':main()

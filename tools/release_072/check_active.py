from freeze import *
if __name__=='__main__':
    freeze();receipt=json.loads((OUT/'activation.json').read_text())
    active={p.relative_to(ROOT).as_posix():sha(p)for p in files(ROOT/'assets')}
    assert active==receipt['assets'],'Source drift: revise the explicit release policy before compiling changes'
    stage=Path(CFG['external_root'])/'staging/r72/ported-source'
    for key,value in active.items():assert sha(stage/key)==value,'Staged source drift'
    print('Current editable source equals verified 0.7.2 build inputs')

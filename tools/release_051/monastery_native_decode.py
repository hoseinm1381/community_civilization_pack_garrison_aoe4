"""Fresh Garrison decode of both compacted private monastery models.

Uses a task-owned SGA and task-owned copy of the game asset index. The official
index and all game archives are read only. Hold the shared native lock.
"""
from __future__ import annotations
import json, sqlite3, struct, subprocess, sys
from pathlib import Path
from common import ROOT, OUT, BASELINE, ARCH, CORE, CONFIG, guarded, exclusive_native, read, sha, write
sys.path.insert(0,str(ROOT/'tools/castle_next'))
from building_selectors import source_map

BASE=OUT/'monastery/reference'
SGA=BASE/'compacted-probe.sga'
INDEX=BASE/'game-assets.sqlite3'
GAME_INDEX=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3')
GAME_CONFIG=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json')

def run(command,log,timeout):
    if log.exists():
        raise AssertionError(f'Preserve previous native log; choose new run path: {log}')
    with log.open('w',encoding='utf-8') as stream:
        proc=subprocess.run([str(x) for x in command],stdout=stream,stderr=subprocess.STDOUT,
                            timeout=timeout,cwd=ROOT)
    assert proc.returncode==0,(proc.returncode,log.read_text(encoding='utf-8')[-3000:])

def stage_sga(receipt):
    source=BASE/'set-members.txt'
    source.write_text(''.join(f"{row['member']}={row['file']}\n" for row in receipt['payloads']),encoding='utf-8')
    assert not SGA.exists()
    run([ARCH,'set-members',BASELINE,source,SGA],BASE/'set-members.log',300)
    assert SGA.is_file() and SGA.stat().st_size>100_000_000
    for row in receipt['payloads']:
        target=BASE/'readback'/row['member'];target.parent.mkdir(parents=True,exist_ok=True)
        run([ARCH,'extract-member',SGA,row['member'],target],BASE/('extract-'+Path(row['member']).parent.name+'-'+Path(row['member']).name+'.log'),45)
        assert sha(target)==row['sha256']

def stage_index():
    assert not INDEX.exists()
    with sqlite3.connect('file:'+GAME_INDEX.as_posix()+'?mode=ro',uri=True) as source:
        with sqlite3.connect(INDEX) as target:source.backup(target)
    with sqlite3.connect(INDEX) as db:
        names=[x[1] for x in db.execute('pragma table_info(resolved_assets)')]
        assert {'logical_path','archive_path','size','id','raw_name','folder','name','extension'}<=set(names)
        maximum=db.execute('select max(id) from resolved_assets').fetchone()[0]
        for age in (3,4):
            old=f'art/civilizations/chinese/structures/monastery/chi_monastery_control_age{age:02}/chi_monastery_control_age{age:02}'
            new=f'art/scenario/cccastle/monastery_age{age:02}/model'
            for extension in ('rgm','rrgeom','rgo','rrmaterial'):
                stock=old+'.'+extension;logical=new+'.'+extension
                row=db.execute('select * from resolved_assets where logical_path=?',(stock,)).fetchone()
                assert row is not None and db.execute('select 1 from resolved_assets where logical_path=?',(logical,)).fetchone() is None
                values=dict(zip(names,row));maximum+=1
                values.update({'id':maximum,'logical_path':logical,'folder':logical.rsplit('/',1)[0],
                               'name':logical.rsplit('/',1)[1],'raw_name':'data:'+logical.replace('/','\\'),
                               'size':(BASE/'readback'/logical).stat().st_size if (BASE/'readback'/logical).exists()
                                     else next(p['bytes'] for p in read(ROOT/'output/castle_next/integration/building-media.json')['payloads'] if p['member']==logical),
                               'archive':'compacted-probe.sga','archive_path':str(SGA),'provider_archive_id':'CCP051MonasteryProbe'})
                db.execute('insert into resolved_assets('+','.join(names)+') values('+','.join('?' for _ in names)+')',tuple(values[n] for n in names))
        db.commit()
        assert db.execute("select count(*) from resolved_assets where provider_archive_id='CCP051MonasteryProbe'").fetchone()[0]==8

def validate_decode(age,receipt):
    logical=f'art/scenario/cccastle/monastery_age{age:02}/model.rgm'
    target=BASE/f'decode-age{age:02}';target.mkdir()
    log=BASE/f'decode-age{age:02}.log'
    run([CORE,'convert','decode-static','--logical-path',logical,'--config',GAME_CONFIG,
         '--index',INDEX,'--output-root',target],log,300)
    manifests=list(target.rglob('decoded-static.json'))
    assert len(manifests)==1,manifests
    doc=read(manifests[0]);assert doc['status']=='decoded'
    rows={r['member']:r for r in receipt['payloads']}
    assert doc['resources']['model']['sha256']==rows[logical]['sha256']
    geom=logical.removesuffix('.rgm')+'.rrgeom'
    assert doc['geometry']['source']['sha256']==rows[geom]['sha256']
    recipe=read(ROOT/f'art/recipes/release_051/monastery/age{age:02}-retained-triangle-ordinals.json')
    donor=read(ROOT/'output/castle_next/donors/donor-manifest.json')['donors'][f'monastery{age:02}']
    before_names,_=source_map(donor)
    after_names,selector=source_map({'decoded_static':doc})
    expected=[ [names[i] for i in ordinals] for names,ordinals in zip(before_names,recipe['retained_triangle_ordinals_by_group'])]
    assert after_names==expected
    native_counts=[g['triangle_count'] for g in doc['geometry']['groups']]
    assert native_counts==[len(row) for row in expected]
    assert selector['all_selector_names']==source_map(donor)[1]['all_selector_names']
    for group in doc['geometry']['groups']:
        assert all(len(set(face))==3 for face in group['triangles'])
        assert max(i for face in group['triangles'] for i in face)<group['vertex_count']
    return {'age':age,'manifest':str(manifests[0]),'manifest_sha256':sha(manifests[0]),
            'model_sha256':rows[logical]['sha256'],'rrgeom_sha256':rows[geom]['sha256'],
            'native_triangle_counts':native_counts,'selector_source_map_exactly_retained':True,
            'all_mscl_names_qualified':True,'invalid_indices':0,'degenerate_triangles':0,
            'native_decode_log':str(log)}

def main():
    guarded();receipt=read(OUT/'monastery/receipt.json')
    assert receipt['status']=='source_payload_ready_native_reference_pending'
    assert not BASE.exists();BASE.mkdir(parents=True)
    with exclusive_native():
        stage_sga(receipt);stage_index()
        ages=[validate_decode(age,receipt) for age in (3,4)]
    result={'status':'passed_fresh_native_garrison_decode_reference_cook_pending',
            'baseline_sga_sha256':sha(BASELINE),'probe_sga':str(SGA),'probe_sga_sha256':sha(SGA),
            'private_index':str(INDEX),'private_index_sha256':sha(INDEX),
            'ages':ages,'official_game_index_untouched':True,'native_match':'pending'}
    write(OUT/'monastery/native-decode.json',result)
    print('MONASTERY051_FRESH_NATIVE_DECODE_PASS',[r['native_triangle_counts'] for r in ages])

if __name__=='__main__':main()

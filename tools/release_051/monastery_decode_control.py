"""Compare Garrison decode of unchanged 050 private model to 051 compaction."""
import sqlite3,subprocess
from pathlib import Path
from common import OUT,BASELINE,CORE,ARCH,ROOT,guarded,exclusive_native,sha,write
from monastery_native_decode import BASE,INDEX,GAME_CONFIG

def main():
    guarded();control=BASE/'control-050-sizefix2';control.mkdir(exist_ok=True)
    dbpath=control/'game-assets.sqlite3';assert not dbpath.exists()
    with sqlite3.connect(INDEX) as source:
        with sqlite3.connect(dbpath) as target:source.backup(target)
    with sqlite3.connect(dbpath) as db:
        db.execute("update resolved_assets set archive_path=? where provider_archive_id='CCP051MonasteryProbe'",(str(BASELINE),))
        assert db.total_changes==8;db.commit()
        for age in (3,4):
            for extension in ('rgm','rrgeom','rgo','rrmaterial'):
                logical=f'art/scenario/cccastle/monastery_age{age:02}/model.{extension}'
                source=OUT/'monastery/baseline-members'/logical
                if not source.exists():
                    source.parent.mkdir(parents=True,exist_ok=True)
                    subprocess.run([str(ARCH),'extract-member',str(BASELINE),logical,str(source)],
                                   cwd=ROOT,capture_output=True,check=True)
                assert source.is_file(),source
                db.execute('update resolved_assets set size=? where logical_path=?',(source.stat().st_size,logical))
        db.commit()
    logical='art/scenario/cccastle/monastery_age03/model.rgm'
    target=control/'decode-age03';target.mkdir()
    log=control/'decode-age03.log';assert not log.exists()
    with exclusive_native():
        with log.open('w',encoding='utf-8') as stream:
            proc=subprocess.run([str(CORE),'convert','decode-static','--logical-path',logical,
                '--config',str(GAME_CONFIG),'--index',str(dbpath),'--output-root',str(target)],
                cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT,timeout=300)
    result={'status':'control_050_decode_passed' if proc.returncode==0 else 'control_050_decode_failed',
            'exit_code':proc.returncode,'log':str(log),'log_tail':log.read_text(encoding='utf-8')[-1500:],
            'baseline_sga_sha256':sha(BASELINE),'task_index_sha256':sha(dbpath),
            'private_model':'unchanged 050 baseline resource'}
    write(OUT/'monastery/decode-control.json',result)
    print(result)

if __name__=='__main__':main()

"""Decode the one uncached unchanged native incense prop into task-owned evidence."""
from pathlib import Path
import sqlite3,subprocess
from common import OUT,ARCH,CORE,ROOT,guarded,exclusive_native,write,sha

def decode(metal):
    name=f'art/civilizations/common/props/incense_burner_large_{metal}/incense_burner_large_{metal}'
    index=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.sqlite3')
    config=Path('C:/Users/RS/AppData/Local/Garrison/Kit/game-assets.local.json')
    rows=[]
    with sqlite3.connect('file:'+index.as_posix()+'?mode=ro',uri=True) as db:
        for ext in ('rgm','rrgeom','rgo','rrmaterial'):
            row=db.execute('select archive_path,size from resolved_assets where logical_path=?',(name+'.'+ext,)).fetchone()
            rows.append({'ext':ext,'archive':row[0] if row else None,'size':row[1] if row else None})
    dst=OUT/('monastery/stock-props/incense' if metal=='iron' else 'monastery/stock-props/incense-bronze')
    dst.mkdir(parents=True,exist_ok=True)
    log=dst/'decode.log'
    if log.exists():
        assert (dst/'receipt.json').exists()
        print('INCENSE_DECODE_PRESERVED',metal)
        return
    with exclusive_native():
        with log.open('w',encoding='utf-8') as stream:
            proc=subprocess.run([str(CORE),'convert','decode-static','--logical-path',name+'.rgm','--config',str(config),
                                 '--index',str(index),'--output-root',str(dst/'decoded')],cwd=ROOT,
                                stdout=stream,stderr=subprocess.STDOUT,timeout=180)
    code=proc.returncode
    manifests=list(dst.rglob('decoded-static.json'))
    write(dst/'receipt.json',{'source':name,'index_rows':rows,'decode_returncode':code,
                             'log':str(log),'log_sha256':sha(log),'manifests':[str(x) for x in manifests]})
    print('INCENSE_DECODE',metal,code,manifests)

def main():
    guarded()
    for metal in ('iron','bronze'):decode(metal)

if __name__=='__main__':main()

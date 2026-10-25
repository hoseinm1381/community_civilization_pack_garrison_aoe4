"""Decode three newly confirmed reachable official Chinese unit models."""
from __future__ import annotations
import json,subprocess
from pathlib import Path
from common import CORE,OUT,guard,owned,sha,write

INDEX=Path.home()/'AppData/Local/Garrison/Kit/game-assets.sqlite3'
CONFIG=INDEX.with_name('game-assets.local.json')
MODELS={
  'monk3':'art/civilizations/chinese/humans/chi_infantry_monk_age03/chi_infantry_monk_age03.rgm',
  'trade2':'art/civilizations/chinese/animals/chi_horse_combined_trade_age02/chi_horse_combined_trade_age02.rgm',
  'trade3':'art/civilizations/chinese/animals/chi_horse_combined_trade_age03/chi_horse_combined_trade_age03.rgm',
}

def main():
    guard()
    if not INDEX.is_file() or not CONFIG.is_file():raise FileNotFoundError('Garrison asset index/config')
    root=owned(OUT/'inventory/additional-official-models')
    receipt=root/'decode.json'
    if root.exists() or receipt.exists():raise FileExistsError('Preserve existing decode')
    entries=[]
    for key,logical in MODELS.items():
        destination=owned(root/key)
        cmd=[str(CORE),'convert','decode-static','--logical-path',logical,
             '--config',str(CONFIG),'--index',str(INDEX),'--output-root',str(destination)]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        manifests=list(destination.rglob('decoded-static.json'))
        if result.returncode or len(manifests)!=1:
            raise RuntimeError(f'{key}: decode exit={result.returncode}, manifests={len(manifests)}, tail={result.stderr[-500:]}')
        manifest=manifests[0]
        entries.append({'key':key,'logical_model':logical,'manifest':str(manifest),
                        'manifest_sha256':sha(manifest)})
    write(receipt,{'schema':'ccp-060-additional-official-decodes/1',
                   'index':str(INDEX),'index_sha256':sha(INDEX),
                   'config':str(CONFIG),'config_sha256':sha(CONFIG),
                   'models':entries,'native_cook':'not_run'})
    print(json.dumps({'receipt':str(receipt),'models':entries}))

if __name__=='__main__':main()

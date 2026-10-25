"""Read-only Garrison decode of confirmed attached equipment/crew bodies."""
from __future__ import annotations
import json,subprocess
from pathlib import Path
from common import CORE,OUT,guard,owned,sha,write

INDEX=Path.home()/'AppData/Local/Garrison/Kit/game-assets.sqlite3'
CONFIG=INDEX.with_name('game-assets.local.json')
MODELS={
 'monk_staff3':'art/civilizations/chinese/weapons/chi_staff_khakkhara_1/chi_staff_khakkhara_1.rgm',
 'monk_staff4':'art/civilizations/chinese/weapons/chi_staff_khakkhara_2/chi_staff_khakkhara_2.rgm',
 'spear_basic':'art/civilizations/common/weapons/melee/spear_basic/spear_basic.rgm',
 'spear_ji':'art/civilizations/chinese/weapons/chi_spear_ji/chi_spear_ji.rgm',
 'combat_elephant3':'art/civilizations/sultanate/animals/sul_elephant_combined_armor_age03/sul_elephant_combined_armor_age03.rgm',
 'siege_cart3':'art/civilizations/english/team_weapons/eng_siege_cart/eng_siege_cart.rgm',
}

def main():
    guard()
    if not INDEX.is_file() or not CONFIG.is_file():raise FileNotFoundError('Garrison asset index/config')
    root=owned(OUT/'inventory/equipment-and-crew-models')
    if root.exists():raise FileExistsError('Preserve previous decode set')
    entries=[]
    for key,logical in MODELS.items():
        destination=owned(root/key)
        cmd=[str(CORE),'convert','decode-static','--logical-path',logical,
             '--config',str(CONFIG),'--index',str(INDEX),'--output-root',str(destination)]
        result=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
        manifests=list(destination.rglob('decoded-static.json'))
        entries.append({'key':key,'logical_model':logical,'exit_code':result.returncode,
                        'manifest':str(manifests[0]) if len(manifests)==1 else None,
                        'manifest_sha256':sha(manifests[0]) if len(manifests)==1 else None,
                        'stderr_tail':result.stderr[-500:] if result.returncode else None})
    write(root/'decode.json',{'schema':'ccp-060-equipment-crew-decodes/1',
        'index':str(INDEX),'index_sha256':sha(INDEX),'config':str(CONFIG),
        'config_sha256':sha(CONFIG),'models':entries})
    print(json.dumps({'receipt':str(root/'decode.json'),'models':entries}))

if __name__=='__main__':main()

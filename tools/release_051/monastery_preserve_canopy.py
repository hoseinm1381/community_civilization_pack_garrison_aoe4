"""Keep the reviewed high-canopy candidate as task-owned diagnostic evidence."""
from __future__ import annotations
import shutil
from common import OUT,ART,RECIPES,guarded,sha,write

def main():
    guarded()
    source=OUT/'monastery';target=source/'diagnostic-canopy-051'
    assert not target.exists();target.mkdir()
    roots=[source/'receipt.json',source/'verification.json',source/'native-readback.json',
           source/'editable-assets.json',source/'payload',source/'previews']
    roots.extend((ART/'monastery/age03/body-051-retained-native-local.obj',
                  ART/'monastery/age04/body-051-retained-native-local.obj',
                  RECIPES/'monastery/age03-retained-triangle-ordinals.json',
                  RECIPES/'monastery/age04-retained-triangle-ordinals.json'))
    saved=[]
    for item in roots:
        rel=item.relative_to(source) if item.is_relative_to(source) else 'external-'+item.name
        dst=target/rel
        if item.is_dir():shutil.copytree(item,dst)
        else:
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(item,dst)
        saved.append({'source':str(item),'diagnostic':str(dst)})
    write(target/'receipt.json',{'status':'preserved_rejected_high_canopy_candidate','files':saved})
    print('PRESERVED_CANOPY051',len(saved))

if __name__=='__main__':main()

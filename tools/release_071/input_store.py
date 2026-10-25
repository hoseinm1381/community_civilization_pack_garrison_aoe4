"""Inspect or restore losslessly packed rebuild/diagnostic input by original key."""
import argparse
import json
from consolidate import STORE, physical
from resources import ResourceStore, sha

if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['list','verify','restore'])
    p.add_argument('key',nargs='?')
    a=p.parse_args()
    store=ResourceStore(STORE)
    if a.command=='list':
        print('\n'.join(store.index))
    elif a.command=='verify':
        for k in store.index: store.read(k)
        print('Verified',len(store.index),'lossless inputs')
    else:
        if a.key not in store.index: raise KeyError('Use list to find an original E/ or F/ key')
        target=physical(a.key)
        row=store.index[a.key]
        if target.exists():
            assert sha(target)==row['sha256'],'Existing edited file preserved; refusing overwrite'
        else:
            store.materialize(a.key,target)
        print(str(target))

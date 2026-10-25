"""Freeze preparation inputs without overwriting prior or active releases."""
import datetime
import json
from common import *

def main():
    links = guard()
    freeze = OUT/'baseline/preparation-freeze.json'
    if freeze.exists():
        print(json.dumps({'status': 'existing-freeze-preserved', 'path': str(freeze)}))
        return
    for root in OWNED:
        root.mkdir(parents=True, exist_ok=True)
    inputs = {'assets': files(ROOT/'assets', reject_links=True), 'normal': files(CFG['source_root']),
              'prior_art': {name: files(ROOT/'art'/name) for name in ('authoring','exports','recipes')},
              'identities': {name: sha(ROOT/name) for name in ('workspace.json', CFG['project_file'])}}
    target = STAGING/'preparation-source/assets'
    if target.exists():
        raise FileExistsError(f'Unfinished snapshot exists; inspect rather than overwrite: {target}')
    copy_manifest(ROOT/'assets', target, inputs['assets'])
    if files(target, reject_links=True) != inputs['assets']:
        raise RuntimeError('Active source changed during snapshot; retain diagnostics and retry explicitly')
    write(freeze, {'schema': 'ccp-060-preparation-freeze/v1',
                  'created_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'status': 'preparation-only-not-final-release-baseline', 'links': links,
                  'source_snapshot': str(target), 'inputs': inputs,
                  'final_baseline_policy': 'Completed final 0.5.3 preferred, otherwise completed final 0.5.2; diagnostic candidates excluded.'})
    print(json.dumps({'status':'frozen', 'path':str(freeze),
                      'asset_files':len(inputs['assets']), 'normal_files':len(inputs['normal'])}))

if __name__ == '__main__':
    main()

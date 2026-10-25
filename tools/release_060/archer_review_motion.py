"""Read two hash-pinned native Archer clips for clothing deformation previews."""
from pathlib import Path
import json
import subprocess
from common import CORE, OUT, guard, owned, read, sha, write
from pilot_decode import CONFIG, INDEX


def main():
    guard()
    manifest = OUT / 'donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json'
    control = read(OUT / 'qualification/archer-matched-control-export.json')
    if sha(manifest) != control['donor_manifest_sha256']:
        raise RuntimeError('Pinned Archer donor drift')
    plan = read(manifest)['animated_asset_import_plan']['layers']['animation']
    source = plan['source']
    folder = owned(OUT / 'qualification/archer-review-motion')
    folder.mkdir(parents=True, exist_ok=True)
    result = []
    for index, expected_name in ((202, 'navigation\\walk_calm_f_01'),
                                 (147, 'ranged\\fire_center_middle')):
        clip = next(c for c in plan['clips'] if c['index'] == index)
        if clip['name'] != expected_name or clip['status'] != 'ready_for_animation_clip_projection':
            raise RuntimeError('Unexpected native clip identity/status')
        dest = folder / f'{index}.json'
        receipt = folder / f'{index}-receipt.json'
        identity = {'manifest': str(manifest), 'manifest_sha256': sha(manifest),
                    'rhka_logical_path': source['rhka_logical_path'],
                    'rhka_sha256': source['rhka_sha256'], 'clip_index': index,
                    'clip_name': expected_name, 'config_sha256': sha(CONFIG),
                    'index_sha256': sha(INDEX)}
        if receipt.exists():
            prior = read(receipt)
            if prior.get('source_identity') != identity or sha(dest) != prior['payload_sha256']:
                raise RuntimeError('Preserve changed clip evidence')
            result.append({'clip_index': index, 'status': 'verified_existing', 'path': str(dest)})
            continue
        if dest.exists():
            raise FileExistsError('Preserve unreceipted native decoder output')
        command = [str(CORE), '-m', 'src.core.animation_clip', '--logical-path',
                   source['rhka_logical_path'], '--clip-index', str(index),
                   '--expected-sha256', source['rhka_sha256'], '--config', str(CONFIG),
                   '--index', str(INDEX), '--output', str(dest)]
        try:
            run = subprocess.run(command, capture_output=True, text=True, encoding='utf-8',
                                 errors='replace', timeout=90)
        except subprocess.TimeoutExpired as error:
            write(folder / f'{index}-failure.json', {'status': 'timeout', 'seconds': 90,
                  'source_identity': identity, 'partial_output_preserved': dest.exists()})
            raise RuntimeError('Native review clip decoder timed out; diagnostic retained') from error
        write(folder / f'{index}-decoder.json', {'returncode': run.returncode,
              'stdout': run.stdout, 'stderr': run.stderr, 'source_identity': identity})
        if run.returncode or not dest.exists():
            raise RuntimeError(f'Native clip decode failed: {index}; inspect saved decoder log')
        payload = read(dest)
        write(receipt, {'schema': 'ccp-060-stock-clip-receipt/v1', 'source_identity': identity,
              'payload_sha256': sha(dest), 'payload_status': payload.get('status'),
              'boundary': 'Native stock clip preview only; no clip replacement or game proof'})
        result.append({'clip_index': index, 'status': payload.get('status'), 'path': str(dest)})
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()

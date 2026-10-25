"""Freeze the complete private art payload and stamp-to-model closure contract."""
import sys
from common import OUT, guarded, read, sha, write
from integrate import STAMP_TARGETS

sys.dont_write_bytecode = True
WORK = OUT / 'integration'


def assemble():
    guarded()
    names = ('barracks-tc-media.json', 'scratch-media.json', 'hideout-media.json')
    inputs = {name: read(WORK / name) for name in names}
    assert all(row['status'] == 'passed' for row in inputs.values())
    payloads = []
    for receipt in inputs.values(): payloads.extend(receipt['payloads'])
    indexed = {}
    for row in payloads:
        assert row['member'] not in indexed, ('duplicate media payload', row['member'])
        assert sha(row['file']) == row['sha256'], row['member']
        indexed[row['member']] = row
    stamp_model_targets = {key: [target] for key, target in STAMP_TARGETS.items()}
    stamp_model_targets['hideout_shelter_default'] = ['hideout_shelter_default']
    stamp_model_targets['hideout_shelter_stone'] = ['hideout_shelter_stone']
    expected_stamps = {'art/stamps/cc020/' + key + '.bin' for key in stamp_model_targets}
    assert expected_stamps == {member for member in indexed if member.startswith('art/stamps/cc020/')}
    models = sorted({'art/scenario/cc020/' + target + '/model'
                     for targets in stamp_model_targets.values() for target in targets})
    assert all(all(stem + suffix in indexed for suffix in ('.rgm', '.rgo', '.rrgeom', '.rrmaterial'))
               for stem in models)
    result = {'status': 'passed', 'source_receipts_sha256': {name: sha(WORK / name) for name in names},
              'stamp_model_targets': stamp_model_targets, 'models': models,
              'payloads': [indexed[key] for key in sorted(indexed)], 'native_runtime': 'unverified'}
    write(WORK / 'media-020.json', result)
    print('MEDIA_020_FROZEN', len(models), len(expected_stamps), len(indexed))
    return result


if __name__ == '__main__': assemble()

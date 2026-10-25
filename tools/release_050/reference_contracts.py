"""Read-only exact 0.4.0 actor reference scan for 0.5.0 visual bindings."""
from __future__ import annotations

import sys
from pathlib import Path

from common import ARCH, BASELINE, CONFIG, GUID, ROOT, WORK, guarded, read, run_logged, sha, write

sys.path.insert(0, CONFIG['garrison_extension'])
sys.path.insert(0, str(ROOT / 'tools/release_010'))
from garrison_shared import rgd

ACTORS = (
    'vn_building_landmark_age2_imperrial_citadel_vit',
    'vn_building_landmark_age2_headquarter_vit',
    'vn_building_unit_religious_control_chi',
    'vn_building_unit_siege_control_chi',
    'vn_building_defense_keep_chi',
    'vn_building_defense_keep_2_chi',
)


def main():
    guarded()
    freeze = read(WORK.parent / 'baseline/freeze-baseline.json')
    assert freeze['status'] == 'immutable_pre_050_baseline'
    assert BASELINE.is_file()
    root = WORK / 'reference-040'
    rows = []
    for actor in ACTORS:
        member = f'attrib/ebps/vietnam/{actor}.rgd'
        target = root / member
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            run_logged('reference040-' + actor, [ARCH, 'extract-member', BASELINE, member, target])
        doc = rgd.read(target.read_bytes())
        refs = []
        for path, node in rgd.flatten(doc.nodes):
            if node.key in ('$PBGNAME', '$PBGMAP') and ('attachment' in path or 'parent_pbg' in path):
                refs.append({'path': path, 'kind': node.kind, 'value': node.value})
        rows.append({'actor': actor, 'member': member, 'sha256': sha(target), 'references': refs})
        print('REFERENCE040', actor, len(refs), flush=True)
    write(WORK / 'reference-040-actors.json', {
        'schema': 'ccp.release050.reference-040-actors/v1', 'status': 'passed',
        'accepted_archive': str(BASELINE), 'accepted_archive_sha256': sha(BASELINE),
        'project_guid': GUID, 'actors': rows,
    })


if __name__ == '__main__':
    main()

"""Trace all first-age landmark visual consumers and their official native owners."""
import json
import sys
import xml.etree.ElementTree as ET
from common import ROOT, OUT, guarded, read, sha, write

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from garrison_shared import rgd

native.CACHEWORK = OUT / 'inventory'

ACTORS = {
    'pho_minh': ('vn_building_landmark_age1_gatehouse_control_chi',),
    'one_pillar': ('vn_building_landmark_age1_vit_one_pilar_pagoda',
                   'vn_building_landmark_age1_headquarters_control_chi'),
}


def inventory():
    guarded()
    frozen = read(OUT / 'source-baseline.json')['assets']
    contracts = {}
    for key, names in ACTORS.items():
        actors = {}
        refs = set()
        for name in names:
            relative = 'attrib/instances/ebps/vietnam/' + name + '.xml'
            path = OUT / 'source-baseline' / relative
            assert sha(path) == frozen[relative]['sha256']
            root = ET.parse(path).getroot()
            observed = [node.get('value') for node in root.iter('instance_reference')
                        if node.get('name') == 'attachments' and node.get('value')]
            actors[name] = {'sha256': sha(path), 'attachments': observed}
            refs.update(observed)
        contracts[key] = {'actors': actors, 'references': sorted(refs)}
    for key, entry in contracts.items():
        # Only the principal building lists are replaced. Outskirts remain untouched.
        refs = [r for r in entry['references'] if ('\\buildings\\' in r and
                ('landmark_1b_chi_ha' in r or 'york_wooden_castle_eng' in r))]
        assert len(refs) == 1, (key, refs)
        ref = refs[0]
        member = 'attrib/' + ref.replace('\\', '/') + '.rgd'
        source = native.stock(member)
        parsed = rgd.read(source.read_bytes())
        stamps = sorted({n.value.replace('\\', '/').lower() for _, n in rgd.flatten(parsed.nodes)
                         if n.key == 'stamp' and n.kind == 'CString' and n.value})
        assert stamps, (key, ref)
        stamp_info = {}
        for stem in stamps:
            path = native.stock(stem + '.bin')
            tree = native.NativeTree(path)
            stamp_info[stem] = {'file': str(path), 'sha256': sha(path),
                                'visuals': native.active_visuals(tree),
                                'object_types': {t: sum(o['type'] == t for o in tree.objects.values())
                                                 for t in sorted({o['type'] for o in tree.objects.values()})}}
        entry.update({'principal_source': ref, 'principal_member': member,
                      'principal_file': str(source), 'principal_sha256': sha(source),
                      'stamps': stamp_info})
    result = {'schema': 'community.release030.landmark-graph/v1', 'status': 'passed',
              'landmarks': contracts, 'runtime': 'unverified'}
    write(OUT / 'inventory/landmarks.json', result)
    print(json.dumps({'status': 'passed', 'stamps': {k: list(v['stamps']) for k, v in contracts.items()}}, indent=2))
    return result


if __name__ == '__main__':
    inventory()

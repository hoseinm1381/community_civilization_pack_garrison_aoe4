"""Read official attachment/stamp graph into a fixed 0.2.0 integration contract."""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from common import OUT, ROOT, STAGING, guarded, sha, write
from source_policy import CONSUMERS

sys.dont_write_bytecode = True
sys.path.append(str(ROOT / 'tools/release_010'))
import integration as native
from garrison_shared import rgd

native.CACHEWORK = OUT / 'inventory'

SOURCES = {
    **{f'barracks_age0{i}': rf'attachments\attachment_lists\civilizations\chinese\buildings\unit_infantry_chi\tier{i}_unit_infantry_control_chi' for i in range(1, 5)},
    **{f'town_center_age0{i}': rf'attachments\attachment_lists\civilizations\chinese\buildings\town_center_chi\tier{i}_town_center_control_chi' for i in range(1, 5)},
    'farm_outskirts': r'attachments\attachment_lists\civilizations\chinese\outskirts\general\chi_farms',
    'hideout': r'attachments\attachment_lists\civilizations\chinese\buildings\defense_outpost_chi\defense_outpost_control_chi',
    'economy_ministry': r'attachments\attachment_lists\civilizations\chinese\buildings\dynasty_pagoda_chi\tier1_pagoda_chi',
}
EXPECTED_STAMPS = {
    **{f'barracks_age0{i}': f'art/stamps/civ_chinese/chi_barracks_age_0{i}' for i in range(1, 5)},
    **{f'town_center_age0{i}': f'art/stamps/civ_chinese/chi_town_center_age_0{i}' for i in range(1, 5)},
    'hideout_default': 'art/stamps/civ_chinese/chi_outpost',
    'hideout_stone': 'art/stamps/civ_chinese/chi_outpost_stone',
    'economy_ministry': 'art/stamps/civ_chinese/chi_dynasty_pagoda',
    **{f'farm_rice_{side}': f'art/stamps/outskirt/farm_rice_{side}_a' for side in ('back', 'front', 'left', 'right')},
}


def inventory():
    guarded()
    frozen_assets = STAGING / 'baseline_source/assets'
    consumers = {}
    for name in CONSUMERS:
        path = frozen_assets / f'attrib/instances/ebps/vietnam/{name}.xml'
        doc = ET.parse(path)
        refs = [e.get('value') for e in doc.iter('instance_reference') if e.get('name') in ('attachments', 'animator_attachments')]
        consumers[name] = {'source': str(path), 'sha256': sha(path), 'attachments': list(dict.fromkeys(refs)),
                           'matching_private_sources': [key for key, value in SOURCES.items() if value in refs]}
    for key in SOURCES:
        assert any(key in actor['matching_private_sources'] for actor in consumers.values()), key
    attachments = {}
    for key, ref in SOURCES.items():
        member = 'attrib/' + ref.replace('\\', '/') + '.rgd'
        path = native.stock(member)
        doc = rgd.read(path.read_bytes())
        fields = [{'path': field, 'value': node.value} for field, node in rgd.flatten(doc.nodes)
                  if node.kind == 'CString' and node.value and node.key in ('stamp', 'parent_animator')]
        attachments[key] = {'source': ref, 'member': member, 'sha256': sha(path),
                            'file': str(path), 'visual_fields': fields}
    stamps = {}
    for key, stem in EXPECTED_STAMPS.items():
        path = native.stock(stem + '.bin')
        tree = native.NativeTree(path)
        stamps[key] = {'source': stem, 'file': str(path), 'sha256': sha(path),
                       'visuals': native.active_visuals(tree),
                       'object_types': {type_name: sum(obj['type'] == type_name for obj in tree.objects.values())
                                        for type_name in sorted({obj['type'] for obj in tree.objects.values()})}}
    result = {'schema': 'community.release020.native-graph/v1', 'status': 'official source inventory',
              'consumers': consumers, 'attachments': attachments, 'stamps': stamps,
              'runtime': 'unverified'}
    write(OUT / 'inventory/native-graph.json', result)
    print('NATIVE_GRAPH', len(consumers), 'consumers', len(attachments), 'attachments', len(stamps), 'stamps')
    return result


if __name__ == '__main__':
    inventory()

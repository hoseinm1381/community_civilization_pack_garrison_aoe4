"""Pin reachable Vietnamese-only weapon-list identities before native derive."""
from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from collections import defaultdict

from common import OUT, ROOT, guard, owned, read, sha, write

GRAPH = OUT/'integration/private-land-graph/plan-v3.json'
OFFICIAL = OUT/'inventory/official_rgd/03b8e431c91920535fa65cdae340ee206f31bbdfbb1740feddb4a0430625a977/decoded/attrib/attachments/attachment_lists/races/chinese/weapons'
TARGET = OUT/'integration/private-equipment-graph/derive-plan-v1.json'

SELECTED = {
    **{f'wpn_range_archer_{age}_chi': 'art\\civilizations\\common\\weapons\\ranged\\bow_recurve\\bow_recurve'
       for age in (2, 3, 4)},
    'wpn_range_crossbow_3_chi': 'art\\civilizations\\common\\weapons\\ranged\\bow_cross\\bow_cross',
    'wpn_range_crossbow_4_chi': 'art\\civilizations\\common\\weapons\\ranged\\bow_arbalest\\bow_arbalest',
    **{f'wpn_melee_{variant}_{age}_chi': 'art\\civilizations\\common\\weapons\\melee\\spear_basic\\spear_basic'
       for age in (1, 2) for variant in ('spearman', 'spearwall')},
    **{f'wpn_melee_spearman_{age}_charge_chi': 'art\\civilizations\\common\\weapons\\melee\\spear_basic\\spear_basic'
       for age in (1, 2)},
    **{f'wpn_melee_{variant}_{age}_chi': 'art\\civilizations\\chinese\\weapons\\chi_spear_ji\\chi_spear_ji'
       for age in (3, 4) for variant in ('spearwall',)},
    **{f'wpn_melee_spearman_{age}_charge_chi': 'art\\civilizations\\chinese\\weapons\\chi_spear_ji\\chi_spear_ji'
       for age in (3, 4)},
}


def main():
    guard()
    reachable = set(read(GRAPH)['reachable_local_entity_ids'])
    edges = defaultdict(list)
    for actor in sorted(reachable):
        source = ROOT/'assets/attrib/instances/ebps/vietnam'/f'{actor}.xml'
        tree = ET.fromstring(source.read_bytes())
        counts = defaultdict(int)
        for node in tree.iter('instance_reference'):
            value = node.get('value', '')
            if node.get('name') != 'animator_attachments':
                continue
            name = value.rsplit('\\', 1)[-1]
            if name in SELECTED:
                expected = f'attachments\\attachment_lists\\races\\chinese\\weapons\\{name}'
                if value != expected:
                    raise ValueError(f'Unexpected weapon owner: {actor} {value}')
                counts[name] += 1
        for name, count in sorted(counts.items()):
            edges[name].append({'actor':actor, 'source':source.relative_to(ROOT).as_posix(),
                                'source_sha256':sha(source), 'before':f'attachments\\attachment_lists\\races\\chinese\\weapons\\{name}',
                                'expected_source_occurrences':count})
    if set(edges) != set(SELECTED):
        raise ValueError(f'Unreached selected equipment: {set(SELECTED)-set(edges)}')
    rows = []
    for name, model in sorted(SELECTED.items()):
        xml = OFFICIAL/f'{name}.xml'
        if not xml.is_file():
            raise FileNotFoundError(xml)
        tree = ET.fromstring(xml.read_bytes())
        slots = [n.get('Value') for n in tree.iter('RGDNode') if n.get('Key') == 'parent_animator']
        if model not in slots:
            raise ValueError(f'Native model absent: {name} {model}')
        digest = hashlib.sha256(('equipment#'+name).encode()).hexdigest()[:7]
        private_name = f'v6w{digest}'
        stock = f'attrib/attachments/attachment_lists/races/chinese/weapons/{name}.rgd'
        ref = f'attachments/attachment_lists/vietnam/release_060/{private_name}'
        rows.append({'stock_member':stock, 'stock_source':stock.removeprefix('attrib/').removesuffix('.rgd'),
                     'derived_name':private_name, 'private_reference':ref,
                     'private_member':f'attrib/{ref}.rgd', 'original_model':model,
                     'model_slot_count':slots.count(model), 'decoded_stock_xml_sha256':sha(xml),
                     'source_consumers':edges[name]})
    result = {'schema':'ccp-060-private-equipment-derive-plan/v1',
              'status':'offline_pinned_native_registration_pending', 'graph_sha256':sha(GRAPH),
              'entries':rows, 'selected_list_count':len(rows),
              'source_actor_count':len({e['actor'] for row in rows for e in row['source_consumers']}),
              'source_edge_count':sum(e['expected_source_occurrences'] for row in rows for e in row['source_consumers']),
              'exclusions':['Monk III staff private selector remains unproven.',
                            'Spear III/IV normal lists lack chi_spear_ji and remain stock.',
                            'Unchanged other weapon variants retain original native model paths.'],
              'native_cook_or_active_source_changed':False}
    if TARGET.exists():
        if read(TARGET) != result:
            raise ValueError('Preserve existing equipment plan')
    else:
        write(owned(TARGET), result)
    print({'plan':str(TARGET), 'lists':len(rows), 'actors':result['source_actor_count'],
           'source_edges':result['source_edge_count']})


if __name__ == '__main__':
    main()

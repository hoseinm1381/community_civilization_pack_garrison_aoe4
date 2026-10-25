"""Inventory exact Vietnamese land actor attachment edges for private 060 identities.

This is an offline plan only. It never derives, cooks, or edits active source.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

from common import OUT, ROOT, guard, owned, read, sha, write

INPUT = OUT/'inventory/continuation/private-consumer-binding-plan-v1.json'
INPUT_SHA = '69a24069088960acdb15d736dc2f5682527441d19d1a51609f94e89f01544a4a'
IDS = OUT/'integration/private-foot-identities/registered-identities.json'
STAGE = OUT/'integration/private-foot-compiled-r1/bindings.json'
AUDIT = OUT/'inventory/coverage-audit-v2.json'
TARGET = OUT/'integration/private-land-graph/plan-v3.json'


def entries(path: Path):
    root = ET.parse(path).getroot()
    for item in root.iter():
        if item.tag == 'instance_reference' and item.attrib.get('name') in ('attachments', 'animator_attachments'):
            value = item.attrib.get('value', '')
            if value.startswith('attachments\\attachment_lists\\'):
                yield value


def main():
    guard()
    if sha(INPUT) != INPUT_SHA:
        raise ValueError('Pinned continuation inventory drift')
    inventory = read(INPUT)
    audit = read(AUDIT)
    reachable = {name for family in audit['family_tier_coverage']
                 for name in family['entity_ids']}
    excluded = {row['id'] for row in audit['excluded_local_candidates']
                if row['category'] == 'ebps'}
    if reachable & excluded or len(reachable) != audit['counts']['local_reachable_entities']:
        raise ValueError('Reachable local actor audit inconsistent')
    identities = read(IDS)
    first = read(STAGE)
    first_members = {row['stock_member'] for row in identities['entries']}
    source = ROOT/'assets/attrib/instances/ebps/vietnam'
    graph = defaultdict(list)
    for path in sorted(source.glob('vn_unit*.xml')):
        if path.stem not in reachable:
            continue
        for value in entries(path):
            member = 'attrib/'+value.replace('\\', '/')+'.rgd'
            graph[member].append({'source':str(path), 'source_sha256':sha(path),
                                  'relative_source':path.relative_to(ROOT).as_posix(),
                                  'before':value})
    known = {row['member'] for row in inventory['additional_reachable_body_lists']}
    known.update(x['member'] for j in inventory['material_jobs'] for x in j['native_attachment_lists'])
    # Inherited Chinese SBPS/EBPS are separately reachable through Vietnamese
    # production. Their tier paths, not similarly named unlinked local actors,
    # own the monk and trade-cart visuals.
    inherited_tiers = {
        'unit_monk_3_chi': ('tier3_monk_chi', 'tier4_monk_chi'),
        'unit_trade_cart_chi': ('tier2_trade_cart_chi', 'tier3_trade_cart_chi', 'tier4_trade_cart_chi'),
    }
    included_stock = {x['id'] for x in audit['included_inherited_stock_actors']}
    if not set(inherited_tiers).issubset(included_stock):
        raise ValueError('Monk or trade cart no longer reachable through producer')
    for actor, tiers in inherited_tiers.items():
        for tier in tiers:
            member = f'attrib/attachments/attachment_lists/civilizations/chinese/units/{tier}.rgd'
            graph[member].append({'source':'official:attrib/ebps/races/chinese/units/'+actor+'.rgd',
                                  'relative_source':None, 'before':member.removeprefix('attrib/').removesuffix('.rgd').replace('/','\\'),
                                  'reachability':'Vietnamese producer -> official Chinese squad -> official Chinese actor'})
    required = []
    for member, consumers in sorted(graph.items()):
        if member in first_members:
            continue
        if not ('/units/' in member or '/animals/' in member):
            continue
        required.append({'stock_member':member, 'source_consumers':consumers,
                         'inventory_pinned':member in known,
                         'private_reference':'attachments/attachment_lists/vietnam/release_060/vn060_'+Path(member).stem,
                         'derived_name':'vn060_'+Path(member).stem})
    names = [x['derived_name'].casefold() for x in required]
    if len(set(names)) != len(names):
        raise ValueError('Colliding derived names require explicit resolution')
    payload = {'schema':'ccp-060-private-land-graph-plan/v3',
               'status':'offline_exact_source_edges_native_registration_pending',
               'input_sha256':INPUT_SHA, 'first_ten_identity_sha256':sha(IDS),
               'coverage_audit_sha256':sha(AUDIT),
               'reachable_local_entity_ids':sorted(reachable),
               'excluded_unlinked_local_entity_ids':sorted(excluded),
               'included_inherited_stock_actor_ids':sorted(included_stock),
               'first_ten_stage_sha256':sha(STAGE),
               'first_ten_stock_members':sorted(first_members),
               'unit_actor_lists':required,
               'siege_consumer_edges':inventory['siege_consumers'],
               'siege_native_members':inventory['siege_native_members'],
               'first_ten_stage_payload_count':len(first['payloads']),
               'limits':['Source list edges are from reachable local actors only. Inherited monk/trade tiers come from current official compiled actor selectors.',
                         'Producer and stock squad edges require separate native closure.',
                         'Native identities, media, active source, and final archive are unchanged.']}
    if TARGET.exists():
        if read(TARGET) != payload:
            raise ValueError('Existing graph plan differs; preserve evidence')
    else:
        write(owned(TARGET), payload)
    print({'plan':str(TARGET), 'additional_lists':len(required),
           'not_in_prior_inventory':[x['stock_member'] for x in required if not x['inventory_pinned']]})


if __name__ == '__main__':
    main()

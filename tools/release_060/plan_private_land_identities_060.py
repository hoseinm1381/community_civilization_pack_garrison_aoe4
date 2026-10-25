"""Freeze one supported native-derive batch for the remaining land graph.

This writes a manifest only. The scheduler owner must separately authorize a cook.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from common import OUT, guard, owned, read, sha, write

GRAPH = OUT/'integration/private-land-graph/plan-v3.json'
INVENTORY = OUT/'inventory/continuation/private-consumer-binding-plan-v1.json'
TARGET = OUT/'integration/private-land-identities/derive-plan-v5.json'


def private_row(member: str, role: str, context: str = ''):
    canonical = member.removeprefix('attrib/').removesuffix('.rgd')
    category, _, remainder = canonical.partition('/')
    digest = hashlib.sha256((member+'#'+context).encode('utf-8')).hexdigest()[:7]
    # Short native names keep all cooked Windows paths below the editor limit.
    name = f'v6i{digest}'
    if category == 'attachments':
        dest = f'attachments/attachment_lists/vietnam/release_060/{name}'
    elif category in ('ebps', 'sbps'):
        dest = f'{category}/vietnam/release_060/{name}'
    else:
        raise ValueError('Unsupported identity category '+member)
    return {'role':role, 'context':context or None, 'stock_member':member, 'stock_source':canonical,
            'derived_name':name, 'private_reference':dest,
            'private_member':'attrib/'+dest+'.rgd'}


def main():
    guard()
    graph = read(GRAPH)
    inventory = read(INVENTORY)
    rows = [private_row(x['stock_member'], 'unit_body_list') for x in graph['unit_actor_lists']]
    # Repeater IV is a separate production actor sharing Crossbow IV's stock
    # list; its approved body needs a second, context-specific private identity.
    rows.append(private_row('attrib/attachments/attachment_lists/civilizations/chinese/units/tier4_crossbowman_chi.rgd',
                            'repeater4_body_list', 'repeater4'))
    # Direct native actor, squad and list resources are all private to Vietnam.
    # English donor and common animation-owner records stay shared and byte-identical.
    siege = graph['siege_native_members']
    chosen = [m for m in siege if m.startswith(('attrib/ebps/races/chinese/',
                 'attrib/sbps/races/chinese/',
                 'attrib/attachments/attachment_lists/races/chinese/',
                 'attrib/attachments/attachment_lists/civilizations/chinese/'))]
    chosen += ['attrib/ebps/races/chinese/units/unit_siege_tower_3_chi.rgd',
               'attrib/sbps/races/chinese/unit_siege_tower_3_chi.rgd',
               'attrib/attachments/attachment_lists/races/chinese/units/unit_siege_tower_3_chi.rgd',
               'attrib/ebps/dev/units/unit_siege_cart.rgd',
               'attrib/attachments/attachment_lists/civilizations/english/units/tier3_siege_cart_eng.rgd']
    chosen += [f'attrib/{category}/races/chinese/{"units/" if category == "ebps" else ""}{stem}.rgd'
               for stem in ('unit_monk_3_chi', 'unit_trade_cart_chi', 'unit_repeater_crossbowman_4_chi')
               for category in ('ebps', 'sbps')]
    # The cart is an actor attachment in Trebuchet squads, not an independent
    # Vietnamese production unit. Its private actor points at the private skin list.
    for member in chosen:
        rows.append(private_row(member, 'siege_private_graph'))
    members = [(x['stock_member'].casefold(), x['context']) for x in rows]
    if len(set(members)) != len(members):
        raise ValueError('Duplicate source and consumer context in identity batch')
    dests = [x['private_member'].casefold() for x in rows]
    if len(set(dests)) != len(dests):
        raise ValueError('Duplicate private identity destination')
    data = {'schema':'ccp-060-private-land-derive-plan/v3',
            'status':'offline_pinned_scheduler_not_acquired',
            'graph_sha256':sha(GRAPH), 'inventory_sha256':sha(INVENTORY),
            'entries':rows, 'unit_lists':len(graph['unit_actor_lists']),
            'repeater4_context_list':1,
            'siege_resources':len(chosen),
            'excluded_existing_first_ten':graph['first_ten_stock_members'],
            'native_cook_or_source_changes':False,
            'limits':['Actor/list/squad copy will preserve original native bytes except PBGID and approved visual/reference leaves.',
                      'Any unsupported derive source must stop with diagnostics; never invent an ID.']}
    if TARGET.exists():
        if read(TARGET) != data:
            raise ValueError('Preserve existing batch plan')
    else:
        write(owned(TARGET), data)
    print({'batch':str(TARGET), 'entries':len(rows), 'unit_lists':data['unit_lists'],
           'siege_resources':data['siege_resources']})


if __name__ == '__main__':
    main()

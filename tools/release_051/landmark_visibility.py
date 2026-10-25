"""Inspect and repair the 0.5.0 landmark model lifecycle in isolated 0.5.1 bytes."""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from common import ARCH, ART, BASELINE, EXPORT, OUT, RECIPES, ROOT, guarded, read, sha, write

sys.path.insert(0, str(Path.home() / 'AppData/Roaming/Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'))
from garrison_shared import relic_chunky as rc


MEMBERS = (
    'art/scenario/cccastle/imperial_citadel/model.rgm',
    'art/scenario/cccastle/resistance_hq/model.rgm',
    'art/scenario/cc050/imperial_citadel_campaign/model.rgm',
)
BASELINE_HASHES = {
    MEMBERS[0]: '4af4e2725af87ffbacb4e7ab786429980daff9310e1beaf4d0084c351f11d4c4',
    MEMBERS[1]: '0ad977fc3b36037665cabed9ffbfdb948fb8faa5c0a55897173848210e4a796d',
    MEMBERS[2]: 'a98865f9d6db1a2850c92da471bf122f8c10e273eef9bbd17c4265fc205bc81b',
}
PARTS = {
    'foundation': 'garrison_part_0000',
    'healthy': ['garrison_part_0001', 'garrison_part_0004',
                'garrison_part_0005', 'garrison_part_0006'],
    'ruins': 'garrison_part_0002',
    'damaged': 'garrison_part_0003',
}
CONSTRUCTION = [f'construct_{stage:02}' for stage in range(0, 100, 5)]
SUPPORTED_STATES = frozenset([*CONSTRUCTION, 'healthy', 'preview', 'targeting',
                              'ruins', *(f'damage_{i}' for i in range(1, 6))])


def lp(raw, offset):
    return rc.read_lp_string(raw, offset)


def selector(chunk):
    name, at = lp(chunk.payload, 0)
    count = struct.unpack_from('<I', chunk.payload, at)[0]
    at += 4
    parts = []
    for _ in range(count):
        part, at = lp(chunk.payload, at)
        parts.append(part)
    assert at == len(chunk.payload)
    return name, parts


def conditions(chunk):
    raw = chunk.payload
    count = struct.unpack_from('<I', raw)[0]
    at = 4
    result = []
    for _ in range(count):
        opcode, flag, one = struct.unpack_from('<IBI', raw, at)
        at += 9
        prop, at = lp(raw, at)
        value, at = lp(raw, at)
        result.append([opcode, flag, one, prop, value])
    assert at == len(raw)
    return result


def model_table(raw):
    doc = rc.parse(raw)
    model = next(c for c in doc.roots if c.tag == b'MODL')
    bp = next(c for c in model.children if c.tag == b'MSBP')
    children = bp.children
    sets = [c for c in children if c.tag == b'MSD ' and len(c.payload) > 4]
    tests = [c for c in children if c.tag == b'CNBP']
    return doc, sets, tests, [dict(selector=selector(s), conditions=conditions(t)) for s, t in zip(sets, tests)]


def pack_selector(name, members):
    return rc.lp_string(name) + struct.pack('<I', len(members)) + b''.join(
        rc.lp_string(member) for member in members)


def pack_conditions(states):
    return struct.pack('<I', len(states)) + b''.join(
        struct.pack('<IBI', 2, 0, 1) + rc.lp_string('life_cycle_state') + rc.lp_string(state)
        for state in states)


def validate_conditions(table):
    """Reject predicates this repair has not qualified against native stock arrays."""
    for row in table:
        for condition in row['conditions']:
            if (not isinstance(condition, list) or len(condition) != 5 or
                    condition[:4] != [2, 0, 1, 'life_cycle_state'] or
                    condition[4] not in SUPPORTED_STATES):
                raise ValueError(f'Unsupported landmark selector condition: {condition!r}')


def visible(table, state):
    validate_conditions(table)
    if state not in SUPPORTED_STATES:
        raise ValueError(f'Unsupported requested state: {state}')
    return sorted({part for row in table for part in row['selector'][1]
                   if [2, 0, 1, 'life_cycle_state', state] in row['conditions']})


def repair(raw):
    doc, sets, tests, old = model_table(raw)
    validate_conditions(old)
    assert len(sets) == len(tests) == 6
    assert [r['selector'][0] for r in old] == [
        'sel_construct_00', 'sel_construct_20', 'sel_construct_40',
        'sel_construct_60', 'sel_heavy_damage', 'sel_ruins']
    assert [r['selector'][1] for r in old] == [
        [PARTS['foundation']], PARTS['healthy'], [], [],
        [PARTS['damaged']], [PARTS['ruins']]]
    assert visible(old, 'healthy') == sorted([PARTS['foundation'], *PARTS['healthy']])
    assert visible(old, 'ruins') == [PARTS['ruins']]
    # The retained owner graph references these exact native selector names.
    # Keep the Garrison construction stages, then hand completed/damaged states
    # to dedicated owner-compatible selectors with no duplicate visible part.
    desired = [
        ('sel_construct_00', [PARTS['foundation']], CONSTRUCTION + ['preview', 'targeting']),
        ('sel_construct_20', PARTS['healthy'], CONSTRUCTION[4:] + ['preview', 'targeting']),
        ('sel_healthy', [PARTS['foundation'], *PARTS['healthy']],
         ['healthy', 'damage_1', 'damage_2']),
        ('sel_construct_60', [], [row[4] for row in old[3]['conditions']]),
        ('sel_damaged', [PARTS['foundation'], PARTS['damaged']],
         ['damage_3', 'damage_4', 'damage_5']),
        ('sel_ruins', [PARTS['ruins']], ['ruins']),
    ]
    edits = {}
    for (name, members, states), selected, condition in zip(desired, sets, tests):
        selected_bytes = pack_selector(name, members)
        condition_bytes = pack_conditions(states)
        if selected_bytes != selected.payload:
            edits[selected.offset] = selected_bytes
        if condition_bytes != condition.payload:
            edits[condition.offset] = condition_bytes
    result = rc.rebuild(doc, lambda chunk: edits.get(chunk.offset))
    _, new_sets, new_tests, new = model_table(result)
    validate_conditions(new)
    assert [r['selector'][0] for r in new] == [r[0] for r in desired]
    for stage in range(0, 100, 5):
        state = f'construct_{stage:02}'
        expected = [PARTS['foundation']] + (PARTS['healthy'] if stage >= 20 else [])
        assert visible(new, state) == sorted(expected), (state, visible(new, state))
    for state in ['healthy', 'damage_1', 'damage_2']:
        assert visible(new, state) == sorted([PARTS['foundation'], *PARTS['healthy']]), state
    for state in ['damage_3', 'damage_4', 'damage_5']:
        assert visible(new, state) == sorted([PARTS['foundation'], PARTS['damaged']]), state
    assert visible(new, 'ruins') == [PARTS['ruins']]
    for state in ['preview', 'targeting']:
        assert visible(new, state) == sorted([PARTS['foundation'], *PARTS['healthy']]), state
    before_leaves = [c for c in rc.walk(doc.roots) if not c.children]
    after_leaves = [c for c in rc.walk(rc.parse(result).roots) if not c.children]
    assert len(before_leaves) == len(after_leaves)
    changed = []
    for a, b in zip(before_leaves, after_leaves):
        assert (a.tag, a.decoded_name) == (b.tag, b.decoded_name)
        if a.payload != b.payload:
            assert a.tag in (b'MSD ', b'CNBP')
            changed.append(a.tag.decode('ascii').strip())
    assert changed and len(new_sets) == len(new_tests) == 6
    member_before = sorted({p for r in old for p in r['selector'][1]})
    member_after = sorted({p for r in new for p in r['selector'][1]})
    assert member_before == member_after
    return result, {'native_selector_names': [r['selector'][0] for r in new],
                    'changed_leaf_types': sorted(set(changed)),
                    'all_nonselector_leaf_payloads_byte_identical': True,
                    'geometry_members_before_after_identical': True,
                    'state_truth': {state: visible(new, state) for state in
                                    [*CONSTRUCTION, 'preview', 'targeting', 'healthy',
                                     *(f'damage_{i}' for i in range(1, 6)), 'ruins']}}


def regression(old_raw, repaired_raw):
    old = model_table(old_raw)[3]
    new = model_table(repaired_raw)[3]
    before = {row['selector'][0]: row['selector'][1] for row in old}
    after = {row['selector'][0]: row['selector'][1] for row in new}
    assert 'sel_healthy' not in before
    assert after['sel_healthy'] == [PARTS['foundation'], *PARTS['healthy']]
    assert after['sel_damaged'] == [PARTS['foundation'], PARTS['damaged']]
    assert after['sel_ruins'] == [PARTS['ruins']]
    invalid_cases = []
    for index, replacement in ((0, 3), (1, 1), (2, 0),
                               (3, 'unknown_property'), (4, 'unqualified_state')):
        invalid = copy.deepcopy(new)
        invalid[0]['conditions'][0][index] = replacement
        try:
            visible(invalid, 'healthy')
        except ValueError:
            invalid_cases.append(['opcode', 'flag', 'one', 'property', 'state'][index])
        else:
            raise AssertionError(f'Unsupported {index} predicate was accepted')
    try:
        visible(new, 'unqualified_state')
    except ValueError:
        invalid_cases.append('requested_state')
    else:
        raise AssertionError('Unsupported requested state was accepted')
    return {'baseline_missing_named_healthy': True,
            'repaired_named_healthy_full_compound': True,
            'unsupported_predicates_rejected': invalid_cases}


def copied(source, target, expected=None):
    source = Path(source)
    target = Path(target)
    assert source.is_file(), source
    original = sha(source)
    if expected is not None:
        assert original == expected, source
    assert any(target.resolve().is_relative_to(root.resolve()) for root in
               (ART, EXPORT, RECIPES, OUT)), target
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copy2(source, target)
    assert sha(target) == sha(source) == original
    return {'source': str(source), 'source_sha256': original,
            'copy': str(target), 'copy_sha256': sha(target), 'bytes': target.stat().st_size}


def editable_references(rows):
    """Pin byte-identical editable art and visual previews for selector-only work."""
    artifacts = {}
    for key in ('imperial_citadel', 'resistance_hq'):
        handoff = read(OUT.parent/'castle_next/landmarks'/key/'handoff.json')
        source_dir = ROOT/'art/authoring/castle_next/landmarks'/key
        assert Path(handoff['source_blend']) == source_dir/(key+'.blend')
        sources = [copied(source_dir/(key+'.blend'), ART/'landmarks'/key/(key+'.blend'),
                          handoff['source_blend_sha256'])]
        sources += [copied(source_dir/name, ART/'landmarks'/key/name)
                    for name in ('albedo.png', 'normal.png', 'roughness.png',
                                 'metalness.png', 'pattern.png')]
        exports = [copied(Path(handoff['export_directory'])/name,
                          EXPORT/'landmarks'/key/name, hash_value)
                   for name, hash_value in sorted(handoff['export_sha256'].items())]
        preview_state = {'healthy': 'healthy', 'damage_3': 'heavy_damage',
                         'ruins': 'ruins'}
        previews = []
        model_row = next(row for row in rows if f'/{key}/' in row['member'])
        for state, old_directory in preview_state.items():
            assert model_row['proof']['state_truth'][state], (key, state)
            src = OUT.parent/'castle_next/landmarks'/key/old_directory/'game-textured.png'
            dst = OUT/'landmarks/previews'/key/(state+'.png')
            entry = copied(src, dst)
            entry['state'] = state
            entry['selector_members'] = model_row['proof']['state_truth'][state]
            entry['visual_gate'] = 'source preview only; native match pending'
            previews.append(entry)
        artifacts[key] = {'editable_sources': sources, 'exports': exports,
                          'previews': previews}
    recipe = {'schema': 'ccp.release051.landmark-selector-repair/v1',
              'status': 'source_art_byte_identical',
              'description': 'The existing editable compound supplies all seven geometry parts. Only model selector and life-cycle predicate tables change.',
              'script': str(ROOT/'tools/release_051/landmark_visibility.py'),
              'baseline_sga': str(BASELINE), 'baseline_sha256': sha(BASELINE),
              'payloads': [{k: row[k] for k in ('member', 'file', 'sha256', 'bytes')} for row in rows],
              'states': rows[0]['proof']['state_truth'], 'artifacts': artifacts,
              'native_runtime': 'pending fresh imported match'}
    write(RECIPES/'landmarks/selector-repair.json', recipe)
    return {'recipe': str(RECIPES/'landmarks/selector-repair.json'),
            'recipe_sha256': sha(RECIPES/'landmarks/selector-repair.json'),
            'artifacts': artifacts}


def inspect():
    guarded()
    assert sha(BASELINE) == '78b90561306f6874872b5f88a5f82c3354e14fceebdf52cf0f0ffba28cbf1e80'
    report = []
    for member in MEMBERS:
        source = OUT/'landmarks'/'baseline'/member
        if not source.exists():
            import subprocess
            source.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(ARCH), 'extract-member', str(BASELINE), member, str(source)], check=True,
                           capture_output=True, text=True)
        raw = source.read_bytes()
        _, sets, tests, table = model_table(raw)
        report.append(dict(member=member, sha256=sha(source), bytes=len(raw),
                           sets=len(sets), tests=len(tests), table=table))
    stock_root = OUT.parent/'castle_next/native-stock/official/art/civilizations'
    for relative in ('chinese/structures/wonder_greatwall_mp/wonder_greatwall_mp.rgm',
                     'chinese_ha_01/structures/landmark_2b/chi_ha_01_landmark_b_age02/chi_ha_01_landmark_b_age02.rgm'):
        source = stock_root/relative
        raw = source.read_bytes()
        _, sets, tests, table = model_table(raw)
        report.append(dict(member='official/'+relative, sha256=sha(source), bytes=len(raw),
                           sets=len(sets), tests=len(tests), table=table))
    write(OUT/'landmarks'/'selector-inspection.json', {'models': report})
    print('LANDMARK_SELECTOR_INSPECTION', len(report))


def archive_readback(rows):
    stage = OUT/'landmarks'/'validation'
    stage.mkdir(parents=True, exist_ok=True)
    listing = stage/'members.txt'
    listing.write_text(''.join(f"{row['member']}={row['file']}\n" for row in rows), encoding='utf-8')
    candidate = stage/'landmarks-051-static.sga'
    if not candidate.exists():
        result = subprocess.run([str(ARCH), 'set-members', str(BASELINE), str(listing), str(candidate)],
                                capture_output=True, text=True, check=True)
        write(stage/'set-members.json', json.loads(result.stdout))
    def listing_for(path):
        result = subprocess.run([str(ARCH), 'list', str(path), '--verify'],
                                capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    before = listing_for(BASELINE)
    after = listing_for(candidate)
    expected = {row['member'] for row in rows}
    first = {row['path']: row for row in before['members']}
    second = {row['path']: row for row in after['members']}
    assert first.keys() == second.keys() and len(first) == 809
    assert before['archive']['name'] == after['archive']['name'] == 'b7fcea91257b408fb9e8ae4d8bc402e1'
    assert all(first[name]['crc'] == second[name]['crc'] and first[name]['size'] == second[name]['size']
               for name in first.keys()-expected)
    assert all(first[name]['crc'] != second[name]['crc'] for name in expected)
    verify = after['archive']['verification']
    assert verify['verified'] and verify['checked_files'] == 809
    assert not verify['crc_mismatches'] and not verify['sha1_mismatches'] and not verify['unhashed_files']
    for row in rows:
        target = stage/'readback'/row['member']
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(ARCH), 'extract-member', str(candidate), row['member'], str(target)],
                           capture_output=True, text=True, check=True)
        assert sha(target) == row['sha256'] and target.stat().st_size == row['bytes']
    neighbors = []
    for row in rows:
        for suffix in ('.rgo', '.rrgeom', '.rrmaterial'):
            member = row['member'].removesuffix('.rgm') + suffix
            frozen = stage/'baseline-neighbors'/member
            current = stage/'readback'/member
            for archive, path in ((BASELINE, frozen), (candidate, current)):
                if not path.exists():
                    path.parent.mkdir(parents=True, exist_ok=True)
                    subprocess.run([str(ARCH), 'extract-member', str(archive), member, str(path)],
                                   capture_output=True, text=True, check=True)
            assert sha(frozen) == sha(current), member
            neighbors.append({'member': member, 'sha256': sha(current),
                              'bytes': current.stat().st_size})
    return {'archive': str(candidate), 'sha256': sha(candidate), 'bytes': candidate.stat().st_size,
            'member_count': len(second), 'identity': after['archive']['name'],
            'archive_verification': after['archive']['verification'],
            'payloads_read_back_exact': True, 'untouched_member_crc_and_size_identical': True,
            'native_owners_geometry_and_materials_read_back_exact': neighbors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive-readback', action='store_true')
    args = parser.parse_args()
    guarded()
    assert sha(BASELINE) == '78b90561306f6874872b5f88a5f82c3354e14fceebdf52cf0f0ffba28cbf1e80'
    rows = []
    for member in MEMBERS:
        source = OUT/'landmarks'/'baseline'/member
        if not source.exists():
            import subprocess
            source.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(ARCH), 'extract-member', str(BASELINE), member, str(source)],
                           check=True, capture_output=True, text=True)
        assert sha(source) == BASELINE_HASHES[member], member
        owner_member = member[:-3] + 'rgo'
        owner = OUT/'landmarks'/'baseline'/owner_member
        if not owner.exists():
            import subprocess
            owner.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run([str(ARCH), 'extract-member', str(BASELINE), owner_member, str(owner)],
                           check=True, capture_output=True, text=True)
        owner_raw = owner.read_bytes()
        native_selector_names = ['sel_healthy', 'sel_damaged', 'sel_ruins']
        owner_leaves = [c for c in rc.walk(rc.parse(owner_raw).roots) if not c.children]
        owner_references = {name: sorted({c.tag.decode('ascii') for c in owner_leaves
                                          if name.encode('ascii') in c.payload})
                            for name in native_selector_names}
        assert all(owner_references.values()), owner_references
        patched, proof = repair(source.read_bytes())
        proof['regression'] = regression(source.read_bytes(), patched)
        target = OUT/'landmarks'/'payload'/member
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(patched)
        assert target.read_bytes() == patched
        assert sha(target) != sha(source)
        rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                     'bytes': target.stat().st_size, 'baseline_sha256': sha(source),
                     'retained_native_owner': {'member': owner_member, 'sha256': sha(owner),
                                               'selector_reference_chunks': owner_references},
                     'proof': proof})
    assert rows[0]['proof']['state_truth'] == rows[1]['proof']['state_truth'] == rows[2]['proof']['state_truth']
    receipt = {'schema': 'ccp.release051.landmark-visibility/v1',
               'status': 'passed_static_model_readback', 'baseline_sga_sha256': sha(BASELINE),
               'static_defect': '0.5.0 model conversion omitted sel_healthy while the exact stock-owner model exposes that named selector and the retained ACTN action graph references it; the repaired model also maps damaged/ruin geometry to named native states',
               'runtime_causality': 'strong inference from completed-state disappearance and missing healthy selector; stock owners vary in other selector names, so fresh match remains necessary',
               'payloads': [{k: row[k] for k in ('member', 'file', 'sha256', 'bytes')} for row in rows],
               'proofs': [{k: row[k] for k in ('member', 'baseline_sha256', 'retained_native_owner', 'proof')} for row in rows],
               'native_match': 'pending; exact completed-state rendering requires fresh imported match'}
    if args.archive_readback:
        receipt['archive_readback'] = archive_readback(rows)
    receipt['editable_references'] = editable_references(rows)
    write(OUT/'landmarks'/'receipt.json', receipt)
    print('LANDMARK_051_STATIC_PASS', len(rows))


if __name__ == '__main__':
    main()

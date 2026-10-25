"""Trace retained native death, ruins, selection, and repair graph exactly."""
from __future__ import annotations

import sys
from pathlib import Path

from common import ROOT, OUT, guarded, read, sha, write
from bindings import ACTORS, STEMS, WORK
from lifecycle import _pairs, _selector, _conditions

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native
from garrison_shared import relic_chunky as rc, rgd


def run():
    guarded()
    media = read(WORK / 'landmark-media.json')
    native_source = read(read(OUT / 'native-source/current.json')['receipt'])
    assert media['status'] == native_source['status'] == 'passed'
    source_run = Path(read(OUT / 'native-source/current.json')['receipt']).parent
    reports = []
    for key, actor_names in ACTORS.items():
        stem = STEMS[key]
        model = WORK / 'payload' / (stem + '.rgm')
        _, pairs = _pairs(model.read_bytes())
        selectors = [(_selector(s), _conditions(c)) for s, c in pairs]
        healthy = {part for (name, parts), predicates in selectors
                   if any(row[-1] == 'healthy' for row in predicates) for part in parts}
        ruins = {part for (name, parts), predicates in selectors
                 if any(row[-1] == 'ruins' for row in predicates) for part in parts}
        assert healthy == {'garrison_part_0000', 'garrison_part_0001'}
        assert ruins == {'garrison_part_0002'}
        rgo_path = Path(media['native_rgo'][stem]['file'])
        assert sha(rgo_path) == media['native_rgo'][stem]['sha256']
        behaviors = {c.decoded_name: c for c in rc.walk(rc.load(rgo_path).roots) if c.tag == b'BVBP'}
        actions = {}
        for name in ('bhv_set_lifecycle_ruins', 'bhv_collapse_ruins', 'bhv_repair_to_healthy'):
            assert name in behaviors
            payloads = [c.payload for c in behaviors[name].children if c.tag == b'BBPD']
            assert len(payloads) == 1
            actions[name] = payloads[0].hex()
        assert b'set_lifecycle_ruins' in bytes.fromhex(actions['bhv_set_lifecycle_ruins'])
        assert b'act_collapse_to_ruins' in bytes.fromhex(actions['bhv_collapse_ruins'])
        assert b'act_repair_to_healthy' in bytes.fromhex(actions['bhv_repair_to_healthy'])
        actors = []
        for actor in actor_names:
            member = f'attrib/ebps/vietnam/{actor}.rgd'
            before = source_run / 'baseline' / member
            after = source_run / 'payload' / member
            fields = dict(rgd.flatten(rgd.read(after.read_bytes()).nodes))
            for variant in ('default', 'campaign'):
                prefix = variant + '/'
                expect = {'health_ext/delete_when_dead': False, 'health_ext/death_seconds': -1.0,
                          'health_ext/can_repair': True,
                          'construction_ext/destroy_stamps': True,
                          'ui_ext/selection_method': 'obb_adjusted_to_terrain',
                          'ui_ext/static_selection_bounds': False,
                          'site_ext/footprint_scale/x': 8.0,
                          'site_ext/footprint_scale/y': 8.0}
                assert all(fields[prefix + path].value == value for path, value in expect.items())
                interactions = [node.value for path, node in fields.items()
                                if path.startswith(prefix + 'interactive_object_ext/') and
                                path.endswith('/interaction_type')]
                assert 'repair' in interactions
            proof = native_source['compiled_proofs'][member]
            assert proof['all_other_compiled_fields_byte_identical']
            actors.append({'name': actor, 'baseline_sha256': sha(before),
                           'new_sha256': sha(after),
                           'default_campaign_native_flags': expect,
                           'repair_interaction_present': True,
                           'only_visual_binding_compiled_edits': proof['edits']})
        handoff = read(OUT / 'landmarks' / key / 'handoff.json')
        reports.append({'landmark': key, 'actors': actors, 'stock_rgo_sha256': sha(rgo_path),
                        'stock_rgo_actions': actions,
                        'custom_rgm_healthy_parts': sorted(healthy),
                        'custom_rgm_ruin_parts': sorted(ruins),
                        'authored_ruin_visual_bounds': handoff['ruin_bounds'],
                        'selection_footprint_remains_8_by_8': True,
                        'selection_method': 'obb_adjusted_to_terrain',
                        'static_selection_bounds': False,
                        'native_stamp_lifetime_and_click_bounds': 'requires fresh match',
                        'repair_after_destruction': 'requires fresh match'})
    result = {'status': 'passed_static_native_graph', 'reports': reports,
              'finding': 'The private stamp points to a custom RGM ruins selector, and the byte-identical stock RGO '
                         'has collapse, set_lifecycle_ruins and repair actions. All consuming actors retain nondeleting '
                         'repairable health state and a repair interaction in default and campaign branches.',
              'limit': 'destroy_stamps=True is inherited; its post-death attachment lifetime and clickable bounds '
                       'are not proven without a client match.'}
    write(OUT / 'landmark-lifecycle-contract.json', result)
    return result


if __name__ == '__main__':
    run()

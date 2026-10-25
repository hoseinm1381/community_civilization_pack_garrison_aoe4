"""Install twelve authored geometries into exact official Chinese native owners."""
from __future__ import annotations

import sys
from pathlib import Path

from common import ROOT, OUT, guarded, read, sha, write
from bindings import WORK, private_building_lists_and_stamps, private_market_actor

sys.path.insert(0, str(ROOT / 'tools/release_010'))
import integration as native

HANDOFF = ROOT / 'art/recipes/release_040/buildings-source.json'


def put(member, raw, rows):
    target = WORK / 'payload' / member
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    rows.append({'member': member, 'file': str(target), 'sha256': sha(target),
                 'bytes': target.stat().st_size})


def assemble():
    guarded()
    native.CACHEWORK = OUT / 'inventory'
    handoff = read(HANDOFF)
    assert handoff['status'] == 'source_export_ready_for_integration'
    assert len(handoff['models']) == 12
    rows, reports = [], []
    for row in handoff['models']:
        original = row['stock_model_stem']
        final = row['private_model_stem']
        assert final == f'art/scenario/cc040/{row["family"]}_age0{row["age"]}/model'
        geometry = Path(row['export_geometry'])
        assert sha(geometry) == row['export_geometry_sha256']
        assert sha(row['editable_blend']) == row['editable_blend_sha256']
        assert sha(row['projection']) == row['projection_sha256']
        assert sha(row['donor_manifest']) == row['donor_manifest_sha256']
        assert sha(row['donor_geometry']['cache_path']) == row['donor_geometry']['sha256']
        assert sha(row['donor_model']['cache_path']) == row['donor_model']['sha256']
        assert sha(row['donor_material']['cache_path']) == row['donor_material']['sha256']
        assert sha(native.stock(original + '.rgm')) == row['donor_model']['sha256']
        own = []
        put(final + '.rgm', native.rebase_model(Path(row['donor_model']['cache_path']).read_bytes(), final), own)
        rgo = native.stock(original + '.rgo')
        put(final + '.rgo', rgo.read_bytes(), own)
        put(final + '.rrgeom', geometry.read_bytes(), own)
        put(final + '.rrmaterial', Path(row['donor_material']['cache_path']).read_bytes(), own)
        reports.append({'key': row['name'], 'family': row['family'], 'age': row['age'],
                        'model': final, 'donor': original, 'native_rgo_sha256': sha(rgo),
                        'selector_sets': row['selector_sets'], 'healthy_selectors': row['healthy_selector_names'],
                        'geometry_audit': row['native_audit'], 'payloads': own,
                        'runtime_culling': 'unverified'})
        rows.extend(own)
    lists = private_building_lists_and_stamps()
    actor = private_market_actor()
    rows.extend(lists['payloads'])
    rows.append(actor['payload'])
    assert len({r['member'] for r in rows}) == len(rows)
    result = {'status': 'passed', 'handoff_sha256': sha(HANDOFF), 'models': reports,
              'payloads': rows, 'native_binding': lists, 'private_market_actor': actor,
              'native_runtime': 'unverified'}
    write(WORK / 'building-media.json', result)
    return result


if __name__ == '__main__':
    assemble()

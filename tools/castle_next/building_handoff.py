"""Freeze the five ordinary Castle building authoring inputs for integration.

This validates source/readback receipts only. It does not cook, package, or
claim Content Editor import or native-match appearance.
"""
from __future__ import annotations

from pathlib import Path

from common import OUT, ROOT, guarded, read, sha, write

BASE = ROOT / 'output/castle_next/buildings'
RECIPE = ROOT / 'art/recipes/castle_next/buildings-source.json'
JOBS = (('monastery', 3), ('monastery', 4), ('siege_workshop', 3),
        ('siege_workshop', 4), ('keep', 3))


def file_hash(path, expected):
    path = Path(path)
    assert path.is_file(), path
    actual = sha(path)
    assert actual == expected, (path, actual, expected)
    return str(path)


def main():
    guarded()
    donors_path = OUT / 'donors/donor-manifest.json'
    donors = read(donors_path)['donors']
    models = read(BASE / 'model-validation.json')
    details = read(BASE / 'details/details-validation.json')
    previews = read(BASE / 'previews/previews.json')
    native = read(BASE / 'native-byte-audit.json')
    shape = read(BASE / 'shape-preflight.json')
    assert models['status'] == 'source_ready_for_integration'
    assert details['status'] == 'authoring_export_only'
    assert previews['status'] == native['status'] == 'passed'
    assert len(models['models']) == len(details['models']) == len(previews['models']) == len(native['models']) == 5
    assert len(shape['models']) == 5
    rows = []
    for family, age in JOBS:
        key = f'{family}{age:02}'
        model = next(r for r in models['models'] if (r['family'], r['age']) == (family, age))
        detail = next(r for r in details['models'] if (r['family'], r['age']) == (family, age))
        preview = next(r for r in previews['models'] if r['key'] == key)
        audit = next(r for r in native['models'] if r['name'] == model['name'])
        assert audit['uv_selector_owner_bytes_preserved'] and audit['index_chunks_byte_identical']
        assert model['nonselector_leaf_chunks_byte_identical'] and model['marker_rgo_unchanged']
        file_hash(model['donor_manifest'], sha(Path(model['donor_manifest'])))
        file_hash(model['native_geometry'], model['native_geometry_sha256'])
        file_hash(model['native_model'], model['native_model_sha256'])
        file_hash(model['donor_blend'], model['donor_blend_sha256'])
        file_hash(model['editable_blend'], model['editable_blend_sha256'])
        file_hash(detail['source_blend'], detail['source_blend_sha256'])
        export = Path(detail['export_dir'])
        file_hash(export / 'building.json', detail['manifest_sha256'])
        file_hash(export / 'model.fbx', detail['fbx_sha256'])
        for label, digest in detail['textures'].items():
            file_hash(export / f'{label}.png', digest)
        for state in ('stock', 'remodel', 'composite'):
            row = preview['states'][state]
            for image, digest in row['images'].items():
                file_hash(BASE / 'previews' / key / state / image, digest)
        contacts = detail['contact_checks']['interfaces']
        assert all(-.18 <= c['gap_m'] <= .08 for c in contacts), (key, contacts)
        stock_tris = preview['stock_selector']['healthy_triangle_count']
        native_tris = preview['remodel_selector']['healthy_triangle_count']
        detail_tris = sum(group['triangles'] for group in detail['geometry'])
        assert native_tris + detail_tris <= stock_tris * 1.10, (key, stock_tris, native_tris, detail_tris)
        if family == 'monastery':
            assert model['hidden_native_selector_names'] and model['omitted_roof_debris']
        else:
            assert not model['hidden_native_selector_names']
        rows.append({
            'key': key,
            'private_model_stem': model['private_model_stem'],
            'stock_model_stem': model['stock_model_stem'],
            'donor_decoded_manifest': model['donor_manifest'],
            'donor_model_sha256': model['donor_model_sha256'],
            'native_model': model['native_model'],
            'native_model_sha256': model['native_model_sha256'],
            'native_geometry': model['native_geometry'],
            'native_geometry_sha256': model['native_geometry_sha256'],
            'donor_blend': model['donor_blend'],
            'editable_blend': model['editable_blend'],
            'detail_source_blend': detail['source_blend'],
            'detail_export_dir': detail['export_dir'],
            'detail_fbx_sha256': detail['fbx_sha256'],
            'detail_material_textures': detail['textures'],
            'healthy_stock_triangles': stock_tris,
            'healthy_remodel_native_triangles': native_tris,
            'detail_triangles': detail_tris,
            'hidden_native_selector_names': model['hidden_native_selector_names'],
            'intersecting_native_roof_trim_names': model['intersecting_native_roof_trim_names'],
            'omitted_roof_debris': model['omitted_roof_debris'],
            'selector_changes': model['selector_changes'],
            'contact_checks': detail['contact_checks'],
            'owner_uv_index_byte_audit': audit,
            'preview_dir': str(BASE / 'previews' / key),
            'preview_proof': preview['proof'],
        })
    write(RECIPE, {
        'schema': 'community-civilization-pack/castle-next-ordinary-building-handoff/v1',
        'status': 'passed',
        'stock_donor_manifest': str(donors_path),
        'stock_donor_manifest_sha256': sha(donors_path),
        'source_reference': 'https://whc.unesco.org/en/list/1732',
        'scope': 'five ordinary Castle models; keep03 shared by both Vietnamese keep actor variants',
        'models': rows,
        'limits': 'Offline export and Garrison preflight only; root handles native cook, archive, import and match gates.',
    })
    print('CASTLE_BUILDING_HANDOFF_PASSED', len(rows), sha(RECIPE))


if __name__ == '__main__':
    main()

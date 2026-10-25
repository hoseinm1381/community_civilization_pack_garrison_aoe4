"""Bind final offline contact and textured QA to the 0.4.0 art inputs."""
from __future__ import annotations

from pathlib import Path

from common import ROOT, OUT, guarded, read, sha, write

DETAIL_HANDOFF = ROOT / 'art/recipes/release_040/building-details-source.json'
BUILDING_HANDOFF = ROOT / 'art/recipes/release_040/buildings-source.json'
CONTACT = OUT / 'buildings/details/contact-audit.json'
TEXTURED = OUT / 'buildings/details/textured-composite-validation.json'
RESULT = OUT / 'buildings/details/art-qa-binding.json'


def verify():
    guarded()
    details, buildings = read(DETAIL_HANDOFF), read(BUILDING_HANDOFF)
    contact, textured = read(CONTACT), read(TEXTURED)
    assert contact['schema'] == 'ccp.release040.building-detail-contact/v1'
    assert contact['status'] == 'passed' and len(contact['models']) == 12
    assert textured['schema'] == 'ccp.release040.building-textured-composite/v1'
    assert textured['status'] == 'offline_preview_only' and len(textured['images']) == 8
    detail_rows = {(r['family'], r['age']): r for r in details['models']}
    building_rows = {(r['family'], r['age']): r for r in buildings['models']}
    assert len(detail_rows) == len(building_rows) == 12
    assert {(r['family'], r['age']) for r in contact['models']} == set(detail_rows)
    exports, blends = {}, {}
    for key, row in detail_rows.items():
        folder = Path(row['export_directory'])
        actual = {p.name: sha(p) for p in folder.iterdir() if p.is_file()}
        assert actual == row['export_sha256'], key
        assert sha(row['editable_blend']) == row['editable_blend_sha256'], key
        exports[f'{key[0]}_age0{key[1]}'] = actual
        blends[f'{key[0]}_age0{key[1]}'] = row['editable_blend_sha256']
    for row in contact['models']:
        key = (row['family'], row['age'])
        assert row['model_translation'] == [0, 0, 0], key
        assert row['roof_support_contacts_passed'] and row['decorative_joints_passed'], key
        assert row['minimum_support_roof_overlap_m'] >= contact['limits']['contact_overlap_m'][0], key
        assert abs(row['footing_vs_adjacent_stock_base_m']) <= contact['limits']['maximum_footing_difference_m'], key
    seen, previews = set(), []
    for row in textured['images']:
        key = (row['family'], row['age'])
        assert row['age'] == 2 and row['view'] in ('game', 'facade')
        assert (key, row['view']) not in seen
        seen.add((key, row['view']))
        assert row['offline_only'] is True
        assert row['detail_blend'] == detail_rows[key]['editable_blend']
        assert row['detail_blend_sha256'] == detail_rows[key]['editable_blend_sha256']
        assert row['donor_blend'] == building_rows[key]['editable_blend']
        assert row['donor_blend_sha256'] == building_rows[key]['editable_blend_sha256']
        assert sha(row['detail_blend']) == row['detail_blend_sha256']
        assert sha(row['donor_blend']) == row['donor_blend_sha256']
        assert sha(row['image']) == row['image_sha256']
        previews.append({'family': key[0], 'age': key[1], 'view': row['view'],
                         'image_sha256': row['image_sha256']})
    assert len(seen) == 8
    result = {'status': 'passed_offline_qa', 'detail_handoff_sha256': sha(DETAIL_HANDOFF),
              'building_handoff_sha256': sha(BUILDING_HANDOFF),
              'contact_audit_sha256': sha(CONTACT), 'textured_preview_sha256': sha(TEXTURED),
              'detail_export_sha256': exports, 'detail_blend_sha256': blends,
              'textured_images': previews, 'native_terrain_contact': 'pending fresh match'}
    write(RESULT, result)
    return result


if __name__ == '__main__':
    verify()

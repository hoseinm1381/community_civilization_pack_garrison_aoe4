"""Compare pinned Chinese spear bind records to the admitted native prototype."""
from pathlib import Path
import json
from common import OUT, guard, read, sha, write


def pinned(record, path_key='path', hash_key='sha256'):
    path = Path(record[path_key])
    if sha(path) != record[hash_key]:
        raise RuntimeError(f'Pinned comparison input changed: {path}')
    return read(path)


def compare(left, right, fields):
    if len(left) != len(right):
        return {'equal': False, 'left_count': len(left), 'right_count': len(right),
                'differences': ['record count differs']}
    differences = []
    for index, (a, b) in enumerate(zip(left, right)):
        for field in fields:
            # Complete list/dictionary equality includes every transform component.
            if field not in a or field not in b or a[field] != b[field]:
                differences.append({'index': index, 'field': field})
    return {'equal': not differences, 'left_count': len(left),
            'right_count': len(right), 'differences': differences}


def main():
    guard()
    donor = read(OUT/'pilots/pilot-decodes.json')['pilots']['spear2']
    prototype_record = read(OUT/'qualification/archer-spearman-rig-comparison.json')['admitted_prototype_manifest']
    native = pinned(donor, 'manifest', 'manifest_sha256')
    prototype = pinned(prototype_record)
    a, b = native['skeleton'], prototype['skeleton']
    bones = compare(a['bones'], b['bones'], ('name', 'parent_index', 'parent_name',
                    'local_reference_transform', 'global_reference_transform'))
    palettes = []
    palette_counts_equal = len(a['skin_palettes']) == len(b['skin_palettes'])
    for left, right in zip(a['skin_palettes'], b['skin_palettes']):
        palettes.append({
            'bones': compare(left['bones'], right['bones'], ('name', 'palette_index',
                'skeleton_index', 'parent_index', 'global_reference_transform', 'inverse_bind_transform')),
            'lod_bindings': compare(left['lod_palettes'], right['lod_palettes'],
                                    ('material', 'effect', 'skin_indices')),
            'donor_lod_names': [x['name'] for x in left['lod_palettes']],
            'prototype_lod_names': [x['name'] for x in right['lod_palettes']],
            'complete_lod_records_equal': left['lod_palettes'] == right['lod_palettes']})
    exact = (bones['equal'] and palette_counts_equal and bool(palettes)
             and all(p['bones']['equal'] and p['lod_bindings']['equal'] for p in palettes))
    report = {
        'schema': 'ccp-060-spearman-prototype-comparison/v1',
        'status': 'exact-compared-bind-records' if exact else 'bind-records-differ',
        'donor': {'path': donor['manifest'], 'sha256': donor['manifest_sha256'],
                  'stock_model': donor['stock_model']['logical_path']},
        'prototype': prototype_record,
        'bones': bones, 'palette_counts_equal': palette_counts_equal, 'palettes': palettes,
        'boundary': 'Read-only compatibility evidence; geometry-group names remain donor-specific and are separately recorded. No validator bypass, export, cook, animation-owner replacement or native-game qualification.'}
    write(OUT/'qualification/spearman-prototype-comparison.json', report)
    print(json.dumps({'status': report['status'], 'bone_count': bones['left_count'],
                      'palette_count': len(palettes)}))


if __name__ == '__main__':
    main()

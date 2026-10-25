"""Assemble private 0.2.0 models and exact native stamp copies from frozen art."""
import hashlib
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path
from common import ARCH, OUT, ROOT, guarded, read, sha, write
from inventory import EXPECTED_STAMPS, native
from integrate import MODEL_PREFIX, PREFIX, STAMP_TARGETS, WORK, payload
from garrison_shared import relic_chunky as rc, model_variants as mv
from garrison_shared import building_project as bp

sys.dont_write_bytecode = True
native.CACHEWORK = OUT / 'inventory'


def assert_cook_member(cooked, member):
    """Compare a used unpacked artifact with a fresh extraction from its hashed SGA."""
    archive = Path(cooked['cook']['archive'])
    assert sha(archive) == cooked['cook']['sha256']
    present = Path(cooked['readback']) / member
    assert present.is_file(), member
    with tempfile.TemporaryDirectory(dir=WORK) as temporary:
        extracted = Path(temporary) / Path(member).name
        result = subprocess.run([str(ARCH), 'extract-member', str(archive), member,
                                 str(extracted)], capture_output=True)
        assert result.returncode == 0, (member, result.stderr[-500:])
        assert sha(extracted) == sha(present), member


def verified_scratch_cook():
    from cook_art import verify_exports
    pointer = read(OUT / 'art-cook/cook-pointer.json')
    frozen = read(pointer['frozen'])
    cooked = read(pointer['receipt'])
    assert sha(pointer['frozen']) == pointer['frozen_sha256']
    art_project = Path(frozen['project'])
    assert cooked['canonical_project'] == str(art_project)
    assert cooked['status'] == 'passed' and frozen['status'] == 'passed'
    assert frozen['assets'] == verify_exports()
    assert sha(art_project / 'mod-project.json') == frozen['project_sha256'] == cooked['canonical_config_sha256']
    assert cooked['canonical_sources_sha256']['mod-project.json'] == frozen['project_sha256']
    for item in frozen['assets']:
        base = f"project/source/art/scenario/garrison/community_020_art/buildings/vn020_{item['asset']}"
        for filename, digest in item['export_files'].items():
            if filename == 'building.json': continue
            assert cooked['canonical_sources_sha256'][base + '/' + filename] == digest
    assert sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    return cooked


def verified_roof_cook():
    from cook_roofs import verify_inputs
    pointer = read(OUT / 'barracks_tc/roof-cook-pointer.json')
    frozen = read(OUT / 'barracks_tc/roof-cook-inputs.json')
    cooked = read(pointer['receipt'])
    assert frozen == verify_inputs() and pointer['inputs_sha256'] == sha(OUT / 'barracks_tc/roof-cook-inputs.json')
    assert frozen['project_sha256'] == cooked['canonical_config_sha256']
    assert cooked['canonical_sources_sha256']['mod-project.json'] == frozen['project_sha256']
    assert cooked['status'] == 'passed' and sha(cooked['cook']['archive']) == cooked['cook']['sha256'] == pointer['archive_sha256']
    return cooked


def verified_shelter_cook():
    from cook_shelters import verify_exports
    pointer = read(OUT / 'shelter-cook/cook-pointer.json')
    frozen = read(pointer['frozen'])
    cooked = read(pointer['receipt'])
    assert pointer['frozen_inputs_sha256'] == sha(pointer['frozen'])
    shelter_project = Path(frozen['project'])
    assert cooked['canonical_project'] == str(shelter_project)
    assert frozen['status'] == cooked['status'] == 'passed' and frozen['assets'] == verify_exports()
    assert sha(shelter_project / 'mod-project.json') == frozen['project_sha256'] == cooked['canonical_config_sha256']
    assert cooked['canonical_sources_sha256']['mod-project.json'] == frozen['project_sha256']
    for item in frozen['assets']:
        base = f"project/source/art/scenario/garrison/community_020_shelters/buildings/vn020_{item['asset']}"
        for filename, digest in item['export_files'].items():
            if filename == 'building.json': continue
            assert cooked['canonical_sources_sha256'][base + '/' + filename] == digest
    assert sha(cooked['cook']['archive']) == cooked['cook']['sha256']
    return cooked


def stamp(source, target, old_model, new_model, expected=1):
    """Copy one stock stamp; rewrite only its model string and private object IDs."""
    source = Path(source)
    target = Path(target)
    tree = native.NativeTree(source)
    memory = bytearray(tree.memory.payload)
    objects = bytearray(tree.chunks[b'ROBJ'].payload)
    creation = bytearray(tree.chunks[b'RNEW'].payload)
    ids = {oid: int.from_bytes(hashlib.sha256(('community020:' + str(target) + ':' + str(oid)).encode()).digest()[:8], 'little')
           for oid in tree.objects}
    changed = []
    for index, (oid, obj) in enumerate(tree.objects.items()):
        at = 8 + index*36
        old, tid, address, owner, checksum = struct.unpack_from('<QQQQI', objects, at)
        assert old == oid
        struct.pack_into('<QQQQI', objects, at, ids[oid], tid, address, ids.get(owner, 0), checksum)
        for name, field in obj['fields'].items():
            position = obj['offset'] + int(field.get('Offset')) - tree.memory.payload_offset
            if name == 'm_objectID':
                previous = struct.unpack_from('<Q', memory, position)[0]
                if previous in ids: struct.pack_into('<Q', memory, position, ids[previous])
            if name != 'm_blueprint': continue
            previous = tree.field(obj, field)['text'].replace('\\', '/')
            if previous.lower() != old_model.lower(): continue
            assert obj['type'] == 'VisualStampBlueprint'
            assert field.get('FieldTypeName') == 'util::ReflectString<StdTraits>'
            displacement, length = struct.unpack_from('<qQ', memory, position)
            replacement = new_model.replace('/', '\\').encode()
            assert len(replacement) <= length
            start = position + displacement
            memory[start:start+length] = replacement + b'\0'*(length-len(replacement))
            struct.pack_into('<Q', memory, position+8, len(replacement))
            changed.append({'id': str(oid), 'before': previous, 'after': new_model})
    assert len(changed) == expected, (source, changed, expected)
    for index in range(struct.unpack_from('<Q', creation)[0]):
        at = 8+29*index
        oid = struct.unpack_from('<Q', creation, at)[0]
        struct.pack_into('<Q', creation, at, ids[oid])
    edits = {tree.memory.offset: bytes(memory), tree.chunks[b'ROBJ'].offset: bytes(objects),
             tree.chunks[b'RNEW'].offset: bytes(creation)}
    raw = rc.rebuild(tree.document, lambda chunk: edits.get(chunk.offset))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    final = native.NativeTree(target)
    assert len(final.objects) == len(tree.objects)
    old_visuals, new_visuals = native.active_visuals(tree), native.active_visuals(final)
    assert len(old_visuals) == len(new_visuals)
    assert all(a['transform'] == b['transform'] for a, b in zip(old_visuals, new_visuals))
    assert sum(v['model'].lower() == new_model.lower() for v in new_visuals) == expected
    return {'source': str(source), 'source_sha256': sha(source), 'output': str(target),
            'sha256': sha(target), 'changed_model_strings': changed,
            'active_visual_count': len(new_visuals), 'native_object_count': len(final.objects),
            'native_nonvisual_and_marker_records_retained': True, 'runtime': 'unverified'}


def donor_models():
    guarded()
    handoff = read(OUT / 'barracks_tc/source-handoff.json')
    assert handoff['status'] == 'source_export_ready_for_integration' and len(handoff['models']) == 8
    roof_pointer = OUT / 'barracks_tc/roof-cook-pointer.json'
    roof = read(OUT / 'barracks_tc/materials-ready.json') if roof_pointer.exists() else None
    roof_cook = verified_roof_cook() if roof else None
    if roof:
        assert roof_cook['status'] == 'passed' and roof_cook['cook']['sha256'] == read(roof_pointer)['archive_sha256']
        assert roof['status'] == 'registered_uncooked' and len(roof['models']) == 8
        roof_models = {(row['family'], row['age']): row for row in roof['models']}
        roof_back = Path(roof_cook['readback'])
    rows, models = [], []
    graph = read(OUT / 'inventory/native-graph.json')
    for row in handoff['models']:
        family = row['family']
        assert family in ('barracks', 'town_center')
        age = row['age']
        key = f'{family}_age0{age}'
        original = row['logical_stock_model']
        assert original == graph['stamps'][key]['visuals'][0]['model']
        final = MODEL_PREFIX + key + '/model'
        assert row['native_binding'] == final
        geometry = Path(row['native_geometry'])
        assert sha(geometry) == row['native_geometry_sha256']
        for field in ('donor_manifest', 'donor_geometry', 'projection', 'donor_blend', 'editable_blend'):
            assert sha(row[field]) == row[field + '_sha256']
        assert sha(native.stock(original + '.rgm')) == row['donor_model_sha256']
        assert sha(native.stock(original + '.rrmaterial')) == row['donor_material_sha256']
        payloads = []
        payload(final + '.rgm', native.rebase_model(native.stock(original + '.rgm').read_bytes(), final), payloads)
        payload(final + '.rgo', native.stock(original + '.rgo').read_bytes(), payloads)
        payload(final + '.rrgeom', geometry.read_bytes(), payloads)
        original_material = native.stock(original + '.rrmaterial').read_bytes()
        if roof:
            material_contract = roof_models[(family, age)]
            assert material_contract['stock_model'] == original
            edits = {}
            for material in material_contract['roof_materials']:
                assert sha(material['image']) == material['image_sha256']
                assert sha(material['registered_project_input']) == material['registered_project_input_sha256']
                cooked_member = mv.texture_member('community_civilization_pack', material['carrier'],
                                                  material['slot']).replace('\\', '/') + '.rrtex'
                cooked_texture = roof_back / cooked_member
                assert cooked_texture.is_file(), cooked_member
                assert_cook_member(roof_cook, cooked_member)
                private_texture = final.rsplit('/', 1)[0] + '/' + material['carrier'] + '.rrtex'
                payload(private_texture, cooked_texture.read_bytes(), payloads)
                edits.setdefault(material['material_name'], {})[material['slot']] = private_texture
            private_material = native.scoped_material(original_material, edits)
            for old, new in zip(rc.parse(original_material).roots, rc.parse(private_material).roots):
                if old.tag != b'GMat': continue
                def slots(chunk):
                    return mv.material_slots(rc.pack_document([rc.pack_chunk(
                        chunk.kind, chunk.tag, chunk.payload, name=chunk.name, version=chunk.version)]))
                before, after = slots(old), slots(new)
                assert before['parameters'] == after['parameters']
                name = old.decoded_name.removesuffix('_collection')
                for slot, value in before['textures'].items():
                    if slot not in edits.get(name, {}): assert after['textures'][slot] == value
            payload(final + '.rrmaterial', private_material, payloads)
        else:
            payload(final + '.rrmaterial', original_material, payloads)
        source_stamp = Path(graph['stamps'][key]['file'])
        private_member = PREFIX + key + '.bin'
        report = stamp(source_stamp, WORK / 'payload' / private_member, original, final)
        payloads.append({'member': private_member, 'file': report['output'], 'sha256': report['sha256'],
                         'bytes': Path(report['output']).stat().st_size})
        models.append({'key': key, 'source_handoff': row, 'principal': final, 'stamp': report,
                       'payloads': payloads, 'native_lifecycle_rgo_preserved': True,
                       'geometry_only': not bool(roof), 'roof_material_cook': roof_cook['cook']['sha256'] if roof else None})
        rows.extend(payloads)
    result = {'status': 'passed', 'source_handoff_sha256': sha(OUT / 'barracks_tc/source-handoff.json'),
              'models': models, 'payloads': rows, 'native_runtime': 'unverified'}
    write(WORK / 'barracks-tc-media.json', result)
    print('BARRACKS_TC_PRIVATE_MEDIA', len(models), len(rows))
    return result


def scratch_models():
    """Rebase the native Ministry/farm cook into private model and stamp keys."""
    guarded()
    from integration_codec import copy_native_markers, intact_damage_conditions, visibility_evidence
    cooked = verified_scratch_cook()
    back = Path(cooked['readback'])
    graph = read(OUT / 'inventory/native-graph.json')
    models, payloads, stamps = [], [], []
    for key in ('ministry', 'farm'):
        source_recipe = read(ROOT / f'art/recipes/release_020/{key}-source.json')
        assert sha(source_recipe['source']) == source_recipe['source_sha256']
        assert {p.name: sha(p) for p in Path(source_recipe['export']).iterdir() if p.is_file()} == source_recipe['export_files']
        base = f'art/scenario/garrison/community_020_art/buildings/vn020_{key}/model'
        cooked_model = back / (base + '.rgm')
        assert cooked_model.is_file()
        for member in (base + '.rgm', base + '.rgo', base + '.rrgeom', base + '.rrmaterial'):
            assert_cook_member(cooked, member)
        final = MODEL_PREFIX + ('economy_ministry' if key == 'ministry' else 'farm_paddy_edge') + '/model'
        original_model = next((v['model'] for v in graph['stamps']['economy_ministry']['visuals']
                               if 'chi_dynasty_pagoda_control_age03' in v['model']), None) if key == 'ministry' else None
        if key == 'ministry':
            donor = native.stock(original_model + '.rgm').read_bytes()
            parts = read(Path(source_recipe['export']) / 'building.json')['parts']
            raw = bp.construction_model(cooked_model.read_bytes(), donor, parts, profile_id='english-house')
            raw, damage = intact_damage_conditions(raw)
            visibility = visibility_evidence(raw, parts)
            raw, markers = copy_native_markers(raw, donor)
            rgo = native.stock(original_model + '.rgo').read_bytes()
        else:
            raw = cooked_model.read_bytes()
            rgo = (back / (base + '.rgo')).read_bytes()
            damage = visibility = markers = None
        raw = native.rebase_model(raw, final)
        own = []
        payload(final + '.rgm', raw, own)
        payload(final + '.rgo', rgo, own)
        payload(final + '.rrgeom', (back / (base + '.rrgeom')).read_bytes(), own)
        cooked_material = (back / (base + '.rrmaterial')).read_bytes()
        edits = {}
        texture_rows = []
        doc = rc.parse(cooked_material)
        for mat in doc.roots:
            if mat.tag != b'GMat': continue
            name = mat.decoded_name.removesuffix('_collection')
            slots = mv.material_slots(rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload,
                                                                      name=mat.name, version=mat.version)]))['textures']
            edits.setdefault(name, {})
            for slot, value in slots.items():
                if not value or value == '__default': continue
                old = value.replace('\\', '/').lower()
                assert old.startswith(base.rsplit('/', 1)[0] + '/') and old.endswith('.rrtex'), (key, old)
                private = final.rsplit('/', 1)[0] + '/' + old.rsplit('/', 1)[1]
                edits[name][slot] = private
                cooked_texture = back / old
                assert cooked_texture.is_file()
                assert_cook_member(cooked, old)
                if private not in {r['member'] for r in texture_rows}:
                    payload(private, cooked_texture.read_bytes(), texture_rows)
        material = native.scoped_material(cooked_material, edits)
        payload(final + '.rrmaterial', material, own)
        own.extend(texture_rows)
        target_keys = ['economy_ministry'] if key == 'ministry' else [
            f'farm_rice_{side}' for side in ('back', 'front', 'left', 'right')]
        for stamp_key in target_keys:
            info = graph['stamps'][stamp_key]
            previous = original_model if key == 'ministry' else 'art/environment/biome_tropical_dry/bushes/sagebush_row/sagebush_row'
            count = 2 if stamp_key == 'farm_rice_back' else 1
            target = WORK / 'payload' / (PREFIX + stamp_key + '.bin')
            report = stamp(info['file'], target, previous, final, expected=count)
            row = {'member': PREFIX + stamp_key + '.bin', 'file': str(target),
                   'sha256': sha(target), 'bytes': target.stat().st_size}
            own.append(row)
            stamps.append({'key': stamp_key, 'model': final, 'native_stamp': report})
        models.append({'key': key, 'principal': final, 'source_recipe': source_recipe,
                       'cooked_model_sha256': sha(cooked_model), 'native_donor': original_model,
                       'construction_damage': damage, 'visibility': visibility,
                       'markers': markers, 'native_rgo_preserved': key == 'ministry', 'payloads': own})
        payloads.extend(own)
    result = {'status': 'passed', 'cook_sha256': cooked['cook']['sha256'],
              'models': models, 'stamps': stamps, 'payloads': payloads,
              'native_runtime': 'unverified'}
    write(WORK / 'scratch-media.json', result)
    print('SCRATCH_020_PRIVATE_MEDIA', len(models), len(payloads))
    return result


def hideout_models():
    """Private native outposts plus two separately cooked visual-only shelters."""
    guarded()
    recipe_path = ROOT / 'art/recipes/release_020/hideout-source.json'
    recipe = read(recipe_path)
    assert recipe['schema'] == 'ccp.020-hideout-recipe/v1' and len(recipe['models']) == 2
    graph = read(OUT / 'inventory/native-graph.json')
    models, payloads, stamp_rows = [], [], []
    for row in recipe['models']:
        variant = row['variant']
        assert variant in ('default', 'stone')
        key = 'hideout_' + variant
        original = graph['stamps'][key]['visuals'][0]['model']
        final = MODEL_PREFIX + key + '/model'
        geometry = Path(row['geometry_export'])
        assert sha(geometry) == row['geometry_sha256']
        assert sha(row['editable_blend']) == row['editable_blend_sha256']
        assert sha(native.stock(original + '.rrgeom')) == row['donor_geometry_sha256']
        own = []
        payload(final + '.rgm', native.rebase_model(native.stock(original + '.rgm').read_bytes(), final), own)
        payload(final + '.rgo', native.stock(original + '.rgo').read_bytes(), own)
        payload(final + '.rrgeom', geometry.read_bytes(), own)
        payload(final + '.rrmaterial', native.stock(original + '.rrmaterial').read_bytes(), own)
        target = WORK / 'payload' / (PREFIX + key + '.bin')
        report = stamp(graph['stamps'][key]['file'], target, original, final)
        own.append({'member': PREFIX + key + '.bin', 'file': str(target),
                    'sha256': sha(target), 'bytes': target.stat().st_size})
        stamp_rows.append({'key': key, 'native_stamp': report})
        models.append({'key': key, 'principal': final, 'donor': original,
                       'donor_rgo_sha256': sha(native.stock(original + '.rgo')),
                       'geometry_sha256': sha(geometry), 'payloads': own})
        payloads.extend(own)
    shelters = verified_shelter_cook()
    back = Path(shelters['readback'])
    for variant in ('default', 'stone'):
        key = 'hideout_shelter_' + variant
        base = f'art/scenario/garrison/community_020_shelters/buildings/vn020_shelter_{variant}/model'
        final = MODEL_PREFIX + key + '/model'
        source = back / (base + '.rgm')
        for member in (base + '.rgm', base + '.rgo', base + '.rrgeom', base + '.rrmaterial'):
            assert_cook_member(shelters, member)
        own = []
        payload(final + '.rgm', native.rebase_model(source.read_bytes(), final), own)
        payload(final + '.rgo', (back / (base + '.rgo')).read_bytes(), own)
        payload(final + '.rrgeom', (back / (base + '.rrgeom')).read_bytes(), own)
        cooked_material = (back / (base + '.rrmaterial')).read_bytes()
        edits, texture_rows = {}, []
        for mat in rc.parse(cooked_material).roots:
            if mat.tag != b'GMat': continue
            name = mat.decoded_name.removesuffix('_collection')
            slots = mv.material_slots(rc.pack_document([rc.pack_chunk(mat.kind, mat.tag, mat.payload,
                                                                      name=mat.name, version=mat.version)]))['textures']
            edits.setdefault(name, {})
            for slot, value in slots.items():
                if not value or value == '__default': continue
                old = value.replace('\\', '/').lower()
                assert old.startswith(base.rsplit('/', 1)[0] + '/') and old.endswith('.rrtex')
                private = final.rsplit('/', 1)[0] + '/' + old.rsplit('/', 1)[1]
                assert_cook_member(shelters, old)
                edits[name][slot] = private
                if private not in {r['member'] for r in texture_rows}:
                    payload(private, (back / old).read_bytes(), texture_rows)
        payload(final + '.rrmaterial', native.scoped_material(cooked_material, edits), own)
        own.extend(texture_rows)
        original_stamp = f'art/stamps/garrison/community_020_shelters/vn020_shelter_{variant}.bin'
        assert_cook_member(shelters, original_stamp)
        target = WORK / 'payload' / (PREFIX + key + '.bin')
        report = stamp(back / original_stamp, target, base, final)
        own.append({'member': PREFIX + key + '.bin', 'file': str(target),
                    'sha256': sha(target), 'bytes': target.stat().st_size})
        stamp_rows.append({'key': key, 'native_stamp': report})
        models.append({'key': key, 'principal': final, 'cooked_model_sha256': sha(source),
                       'payloads': own})
        payloads.extend(own)
    result = {'status': 'passed', 'hideout_recipe_sha256': sha(recipe_path),
              'shelter_cook_sha256': shelters['cook']['sha256'],
              'models': models, 'stamps': stamp_rows, 'payloads': payloads,
              'native_runtime': 'unverified'}
    write(WORK / 'hideout-media.json', result)
    print('HIDEOUT_020_PRIVATE_MEDIA', len(models), len(payloads))
    return result


if __name__ == '__main__':
    command = sys.argv[1] if len(sys.argv) > 1 else 'donor'
    {'donor': donor_models, 'scratch': scratch_models, 'hideout': hideout_models}[command]()

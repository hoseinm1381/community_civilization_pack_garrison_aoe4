"""Private 0.4.0 native stamp clones with tightly scoped visual edits."""
from __future__ import annotations

import hashlib
import math
import struct
from pathlib import Path

from garrison_shared import relic_chunky as rc


def clone_visual_stamp(source, destination, old_model, new_model, *, visual_scale=1.0):
    """Re-id a stamp, change one principal model and scale only other visuals.

    The whole One Pillar compound needs uniform art scaling while functional
    stamp objects and the model's inherited marker owner stay unchanged.
    `visual_scale` applies to each retained decorative VisualStampBlueprint's
    position relative to the principal model and to its x/y/z scale.
    """
    from integration_native import NativeTree
    from integration import active_visuals

    assert visual_scale > 0 and math.isfinite(visual_scale)
    source, destination = Path(source), Path(destination)
    tree = NativeTree(source)
    visuals = active_visuals(tree)
    principal = [row for row in visuals if row['model'].lower() == old_model.lower()]
    assert len(principal) == 1, (old_model, principal)
    center = principal[0]['transform'][4:7]
    active_decor_ids = {int(row['id']) for row in visuals if row['id'] != principal[0]['id']}

    memory = bytearray(tree.memory.payload)
    objects = bytearray(tree.chunks[b'ROBJ'].payload)
    creation = bytearray(tree.chunks[b'RNEW'].payload)
    ids = {oid: int.from_bytes(hashlib.sha256(
        ('community040:' + destination.as_posix() + ':' + str(oid)).encode()).digest()[:8], 'little')
        for oid in tree.objects}
    assert len(set(ids.values())) == len(ids)
    changed, scaled = [], []
    for index, (oid, obj) in enumerate(tree.objects.items()):
        at = 8 + index * 36
        old, tid, address, owner, checksum = struct.unpack_from('<QQQQI', objects, at)
        assert old == oid
        struct.pack_into('<QQQQI', objects, at, ids[oid], tid, address, ids.get(owner, 0), checksum)
        for name, field in obj['fields'].items():
            pos = obj['offset'] + int(field.get('Offset')) - tree.memory.payload_offset
            if name == 'm_objectID':
                previous = struct.unpack_from('<Q', memory, pos)[0]
                if previous in ids:
                    struct.pack_into('<Q', memory, pos, ids[previous])
            if obj['type'] != 'VisualStampBlueprint':
                continue
            if name == 'm_blueprint':
                previous = tree.field(obj, field)['text'].replace('\\', '/')
                if previous.lower() != old_model.lower():
                    continue
                assert field.get('FieldTypeName') == 'util::ReflectString<StdTraits>'
                displacement, length = struct.unpack_from('<qQ', memory, pos)
                replacement = new_model.replace('/', '\\').encode()
                assert len(replacement) <= length
                start = pos + displacement
                memory[start:start + length] = replacement + b'\0' * (length - len(replacement))
                struct.pack_into('<Q', memory, pos + 8, len(replacement))
                changed.append(previous)
            elif name == 'm_transform' and visual_scale != 1:
                if oid not in active_decor_ids:
                    continue
                model = tree.field(obj, obj['fields']['m_blueprint'])['text'].replace('\\', '/')
                if model.lower() == old_model.lower():
                    continue  # Principal geometry was scaled in Blender.
                values = list(struct.unpack_from('<10f', memory, pos))
                before = values[:]
                for axis in range(3):
                    values[4 + axis] = center[axis] + visual_scale * (values[4 + axis] - center[axis])
                    values[7 + axis] *= visual_scale
                assert all(math.isfinite(value) for value in values)
                struct.pack_into('<10f', memory, pos, *values)
                scaled.append({'model': model, 'before': before, 'after': values})
    assert changed == [old_model], changed
    assert (len(scaled) == len(visuals) - 1) if visual_scale != 1 else not scaled
    for index in range(struct.unpack_from('<Q', creation, 0)[0]):
        at = 8 + 29 * index
        oid = struct.unpack_from('<Q', creation, at)[0]
        struct.pack_into('<Q', creation, at, ids[oid])
    edits = {tree.memory.offset: bytes(memory), tree.chunks[b'ROBJ'].offset: bytes(objects),
             tree.chunks[b'RNEW'].offset: bytes(creation)}
    raw = rc.rebuild(tree.document, lambda chunk: edits.get(chunk.offset))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(raw)
    final = NativeTree(destination)
    after = active_visuals(final)
    assert len(final.objects) == len(tree.objects) and len(after) == len(visuals)
    assert after[0]['model'].lower() == new_model.lower()
    assert [r['model'] for r in after[1:]] == [r['model'] for r in visuals[1:]]
    for prior, current in zip(visuals[1:], after[1:]):
        assert prior['transform'][:4] == current['transform'][:4]  # rotation
    return {'source': str(source), 'destination': str(destination),
            'changed_principal': [old_model, new_model],
            'scaled_decorative_visuals': scaled,
            'functional_object_count_unchanged': len(final.objects) == len(tree.objects),
            'native_runtime': 'unverified'}

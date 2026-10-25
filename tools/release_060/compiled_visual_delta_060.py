"""Expected-value native visual edits using installed Garrison's RGD codec."""
import copy
import re
import sys
from common import CFG

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd


def _allowed(path: str, policy: str, approved_paths: set[str] | None = None) -> bool:
    if policy == 'body':
        return bool(re.fullmatch(r'[^/]+/pbgid', path) or
                    re.fullmatch(r'[^/]+/attachment_lists/.+/animator_(?:merge_mesh|skin)_attachment/meshes/animator\d+', path))
    if policy == 'actor':
        return bool(re.fullmatch(r'[^/]+/tier_ext/.+/attachments/\$PBGNAME', path))
    if policy == 'actor_extended':
        return bool(re.fullmatch(r'[^/]+/tier_ext/.+/attachments/\$PBGNAME', path) or
                    re.fullmatch(r'[^/]+/entity_blueprint_ext/animator_attachments/\$PBGNAME', path))
    if policy == 'graph':
        return bool(re.fullmatch(r'[^/]+/pbgid', path) or
                    (approved_paths and path in approved_paths and path.endswith('/$PBGNAME')))
    if policy == 'body_media':
        return bool(approved_paths and path in approved_paths and
                    (re.fullmatch(r'[^/]+/attachment_lists/parent_animator', path) or
                     re.fullmatch(r'[^/]+/attachment_lists/.+/animator_(?:merge_mesh|skin|sim)_attachment/(?:meshes/animator\d+|animator)', path)))
    if policy == 'actor_media':
        return bool(approved_paths and path in approved_paths and
                    re.fullmatch(r'[^/]+/entity_blueprint_ext/alternate_sua', path))
    raise ValueError('Unknown visual policy')

def patch_visual_rgd(original: bytes, changes: list[dict], policy: str,
                     approved_paths: set[str] | None = None) -> tuple[bytes, list[dict]]:
    if not changes:
        raise ValueError('Empty visual delta')
    paths = [entry['path'] for entry in changes]
    if len(set(paths)) != len(paths):
        raise ValueError('Duplicate visual paths')
    if any(not _allowed(path, policy, approved_paths) for path in paths):
        raise ValueError('Edit outside visual policy')
    document = rgd.read(original)
    if rgd.write(document) != original:
        raise ValueError('Native codec does not preserve original bytes')
    for entry in changes:
        node = rgd.find(document.nodes, entry['path'])
        if node.kind not in ('CString', 'Int'):
            raise ValueError('Only native string and identity integer leaves may change')
        if type(node.value) is not type(entry['before']) or node.value != entry['before']:
            raise ValueError('Expected value differs at '+entry['path'])
        if type(node.value) is not type(entry['after']) or entry['after'] == entry['before']:
            raise ValueError('Changed value must retain native type and differ')
        node.value = entry['after']
    result = rgd.write(document)
    restored = rgd.read(result)
    proof = []
    for entry in changes:
        node = rgd.find(restored.nodes, entry['path'])
        if node.value != entry['after']:
            raise ValueError('Native delta readback differs')
        proof.append(copy.deepcopy(entry))
        node.value = entry['before']
    if rgd.write(restored) != original:
        raise ValueError('Visual delta is not byte-reversible')
    return result, proof

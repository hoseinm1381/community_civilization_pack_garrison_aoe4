"""Stage authorized actor2-only Tugh worker owner using original native bytes."""
from __future__ import annotations

import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from common import ARCH, CFG, OUT, ROOT, guard, owned, read, sha, write
from compiled_visual_delta_060 import patch_visual_rgd

sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd

UPSTREAM = OUT/'integration/private-equipment-stage-r1/stage.json'
LAND_IDS = OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json'
COMPOSITION = OUT/'integration/tug-worker-stock-compatible-r1/media.json'
DEST = OUT/'integration/worker-elephant-owner-stage-r2'
OFFICIAL = Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
STOCK_MEMBER = 'attrib/attachments/attachment_lists/civilizations/sultanate_ha_tug/units/tier2_worker_elephant_sul_ha_tug.rgd'
CATTLE_MEMBER = 'attrib/attachments/attachment_lists/gaia/animals/gaia_herdable_cattle_mal.rgd'
OLD_PARENT = r'attachments\attachment_lists\gaia\animals\gaia_herdable_cattle_mal'
NEW_PARENT = r'attachments\attachment_lists\civilizations\sultanate_ha_tug\units\tier2_worker_elephant_sul_ha_tug'
OLD_MODEL = r'art\civilizations\sultanate_ha_tug\animals\tug_elephant_worker_age01\tug_elephant_worker_age01'


def main():
    guard()
    if DEST.exists():
        raise FileExistsError('Preserve existing actor2 owner stage')
    upstream, ids, media = read(UPSTREAM), read(LAND_IDS), read(COMPOSITION)
    identity = [x for x in ids['entries'] if x['stock_member'] == CATTLE_MEMBER]
    if len(identity) != 1:
        raise ValueError('Actor2-only cattle identity absent or ambiguous')
    identity = identity[0]
    if identity['private_member'] not in {x['member'] for x in upstream['payloads']}:
        raise ValueError('Actor2 private list missing from upstream graph')
    graph = read(OUT/'integration/private-land-graph/plan-v3.json')
    consumers = [x for x in graph['unit_actor_lists'] if x['stock_member'] == CATTLE_MEMBER]
    if len(consumers) != 1 or {Path(x['relative_source']).stem for x in consumers[0]['source_consumers']} != {'vn_unit_war_elephant_2_vit'}:
        raise ValueError('Private cattle list is not actor2-exclusive')
    if (media['model_logical_path'] != 'art/scenario/garrison/v60b01/m031/m031.rgm'
            or media['required_geometry_replacement'] is not False
            or media['stock_native_group_count'] != 24
            or media['stock_skin_palettes'] != 8
            or media['stock_skeleton_bones'] != 140
            or media['target_actor'] != 'vn_unit_war_elephant_2_vit'):
        raise ValueError('Worker media is not pinned compatible stock remix')
    media_rows = []
    for row in media['payloads']:
        path = Path(row['path'])
        if sha(path) != row['sha256']:
            raise ValueError('Qualified worker media drift '+row['member'])
        media_rows.append({**row,'bytes':path.stat().st_size,'before_sha256':None,
                           'kind':'qualified_stock_worker_remix'})
    model = media['model_logical_path'].removesuffix('.rgm').replace('/','\\')
    stock = owned(DEST/'stock'/STOCK_MEMBER)
    stock.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([str(ARCH),'extract-member',str(OFFICIAL),STOCK_MEMBER,str(stock)],
                   check=True,capture_output=True,text=True)
    raw = stock.read_bytes()
    doc = rgd.read(raw)
    if rgd.write(doc) != raw:
        raise ValueError('Installed Tugh owner native codec roundtrip differs')
    model_paths = [(p,n.value) for p,n in rgd.flatten(doc.nodes)
                   if n.kind == 'CString' and n.value == OLD_MODEL]
    if len(model_paths) != 1 or not model_paths[0][0].endswith('/animator_merge_mesh_attachment/meshes/animator0'):
        raise ValueError('Tugh worker visible model leaf differs')
    edits = [{'path':p,'before':n.value,'after':identity['pbgid']}
             for p,n in rgd.flatten(doc.nodes) if n.key == 'pbgid']
    edits.append({'path':model_paths[0][0], 'before':OLD_MODEL,'after':model})
    cooked,proof = patch_visual_rgd(raw,edits,'body')
    payload = owned(DEST/'payload'/identity['private_member'])
    payload.parent.mkdir(parents=True,exist_ok=True)
    payload.write_bytes(cooked)
    source_rows = {x['relative']:x for x in upstream['source_rows']}
    relative = 'assets/attrib/instances/'+identity['private_reference']+'.xml'
    before_source = source_rows.get(relative)
    if not before_source or before_source['source_sha256'] is not None:
        raise ValueError('Expected new private actor2 list XML absent')
    prior = Path(before_source['staged_path'])
    if sha(prior) != before_source['staged_sha256']:
        raise ValueError('Upstream private list XML drift')
    old = prior.read_bytes()
    before = ('value="'+OLD_PARENT+'"').encode()
    after = ('value="'+NEW_PARENT+'"').encode()
    if old.count(before) != 1:
        raise ValueError('Expected actor2 stock parent missing')
    changed = old.replace(before,after,1)
    if changed.replace(after,before,1) != old:
        raise ValueError('Source parent edit not byte-reversible')
    tree = ET.fromstring(changed)
    parents = [x for x in tree.iter('instance_reference') if x.get('name') == 'parent_pbg']
    if len(parents) != 1 or parents[0].get('value') != NEW_PARENT:
        raise ValueError('Changed source parent readback differs')
    source = owned(DEST/'source'/relative)
    source.parent.mkdir(parents=True,exist_ok=True)
    source.write_bytes(changed)
    source_rows[relative] = {'relative':relative,'source_sha256':None,
                             'staged_path':str(source),'staged_sha256':sha(source),
                             'upstream_sha256':sha(prior),'private_pbgid':identity['pbgid'],
                             'source_parent_before':OLD_PARENT,'source_parent_after':NEW_PARENT}
    aggregate = {x['member']:x for x in upstream['payloads']}
    aggregate[identity['private_member']] = {'member':identity['private_member'],
        'path':str(payload),'sha256':sha(payload),'bytes':payload.stat().st_size,
        'before_sha256':None,'kind':'actor2_original_tugh_owner_private_model',
        'stock_member':STOCK_MEMBER,'stock_sha256':sha(stock),
        'replaces_upstream_cattle_list_sha256':next(x['sha256'] for x in upstream['payloads'] if x['member']==identity['private_member']),
        'edits':proof}
    for row in media_rows:
        if row['member'] in aggregate:
            raise ValueError('Worker media member collision')
        aggregate[row['member']] = row
    freeze = read(OUT/'baseline/final053/freeze.json')
    payloads = []
    for member,row in sorted(aggregate.items()):
        path = Path(row['path'])
        if sha(path) != row['sha256'] or path.stat().st_size != row['bytes']:
            raise ValueError('Aggregate payload drift '+member)
        baseline = freeze['archive_members'].get(member)
        payloads.append({**row,'before_sha256':baseline['sha256'] if baseline else None})
    sources = []
    for relative,row in sorted(source_rows.items()):
        if row['source_sha256'] is not None and sha(ROOT/relative) != row['source_sha256']:
            raise ValueError('Active source drift '+relative)
        if sha(row['staged_path']) != row['staged_sha256']:
            raise ValueError('Aggregate staged source drift '+relative)
        sources.append(row)
    write(DEST/'stage.json',{'schema':'ccp-060-worker-elephant-owner-stage/v1',
          'status':'actor2_stock_tugh_owner_clone_with_private_compatible_media_staged',
          'upstream_stage_sha256':sha(UPSTREAM),'land_identity_sha256':sha(LAND_IDS),
          'composition_sha256':sha(COMPOSITION),'installed_stock_archive_sha256':sha(OFFICIAL),
          'installed_tugh_list_sha256':sha(stock), 'baseline_sga_sha256':freeze['sga_sha256'],
          'actor2_only_private_list':identity['private_member'],
          'original_native_inverse_edits':proof,
          'source_parent_byte_inverse':True,
          'payloads':payloads,'source_rows':sources,
          'full_baseline_to_aggregate_changed_member_allowlist':sorted(aggregate),
          'active_source_or_final_archive_changed':False,
          'rebuild_policy':'Reapply pinned original-native compiled overlay and qualified media after Content Editor build.'})
    print(json.dumps({'stage':str(DEST/'stage.json'),'payloads':len(payloads),
                      'sources':len(sources),'worker_model':media['model_logical_path']},indent=2))


if __name__ == '__main__':
    main()

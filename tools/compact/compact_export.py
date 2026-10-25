"""Create an independent, current-work store. Never change the source snapshot."""
import argparse
import collections
import copy
import json
from pathlib import Path
import struct
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'collaboration'))
from store import Reader, load, write_json, file_sha

BASELINE = 'external/output/release_083/delivery/final-v2/community_civilization_pack.sga'
FINAL = 'external/output/release_084/delivery/final-v1/'


def retain(key):
    if key == BASELINE:
        return True
    if key.lower().endswith(('.wav', '.pyc', '.pyo', '.blend1', '.blend2')):
        return False
    if key.startswith(('external/output/release_084/local/generation/',
                       'external/output/release_084/local/auditions/',
                       'external/output/release_084/local/delivery/',
                       'external/output/release_084/local/shutdown-checkpoints/',
                       'external/output/release_084/generation/')):
        return False
    if key.startswith('external/output/') and any(x in key for x in (
            '/release_081/delivery/', '/release_082_animation/delivery-v1/',
            '/release_083/delivery/', '/release_0712/delivery/', '/consolidation_080/delivery/')):
        return False
    if key.startswith(FINAL) and (key.endswith(('community_civilization_pack.sga', 'attributes-overlay.sga'))):
        return False
    if any(p in ('readback', 'fresh-readback') for p in key.split('/')):
        return False
    return True


def required_payloads(doc, policy):
    by_sha = collections.defaultdict(list)
    for key, row in doc['files'].items():
        by_sha[row['sha256']].append(key)
    required = set()
    for member, row in policy['payload'].items():
        options = by_sha.get(row['sha256'], [])
        # Use a retained source with identical bytes; original paths remain evidence.
        options = sorted(options, key=lambda k: (not retain(k), len(k), k))
        if not options:
            raise ValueError('Missing current payload: ' + member)
        required.add(options[0])
    return required


def repack(folder, doc, destination, keys, pack_bytes=40_000_000):
    """Copy ZIP local records without lossy conversion or recompression.

    Input Writer archives are seekable, nonencrypted ZIPs without data descriptors.
    Reader.verify independently checks all destination chunks/files after export.
    """
    folder = Path(folder).resolve()
    destination = Path(destination).resolve()
    if destination == folder or destination.is_relative_to(folder):
        raise ValueError('Destination must be independent')
    destination.mkdir(parents=True, exist_ok=False)
    chunks = {h for key in keys for h in doc['files'][key]['chunks']}
    result = dict(schema=doc['schema'], files={k:doc['files'][k] for k in sorted(keys)},
                  chunks={}, packs={}, provenance=copy.deepcopy(doc.get('provenance', {})))
    grouped = collections.defaultdict(list)
    for h in chunks:
        grouped[doc['chunks'][h]['pack']].append(h)
    output = None
    number = 0
    count = 0

    def close():
        if output is not None:
            output.close()
            path = destination / name
            result['packs'][name] = dict(bytes=path.stat().st_size, sha256=file_sha(path))

    try:
        for old_pack, hashes in sorted(grouped.items()):
            old_path = folder / old_pack
            if file_sha(old_path) != doc['packs'][old_pack]['sha256']:
                raise ValueError('Corrupt input pack: ' + old_pack)
            with zipfile.ZipFile(old_path) as source, old_path.open('rb') as raw:
                for h in sorted(hashes, key=lambda v: source.getinfo(v).header_offset):
                    info = source.getinfo(h)
                    if info.flag_bits & 9 or info.compress_type not in (zipfile.ZIP_DEFLATED, zipfile.ZIP_STORED):
                        raise ValueError('Unsupported ZIP chunk flags/type')
                    raw.seek(info.header_offset)
                    header = raw.read(30)
                    if len(header) != 30 or header[:4] != b'PK\x03\x04':
                        raise ValueError('Invalid ZIP local record')
                    name_length, extra_length = struct.unpack_from('<HH', header, 26)
                    tail = raw.read(name_length + extra_length + info.compress_size)
                    if len(tail) != name_length + extra_length + info.compress_size:
                        raise ValueError('Truncated ZIP chunk')
                    record = header + tail
                    if output is not None and output.fp.tell() + len(record) > pack_bytes:
                        close()
                        output = None
                    if output is None:
                        number += 1
                        name = f'pack-{number:05d}.zip'
                        output = zipfile.ZipFile(destination/name, 'x', allowZip64=True)
                    copied = copy.copy(info)
                    copied.header_offset = output.fp.tell()
                    output.fp.write(record)
                    output.filelist.append(copied)
                    output.NameToInfo[copied.filename] = copied
                    output.start_dir = output.fp.tell()
                    output._didModify = True
                    result['chunks'][h] = dict(pack=name, bytes=doc['chunks'][h]['bytes'])
                    count += 1
            print('REPACKED', old_pack, 'CHUNKS', count, 'PACKS', number, flush=True)
        close()
        output = None
    finally:
        if output is not None:
            output.close()
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-index', type=Path, required=True)
    p.add_argument('--destination', type=Path, required=True)
    args = p.parse_args()
    old = load(args.source_index)
    reader = Reader(args.source_index.parent, old)
    try:
        policy = json.loads(reader.read(FINAL+'changed-member-policy.json'))
        required = required_payloads(old, policy)
        keys = {k for k in old['files'] if retain(k)} | required
        if BASELINE not in keys:
            raise ValueError('Immediate baseline missing')
        doc = repack(args.source_index.parent, old, args.destination, keys)
        doc['provenance']['compact_policy'] = 'current-work-ogg/v1'
        doc['provenance']['original_index_sha256'] = file_sha(args.source_index)
        # Resolve old paths by hash in the compact CLI; never rewrite frozen policy.
        by_sha = {old['files'][k]['sha256']:k for k in required}
        doc['current_payloads'] = {m:dict(key=by_sha[row['sha256']],
                                        sha256=row['sha256']) for m,row in policy['payload'].items()}
        from dev import path_key
        doc['aliases'] = {path_key(row['file'], old):by_sha[row['sha256']] for row in policy['payload'].values()}
        write_json(args.destination/'index.json.gz', doc)
        omitted = {k:v for k,v in old['files'].items() if k not in keys}
        reasons = collections.defaultdict(lambda:dict(files=0,expanded_bytes=0))
        for k,row in omitted.items():
            group = 'uncompressed-audio' if k.endswith('.wav') else '/'.join(k.split('/')[:4])
            reasons[group]['files'] += 1
            reasons[group]['expanded_bytes'] += row['bytes']
        write_json(args.destination/'selection.json', dict(files=len(keys), packs=len(doc['packs']),
                   packed_bytes=sum(v['bytes'] for v in doc['packs'].values()),
                   omitted=dict(reasons), original_history_preserved=True,
                   current_payload_members=len(policy['payload']), wav_files=0))
        print('COMPACT_EXPORT_COMPLETE',len(keys),sum(v['bytes'] for v in doc['packs'].values()),flush=True)
    finally:
        reader.close()


if __name__ == '__main__':
    main()

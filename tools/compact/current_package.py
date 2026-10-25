"""Exact current-package reconstruction using a retained baseline and small deltas."""
import io
import copy
import json
from pathlib import Path
import shutil
import tempfile
import zipfile


def apply_verification_delta(original, delta):
    """Small releases reuse the immutable full member map from the prior index."""
    if not delta:
        return copy.deepcopy(original)
    metadata=delta.get('metadata', {})
    if (set(delta)-{'metadata','member_sha256'} or
        {'mounts','member_sha256'} & set(metadata) or
        set(delta.get('member_sha256', {}))-set(original['member_sha256'])):
        raise ValueError('Sparse verification may only replace existing members')
    result=copy.deepcopy({k:original[k] for k in ('mounts','member_sha256')})
    result.update(metadata)
    result['member_sha256'].update(delta.get('member_sha256', {}))
    return result


def write_package(target, entries, sources):
    target = Path(target)
    if target.exists():
        raise FileExistsError('Existing package preserved')
    names = [row['filename'] for row in entries]
    if len(set(names)) != len(names) or set(names) != set(sources):
        raise ValueError('Package member policy differs')
    for name in names:
        if '/' in name or '\\' in name or ':' in name or name in ('', '.', '..'):
            raise ValueError('Unsafe package member')
    with zipfile.ZipFile(target, 'x', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for row in entries:
            info = zipfile.ZipInfo(row['filename'], tuple(row['date_time']))
            for field in ('compress_type', 'create_system', 'create_version',
                          'extract_version', 'external_attr', 'internal_attr'):
                setattr(info, field, row[field])
            info.extra = bytes.fromhex(row.get('extra_hex', ''))
            info.comment = bytes.fromhex(row.get('comment_hex', ''))
            info._compresslevel = 6
            with Path(sources[info.filename]).open('rb') as src, z.open(info, 'w') as dst:
                shutil.copyfileobj(src, dst, 1024*1024)


def rebuild(args, reader):
    from store import file_sha, sha, write_json
    import dev
    policy = reader.doc['milestone']
    if not args.archive_tool:
        raise ValueError('Current package reconstruction requires --archive-tool PATH')
    dest = args.destination.resolve()
    if dest.exists():
        raise FileExistsError('Use a new destination; previous work is preserved')
    dest.mkdir(parents=True)
    expected = json.loads(reader.read(policy['verification']))
    expected = apply_verification_delta(expected, policy.get('verification_delta', {}))
    baseline = dest/'baseline-084.sga'
    with zipfile.ZipFile(io.BytesIO(reader.read(policy['baseline_zip_key']))) as z:
        with z.open('community_civilization_pack.sga') as src, baseline.open('xb') as dst:
            shutil.copyfileobj(src, dst)
    if file_sha(baseline) != policy['baseline_sga_sha256']:
        raise ValueError('Baseline archive differs')
    current = baseline
    replacements = {}
    for number, step in enumerate(policy['steps']):
        lines = []
        for i, row in enumerate(step['payloads']):
            data = reader.read(row['key'])
            if sha(data) != row['sha256'] or expected['member_sha256'][row['member']] != row['sha256']:
                raise ValueError('Delta differs from final member policy')
            p = dest/f'payload-{number}-{i}.bin'
            p.write_bytes(data)
            lines.append(row['member']+'='+str(p)+'\n')
            replacements[row['member']] = row['sha256']
        manifest = dest/f'members-{number}.txt'
        manifest.write_bytes(''.join(lines).encode('utf-8'))
        target = dest/f'overlay-{number}.sga'
        dev.run([args.archive_tool, 'set-members', current, manifest, target,
                 '--alias', step['alias']], dest, f'assemble-{number}')
        current = target
    final = dest/'community_civilization_pack.sga'
    current.rename(final)
    if file_sha(final) != expected['sga_sha256']:
        raise ValueError('Reconstructed archive is not the exact current release')
    listing = json.loads(dev.run([args.archive_tool, 'list', final, '--verify'], dest, 'final-list'))
    if (listing['archive']['name'] != dev.NAMESPACE or
        not listing['archive']['verification']['verified'] or
        {m['path']:m['toc'] for m in listing['members']} != expected['mounts']):
        raise ValueError('Archive namespace, verification or mounts differ')
    with tempfile.TemporaryDirectory(prefix='ccp-milestone-readback-') as tmp:
        root = Path(tmp)
        dev.run([args.archive_tool, 'extract', final, root, '--filter', '.'], dest, 'fresh-extract')
        actual = {p.relative_to(root).as_posix():file_sha(p) for p in root.rglob('*') if p.is_file()}
        if actual != expected['member_sha256']:
            raise ValueError('Fresh member hashes differ')
    sources = {'community_civilization_pack.sga':final}
    for name, key in policy['package_text'].items():
        path = dest/name
        path.write_bytes(reader.read(key))
        sources[name] = path
    package = dest/f"community_civilization_pack-{policy['version']}.zip"
    write_package(package, policy['zip_entries'], sources)
    if file_sha(package) != expected['zip_sha256'] or package.stat().st_size != expected['zip_bytes']:
        raise ValueError('Reconstructed ZIP differs from the exact release')
    with zipfile.ZipFile(package) as z:
        if z.testzip() is not None:
            raise ValueError('ZIP integrity failure')
    write_json(dest/'verification.json', expected)
    write_json(dest/'compact-rebuild-proof.json', dict(version=policy['version'],
        sga_sha256=file_sha(final),zip_sha256=file_sha(package),members=len(actual),
        changed_members=sorted(replacements),native_compile_run=False,native_game_test=False))
    print('EXACT_CURRENT_PACKAGE_VERIFIED', package, flush=True)

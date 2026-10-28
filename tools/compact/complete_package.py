"""Reassemble an accepted complete member policy, including explicit omissions.

Reuses the immutable pre-art baseline and existing media/overlays. Does not store
another full SGA/ZIP, copy a source checkout or read the candidate workspace.
"""
import io,json,hashlib,zipfile,concurrent.futures,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'collaboration'))
from store import file_sha,write_json
from current_package import write_package,apply_verification_delta
import dev

def check_policy(policy, expected, prior):
    from portable import check_member
    if policy.get('assembly_mode')!='complete-members':raise ValueError('Unsupported assembly policy')
    hashes=expected['member_sha256'];mounts=expected['mounts']
    if set(hashes)!=set(mounts):raise ValueError('Member/mount closure differs')
    for member in hashes:
        check_member(member)
        if mounts[member] not in ('attrib','data','info','locale'):raise ValueError('Unexpected mount')
    payloads={r['member']:r for r in policy['payloads']}
    if len(payloads)!=len(policy['payloads']):raise ValueError('Duplicate payload member')
    for member,row in payloads.items():
        if hashes.get(member)!=row['sha256'] or mounts[member]!=row['mount']:raise ValueError('Payload differs from final policy')
    omissions=set(policy['deleted_members_vs090'])
    if len(omissions)!=len(policy['deleted_members_vs090']) or omissions!=set(prior['member_sha256'])-set(hashes):raise ValueError('Omissions escape explicit policy')
    required={m for m,h in hashes.items() if prior['member_sha256'].get(m)!=h}
    if set(payloads)!=required:raise ValueError('Changed member closure differs')
    return payloads

def rebuild(args,reader):
    policy=reader.doc['milestone'];basepolicy=policy['baseline'];dest=args.destination.resolve()
    if dest.exists():raise FileExistsError('Previous build preserved: '+str(dest))
    dest.mkdir(parents=True)
    expected=json.loads(reader.read(policy['verification']))
    prior=apply_verification_delta(json.loads(reader.read(basepolicy['verification'])),basepolicy.get('verification_delta',{}))
    payloads=check_policy(policy,expected,prior)
    baseline=dest/'baseline.sga'
    with zipfile.ZipFile(io.BytesIO(reader.read(basepolicy['baseline_zip_key']))) as z:
        with z.open('community_civilization_pack.sga') as src,baseline.open('xb') as dst:
            import shutil;shutil.copyfileobj(src,dst,1024*1024)
    if file_sha(baseline)!=basepolicy['baseline_sga_sha256']:raise ValueError('Immutable baseline differs')
    basefiles=dest/'baseline-members';dev.run([args.archive_tool,'extract',baseline,basefiles,'--filter','.'],dest,'baseline-extract')
    files={k:basefiles/k for k in expected['member_sha256']}
    # Original 0.9 steps remain available through their existing immutable keys.
    winners={row['member']:row for step in basepolicy['steps'] for row in step['payloads']}
    winners.update(payloads)
    for i,(member,row) in enumerate(sorted(winners.items())):
        if member not in files:continue
        data=reader.read(row['key']);h=hashlib.sha256(data).hexdigest()
        if h!=expected['member_sha256'][member]:raise ValueError('Stored final payload differs: '+member)
        target=dest/'payload'/member;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);files[member]=target
    # Verify every selected input before invoking the archive writer.
    def verify(item):
        member,path=item
        if file_sha(path)!=expected['member_sha256'][member]:raise ValueError('Rebuild input differs: '+member)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:list(pool.map(verify,files.items()))
    seed=dest/'empty-seed.sga';seed.write_bytes(reader.read(policy['empty_seed_key']))
    if file_sha(seed)!=policy['empty_seed_sha256']:raise ValueError('Empty seed differs')
    seedlist=json.loads(dev.run([args.archive_tool,'list',seed,'--verify'],dest,'seed-list'))
    if seedlist['member_count'] or seedlist['archive']['name']!=dev.NAMESPACE:raise ValueError('Invalid seed namespace/inventory')
    current=seed;final=dest/'community_civilization_pack.sga'
    for alias in ('attrib','info','locale','data'):
        manifest=dest/(alias+'-members.txt');manifest.write_text(''.join(m+'='+str(files[m])+'\n' for m in sorted(files) if expected['mounts'][m]==alias))
        target=final if alias=='data' else dest/('assembly-'+alias+'.sga')
        print('ASSEMBLE_CURRENT',alias,flush=True)
        dev.run([args.archive_tool,'set-members',current,manifest,target,'--alias',alias],dest,'assemble-'+alias);current=target
    if file_sha(final)!=expected['sga_sha256']:raise ValueError('Reconstructed owning SGA differs from accepted release')
    listing=json.loads(dev.run([args.archive_tool,'list',final,'--verify'],dest,'final-list'))
    if listing['archive']['name']!=dev.NAMESPACE or not listing['archive']['verification']['verified'] or {m['path']:m['toc'] for m in listing['members']}!=expected['mounts']:raise ValueError('Final namespace/mounts/inventory differs')
    fresh=dest/'final-members';print('READBACK_CURRENT',flush=True)
    dev.run([args.archive_tool,'extract',final,fresh,'--filter','.'],dest,'final-extract')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for member,h in zip(expected['member_sha256'],pool.map(file_sha,(fresh/m for m in expected['member_sha256']))):
            if h!=expected['member_sha256'][member]:raise ValueError('Fresh final member differs: '+member)
    sources={'community_civilization_pack.sga':final}
    for name,key in policy['package_text'].items():
        path=dest/name;path.write_bytes(reader.read(key));sources[name]=path
    package=dest/f"community_civilization_pack-{policy['version']}.zip"
    print('ZIP_CURRENT',flush=True);write_package(package,policy['zip_entries'],sources,policy['zip_compresslevel'])
    if file_sha(package)!=expected['zip_sha256'] or package.stat().st_size!=expected['zip_bytes']:raise ValueError('Reconstructed import ZIP differs')
    with zipfile.ZipFile(package) as z:
        if z.testzip() is not None:raise ValueError('ZIP CRC mismatch')
    write_json(dest/'verification.json',expected)
    write_json(dest/'compact-rebuild-proof.json',dict(version=policy['version'],sga_sha256=file_sha(final),zip_sha256=file_sha(package),members=len(files),inputs_from_immutable_store=True,omitted_members=len(policy['deleted_members_vs090']),source_art_recook=False,native_game_test=False))
    print('EXACT_CURRENT_PACKAGE_VERIFIED',package,flush=True)

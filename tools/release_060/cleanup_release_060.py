"""Remove only verified full-archive extraction caches after ZIP qualification."""
import argparse
from pathlib import Path
import subprocess
from common import OUT, files, guard, owned, read, sha, write
from inspect_delivery_060 import inspect_delivery
from pin_final053 import PIN, SGA_SHA, ZIP_SHA


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--execute',action='store_true')
    args=ap.parse_args();guard()
    target=owned(OUT/'qualification/cleanup-r1.json')
    if target.exists():raise FileExistsError('Preserve cleanup evidence')
    package=read(OUT/'qualification/final-package-r1.json')
    delivery=owned(package['zip']);proof=inspect_delivery(delivery)
    if proof['zip_sha256']!=package['zip_sha256']:raise ValueError('Qualified ZIP changed')
    candidate=OUT/'assembly/candidate-r2/community_civilization_pack.sga'
    if sha(candidate)!=proof['sga_sha256']:raise ValueError('Candidate differs from packaged SGA')
    if sha(PIN/'community_civilization_pack-0.5.3.zip')!=ZIP_SHA or sha(PIN/'community_civilization_pack.sga')!=SGA_SHA:
        raise ValueError('Rollback baseline changed')
    rows=[]
    for label in ('r1','r2'):
        folder=owned(OUT/('qualification/final-archive-'+label))
        path=owned(folder/'members')
        if path.resolve()!=OUT.resolve()/'qualification'/('final-archive-'+label)/'members':
            raise ValueError('Unexpected resolved extraction target')
        # Full inventories reject all nested links/reparse targets before recursive removal.
        actual=files(path,reject_links=True,exclude_release_060=False)
        receipt=read(folder/'receipt.json');archive=owned(receipt['candidate'])
        if actual!=receipt['members'] or sha(archive)!=receipt['candidate_sha256']:
            raise ValueError('Extraction cannot be regenerated from retained candidate')
        rows.append({'target':str(path.resolve()),'files':len(actual),
            'bytes':sum(r['bytes'] for r in actual.values()),'basis':str(archive),
            'basis_sha256':sha(archive),'member_inventory_receipt':str(folder/'receipt.json'),
            'member_inventory_receipt_sha256':sha(folder/'receipt.json')})
    result={'schema':'ccp-060-post-package-cache-cleanup/v1','status':'inventoried_not_removed',
        'targets':rows,'planned_bytes':sum(r['bytes'] for r in rows),
        'retained':'All editable art/media, exports, recipes, native cook inputs/archives/readbacks used by qualification, IDs, source snapshots, decoded manifests, failed diagnostics, baseline readbacks, candidate SGAs, prior releases, tools and receipts.',
        'regeneration':'sga-archiver extract <basis-sga> <members-directory> --filter .',
        'zip_sha256_before':proof['zip_sha256'],'sga_sha256_before':proof['sga_sha256']}
    write(OUT/'qualification/cleanup-plan-r1.json',result)
    if not args.execute:print(result);return
    for row in rows:
        guard();path=Path(row['target'])
        if not path.resolve().is_relative_to((OUT/'qualification').resolve()) or path.is_junction() or path.is_symlink():
            raise ValueError('Cleanup target changed')
        # Native PowerShell removes only the already resolved, enumerated literal target.
        literal="'"+str(path).replace("'","''")+"'"
        subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',
                        '$ErrorActionPreference = \'Stop\'; Remove-Item -LiteralPath '+literal+' -Recurse -Force'],
                       check=True,capture_output=True,text=True)
        if path.exists():raise RuntimeError('Extraction directory remains')
    after=inspect_delivery(delivery)
    if after['zip_sha256']!=proof['zip_sha256'] or sha(candidate)!=proof['sga_sha256']:
        raise ValueError('Delivery changed during cleanup')
    if sha(PIN/'community_civilization_pack-0.5.3.zip')!=ZIP_SHA:raise ValueError('Rollback ZIP changed')
    result.update(status='verified_regenerable_extractions_removed_delivery_hashes_unchanged',
        reclaimed_bytes=result['planned_bytes'],zip_sha256_after=after['zip_sha256'],
        sga_sha256_after=sha(candidate),rollback_zip_sha256_after=ZIP_SHA)
    write(target,result);print(result['status']);print('Reclaimed bytes: '+str(result['reclaimed_bytes']))


if __name__=='__main__':main()

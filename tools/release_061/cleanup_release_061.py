"""Remove only complete regenerable061 archive readbacks after ZIP verification."""
import subprocess
from common import *
from package_release_061 import inspect_zip


def main():
    guard();baseline();target=owned(OUT/'qualification/cleanup-r1.json')
    if target.exists():raise FileExistsError('Preserve cleanup evidence')
    package=read(OUT/'qualification/package-r1.json');delivery=owned(package['zip'])
    verified=inspect_zip(delivery)
    if verified['zip_sha256']!=package['zip_sha256']:raise ValueError('Package changed')
    rows=[]
    for label in ('mount-fix-r1','final-r1'):
        folder=owned(OUT/'qualification'/label);path=owned(folder/'members')
        expected=(OUT.resolve()/'qualification'/label/'members')
        if path.resolve()!=expected:raise ValueError('Unexpected cleanup target')
        proof=read(folder/'receipt.json');archive=owned(proof['candidate'])
        actual=files(path)
        if actual!=proof['member_hashes'] or sha(archive)!=proof['candidate_sha256']:
            raise ValueError('Readback not reproducible from retained archive')
        rows.append({'target':str(path.resolve()),'files':len(actual),
            'bytes':sum(r['bytes'] for r in actual.values()),'basis':str(archive),'basis_sha256':sha(archive),
            'inventory':str(folder/'receipt.json'),'inventory_sha256':sha(folder/'receipt.json')})
    report={'schema':'ccp-061-regenerable-readback-cleanup/v1','targets':rows,
        'zip_sha256_before':verified['zip_sha256'],'sga_sha256_before':verified['sga_sha256'],
        'retained':'All old releases, model cook archives/readbacks, decoded manifests, art, textures, editable sources, source/cook staging, payloads, recipes, diagnostics, tools, reports and complete hash inventories.',
        'regenerate':'sga-archiver extract <basis> <target> --filter .'}
    write(OUT/'qualification/cleanup-plan-r1.json',report)
    for row in rows:
        guard();path=Path(row['target'])
        if not path.resolve().is_relative_to((OUT/'qualification').resolve()) or path.is_junction() or path.is_symlink():
            raise ValueError('Cleanup target changed')
        literal="'"+str(path).replace("'","''")+"'"
        subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',
            '$ErrorActionPreference = \'Stop\'; Remove-Item -LiteralPath '+literal+' -Recurse -Force'],
            check=True,capture_output=True,text=True)
        if path.exists():raise ValueError('Cleanup directory remains')
    after=inspect_zip(delivery)
    final=owned(OUT/'final-r1/community_civilization_pack.sga')
    if after['zip_sha256']!=verified['zip_sha256'] or sha(final)!=verified['sga_sha256']:
        raise ValueError('Delivery changed during cleanup')
    baseline()
    report.update(status='verified_readback_caches_removed_delivery_and_rollback_hashes_unchanged',
        reclaimed_bytes=sum(r['bytes'] for r in rows),zip_sha256_after=after['zip_sha256'],
        sga_sha256_after=sha(final),rollback060_zip_sha256=sha(ZIP060))
    write(target,report);print(report['status']);print(report['reclaimed_bytes'])


if __name__=='__main__':main()

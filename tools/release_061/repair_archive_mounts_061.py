"""Reconstruct 060 bytes with private RGDs in the engine's attrib TOC."""
from common import *


def validate_tocs(listing):
    rows=listing['members'];names=[r['path'].casefold() for r in rows]
    if len(names)!=len(set(names)):raise ValueError('Ambiguous member path')
    wrong=[]
    for r in rows:
        if r['path'].startswith('attrib/') and r['toc']!='attrib':wrong.append(r['path'])
        if r['path'].startswith(('art/','scar/','ui/')) and r['toc']!='data':wrong.append(r['path'])
    if wrong:raise ValueError('Resources mounted in wrong TOC: '+str(wrong[:4]))


def mount_delta(before,after,expected):
    a={r['path']:r['toc'] for r in before['members']};b={r['path']:r['toc'] for r in after['members']}
    if a.keys()!=b.keys():raise ValueError('Mount repair must preserve exact member names')
    changed={n:(a[n],b[n]) for n in a if a[n]!=b[n]}
    if changed!={n:('data','attrib') for n in expected}:raise ValueError('Unexpected mount delta')
    validate_tocs(after)
    return changed


def main():
    guard();frozen=baseline()
    handoff=read(OLD/'integration/final-binding-handoff-v3.json')
    final053=OLD/'baseline/final053/community_civilization_pack.sga'
    if sha(final053)!=handoff['baseline_sga_sha256']:raise ValueError('Exact final053 required')
    rows=handoff['payloads'];attrib=[r for r in rows if r['member'].startswith('attrib/')]
    art=[r for r in rows if r['member'].startswith('art/')]
    if (len(attrib),len(art),len(rows))!=(142,305,447):raise ValueError('Unexpected final060selection')
    for row in rows:
        p=Path(row['path'])
        if sha(p)!=row['sha256'] or p.stat().st_size!=row['bytes']:raise ValueError('Pinned060payload changed')
    folder=owned(OUT/'mount-fix-r1')
    if folder.exists():raise FileExistsError('Preserve mount repair candidate')
    folder.mkdir(parents=True)
    current=final053
    for alias,selected in (('attrib',attrib),('data',art)):
        mapping=owned(folder/(alias+'.txt'))
        mapping.write_text(''.join(r['member']+'='+r['path']+'\n' for r in selected),encoding='utf-8')
        target=owned(folder/('attrib-stage.sga' if alias=='attrib' else 'community_civilization_pack.sga'))
        result=command('set-members',current,mapping,target,'--alias',alias,timeout=240)
        write(folder/(alias+'-assembly.json'),result);current=target
    listing=command('list',current,'--verify')
    if not listing['archive']['verification']['verified']:raise ValueError('CRC verification failed')
    before=read(OUT/'baseline/listing060.json')
    expected={r['member'] for r in attrib if r['before_sha256'] is None}
    if len(expected)!=80:raise ValueError('Expected80privateidentityresources')
    delta=mount_delta(before,listing,expected)
    write(folder/'listing.json',listing)
    write(folder/'receipt.json',{'schema':'ccp-061-blueprint-mount-repair/v1',
        'status':'correct_native_mounts_crc_verified_pending_full_byte_readback',
        'baseline_sga_sha256':SGA060_SHA,'candidate':str(current),'candidate_sha256':sha(current),
        'toc_changes':delta,'expected_member_hashes':frozen['archive_members'],
        'changed_member_bytes':[],'rebuilt_from_final053_sha256':sha(final053),
        'handoff_sha256':sha(OLD/'integration/final-binding-handoff-v3.json'),
        'native_match_verified':False})
    print('Corrected80privateblueprint mounts: '+str(current));print(sha(current))


if __name__=='__main__':main()

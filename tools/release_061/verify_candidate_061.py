"""Full byte and mount regression against exact060, plus explicit Castle repairs."""
import argparse
from common import *
from repair_archive_mounts_061 import validate_tocs,mount_delta


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--label',required=True)
    ap.add_argument('--delta',type=Path);args=ap.parse_args();guard();frozen=baseline()
    import re
    if not re.fullmatch('[a-z0-9-]{1,25}',args.label):raise ValueError('Safe new evidence label required')
    candidate=owned(args.candidate);folder=owned(OUT/'qualification'/args.label)
    if folder.exists():raise FileExistsError('Preserve previous verification')
    delta=read(owned(args.delta))['payloads'] if args.delta else []
    allowed={}
    for row in delta:
        member=row['member']
        existing_model=member.startswith(('art/scenario/cccastle/imperial_citadel/model.',
            'art/scenario/cccastle/resistance_hq/model.','art/scenario/cc050/imperial_citadel_campaign/model.'))
        new_texture=(member.startswith('art/scenario/cc061/') and member.endswith('.rrtex'))
        if not (existing_model or new_texture):
            raise ValueError('Repair outside Castle visual scope')
        if row['before_sha256']!=frozen['archive_members'].get(member,{}).get('sha256'):raise ValueError('Wrong before hash')
        if new_texture and member in frozen['archive_members']:raise ValueError('Unexpected061texture baseline')
        if sha(owned(row['path']))!=row['sha256']:raise ValueError('Repair payload changed')
        if member in allowed:raise ValueError('Duplicate repair member')
        allowed[member]=row
    listing=command('list',candidate,'--verify');validate_tocs(listing)
    if not listing['archive']['verification']['verified']:raise ValueError('Archive verification failed')
    if listing['archive']['name'].replace('-','').lower()!=CFG['project_guid'].replace('-','').lower():raise ValueError('Archive identity changed')
    original=read(OUT/'baseline/listing060.json')
    private={r['path'] for r in original['members'] if r['path'].startswith('attrib/') and r['toc']=='data'}
    if len(private)!=80:raise ValueError('Unexpected060mountbaseline')
    expected_names=set(frozen['archive_members'])|set(allowed)
    if {r['path'] for r in listing['members']}!=expected_names:raise ValueError('Unexpected candidate names')
    existing_listing={'members':[r for r in listing['members'] if r['path'] in frozen['archive_members']]}
    toc=mount_delta(original,existing_listing,private)
    folder.mkdir(parents=True);write(folder/'listing.json',listing)
    digest=sha(candidate);extraction=command('extract',candidate,folder/'members','--filter','.',timeout=240)
    write(folder/'extraction.json',extraction);actual=files(folder/'members')
    if actual.keys()!=expected_names:raise ValueError('Unexpected member additions/removals')
    changed={n for n in actual if actual[n]!=frozen['archive_members'].get(n)}
    if changed!=allowed.keys():raise ValueError('Delta differs from explicit Castle repair allowlist')
    for n,row in allowed.items():
        if actual[n]['sha256']!=row['sha256']:raise ValueError('Wrong repaired bytes')
    if sha(candidate)!=digest:raise ValueError('Candidate changed during verification')
    if files(ROOT/'assets')!=frozen['source']:raise ValueError('Active editable source changed')
    if files(Path(CFG['source_root']))!=frozen['normal']:raise ValueError('Normal edition changed')
    if any(sha(ROOT/n)!=v for n,v in frozen['identities'].items()):raise ValueError('Project identity changed')
    art=read(OUT/'baseline/art-inputs.json')['files']
    for relative,record in art.items():
        p=ROOT/'art'/relative
        if not p.is_file() or sha(p)!=record['sha256'] or p.stat().st_size!=record['bytes']:
            raise ValueError('Prior editable art changed: '+relative)
    protected=read(OLD/'baseline/final053/freeze.json')['preserved053_resources']
    # Castle material edits are allowed by this061fix request; ability remains protected.
    for row in protected:
        if row['member'] not in allowed and actual[row['member']]['sha256']!=row['sha256']:
            raise ValueError('Protected053resource changed outside explicit repair')
    write(folder/'receipt.json',{'schema':'ccp-061-full-candidate-verification/v1',
        'status':'complete_archive_bytes_mounts_source_normal_and_identity_verified',
        'candidate':str(candidate),'candidate_sha256':digest,'baseline_sga_sha256':SGA060_SHA,
        'member_count':len(actual),'changed_members':sorted(changed),'unchanged_member_count':len(actual)-len(changed),
        'mount_changes':toc,'member_hashes':actual,'repair_payloads':delta,
        'source_unchanged':True,'normal_unchanged':True,'identity_unchanged':True,
        'prior_art_file_count':len(art),'prior_art_unchanged':True,
        'native_rendering_verified':False,'native_gameplay_verified':False,'multiplayer_verified':False})
    print('Fullbyte/mountverification passed: '+str(folder/'receipt.json'))


if __name__=='__main__':main()

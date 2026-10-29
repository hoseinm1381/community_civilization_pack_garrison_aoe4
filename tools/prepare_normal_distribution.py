"""Verify a native Normal SGA and prepare the local-play ZIP without installing.

The archive tool is supplied explicitly; the portable source needs no Garrison.
"""
import argparse, hashlib, json, subprocess, zipfile
from pathlib import Path
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
GUID='a743d7d1d7534cf78817e29d8ded7366'

def sha(data):return hashlib.sha256(data).hexdigest()
def normal(data):return '\n'.join(data.decode('utf-8-sig').splitlines())

def prepare(archive, tool, out):
    out.mkdir(parents=True,exist_ok=True)
    def command(*args):
        result=subprocess.run([str(tool),*map(str,args)],capture_output=True,check=True)
        return json.loads(result.stdout.decode('utf-8-sig'))
    listing=command('list','--verify',archive)
    (out/'archive-list.json').write_text(json.dumps(listing,indent=2)+'\n')
    assert listing['archive']['name']==GUID
    assert listing['archive']['verification']['verified']
    entries={row['path'].lower():row for row in listing['members']}
    assert not any('ps_probe_' in name for name in entries)
    instances=list((ROOT/'assets/attrib/instances').rglob('*.xml'))
    for source in instances:
        member='attrib/'+source.relative_to(ROOT/'assets/attrib/instances').with_suffix('.rgd').as_posix().lower()
        assert member in entries,member
    for source in (ROOT/'assets/ui/icons/korea').rglob('*.png'):
        assert source.relative_to(ROOT/'assets').with_suffix('.rrtex').as_posix().lower() in entries

    # Content-addressed readback never overwrites evidence from another build.
    payload=archive.read_bytes(); archive_sha=sha(payload)
    readback=out/'readback'/archive_sha[:16];readback.mkdir(parents=True,exist_ok=True)
    def extract(member):
        target=readback/member
        if not target.exists():
            target.parent.mkdir(parents=True,exist_ok=True)
            command('extract-member',archive,member,target)
        return target
    scripts=[]
    for source in sorted((ROOT/'assets/scar').rglob('*.scar')):
        member=source.relative_to(ROOT/'assets').as_posix().lower()
        assert member in entries,member
        actual=extract(member).read_bytes()
        assert normal(actual)==normal(source.read_bytes()),member
        scripts.append({'member':member,'sha256':sha(actual)})
    research=(readback/'scar/korea/research.scar').read_text(encoding='utf-8-sig')
    assert 'resource_cap_action_player_modifier' not in research
    assert 'math.min(2, player.research.allowances)' in research

    def decode(member):
        raw=extract(member);xml=raw.with_suffix('.xml')
        if not xml.exists():command('decode-rgd',raw,xml)
        return E.parse(xml).getroot()
    times=[]
    repairs=json.loads((ROOT/'docs/korea-construction.json').read_text())['changes']
    for row in repairs:
        member='attrib/'+row['blueprint'].replace('\\','/')+'.rgd'
        decoded=decode(member)
        scopes=decoded.findall("RGDNode[@Type='List']")
        for scope in scopes:
            field=scope.find("RGDNode[@Key='cost_ext']/RGDNode[@Key='time_cost']/RGDNode[@Key='time_seconds']")
            assert field is not None and float(field.get('Value'))==float(row['after']),(member,scope.get('Key'))
        times.append({'member':member,'seconds':float(row['after']),'variants':[s.get('Key') for s in scopes]})
    army=decode('attrib/army/standard_mode/normal_chinese_ha_01.rgd')
    caps=army.findall(".//RGDNode[@Key='resource_max_cap']")
    assert caps and all(float(c.find("RGDNode[@Key='merc_byz']").get('Value'))==100000 for c in caps)
    assert all(float(c.find("RGDNode[@Key='action']").get('Value'))==2 for c in caps)
    resource=decode('attrib/resource_type_info/merc_byz.rgd')
    strings=[n.get('Value') for n in resource.iter('RGDNode')]
    assert 'korea\\bookicon' in strings and 'resources\\resource_olive_oil' in strings

    playable=out/'Community_Civilization_Pack_Normal-local.zip'
    with zipfile.ZipFile(playable,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        z.writestr('Community_Civilization_Pack_Normal/Vietnam_v2.sga',payload)
    with zipfile.ZipFile(playable) as z:
        assert z.testzip() is None
        assert z.namelist()==['Community_Civilization_Pack_Normal/Vietnam_v2.sga']
        assert sha(z.read(z.namelist()[0]))==archive_sha
    assert playable.stat().st_size<600000000
    korean=[r for r in listing['members'] if '/korea/' in r['path']]
    receipt={'archive_sha256':archive_sha,'archive_bytes':len(payload),
        'archive_namespace':GUID,'archive_members':len(entries),'verified_members':listing['archive']['verification']['checked_files'],
        'compiled_local_instances':len(instances),'matching_scar_files':len(scripts),
        'construction_readback':times,'stock_action_cap':2,'literature_cap':100000,
        'korean_exclusive_member_count':len(korean),
        'korean_exclusive_stored_bytes':sum(r['stored_size'] for r in korean),
        'korean_exclusive_decoded_bytes':sum(r['size'] for r in korean),
        'playable_zip':playable.name,'playable_zip_bytes':playable.stat().st_size,
        'playable_zip_sha256':sha(playable.read_bytes()),'scripts':scripts,
        'native_gameplay_after_latest_repairs':'not tested','vram_and_frame_time':'not measured'}
    (out/'package-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('scripts','construction_readback')},indent=2))
    return receipt

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path,required=True)
    parser.add_argument('--archiver',type=Path,required=True)
    parser.add_argument('--output',type=Path,default=ROOT/'output/normal-release')
    args=parser.parse_args();prepare(args.archive.resolve(),args.archiver.resolve(),args.output.resolve())

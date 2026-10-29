"""Check private Korean source, asset budgets and optional native/preservation evidence.

Default checks are portable. --official-cache accepts the current owned archive
snapshot from import_korea.py --prepare; it is not needed by ordinary builds.
"""
import argparse
import csv
import hashlib
import json
import struct
import xml.etree.ElementTree as E
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(official_cache=None, baseline=None, donor=None):
    ledger = json.loads((ROOT/'docs/korea-import.json').read_text())
    base = ROOT/'assets/attrib/instances'
    private = [base/Path(row['private'].replace('\\','/')+'.xml') for row in ledger['instances']]
    assert len(private)==378 and all(p.is_file() for p in private)
    assert len({row['pbg_id'] for row in ledger['instances']})==len(private)
    for row,p in zip(ledger['instances'],private):
        tree=E.parse(p).getroot()
        assert tree.find("uniqueid[@name='pbgid']").get('value')==str(row['pbg_id'])
        for node in tree.iter():
            assert node.get('mod','') in ('',ledger['destination_guid']), (p,node.attrib)
    try:
        from .korea_resource_contract import verify as verify_resources
    except ImportError:
        from korea_resource_contract import verify as verify_resources
    verify_resources(ROOT)
    scars=sorted((ROOT/'assets/scar/korea').glob('*.scar'))
    icons=sorted((ROOT/'assets/ui/icons/korea').rglob('*.png'))
    decoded=0
    for p in icons:
        raw=p.read_bytes(); assert raw[:8]==b'\x89PNG\r\n\x1a\n'
        width,height=struct.unpack('>2I',raw[16:24]);decoded+=width*height*4
    locale=next((ROOT/'assets/locdb').glob('*_en.csv'))
    incoming_ids=set(ledger['localization_map'].values())|{'11990','11991','11992','11993','11994','12000'}
    rows=list(csv.DictReader(locale.open(encoding='utf-8-sig',newline='')))
    assert incoming_ids <= {r['ID'] for r in rows}
    localization_bytes=sum(len(r['Text'].encode('utf-8')) for r in rows if r['ID'] in incoming_ids)
    shared=[base/'army/standard_mode/normal_chinese_ha_01.xml',base/'resource_type_info/merc_byz.xml']
    loading=ROOT/'assets/scar/ccp/loading.scar'
    files=private+shared+scars+icons+[loading]
    result={'source_gate':'passed','private_instances':len(private),'scar_modules':len(scars),'icons':len(icons),
        'tuning_xml_bytes':sum(p.stat().st_size for p in private+shared),
        'shared_resource_overrides':len(shared),
        'shared_loading_scar_bytes':loading.stat().st_size,
        'scar_bytes':sum(p.stat().st_size for p in scars),
        'icon_source_bytes':sum(p.stat().st_size for p in icons),
        'new_localization_text_bytes':localization_bytes,
        'additional_source_bytes':sum(p.stat().st_size for p in files)+localization_bytes,
        'source_deflate_estimate_bytes':sum(len(zlib.compress(p.read_bytes(),9)) for p in files),
        'icon_rgba8_decoded_base_level_bytes':decoded,'icon_rgba8_full_mip_estimate_bytes':(decoded*4+2)//3,
        'additional_custom_3d_geometry':0,'asset_budget_bytes':300000000,
        'final_archive_bytes':None,'final_zip_bytes':None,'incremental_final_zip_bytes':None,
        'native_vram_frame_time':'not measured',
        'note':'Source deflate is a source-only proxy, excluding native RGD/rrtex cooking and archive/ZIP framing. RGBA8 is not measured GPU residency.'}
    assert result['additional_source_bytes']<200000000
    if official_cache:
        official=json.loads(official_cache.read_text())
        missing=[]
        for p in private:
            for node in E.parse(p).getroot().iter('instance_reference'):
                value=node.get('value','')
                if value and not node.get('mod') and value not in official:missing.append((str(p),value))
        assert not missing, missing
        result['current_official_direct_reference_errors']=0
    if baseline:
        saved=json.loads(baseline.read_text())
        changed=[p for p in saved['dirty'] if digest(ROOT/p)!=saved['normal'][p]]
        assert not changed,changed
        result['preserved_dirty_persia_files']=len(saved['dirty'])
        if donor:
            changed=[p for p,h in saved['donor'].items() if digest(donor/p)!=h]
            assert not changed,changed
            result['donor_files_unchanged']=len(saved['donor'])
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official-cache',type=Path)
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--donor',type=Path)
    parser.add_argument('--update-budget',action='store_true')
    args=parser.parse_args()
    result=check(args.official_cache,args.baseline,args.donor)
    if args.update_budget:(ROOT/'docs/korea-budget.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

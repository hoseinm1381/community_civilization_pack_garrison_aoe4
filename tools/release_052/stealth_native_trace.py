"""Read-only extraction of the stock Fort of the Huntress stealth contract."""
from __future__ import annotations
import hashlib, json, subprocess, sys, xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage

CFG=configuration(ROOT)
OUT=Path(CFG['external_root'])/'output/release_052/stealth/official'
ATTRIB=Path('E:/Games/steamapps/common/Age of Empires IV/cardinal/archives/Attrib.sga')
MEMBERS=(
    'attrib/ebps/races/malian/buildings/building_landmark_age3_landmarkf_mal.rgd',
    'attrib/statemodel_schema/buildings/civilizations/malian/landmark_stealth_castle_mal.rgd',
    'attrib/info/buff_info/races/malian/stealth_landmark_aura_mal.rgd',
    'attrib/ebps/races/malian/units/unit_gbeto_2_mal.rgd',
    'attrib/entity_modifier_type.rgd',
    'attrib/type_camouflage.rgd',
    'attrib/modifier_tooltip/camouflage_enable.rgd',
    'attrib/abilities/always_on_abilities/ayyubid_cmp/spy_passive_stealth_dummy_ayy.rgd',
    'attrib/ebps/races/ayyubid_cmp/units/unit_spy_ayy.rgd',
    'attrib/ebps/races/japanese/units/unit_shinobi_2_jpn.rgd',
)
ARCH=Path(CFG['archive_tool'])

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(*args):
    p=subprocess.run([str(x) for x in args],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=120)
    if p.returncode:raise RuntimeError(f'{args!r}\n{p.stdout[-3000:]}\n{p.stderr[-3000:]}')
    return p.stdout

def main():
    check_storage(ROOT,CFG)
    results=[]
    for member in MEMBERS:
        results.append(trace(member))
    target=OUT/'fort-trace.json';target.write_text(json.dumps({'schema':'ccp.release052.stock-stealth-trace/v1',
        'source_archive':str(ATTRIB),'objects':results,'status':'read_only_native_decoded'},indent=2)+'\n',encoding='utf-8')
    print('FORT_TRACE',[(x['member'],len(x['matching_fields'])) for x in results],target)

def trace(member):
    binary=OUT/member
    binary.parent.mkdir(parents=True,exist_ok=True)
    if not binary.exists():run(ARCH,'extract-member',ATTRIB,member,binary)
    decoded=binary.with_suffix('.xml')
    if not decoded.exists():run(ARCH,'decode-rgd',binary,decoded)
    root=ET.parse(decoded).getroot()
    rows=[]
    keywords=('stealth','aura','influence','modifier','ability','range','radius','proximity',
              'requirement','camouflage','revealed','reveal')
    def walk(node,path):
        key=node.get('Key','')
        now=f'{path}/{key}' if key else path
        value=node.get('Value')
        if value is not None and any(s in (now+' '+value).lower() for s in keywords):
            rows.append({'path':now,'value':value})
        for child in node.findall('RGDNode'):walk(child,now)
    for child in root.findall('RGDNode'):walk(child,'')
    return {'member':member,'rgd_sha256':sha(binary),'decoded_sha256':sha(decoded),
            'matching_fields':rows}

if __name__=='__main__':main()

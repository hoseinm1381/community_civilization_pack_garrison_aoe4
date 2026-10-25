"""Inspect installed Showcase resources without executing or changing the mod."""
from pathlib import Path
import hashlib,importlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import check_storage
check_storage(ROOT,CFG)
OUT=ROOT/'output/release_081_animation/showcase-inspection-20261024'
OUT.mkdir(exist_ok=True)
LIB=Path.home()/'AppData/Local/Garrison/library'
group=json.loads((LIB/'groups/modding_showcase_full.json').read_text())
(OUT/'installed-group.json').write_text(json.dumps(group,indent=2))
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent))
rgd=importlib.import_module('garrison.rgd')
archives=[]
for key in ['modding_showcase_mode','modding_showcase_tuning']:
    source=LIB/key/(key+'.sga')
    listing=json.loads(subprocess.check_output([CFG['archive_tool'],'list',str(source),'--verify'],text=True))
    assert listing['archive']['verification']['verified']
    (OUT/(key+'-listing.json')).write_text(json.dumps(listing,indent=2))
    selected=[x['path'] for x in listing['members'] if x['path'].endswith(('.rgd','.scar','.lua','.rhka','.rootmotion','.rgo','.rgm'))]
    argv=[CFG['archive_tool'],'extract',str(source),str(OUT/key)]
    missing=[member for member in selected if not (OUT/key/member).exists()]
    for member in missing:argv+=['--member',member]
    if missing:
        proc=subprocess.run(argv,capture_output=True,text=True);assert proc.returncode==0,proc.stderr
        (OUT/(key+'-extract.log')).write_text(proc.stdout+proc.stderr)
    flattened={}
    for file in (OUT/key).rglob('*.rgd'):
        try:
            decoded=rgd.read(file.read_bytes())
            flattened[str(file.relative_to(OUT/key))]={path:node.value for path,node in rgd.flatten(decoded.nodes) if isinstance(node.value,(str,int,float,bool,type(None)))}
        except Exception as e:
            flattened[str(file.relative_to(OUT/key))]={'decode_error':str(e)}
    (OUT/(key+'-fields.json')).write_text(json.dumps(flattened,indent=2))
    archives.append({'key':key,'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'members':len(listing['members']),'archive_verified':True})
(OUT/'provenance.json').write_text(json.dumps({'archives':archives,'installed_changed':False,'mod_code_executed':False},indent=2))
print('SHOWCASE_INSPECTION',str(OUT))

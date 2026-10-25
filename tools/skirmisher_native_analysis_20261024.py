"""Decode current skirmisher media and read compiled bindings without edits."""
from pathlib import Path
import json,sys,subprocess,importlib.util,importlib,hashlib,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/skirmisher_analysis_20261024';CFG=json.loads((ROOT/'workspace.json').read_text())
sys.path.insert(0,str(ROOT/'tools'));from workspace_support import check_storage
check_storage(ROOT,CFG)
sys.path.insert(0,str(ROOT/'tools/release_079'))
spec=importlib.util.spec_from_file_location('decoder_index',ROOT/'tools/release_079/decode_diagnostic.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
archive=ROOT/'output/release_081/delivery/final-v1/community_civilization_pack.sga'
listing=json.loads(subprocess.check_output([CFG['archive_tool'],'list',str(archive),'--verify']))
module.INDEX=OUT/'private-index.sqlite3'
if not module.INDEX.exists():module.create_index(archive,listing['members'],listing['archive']['name'])
config=json.loads(module.ORIGINAL_INDEX.with_name('game-assets.local.json').read_text());config['index_path']=str(module.INDEX)
empty=OUT/'empty-game/cardinal/archives';empty.mkdir(parents=True,exist_ok=True);config['game_root']=str(empty.parents[1])
(OUT/'private-config.json').write_text(json.dumps(config))
for family in ['skirmisher2','skirmisher4','javelin2']:
    args=[CFG['garrison_core'],'convert','decode-static','--logical-path',f'art/scenario/garrison/cc076/{family}/model.rgm','--config',str(OUT/'private-config.json'),'--index',str(module.INDEX),'--output-root',str(OUT/'decoded'/family)]
    p=subprocess.run(args,capture_output=True,text=True);(OUT/(family+'-decode.log')).write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
sys.path.insert(0,str(Path(CFG['garrison_extension']).parent));rgd=importlib.import_module('garrison.rgd')
readback=ROOT/'output/release_081/delivery/final-v1/readback'
refs={}
for path in (readback/'attrib').rglob('*.rgd'):
    if 'skirmisher' not in path.name:continue
    rows={name:node.value for name,node in rgd.flatten(rgd.read(path.read_bytes()).nodes) if isinstance(node.value,str) and any(w in node.value.lower() for w in ['skirm','javelin','projectile','base_','throw'])}
    if rows:refs[str(path.relative_to(readback))]=rows
(OUT/'compiled-bindings.json').write_text(json.dumps(refs,indent=2))
print('NATIVE_ANALYSIS_COMPLETE')

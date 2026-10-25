"""Record owned rebuild inputs and independently recheck final ZIP artifacts."""
from pathlib import Path
import hashlib,json,zipfile
from email.parser import Parser
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_082_animation'
RES=Path(r'F:\aoe_4_temp\Community_civilization_pack_garrison_temp\resources_082_animation')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(Path(p).read_text())
selected=read(OUT/'encoded-v3/receipt.json');rebuilt=read(OUT/'encoded-rebuild-v1/receipt.json')
for label in selected:assert selected[label]['sha256']==rebuilt[label]['sha256'],label
packages=read(OUT/'delivery-v1/receipts.json')
for receipt in packages:
    path=Path(receipt['zip']);assert sha(path)==receipt['zip_sha256']
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        assert json.loads(z.read('garrison.json'))['details']['version']==receipt['version']
        with z.open('community_civilization_pack.sga') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==receipt['sga_sha256']
base=ROOT/'output/release_081/delivery/final-v1'
assert sha(base/'community_civilization_pack-0.8.1.zip')=='75963810d5b241680fad90ff5b4c4f81cb0ba37f550c3b2e65b103f0250fd3e0'
lock=[]
for path in sorted((RES/'runtime').glob('*.dist-info/METADATA')):
    fields=Parser().parsestr(path.read_text(encoding='utf-8'),headersonly=True)
    lock.append(fields['Name']+'=='+fields['Version'])
assert 'soulstruct-havok==1.5.0' in lock
(RES/'requirements.lock.txt').write_text('\n'.join(sorted(lock))+'\n')
manifest={'required_preserved_rebuild_inputs':True,'python_abi':'cp313-win_amd64','wheels':{p.name:sha(p) for p in sorted((RES/'wheels').glob('*.whl'))},'runtime':str(RES/'runtime'),'lock_sha256':sha(RES/'requirements.lock.txt')}
(RES/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
recipe={'source':str(ROOT/'art/authoring/release_082_animation/v2/buffalo-idle-walk.blend'),'source_sha256':sha(ROOT/'art/authoring/release_082_animation/v2/buffalo-idle-walk.blend'),
        'native_source':str(ROOT/'output/release_081/animation/source/art/civilizations/common/animals/archetypes/base_cattle/base_cattle.rhka'),
        'source_samples_sha256':sha(OUT/'source-v2/samples.json'),'selected_encoding':selected,'owned_runtime_manifest':str(RES/'manifest.json'),
        'byte_identical_rebuild':True,'rebuild_receipt':str(OUT/'encoded-rebuild-v1/receipt.json'),
        'scripts_sha256':{p.name:sha(p) for p in sorted((ROOT/'tools/release_082_animation').glob('*.py'))},
        'integration_recipe':str(OUT/'integration-v2/recipe.json'),'qa':str(OUT/'qa-v2/proof.json'),'packages':packages,
        'native_game_tested':False,'import_tested':False,'save_load_tested':False,'multiplayer_tested':False}
dest=ROOT/'art/recipes/release_082_animation';dest.mkdir(parents=True,exist_ok=True)
(dest/'recipe.json').write_text(json.dumps(recipe,indent=2)+'\n')
(OUT/'completion.json').write_text(json.dumps({'byte_identical_owned_runtime_rebuild':True,'zip_recheck':True,'baseline_081_zip_preserved':True,'recipe':str(dest/'recipe.json'),'source_sha256':recipe['source_sha256'],'native_game_tested':False},indent=2)+'\n')
print('FINAL_VERIFIED',[(r['version'],r['zip_sha256']) for r in packages])

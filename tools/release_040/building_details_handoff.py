"""Freeze the twelve authored detail exports for the native integration worker."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/release_040/buildings/details'
TARGET=ROOT/'art/recipes/release_040/building-details-source.json'
DONORS=json.loads((ROOT/'art/recipes/release_040/buildings-donors.json').read_text(encoding='utf8'))['models']
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
rows=[]
for family in ('blacksmith','stable','archery_range','market'):
    for age in (2,3,4):
        source=OUT/family/f'age{age:02}'/'source.json'
        assert source.exists(),source
        receipt=json.loads(source.read_text(encoding='utf8'))
        assert receipt['family']==family and receipt['age']==age
        directory=Path(receipt['export_dir']);blend=Path(receipt['source_blend'])
        names=('building.json','model.fbx','albedo.png','normal.png','roughness.png','metalness.png')
        hashes={name:sha(directory/name) for name in names}
        assert hashes['building.json']==receipt['manifest_sha256']
        assert hashes['model.fbx']==receipt['fbx_sha256']
        assert sha(blend)==receipt['source_blend_sha256']
        donor=next(row for row in DONORS if row['family']==family and row['age']==age)
        rows.append({'family':family,'age':age,'export_directory':str(directory),
                     'export_sha256':hashes,'editable_blend':str(blend),
                     'editable_blend_sha256':sha(blend),
                     'stock_model_stem':donor['logical_path'].removesuffix('.rgm'),
                     'private_model_stem':receipt['private_model_stem'],
                     'stages':receipt['stages'],
                     'composite_game':receipt['composite_game'],
                     'composite_facade':receipt['composite_facade']})
assert len(rows)==12
TARGET.write_text(json.dumps({'schema':'ccp.release040.building-details-source/v1',
                              'status':'authoring_export_only','models':rows},indent=2)+'\n',encoding='utf8')
print('DETAIL_HANDOFF_READY',len(rows),TARGET)

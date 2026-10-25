"""Read-only native material audit for Castle landmark owner-colour masks.

Extracts only official material references into Castle-owned output, compares the
Garrison static-PBR material with official building/team-colour contracts, and
writes an evidence receipt. It does not edit assets or cook an archive.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import struct
import zlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from common import CFG, EXTERNAL, ROOT as COMMON_ROOT, sha, guarded  # noqa: E402

OUT = EXTERNAL / 'output/castle_next/owner-colour'
OFFICIAL = OUT / 'official'
RECEIPT = OUT / 'owner-colour-audit.json'
DB_PATH = Path(r'C:\Users\RS\AppData\Local\Garrison\Kit\game-assets.sqlite3')
EXTENSION = Path(CFG['garrison_extension'])
ARCHIVER = Path(CFG['archive_tool'])
BLENDER_PYTHON = Path(CFG['blender_python'])
ASSET_ROOT = ROOT / 'art/exports/castle_next/landmarks'
AUTHORING_ROOT = ROOT / 'art/authoring/castle_next/landmarks'
PREPARE_REPORT = OUT / 'owner-colour-prepare.json'

ASSETS = {
    'chinese_keep_age03': 'art/civilizations/chinese/structures/keep/chi_keep_control_age03/chi_keep_control_age03.rrmaterial',
    'english_keep_age03': 'art/civilizations/english/structures/keep/eng_keep_control_age03/eng_keep_control_age03.rrmaterial',
    'english_battering_ram': 'art/civilizations/english/team_weapons/eng_battering_ram/eng_battering_ram.rrmaterial',
}
STATIC_MATERIALS = {
    'keep_detail_staticpbr': EXTERNAL / 'output/castle_next/integration/readback-ccnext-rdet01-a950fc203176/art/scenario/garrison/community_castle_next_details/buildings/detail_keep_age03/model.rrmaterial',
    'monastery_detail_staticpbr': EXTERNAL / 'output/castle_next/integration/readback-ccnext-rdet01-a950fc203176/art/scenario/garrison/community_castle_next_details/buildings/detail_monastery_age03/model.rrmaterial',
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_extract(member: str, archive: Path, dest: Path, expected_size: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    resolved = dest.resolve()
    if not resolved.is_relative_to(OUT.resolve()):
        raise ValueError(f'Extraction target outside assigned owner-colour output: {dest}')
    with tempfile.TemporaryDirectory(prefix='extract-', dir=OUT) as temp:
        staged = Path(temp) / 'resource.rrmaterial'
        result = subprocess.run([str(ARCHIVER), 'extract-member', str(archive), member, str(staged)],
                                capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError:
            payload = {'stdout': result.stdout[-2000:]}
        if not staged.is_file() or staged.stat().st_size != expected_size:
            raise RuntimeError(f'Archive extraction mismatch for {member}: {payload}')
        if dest.exists():
            if sha(dest) != sha(staged):
                raise RuntimeError(f'Existing official material copy differs from source archive: {dest}')
        else:
            os.replace(staged, dest)


def database_record(member: str) -> dict:
    db = sqlite3.connect(f'file:{DB_PATH.as_posix()}?mode=ro', uri=True)
    try:
        row = db.execute('select archive_path, size, product_version, verified from resolved_assets '
                         'where lower(logical_path)=?', (member.lower(),)).fetchone()
    finally:
        db.close()
    if not row:
        raise FileNotFoundError(f'Official game index has no resource: {member}')
    archive = Path(row[0])
    stat = archive.stat()
    return {'member': member, 'archive': str(archive), 'archive_size': stat.st_size,
            'archive_mtime_ns': stat.st_mtime_ns, 'indexed_member_size': row[1],
            'product_version': row[2], 'verified_index_record': bool(row[3])}


def decode_material(path: Path) -> dict:
    # The Garrison codec is compiled for the configured Blender Python (CPython 3.13).
    script = r'''
import json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from garrison_shared import relic_chunky as rc, model_variants as mv
p=Path(sys.argv[2])
rows=[]
for material in rc.load(p).roots:
    if material.tag != b'GMat':
        continue
    one=rc.pack_document([rc.pack_chunk(material.kind, material.tag, material.payload,
        name=material.name, version=material.version)])
    slots=mv.material_slots(one)
    data=next((x.payload[4:].decode('utf-8','replace')
               for x in material.children if x.tag == b'MatD'), None)
    params=slots.get('parameters',{})
    rows.append({'material_name':material.decoded_name,'shader_descriptor':data,
        'texture_slots':slots.get('textures',{}),
        'parameters':{k:params[k] for k in ('secondaryMaskStrength567','secondaryMaskStrength234',
            'mask23LevelMinMax','mask45LevelMinMax','mask67LevelMinMax','options') if k in params}})
print(json.dumps({'path':str(p),'materials':rows}))
'''
    result = subprocess.run([str(BLENDER_PYTHON), '-c', script, str(EXTENSION), str(path)],
                            capture_output=True, text=True, encoding='utf-8', errors='replace', check=True)
    return json.loads(result.stdout)


def source_image_record(path: Path) -> dict:
    row = {'path': str(path.resolve()), 'sha256': sha(path), 'size': path.stat().st_size}
    image_script = r'''
import json,sys
from PIL import Image
im=Image.open(sys.argv[1]).convert('RGBA')
p=list(im.getdata());r=[x[0] for x in p]
print(json.dumps({'size':list(im.size),'mode':'RGBA','red_min':min(r),'red_max':max(r),
 'red_nonzero_fraction':sum(x>0 for x in r)/len(r),'red_white_fraction':sum(x>=250 for x in r)/len(r),
 'green_nonzero_fraction':sum(x[1]>0 for x in p)/len(p),'blue_nonzero_fraction':sum(x[2]>0 for x in p)/len(p)}))
'''
    try:
        result = subprocess.run([str(Path(CFG['python'])), '-c', image_script, str(path)],
                                capture_output=True, text=True, encoding='utf-8', check=True)
        row['image'] = json.loads(result.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError):
        row['image'] = {'inspection': 'Image-channel inspection failed; exact file hash retained'}
    return row


def _safe_child(root: Path, child: Path) -> Path:
    """Resolve a project-relative path and reject symlink/junction escapes."""
    root = root.resolve()
    candidate = child.resolve()
    if not candidate.is_relative_to(root):
        raise ValueError(f'Path escapes candidate project: {child}')
    return candidate


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temp.replace(path)


def _material_source(name: str, rel_paths: dict[str, str]) -> bytes:
    """Build a Garrison source material using the stock structure shader route.

    `roughnessTex` is retained from the four-map Garrison object-PBR authoring
    contract. The installed native structure materials prove `maskTex5`,
    `secondaryMaskStrength567`, `albedoTex`, `normalMap`, and `metalTex`; they do
    not prove that the structure shader consumes a separate roughness texture.
    The candidate therefore preserves that input but records the roughness slot
    as a native-cook qualification item rather than claiming it is supported.
    """
    root = ET.Element('materialSet')
    material = ET.SubElement(root, 'material', {
        'name': name, 'type': 'shader', 'source': 'structure'})
    params = [
        ('g_emissiveFactor', 'float', '1'),
        ('albedoTex', 'tex2D', rel_paths['albedo']),
        ('normalMap', 'tex2D', rel_paths['normal']),
        ('metalTex', 'tex2D', rel_paths['metalness']),
        ('roughnessTex', 'tex2D', rel_paths['roughness']),
        ('maskTex5', 'tex2D', rel_paths['pattern']),
        ('albedoTex7', 'tex2D', rel_paths['albedo']),
        ('metalTex7', 'tex2D', rel_paths['metalness']),
    ]
    # The native structure burner resolves defaults from source PNGs, which
    # are absent in the distributed kit. Bind every measured stock texture
    # slot explicitly. Inactive layers receive the same atlas; masks disable
    # overlays and make the atlas fully opaque.
    audit=json.loads(RECEIPT.read_text(encoding='utf-8'))
    names=audit['shader_profiles']['english_battering_ram'][0]['texture_slot_names']
    supplied={p[0] for p in params}
    for slot in names:
        if slot=='__default' or slot in supplied:continue
        if slot.startswith('normalMap'):path=rel_paths['normal']
        elif slot.startswith('metalTex'):path=rel_paths['metalness']
        elif slot.startswith('albedoTex') or slot.endswith('Albedo'):path=rel_paths['albedo']
        elif slot=='maskAlpha':path=rel_paths['white']
        else:path=rel_paths['black']
        params.append((slot,'tex2D',path))
    for key, kind, value in params:
        ET.SubElement(material, 'param', {'name': key, 'type': kind, 'value': value})
    return (ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n')

def structure_parameters():
    """Stock shader constants, neutral atlas grading, documented team mask."""
    sys.path.insert(0,str(EXTENSION))
    from garrison_shared import model_variants as mv
    audit=json.loads(RECEIPT.read_text(encoding='utf-8'))
    source=Path(audit['official_sources']['english_battering_ram']['file'])
    assert sha(source)==audit['official_sources']['english_battering_ram']['sha256']
    params={key:value['values'] for key,value in mv.material_slots(source.read_bytes())['parameters'].items()}
    for key in params:
        if any(key.startswith(s) for s in ('highlightColor','midtoneColor','shadowColor')):params[key]=['.5','.5','.5','1']
        if key.startswith('heightBias'):params[key]=['0','0','0','0']
    params.update({'secondaryMaskStrength567':['0','.57','0','0'],
                   'secondaryMaskStrength234':['0','0','0','0'],
                   'mask23LevelMinMax':['0','1','0','1'],
                   'mask45LevelMinMax':['0','1','0','1'],
                   'mask67LevelMinMax':['0','1','0','1']})
    return params


def prepare_project(project, assets) -> dict:
    """Prepare an isolated owner-colour material candidate after registration.

    `project` is the registered Garrison mod-project root. `assets` is the same
    row sequence returned by `cook.asset_inputs('landmarks')`; each row needs
    `key`, and may supply `pattern_path`. This function never edits that source
    project: it copies it into this script's owned `OUT/candidate-project-*`
    directory, then changes the cloned source material and its tracked hashes.
    It returns the candidate root for a later, separately authorized cook.
    """
    guarded()
    source_project = Path(project).resolve()
    if not (source_project / 'mod-project.json').is_file():
        raise FileNotFoundError(f'Registered Garrison project missing mod-project.json: {source_project}')
    config = json.loads((source_project / 'mod-project.json').read_text(encoding='utf-8'))
    if config.get('schema') != 'garrison.mod-project/v1':
        raise ValueError(f'Unsupported project schema: {config.get("schema")!r}')
    rows = list(assets)
    required = {'imperial_citadel', 'resistance_hq'}
    if {row.get('key') for row in rows} != required:
        raise ValueError(f'Expected exactly both registered Castle landmarks: {sorted(required)}')
    input_hash = sha(source_project / 'mod-project.json')
    token = hashlib.sha256((str(source_project).lower() + ':' + input_hash+':defaults-v4-native-parameters').encode()).hexdigest()[:12]
    candidate_root = OUT / f'candidate-project-{token}' / source_project.name
    if candidate_root.exists():
        raise FileExistsError(f'Append-only candidate already exists; inspect before reuse: {candidate_root}')
    candidate_parent = candidate_root.parent
    candidate_parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_project, candidate_root, ignore=shutil.ignore_patterns('.garrison.lock'))

    copied = json.loads((candidate_root / 'mod-project.json').read_text(encoding='utf-8'))
    by_name = {row['name']: row for row in copied.get('buildings', [])}
    if set(by_name) != required:
        raise ValueError(f'Candidate project does not contain exactly two landmark registrations: {sorted(by_name)}')
    detail_rows = []
    for asset in rows:
        key = asset['key']
        building = by_name[key]
        directory = building['directory'].replace('/', '\\')
        source_dir = _safe_child(candidate_root, candidate_root / 'project/source' / Path(directory))
        material_path = _safe_child(candidate_root, source_dir / 'model.material')
        if not material_path.is_file():
            raise FileNotFoundError(f'Registered source material missing for {key}: {material_path}')
        source_material = ET.parse(material_path).getroot()
        materials = source_material.findall('material')
        if len(materials) != 1:
            raise ValueError(f'Expected a single atlas material in {material_path}; found {len(materials)}')
        material_name = materials[0].get('name')
        if not material_name:
            raise ValueError(f'Material name missing in {material_path}')
        pattern = Path(asset.get('pattern_path') or AUTHORING_ROOT / key / 'pattern.png').resolve()
        if not pattern.is_file():
            raise FileNotFoundError(f'Pattern source missing for {key}: {pattern}')
        destination_pattern = _safe_child(candidate_root, source_dir / 'pattern.png')
        if destination_pattern.exists():
            raise FileExistsError(f'Candidate pattern path already exists: {destination_pattern}')
        shutil.copyfile(pattern, destination_pattern)
        rel = lambda filename: (Path(directory) / filename).as_posix().replace('/', '\\')
        params = {
            'albedo': rel('albedo.png'),
            'normal': rel('normal.png'),
            'metalness': rel('metalness.png'),
            'roughness': rel('roughness.png'),
            'pattern': rel('pattern.png'),
            'white': rel('default_white.png'),
            'black': rel('default_black.png'),
        }
        def solid_png(path,value):
            def chunk(tag,data):return struct.pack('>I',len(data))+tag+data+struct.pack('>I',zlib.crc32(tag+data)&0xffffffff)
            raw=b''.join(b'\x00'+bytes((value,value,value,255))*4 for _ in range(4))
            path.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',4,4,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b''))
        for filename,value in (('default_white.png',255),('default_black.png',0)):
            target=source_dir/filename;solid_png(target,value)
            building['files'][rel(filename).replace('\\','/')]=sha(target)
        for filename in ('albedo.png', 'normal.png', 'metalness.png', 'roughness.png'):
            if not (source_dir / filename).is_file():
                raise FileNotFoundError(f'Registered PBR map missing for {key}: {source_dir / filename}')
        material_bytes = _material_source(material_name, params)
        material_path.write_bytes(material_bytes)
        for relpath, file_path in ((rel('model.material'), material_path), (rel('pattern.png'), destination_pattern)):
            building['files'][relpath.replace('\\', '/')] = sha(file_path)
        detail_rows.append({
            'key': key,
            'material_name': material_name,
            'material_path': str(material_path),
            'material_sha256': sha(material_path),
            'pattern_source': str(pattern),
            'pattern_source_sha256': sha(pattern),
            'pattern_candidate': str(destination_pattern),
            'pattern_candidate_sha256': sha(destination_pattern),
            'texture_parameters': params,
            'structure_shader_parameters': {
                'source': 'structure',
                'maskTex5': params['pattern'],
                'secondaryMaskStrength567': {'type': 'float4', 'value': '0 0.57 0 0'},
                'pbr_maps': {'albedoTex': params['albedo'], 'normalMap': params['normal'],
                             'metalTex': params['metalness'], 'roughnessTex': params['roughness']},
            },
        })
    _atomic_json(candidate_root / 'mod-project.json', copied)
    report = {
        'schema': 'community-civilization-pack/castle-owner-colour-candidate/v1',
        'status': 'isolated_structure_shader_candidate_pending_native_cook',
        'candidate_revision': 4,
        'parameter_postprocess':'Garrison model_variants.rewrite_material applies typed Float4 after native source cook; float4 source XML is not used.',
        'source_project': str(source_project),
        'source_project_config_sha256': input_hash,
        'candidate_project': str(candidate_root),
        'candidate_project_config_sha256': sha(candidate_root / 'mod-project.json'),
        'assets': detail_rows,
        'provenance': {
            'material_source_format': 'Garrison source materialSet XML, observed in frozen release_040 landmark project model.material files.',
            'structure_shader_contract': 'Official decoded Chinese/English building RRMaterials use GMat descriptor structure and include maskTex5 and secondaryMaskStrength567; installed Garrison new-units-and-maps guide sets maskTex5 red to team colour and strength567 to 0 0.57 0 0.',
            'parameter_type_provenance': 'RRMaterial readback identifies secondaryMaskStrength567 as Float4; source XML scalar/texture parameter syntax is observed in Garrison-generated object materials. The float4 XML serialization must be confirmed by candidate cook.',
            'limits': [
                'This is an isolated candidate only; no cook or runtime owner-colour test has run.',
                'Official structure materials prove albedoTex, normalMap, and metalTex texture slots; a separate roughnessTex slot on structure is unverified and retained as a candidate mapping from the atlas.',
                'maskTex5 PNG-to-RRTex conversion and UV channel alignment require native cook/readback and match qualification.'
            ],
        },
    }
    _atomic_json(PREPARE_REPORT, report)
    return report


def run() -> dict:
    guarded()
    if not DB_PATH.is_file():
        raise FileNotFoundError(f'Read-only Garrison official asset index missing: {DB_PATH}')
    OFFICIAL.mkdir(parents=True, exist_ok=True)
    stock = {}
    for key, member in ASSETS.items():
        provider = database_record(member)
        target = OFFICIAL / member
        safe_extract(member, Path(provider['archive']), target, provider['indexed_member_size'])
        provider['file'] = str(target.resolve())
        provider['sha256'] = sha(target)
        provider['decoded'] = decode_material(target)
        stock[key] = provider

    generated = {}
    for key, path in STATIC_MATERIALS.items():
        if path.is_file():
            generated[key] = {'path': str(path.resolve()), 'sha256': sha(path),
                              'decoded': decode_material(path)}
        else:
            generated[key] = {'status': 'missing', 'expected_path': str(path)}

    patterns = {}
    for family in ('imperial_citadel', 'resistance_hq'):
        candidates = [AUTHORING_ROOT / family / 'pattern.png', ASSET_ROOT / family / 'pattern.png']
        source = next((p for p in candidates if p.is_file()), None)
        patterns[family] = source_image_record(source) if source else {'status': 'missing'}

    guide = EXTENSION / 'guide/new-units-and-maps.html'
    guide_text = guide.read_text(encoding='utf-8') if guide.is_file() else ''
    guide_evidence = {
        'path': str(guide.resolve()) if guide.is_file() else str(guide),
        'sha256': sha(guide) if guide.is_file() else None,
        'anchor': 'a-model-painted-differently-model-variants',
        'contract': 'Slot maskTex5 red means team colour. Documented parameter value: secondaryMaskStrength567 = 0 0.57 0 0.',
        'contract_present_in_installed_guide': ('maskTex5' in guide_text and '0.57' in guide_text and 'team colour here' in guide_text),
    }

    shader_profiles = {}
    for key, row in {**stock, **generated}.items():
        materials = row.get('decoded', {}).get('materials', [])
        shader_profiles[key] = [{'name': mat['material_name'],
            'descriptor': mat.get('shader_descriptor'),
            'has_maskTex5': 'maskTex5' in mat.get('texture_slots', {}),
            'maskTex5': mat.get('texture_slots', {}).get('maskTex5'),
            'strength567': mat.get('parameters', {}).get('secondaryMaskStrength567'),
            'object_owner_mask_slot': next((slot for slot in mat.get('texture_slots', {})
                if 'pattern' in slot.lower() or 'owner' in slot.lower() or 'team' in slot.lower()), None),
            'texture_slot_names': sorted(mat.get('texture_slots', {}))} for mat in materials]

    receipt = {
        'schema': 'community-civilization-pack/castle-owner-colour-audit/v1',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'native_stock_contract_identified_custom_static_binding_unqualified',
        'official_sources': stock,
        'existing_garrison_static_materials': generated,
        'landmark_pattern_sources': patterns,
        'installed_guide_evidence': guide_evidence,
        'shader_profiles': shader_profiles,
        'evidence_conclusion': {
            'garrison_static_shader': 'GMat descriptor object; current Garrison readback exposes albedoTexture, normalMap, metalTex, and g_emissiveFactor; no pattern/team/owner texture slot is emitted.',
            'native_stock_team_colour_recipe': 'Installed Garrison guide new-units-and-maps.html documents the stock eng_battering_ram structure material variant: red in maskTex5 means team colour; set secondaryMaskStrength567 to 0 0.57 0 0.',
            'native_building_shader': 'Official English and Chinese building materials use the same structure descriptor and expose maskTex5 plus secondaryMaskStrength567. Chinese keep main has 0.11,0.69,0,0 and English keep main has 0.91,0.48,0,0. The guide specifically qualifies the ram variant, so building response on the custom atlas still needs a native reference cook/match check.',
            'safe_boundary': 'No active XML, Blender scene, Garrison project, or native archive was changed/cooked. Official resources were extracted read-only from the indexed game archives into this owned output folder.',
            'remaining_gate': 'Need isolated supported image-to-RRTex generation for each pattern PNG and an integration-agent/root-authorized native reference cook of a candidate structure material on the actual custom static mesh before claiming team-colour binding.'
        },
        'limitations': ['No native cook or in-game owner-colour check was run.',
                        'The Garrison guide qualifies maskTex5 on the English ram model variant; equivalent owner-colour response on a custom staticPBR/structure-shader mesh is not yet qualified.'],
    }
    temporary = RECEIPT.with_suffix('.tmp')
    temporary.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    temporary.replace(RECEIPT)
    print(json.dumps({'status': receipt['status'], 'receipt': str(RECEIPT),
                      'sha256': sha(RECEIPT), 'official_materials': list(stock),
                      'pattern_sources': list(patterns)}, indent=2))
    return receipt


if __name__ == '__main__':
    run()

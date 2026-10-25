"""Isolated local recording recipes; cloud originals and recipe IDs stay immutable."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess

VOICES = dict(CIV_M='Hải Đăng', CIV_F='Ngọc Huyền', SCOUT='Xuân Vĩnh',
              SCOUT_F='Trúc Ly', INFANTRY='Quốc Tuấn', INFANTRY_F='Đoan Trang',
              ARCHER='Phạm Tuyên', SKIRMISHER='Thiện Minh', CROSSBOW='Minh Đức',
              GUNNER='Thanh Bình', CAVALRY='Adam bựa', MONK='Thiền Tâm Đức',
              TRADER='Hải Đăng', SIEGE='Quốc Tuấn', NAVAL_FISH='Xuân Vĩnh',
              NAVAL_TRADE='Phạm Tuyên', NAVAL_MILITARY='Minh Đức',
              NAVAL_TRANSPORT='Thanh Bình', NAVAL_FIRE='Thiện Minh')
SDK_REVISION = '04044e1b8f822f946bafb2c88b716459f4164152'
MODEL_REVISION = '61b85e3d937fbbacb387714180e8182823512523'


def local_guard():
    # Workspace's established junction check uses pathlib.is_junction (Python 3.12+).
    # Keep that validator unchanged; the CUDA runtime deliberately uses Python 3.11.
    root = Path(__file__).resolve().parents[2]
    configured_python = json.loads((root / 'workspace.json').read_text())['python']
    subprocess.run([configured_python, '-c',
        "import sys; sys.path.insert(0,'tools/release_084'); from pipeline import guard; guard()"],
        cwd=str(root), check=True, capture_output=True)


def local_jobs(source, voices, revision):
    result = []
    for original in source:
        job = copy.deepcopy(original)
        job['cloud_recipe_id'] = original['id']
        job['casting'] = dict(provider='local-vieneu', model='VieNeu-TTS-v3-Turbo',
                              voice=voices[job['role']], revision=revision)
        if job.get('kind') == 'nonverbal_effort':
            job['performance_recipe'] = 'phonetic-effort-v1'
            job['phonetic_input'] = effort_input(job)
        recipe = {k: v for k, v in job.items() if k != 'id'}
        job['id'] = hashlib.sha256(json.dumps(recipe, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        result.append(job)
    return result


def take_seed(job_id, attempt):
    if attempt not in range(3):
        raise ValueError('Local retakes are limited to three attempts')
    return int(hashlib.sha256(f'{job_id}:{attempt}'.encode()).hexdigest()[:8], 16)


def synthesis_text(job):
    if job['kind'] != 'dialogue':
        raise ValueError('Nonverbal local delivery requires a separately qualified recipe')
    return job['text']


def effort_input(job):
    if job.get('kind') != 'nonverbal_effort' or job.get('event') not in ['death','pain_light']:
        raise ValueError('Unsupported local effort recipe')
    number = job['phrase_number']
    if number not in range(1,7): raise ValueError('Effort alternative outside approved six-line pool')
    vowel = ['Hự','Ư','Á','Hừ','A','Ơ'][number-1]
    return vowel + ('...' if job['event']=='death' else '!')


def performance_text(job):
    if job.get('kind') == 'dialogue': return synthesis_text(job)
    if job.get('performance_recipe') != 'phonetic-effort-v1' or job.get('phonetic_input') != effort_input(job):
        raise ValueError('Unqualified or changed local effort recipe')
    return job['phonetic_input']


def text_qualified_roles(results, roles):
    return {role for role in roles if all(
        sum(results.get(f'{role}-{context}-T{take}', {}).get('text_match') is True for take in range(1, 4)) >= 2
        for context in ['calm', 'urgent', 'quiet'])}


def actor_qualified_roles(results, voices):
    passed = {}
    for role, voice in voices.items():
        for context in ['calm', 'urgent', 'quiet']:
            hashes = passed.setdefault((voice, context), set())
            for take in range(1, 4):
                row = results.get(f'{role}-{context}-T{take}', {})
                if row.get('text_match') is True: hashes.add(row['sha256'])
    return {role for role, voice in voices.items() if all(len(passed.get((voice, context), ())) >= 2
            for context in ['calm', 'urgent', 'quiet'])}


def local_manifest(source, voices=None):
    voices = voices or VOICES
    jobs = local_jobs(source['jobs'], voices, MODEL_REVISION + ':' + SDK_REVISION)
    remap = {j['cloud_recipe_id']: j['id'] for j in jobs}
    result = copy.deepcopy(source)
    result['schema'] = 'ccp-084-local-recording-manifest/v1'
    result['jobs'] = jobs
    for alias in result['aliases']: alias['job'] = remap[alias['job']]
    for pool in result.get('pools', []): pool['jobs'] = [remap[key] for key in pool['jobs']]
    result['qualification'] = 'candidate only; pronunciation, acting and nonverbal delivery pending local auditions'
    result['voice_reuse'] = {v: [k for k, voice in voices.items() if voice == v]
                           for v in set(voices.values()) if list(voices.values()).count(v) > 1}
    result['voice_reuse_reason'] = 'Shared Northern preset actors perform independent role-specific recordings; no cross-role audio aliases.'
    return result

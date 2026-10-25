"""Explicit delivery scope; never rewrite historical generation recipes/state."""
import copy
import json
from pipeline import digest
from providers import OUT


def spoken_manifest(manifest):
    result=copy.deepcopy(manifest)
    if any(j.get('kind') not in {'dialogue','nonverbal_effort'} for j in manifest['jobs']):
        raise ValueError('Unknown job kind in spoken delivery scope')
    keep={j['id'] for j in manifest['jobs'] if j['kind']=='dialogue'}
    for pool in manifest['pools']:
        inside=set(pool['jobs']) & keep
        if inside and inside!=set(pool['jobs']):raise ValueError('Mixed dialogue/effort response pool')
    result['jobs']=[j for j in result['jobs'] if j['id'] in keep]
    result['aliases']=[a for a in result['aliases'] if a['job'] in keep]
    result['pools']=[p for p in result['pools'] if set(p['jobs'])<=keep]
    return result


def delivery_manifest(manifest):
    policy_file=OUT/'local/delivery-scope.json'
    if not policy_file.exists():return manifest
    policy=json.loads(policy_file.read_text())
    if (policy.get('user_approved') is not True or policy.get('scope')!='spoken-dialogue-with-stock-efforts' or
        policy.get('generation_manifest_sha256')!=digest(OUT/'local/recording-manifest.json')):
        raise RuntimeError('Delivery scope approval does not match frozen generation recipes')
    return spoken_manifest(manifest)


def require_stock_effort_preservation(proof):
    if not proof or proof.get('stock_effort_preservation_complete') is not True:
        raise RuntimeError('Spoken-only delivery must preserve original stock pain/death sounds before suppression')

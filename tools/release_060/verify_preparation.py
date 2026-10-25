"""Verify preparation preservation without treating concurrent work as our own."""
import json
from pathlib import Path
from common import ROOT, CFG, OUT, STAGING, files, guard, read, sha, write

def validate_freeze(freeze):
    if freeze.get('schema') != 'ccp-060-preparation-freeze/v1' or freeze.get('status') != 'preparation-only-not-final-release-baseline':
        raise ValueError('Unexpected preparation freeze schema/status')
    expected = (STAGING/'preparation-source/assets').resolve()
    if Path(freeze.get('source_snapshot','')).resolve() != expected:
        raise ValueError('Preparation snapshot path does not match owned staging')
    if not isinstance(freeze.get('inputs'),dict):
        raise ValueError('Preparation freeze has no input inventory')
    for section in ('assets','normal','prior_art','identities'):
        if not isinstance(freeze['inputs'].get(section),dict):
            raise ValueError(f'Preparation freeze missing {section}')
    return expected

def differences(expected, actual):
    return {'added': sorted(set(actual)-set(expected)),
            'removed': sorted(set(expected)-set(actual)),
            'changed': sorted(k for k in set(expected)&set(actual) if expected[k]!=actual[k])}

def main():
    guard()
    freeze = read(OUT/'baseline/preparation-freeze.json')
    snapshot = validate_freeze(freeze)
    original = freeze['inputs']
    checks = {'frozen_source_copy': differences(original['assets'],files(snapshot,reject_links=True)),
              'normal_edition': differences(original['normal'],files(CFG['source_root'])),
              'active_source': differences(original['assets'],files(ROOT/'assets'))}
    for part, expected in original['prior_art'].items():
        checks['prior_art_'+part] = differences(expected,files(ROOT/'art'/part))
    current_identity = {name:sha(ROOT/name) for name in original['identities']}
    checks['identities'] = differences(original['identities'],current_identity)
    preserved = all(not any(delta.values()) for delta in checks.values())
    report = {'schema':'ccp-060-preparation-preservation/v1',
              'status':'unchanged' if preserved else 'drift-requires-attribution',
              'checks':checks,
              'note':'Concurrent landmark work may change active inputs; inspect drift, never overwrite or refresh the preparation freeze to hide it.'}
    write(OUT/'preparation-preservation.json',report)
    print(json.dumps(report,indent=2))
    return 0 if preserved else 2

if __name__=='__main__':
    raise SystemExit(main())

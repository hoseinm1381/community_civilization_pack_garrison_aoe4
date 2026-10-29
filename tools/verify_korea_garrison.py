"""Portable Korea/Garrison preservation pins for this candidate's exact scope."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(data):return hashlib.sha256(data).hexdigest()


def verify(root=ROOT):
    doc=json.loads((root/'docs/korea-garrison-port.json').read_text())
    for rel,digest in doc['unchanged_baseline_assets'].items():
        assert sha((root/rel).read_bytes())==digest,('Unrelated Garrison source changed',rel)
    for rel,digest in doc['korean_tuning_and_icons'].items():
        assert sha((root/rel).read_bytes())==digest,('Korean source translation differs',rel)
    for rel,digest in doc['korean_scar_normalized'].items():
        data=(root/rel).read_text(encoding='utf-8-sig').encode()
        assert sha(data)==digest,('Korean behavior differs',rel)
    prefix=doc['preserved_locale_prefix']
    assert sha((root/prefix['file']).read_bytes()[:prefix['bytes']])==prefix['sha256']
    assert len(doc['changed_existing_assets'])==5
    assert len(doc['new_assets'])==425
    mode=(root/'assets/scar/winconditions/VietnamMode.scar').read_text()
    assert mode.count('VietnamVoice_Start(state.civilizations)')==2
    assert mode.count('VietnamPresentation_Update()')==1
    assert 'KoreaLifecycle_Start(state.civilizations)' in mode
    assert 'KoreaLifecycle_Cleanup()' in mode
    return dict(status='passed',preserved_baseline_assets=len(doc['unchanged_baseline_assets']),
                private_korean_definitions=378,added_assets=425,changed_existing_assets=5)


if __name__=='__main__':print(json.dumps(verify(),indent=2))

"""Immutable 0.7.4 baseline for the seven-building visual revision."""
from pathlib import Path
import hashlib, json, shutil, subprocess, sys, zipfile

ROOT = Path(__file__).resolve().parents[2]
CFG = json.loads((ROOT/'workspace.json').read_text())
OUT = ROOT/'output/release_075/baseline'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    sys.path.insert(0, str(ROOT/'tools'))
    from workspace_support import check_storage
    check_storage(ROOT, CFG)
    if OUT.exists():
        raise RuntimeError('Baseline exists; never refresh an immutable freeze')
    delivery = ROOT/'output/release_074/delivery'
    proof = json.loads((ROOT/'output/release_074/delivery-proof.json').read_text())
    assert sha(delivery/'community_civilization_pack-0.7.4.zip') == proof['zip_sha256']
    assert sha(delivery/'community_civilization_pack.sga') == proof['sga_sha256']
    subprocess.run([CFG['python'], '-B', str(ROOT/'tools/release_073/check_identity.py'), '--archive', str(delivery/'community_civilization_pack.sga')], check=True)
    OUT.mkdir(parents=True)
    protected = {}
    for folder in ('assets', 'art/authoring', 'art/exports', 'art/recipes', 'tools', 'docs'):
        for p in sorted((ROOT/folder).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts and 'release_075' not in p.parts:
                protected[p.relative_to(ROOT).as_posix()] = sha(p)
    for name in (CFG['project_file'], 'workspace.json', 'STORAGE.md'):
        protected[name] = sha(ROOT/name)
    normal = Path(CFG['source_root'])
    normal_hashes = {p.relative_to(normal).as_posix(): sha(p) for p in sorted((normal/'assets').rglob('*')) if p.is_file()}
    for p in normal.glob('*.aoe4mod'):
        normal_hashes[p.name] = sha(p)
    for name, value in [('protected.json', protected), ('normal.json', normal_hashes), ('delivery.json', proof)]:
        (OUT/name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')
    with zipfile.ZipFile(OUT/'source.zip', 'x', zipfile.ZIP_DEFLATED) as z:
        for rel in protected:
            if rel.startswith('assets/') or rel in (CFG['project_file'], 'workspace.json'):
                z.write(ROOT/rel, rel)
    for name in ('community_civilization_pack-0.7.4.zip','community_civilization_pack.sga'):
        shutil.copy2(delivery/name, OUT/name)
        assert sha(OUT/name) == sha(delivery/name)
    shutil.copy2(ROOT/'output/release_074/verification-v1.json', OUT/'package-members.json')
    (OUT/'complete.json').write_text(json.dumps({'protected_files':len(protected),'normal_files':len(normal_hashes),'native_acceptance':'not asserted','baseline':'0.7.4'},indent=2)+'\n')
    print((OUT/'complete.json').read_text())

if __name__ == '__main__': main()

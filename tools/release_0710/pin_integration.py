"""Pin independently reviewed payloads and the preserved editable rebuild inputs."""
from common import *
from package_policy import merge_payloads

def main():
    guard()
    receipts=[OUT/'buffalo/payload.json',OUT/'hideout/payload.json',OUT/'hud/receipt.json']
    groups=[]
    for path in receipts:
        receipt=read(path)
        assert receipt.get('proof_files'),('Missing proof hashes',path)
        for p,h in receipt['proof_files'].items():assert sha(p)==h,('Stale proof',p)
        groups.append(receipt['members'])
    payload=merge_payloads(groups)
    files=[]
    for folder in (ART,EXPORT,RECIPES,ROOT/'tools/release_0710'):
        files.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts
                     and p != RECIPES/'integration.json' and p.suffix != '.blend1')
    files.extend([ROOT/'tools/build_release_0710.ps1',ROOT/'tests/test_hud_0710.py'])
    write(RECIPES/'integration.json',{'version':'0.7.10','reviewed':True,
        'baseline_sga_sha256':EXPECTED,
        'payload_receipts':[{'file':str(p),'sha256':sha(p)} for p in receipts],
        'rebuild_input_hashes':{str(p):sha(p) for p in sorted(set(files))},
        'allowlisted_members':sorted(payload),
        'influence_resize':'omitted under explicit approved fallback',
        'native_game_tested':False})
    print('PINNED',len(payload),'members',len(set(files)),'rebuild inputs')

if __name__=='__main__':main()

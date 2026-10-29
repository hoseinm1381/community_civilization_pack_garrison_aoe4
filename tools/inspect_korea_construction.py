"""Read-only current official evidence and compact pre-repair receipt."""
import gzip, hashlib, json, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as E
import official_archive

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'work/korea_construction_20261029'
OUT.mkdir(exist_ok=True)
if not (OUT/'before.json').exists():
    files = list((ROOT/'assets').rglob('*'))
    (OUT/'before.json').write_text(json.dumps({str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()},indent=2))
    (OUT/'before.patch').write_bytes(subprocess.check_output(['git','diff','--binary'],cwd=ROOT))
    for name in ('research.scar','lifecycle.scar'):
        (OUT/(name+'.gz')).write_bytes(gzip.compress((ROOT/'assets/scar/korea'/name).read_bytes()))

archive = official_archive.archive_path()
data = {}
for name, raw in official_archive.members(archive, lambda n: n.endswith('.xml') and (
    'chinese_ha_01' in n or 'modifier' in n or n.startswith('instances\\ebps\\races\\chinese\\buildings\\')
    or n.startswith('instances\\ebps\\races\\common\\buildings\\')
    or n.startswith('instances\\ebps\\races\\core\\buildings\\'))):
    data[name] = raw.decode('utf-8-sig')
(OUT/'official.json').write_text(json.dumps(data))
print('OFFICIAL_RECORDS',len(data))

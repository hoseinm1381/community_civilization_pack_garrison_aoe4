"""Read native RGM bounds using installed Garrison parser; no cook or mutation."""
import bpy, importlib.util, os, sys, json, struct
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(os.environ['APPDATA'])/'Blender Foundation/Blender/5.2/extensions/raw_githubusercontent_com/garrison'
s=importlib.util.spec_from_file_location('garrison_shared',str(E/'garrison_shared.cp313-win_amd64.pyd'));m=importlib.util.module_from_spec(s);sys.modules['garrison_shared']=m;s.loader.exec_module(m)
from garrison_shared import relic_chunky as rc
rows=[]
for age in range(1,5):
 d=json.loads(next((R/f'art/stock_cache/houses_010/age{age:02}').rglob('decoded-static.json')).read_text());raw=Path(d['resources']['model']['cache_path']).read_bytes();doc=rc.parse(raw)
 chunks=[{'offset':c.offset,'tag':c.tag.decode(),'payload_size':len(c.payload),'float_values':list(struct.unpack('<'+'f'*(len(c.payload)//4),c.payload)) if len(c.payload)%4==0 and len(c.payload)<=128 else None} for c in rc.walk(doc.roots) if c.tag in [b'BBOX',b'BOUN']]
 rows.append({'age':age,'source_rgm':d['resources']['model']['cache_path'],'bounds_chunks':chunks})
(R/'output/release_010/houses/native-bounds-inspect.json').write_text(json.dumps(rows,indent=2));print(json.dumps(rows))

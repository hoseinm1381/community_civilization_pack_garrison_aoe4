"""Read the complete installed Attrib archive for references to privately cloned units."""
import json
from pathlib import Path
import re
import subprocess
import sys

from common import ARCH, CFG, OUT, STAGING, files, guard, owned, read, sha, write
sys.path.insert(0,CFG['garrison_extension'])
from garrison_shared import rgd

NAMES=('unit_monk_3_chi','unit_trade_cart_chi','unit_ram_3_chi','unit_workshop_ram_3_chi',
       'unit_repeater_crossbowman_4_chi','unit_siege_tower_3_chi','unit_springald_3_chi',
       'unit_trebuchet_4_cw_chi','unit_trebuchet_4_tr_chi','unit_siege_cart')


def main():
    guard();folder=owned(OUT/'inventory/stock-reference-closure-r1')
    receipt=folder/'report.json'
    if receipt.exists():raise FileExistsError('Preserve prior full reference audit')
    archive=Path(r'E:\Games\steamapps\common\Age of Empires IV\cardinal\archives\Attrib.sga')
    raw=owned(STAGING/'a/refs');listing_path=folder/'listing.json';extraction_path=folder/'extraction.json'
    digest=sha(archive)
    if not listing_path.exists():
        result=subprocess.run([str(ARCH),'list',str(archive),'--verify'],capture_output=True,text=True,timeout=180)
        if result.returncode:raise RuntimeError(result.stderr)
        listing=json.loads(result.stdout)
        if not listing['archive']['verification']['verified']:raise ValueError('Stock archive verification failed')
        write(listing_path,listing)
    listing=read(listing_path);expected={r['path'] for r in listing['members'] if '.rgd' in r['path']}
    if not extraction_path.exists():
        if raw.exists():raise FileExistsError('Preserve incomplete stock extraction')
        result=subprocess.run([str(ARCH),'extract',str(archive),str(raw),'--filter','.rgd'],capture_output=True,text=True,timeout=240)
        (folder/'extract.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        if result.returncode:raise RuntimeError('Full stock reference extraction failed')
        write(extraction_path,json.loads(result.stdout))
    inventory=files(raw,reject_links=True,exclude_release_060=False)
    if set(inventory)!=expected or sha(archive)!=digest:raise ValueError('Full stock RGD inventory differs')
    patterns={name:re.compile(r'(?<![a-z0-9_])'+name+r'(?![a-z0-9_])',re.I) for name in NAMES}
    matches=[];decoded=0
    for relative,row in inventory.items():
        path=raw/relative;data=path.read_bytes()
        candidates=[name for name in NAMES if name.encode() in data.lower()]
        if not candidates:continue
        document=rgd.read(data);decoded+=1;hits=[]
        for node_path,node in rgd.flatten(document.nodes):
            if not isinstance(node.value,str):continue
            names=[name for name in candidates if patterns[name].search(node.value)]
            if names:hits.append({'path':node_path,'value':node.value,'kind':node.kind,'identities':names})
        if hits:matches.append({'member':relative,'path':str(path),'sha256':row['sha256'],'hits':hits})
    write(receipt,{'schema':'ccp-060-full-stock-identity-reference-audit/v1',
        'status':'all_installed_stock_rgds_searched_exact_identity_tokens',
        'archive':str(archive),'archive_sha256':digest,'listing_sha256':sha(listing_path),
        'native_rgd_count':len(inventory),'target_names':NAMES,'matching_documents_decoded':decoded,
        'matches':matches,'matching_members':len(matches),
        'qualification_limit':'CString identity references; arbitrary runtime or external numeric filters are not inferred',
        'native_acceptance':False})
    print(json.dumps({'report':str(receipt),'all_rgds':len(inventory),'matching_members':len(matches)}))


if __name__=='__main__':main()

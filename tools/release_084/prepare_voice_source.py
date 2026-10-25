"""Stage editable native children using verified Garrison-allocated identities."""
import json
from pathlib import Path
import shutil
import sys
import xml.etree.ElementTree as ET
from pipeline import guard,digest,save_json
from providers import ROOT,OUT


def main():
    guard();cfg=json.loads((ROOT/'workspace.json').read_text())
    complete=OUT/'integration/voice-identities-complete.json'
    identity_file=complete if complete.exists() else OUT/'integration/voice-identities-v1/receipt.json'
    identity=json.loads(identity_file.read_text())
    audit_file=OUT/'integration/voice-identities-complete-audit.json' if complete.exists() else identity_file.parent/'identity-audit.json'
    audit=json.loads(audit_file.read_text())
    if not audit['passed'] or audit['receipt_sha256']!=digest(identity_file):raise RuntimeError('Verified identity inputs required')
    baseline=json.loads((OUT/'baseline.json').read_text())
    revision='v2' if complete.exists() else 'v1'
    dest=Path(cfg['external_root'])/'staging/release_084'/('source-draft-'+revision)
    if dest.exists():raise FileExistsError('Preserve staged source drafts')
    # Validate the accepted source before copying into the isolated release tree.
    assets=ROOT/'assets'
    protected={Path(p).relative_to(assets).as_posix():h for p,h in baseline['protected'].items() if Path(p).is_relative_to(assets)}
    if any(digest(assets/p)!=h for p,h in protected.items()):raise RuntimeError('Protected active source changed')
    dest.mkdir(parents=True);shutil.copytree(assets,dest/'assets')
    shutil.copy2(ROOT/cfg['project_file'],dest/cfg['project_file'])
    if any(digest(dest/'assets'/p)!=h for p,h in protected.items()):raise RuntimeError('Isolated source copy mismatch')
    sys.path.insert(0,cfg['garrison_extension']);from garrison_shared import rgd
    added=[]
    for row in identity['identities']:
        if digest(row['compiled'])!=row['compiled_sha256']:raise RuntimeError('Allocated identity changed')
        family='attachments/attachment_lists' if row['category']=='attachments' else row['category']
        root=ET.Element('instance',version='2',description='Private 0.8.4 Vietnamese voice-owner identity',template=family.replace('/','\\'))
        donor=row['source'].removeprefix('attrib/').removesuffix('.rgd').replace('/','\\')
        native=rgd.read(Path(row['source_file']).read_bytes())
        for branch in native.nodes:
            if branch.key=='default':node=root
            else:node=ET.SubElement(root,'variant',name=str(branch.key))
            ET.SubElement(node,'uniqueid',name='pbgid',value=str(row['pbgid']))
            ET.SubElement(node,'instance_reference',name='parent_pbg',value=donor)
        ET.indent(root,space='\t')
        path=dest/'assets/attrib/instances'/family/'vietnam/release_084'/(row['name']+'.xml')
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(ET.tostring(root,encoding='utf-8',xml_declaration=True)+b'\n')
        ET.parse(path)
        if root.find("list[@name='extensions']") is not None:raise RuntimeError('Identity source must not append extensions')
        added.append(dict(path=str(path),sha256=digest(path),pbgid=row['pbgid'],parent=donor,
                          variants=[n.get('name') for n in root.findall('variant')]))
    save_json(OUT/'integration'/('source-draft-'+revision+'.json'),dict(schema='ccp-084-isolated-source-draft/v1',
              root=str(dest),project=str(dest/cfg['project_file']),project_sha256=digest(dest/cfg['project_file']),
              identity_receipt_sha256=digest(identity_file),unchanged_baseline_source_files=len(protected),
              added=added,active_source_modified=False,production_references_changed=False,
              speech_suppression=False,new_extensions=0,native_compile=False,
              note='Editable identity preparation only; final typed speech and reference overlay is not active.'))
    print('VOICE_SOURCE_STAGED',len(protected),'baseline files preserved;',len(added),'new identity sources',flush=True)


if __name__=='__main__':main()

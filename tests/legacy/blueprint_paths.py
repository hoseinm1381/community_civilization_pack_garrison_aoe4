"""Resolve current organized instances without rewriting historical snapshots."""
from pathlib import Path
import json,os,xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets/attrib/instances'
MAPPING=json.loads((ROOT/'docs/blueprint-folders.json').read_text())

def relocated(key):return MAPPING.get(key,key)

def blueprint_key(kind,name):
    return relocated(kind+'\\vietnam\\'+name.removesuffix('.xml'))

def current_path(path):
    if not isinstance(path,(str,os.PathLike)):return path
    candidate=Path(path)
    try:relative=candidate.resolve().relative_to(A.resolve())
    except ValueError:return path
    if candidate.suffix.lower()!='.xml':return path
    key=relative.with_suffix('').as_posix().replace('/','\\')
    return A/(MAPPING[key].replace('\\','/')+'.xml') if key in MAPPING else path

def parse_current_xml(path,*args,**kwargs):
    actual=current_path(path)
    tree=E.parse(actual,*args,**kwargs)
    # Historical snapshots retain old physical paths on disk, but their logical
    # references compare to the same currently relocated blueprints.
    if isinstance(actual,(str,os.PathLike)) and not Path(actual).resolve().is_relative_to(A.resolve()):
        remap_xml_references(tree.getroot())
    return tree

def remap_xml_references(root):
    for node in root.iter('instance_reference'):
        if node.get('value') in MAPPING:node.set('value',MAPPING[node.get('value')])
    return root

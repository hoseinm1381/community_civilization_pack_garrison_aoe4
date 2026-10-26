"""Small inspection model for sparse cattle deltas; not engine/runtime proof."""
from blueprint_paths import parse_current_xml, current_path, blueprint_key, relocated, remap_xml_references
import copy
from pathlib import Path
import xml.etree.ElementTree as E

ROOT=Path(__file__).resolve().parents[1]
DONORS=ROOT/'work/vietnam_redesign/batch_20261021/evidence'
NATIVE={'ebps':r'ebps\races\malian\animals\gaia_herdable_cattle_mal',
        'sbps':r'sbps\races\malian\animals\herdable_cattle_mal'}

def raw_cattle(kind):
    return parse_current_xml(ROOT/f'assets/attrib/instances/{kind}/vietnam/vn_unit_water_buffalo_vit.xml').getroot()

def effective_cattle(kind):
    delta=raw_cattle(kind)
    if delta.find('instance_reference[@name="parent_pbg"]').get('value') != NATIVE[kind]:
        return delta  # Historical standalone form, useful for pre-repair failures.
    stem='gaia_herdable_cattle_mal' if kind=='ebps' else 'herdable_cattle_mal'
    native=parse_current_xml(DONORS/f'{kind}__{stem}.xml').getroot()
    def merge(base,change):
        if change.tag=='template_reference' and base.get('value') != change.get('value'):
            base.clear();base.attrib.update(change.attrib)
            base.extend(copy.deepcopy(list(change)));return
        for k,v in change.attrib.items():
            if not k.startswith('List.') and k!='overrideParent':base.set(k,v)
        if change.tag=='list' and change.get('overrideParent')=='True':
            base[:]=copy.deepcopy(list(change));return
        for child in change:
            item=child.get('List.ParentItemID',child.get('List.ItemID'))
            match=next((x for x in base if x.tag==child.tag and
                        (x.get('List.ItemID')==item if item else x.get('name')==child.get('name'))),None)
            if match is None:base.append(copy.deepcopy(child))
            else:merge(match,child)
    merge(native.find('list'),delta.find('list'))
    native.find('uniqueid').set('value',delta.find('uniqueid').get('value'))
    return native

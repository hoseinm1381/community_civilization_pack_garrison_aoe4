"""Verify the two owner-approved shared resource exceptions, with stock preservation."""
import hashlib
import json
import xml.etree.ElementTree as E


def semantic_digest(tree):
    data = E.canonicalize(E.tostring(tree, encoding='unicode'), strip_text=True)
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def verify(root):
    receipt = json.loads((root/'docs/korea-shared-resource.json').read_text())
    base = root/'assets/attrib/instances'
    army_key = receipt['army']['key']
    army = E.parse(base/(army_key.replace('\\', '/')+'.xml')).getroot()
    cap = army.find("group/enum_table[@name='resource_max_cap']/float[@name='merc_byz']")
    assert cap is not None and cap.get('value') == '100000', 'Literature storage must be enabled'
    cap.set('value', '0')
    assert semantic_digest(army) == receipt['official_semantic_sha256'][army_key], 'Unapproved Zhu Xi army change'

    resource_key = receipt['resource']['key']
    resource = E.parse(base/(resource_key.replace('\\', '/')+'.xml')).getroot()
    overrides = resource.find("group/group[@name='ui']/list[@name='overrides']")
    new = [x for x in overrides if x.find("instance_reference[@value='racebps\\chinese_ha_01']") is not None]
    assert len(new) == 1, 'Expected one Zhu Xi resource presentation override'
    item = new[0]
    assert item.get('List.ItemID') == str(receipt['resource']['ui_list_item_id'])
    assert item.get('List.ListAction') == 'Append' and item.get('List.ParentItemID') is None
    ui = item.find('group')
    assert {x.get('name'): x.get('value') for x in ui} == {
        'name': '11993', 'description': '11994', 'icon_primary': 'korea\\bookicon',
        'icon_insufficient': 'korea\\book_unavailable', 'kicker_texture': 'korea\\bookicon'}
    overrides.remove(item)
    assert semantic_digest(resource) == receipt['official_semantic_sha256'][resource_key], 'Stock olive-oil data changed'
    return True

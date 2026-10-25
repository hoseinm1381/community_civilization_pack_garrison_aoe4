import unittest, xml.etree.ElementTree as E
import hashlib, json, re, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOWER=ROOT/'assets/attrib/instances/ebps/vietnam/buildings/landmarks/feudal/vn_building_landmark_age1_gatehouse_control_chi.xml'

class SourceTests(unittest.TestCase):
    def test_resource_return_has_a_native_interaction_at_both_variants(self):
        root=E.parse(TOWER).getroot()
        for scope in [root,*root.findall('variant')]:
            node=scope.find("./list[@name='extensions']/template_reference[@value='ebpextensions\\interactive_object_ext']/list[@name='type_list']")
            types=[n.find("enum[@name='interaction_type']").get('value') for n in node]
            self.assertEqual(types.count('resource_drop_off'),1)
            self.assertEqual(types.count('repair'),1)
            self.assertEqual(types.count('construct'),1)
            self.assertEqual(types.count('seek_shelter_destination'),1)

    def test_source_delta_is_only_the_guard_and_dropoff_interaction(self):
        out=ROOT/'output/release_085'
        before=json.loads((out/'088-source-before.json').read_text())
        after={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'assets').rglob('*') if p.is_file()}
        policy=json.loads((out/'088-source-policy.json').read_text())
        self.assertEqual(set(after),set(before))
        self.assertEqual(sorted(k for k in after if after[k]!=before[k]),sorted(policy['changed']))
        def structure(n):return (n.tag,sorted(n.attrib.items()),[structure(x) for x in n])
        with zipfile.ZipFile(out/'088-before-source.zip') as z:
            old=E.fromstring(z.read(TOWER.relative_to(ROOT).as_posix()))
            current=E.parse(TOWER).getroot()
            for scope in [current,*current.findall('variant')]:
                node=scope.find("./list[@name='extensions']/template_reference[@value='ebpextensions\\interactive_object_ext']/list[@name='type_list']")
                drop=next(n for n in node if n.find("enum[@name='interaction_type']").get('value')=='resource_drop_off')
                node.remove(drop)
            self.assertEqual(structure(current),structure(old))
            original=z.read('assets/scar/vietnam/flooded_citadel.scar').decode('utf-8')
        current=(ROOT/'assets/scar/vietnam/flooded_citadel.scar').read_text(encoding='utf-8')
        current=re.sub(r'-- BEGIN GENERATED 088 MOBILITY GUARD.*?-- END GENERATED 088 MOBILITY GUARD\n','',current,flags=re.S)
        patched='''        moving = false
        if knownMoving[key] then
            local speed = BP_GetEntityBPDefaultSpeed(blueprint, false, player.id)
            moving = speed > 0
            print("VIETNAM_V2_FLOODED_TARGET blueprint=" .. BP_GetName(blueprint) .. " base_speed=" .. tostring(speed))
        end'''
        oldbody='''        local speed = BP_GetEntityBPDefaultSpeed(blueprint, false, player.id)
        moving = speed > 0
        print("VIETNAM_V2_FLOODED_TARGET blueprint=" .. BP_GetName(blueprint) .. " base_speed=" .. tostring(speed))'''
        self.assertEqual(current.count(patched),1)
        current=current.replace(patched,oldbody)
        normalize=lambda s:re.sub(r'\n{3,}','\n\n',s.replace('\r\n','\n')).strip()
        self.assertEqual(normalize(current),normalize(original))

if __name__=='__main__':unittest.main()

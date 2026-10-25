"""Actual native fixtures: narrow visual edits must be byte-reversible."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CFG, OUT, RECIPES, read
sys.path.insert(0, CFG['garrison_extension'])
from garrison_shared import rgd
from compiled_visual_delta_060 import patch_visual_rgd


class CompiledVisualDeltaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        row = read(RECIPES/'foot-body-private-binding-plan.json')['entries'][0]
        cls.raw = Path(row['stock_slots'][0]['raw_archive_member_path']).read_bytes()
        cls.doc = rgd.read(cls.raw)

    def test_private_body_changes_only_identity_and_exact_render_slots(self):
        changes = []
        for path, node in rgd.flatten(self.doc.nodes):
            if node.key == 'pbgid':
                changes.append({'path':path, 'before':node.value, 'after':2000000000})
            elif node.key == 'animator0':
                changes.append({'path':path, 'before':node.value, 'after':r'art\scenario\garrison\v60test\body\body'})
        changed, proof = patch_visual_rgd(self.raw, changes, 'body')
        self.assertEqual(len(proof), 6)
        decoded = rgd.read(changed)
        for entry in changes:
            self.assertEqual(rgd.find(decoded.nodes, entry['path']).value, entry['after'])
            rgd.find(decoded.nodes, entry['path']).value = entry['before']
        self.assertEqual(rgd.write(decoded), self.raw)

    def test_body_policy_rejects_parent_metadata_changes(self):
        with self.assertRaisesRegex(ValueError, 'visual policy'):
            patch_visual_rgd(self.raw, [{'path':'default/parent_pbg/$PBGNAME', 'before':'', 'after':'wrong'}], 'body')

    def test_rejects_wrong_expected_value(self):
        with self.assertRaisesRegex(ValueError, 'Expected value'):
            patch_visual_rgd(self.raw, [{'path':'default/pbgid', 'before':-1, 'after':2000000000}], 'body')

    def test_rejects_duplicate_paths(self):
        edit = {'path':'default/pbgid', 'before':1287685, 'after':2000000000}
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            patch_visual_rgd(self.raw, [edit, edit], 'body')

    def test_actor_attachment_reference_preserves_all_other_fields(self):
        freeze = read(OUT/'baseline/final053/freeze.json')
        member = next(p for p in freeze['archive_members'] if '/ebps/' in p and p.endswith('/vn_unit_archer_2_vit.rgd'))
        raw = (OUT/'baseline/final053/archive-members'/member).read_bytes()
        doc = rgd.read(raw)
        edits = [{'path':p, 'before':n.value, 'after':CFG['project_guid'].replace('-','')+':vn060_body_archer2'}
                 for p,n in rgd.flatten(doc.nodes) if n.kind=='CString' and n.value=='tier2_archer_chi']
        changed, proof = patch_visual_rgd(raw, edits, 'actor')
        self.assertEqual(len(proof), 2)
        restored = rgd.read(changed)
        for edit in edits:
            rgd.find(restored.nodes, edit['path']).value=edit['before']
        self.assertEqual(rgd.write(restored), raw)

    def test_actor_policy_rejects_gameplay_reference(self):
        with self.assertRaisesRegex(ValueError, 'visual policy'):
            patch_visual_rgd(self.raw, [{'path':'default/combat_ext/weapon/$PBGNAME','before':'x','after':'y'}], 'actor')

    def test_elephant_root_animator_list_can_be_private_without_touching_scale(self):
        member='attrib/ebps/vietnam/vn_unit_war_elephant_2_vit.rgd'
        raw=(OUT/'baseline/final053/archive-members'/member).read_bytes()
        document=rgd.read(raw)
        changes=[{'path':path,'before':node.value,
                  'after':CFG['project_guid'].replace('-','')+':v6icattle'}
                 for path,node in rgd.flatten(document.nodes)
                 if node.key=='$PBGNAME' and node.value=='gaia_herdable_cattle_mal']
        self.assertEqual(len(changes),2)
        with self.assertRaisesRegex(ValueError, 'visual policy'):
            patch_visual_rgd(raw,changes,'actor')
        result,_=patch_visual_rgd(raw,changes,'actor_extended')
        restored=rgd.read(result)
        for change in changes:
            rgd.find(restored.nodes,change['path']).value=change['before']
        self.assertEqual(rgd.write(restored),raw)

    def test_private_graph_requires_exact_approved_native_reference_leaf(self):
        record=next(x for x in read(OUT/'integration/private-land-graph/native-reference-plan-v1/plan.json')['resources']
                    if x['member']=='attrib/ebps/races/chinese/units/unit_monk_3_chi.rgd')
        raw=Path(record['path']).read_bytes()
        doc=rgd.read(raw)
        path='default/tier_ext/tier_group_list/tier_group/tier/attachments/$PBGNAME'
        before=rgd.find(doc.nodes,path).value
        change={'path':path,'before':before,
                'after':CFG['project_guid'].replace('-','')+':v6iprivatemonk3'}
        with self.assertRaisesRegex(ValueError,'visual policy'):
            patch_visual_rgd(raw,[change],'graph')
        edited,_=patch_visual_rgd(raw,[change],'graph',approved_paths={path})
        back=rgd.read(edited)
        rgd.find(back.nodes,path).value=before
        self.assertEqual(rgd.write(back),raw)

    def test_qualified_equipment_and_monk_staff_media_are_exact_leaf_only(self):
        equipment=read(OUT/'integration/private-equipment-identities/native-batch-v1/registered-identities.json')
        bow=next(x for x in equipment['entries'] if x['stock_member'].endswith('/wpn_range_archer_2_chi.rgd'))
        raw=Path(bow['stock_path']).read_bytes()
        path='default/attachment_lists/parent_animator'
        before=rgd.find(rgd.read(raw).nodes,path).value
        change={'path':path,'before':before,'after':r'art\scenario\garrison\v60test\bow\bow'}
        with self.assertRaisesRegex(ValueError,'visual policy'):
            patch_visual_rgd(raw,[change],'body_media')
        changed,_=patch_visual_rgd(raw,[change],'body_media',approved_paths={path})
        restored=rgd.read(changed)
        rgd.find(restored.nodes,path).value=before
        self.assertEqual(rgd.write(restored),raw)
        land=read(OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json')
        monk=next(x for x in land['entries'] if x['stock_member'].endswith('/tier3_monk_chi.rgd'))
        raw=Path(monk['stock_path']).read_bytes()
        path='default/attachment_lists/attachment_lists/attachment_list/attachment_list/animator_sim_attachment/animator'
        before=rgd.find(rgd.read(raw).nodes,path).value
        changed,_=patch_visual_rgd(raw,[{'path':path,'before':before,
                         'after':r'art\scenario\garrison\v60test\staff\staff'}],
                         'body_media',approved_paths={path})
        restored=rgd.read(changed)
        rgd.find(restored.nodes,path).value=before
        self.assertEqual(rgd.write(restored),raw)
        with self.assertRaisesRegex(ValueError,'visual policy'):
            patch_visual_rgd(raw,[{'path':'default/parent_pbg/$PBGNAME',
                                   'before':'x','after':'y'}],
                             'body_media',approved_paths={'default/parent_pbg/$PBGNAME'})

    def test_private_siege_actor_alternate_sua_is_exact_visual_leaf(self):
        stage=read(OUT/'integration/qualified-list-media-stage-r1/stage.json')
        ids=read(OUT/'integration/private-land-identities/native-batch-v5/registered-identities.json')
        identity=next(x for x in ids['entries'] if x['stock_member'].endswith('/unit_ram_3_chi.rgd'))
        row=next(x for x in stage['payloads'] if x['member']==identity['private_member'])
        raw=Path(row['path']).read_bytes()
        path='default/entity_blueprint_ext/alternate_sua'
        before=rgd.find(rgd.read(raw).nodes,path).value
        edit={'path':path,'before':before,'after':r'art\scenario\garrison\v60test\ram\ram'}
        with self.assertRaisesRegex(ValueError,'visual policy'):
            patch_visual_rgd(raw,[edit],'actor_media')
        updated,_=patch_visual_rgd(raw,[edit],'actor_media',approved_paths={path})
        restored=rgd.read(updated)
        rgd.find(restored.nodes,path).value=before
        self.assertEqual(rgd.write(restored),raw)
        with self.assertRaisesRegex(ValueError,'visual policy'):
            patch_visual_rgd(raw,[{'path':'default/site_ext/footprint_scale/x',
                                   'before':1.0,'after':2.0}],
                             'actor_media',approved_paths={'default/site_ext/footprint_scale/x'})


if __name__ == '__main__':
    unittest.main()

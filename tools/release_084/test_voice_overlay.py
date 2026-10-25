import copy
from types import SimpleNamespace as N
import unittest


def node(key,value,kind='Table'):
    return N(key=key,value=value,kind=kind)


class OverlayTests(unittest.TestCase):
    def test_presentation_only_changes_are_reversible_and_parent_aliases_stay(self):
        from voice_overlay import patch_nodes,undo_changes
        ref=lambda:node('ref',[node('$PBGMAP','sbps','CString'),node('$PBGNAME','ship','CString')])
        parent=ref();parent.key='parent_pbg'
        original=[node('default',[node('speech_ext',[node('voice','stock','CString')]),
                    node('health',100,'Float'),node('spawner',[ref()]),parent,
                    node('base_unit','ship','CString'),node('list',[node('attachment_speaker_code','female','CString')])])]
        nodes=copy.deepcopy(original)
        changes=patch_nodes(nodes,{'default/speech_ext'}, {'default/list/attachment_speaker_code'}, {('sbps','ship'):'owner:private_ship'})
        branch=nodes[0].value
        self.assertEqual([x.key for x in branch],['health','spawner','parent_pbg','base_unit','list'])
        self.assertEqual(branch[1].value[0].value[1].value,'owner:private_ship')
        self.assertEqual(branch[2].value[1].value,'ship')
        self.assertEqual(branch[3].value,'ship')
        self.assertEqual(branch[4].value[0].value,'')
        undo_changes(changes)
        self.assertEqual(nodes,original)

    def test_unlisted_speech_fields_cannot_be_silently_muted(self):
        from voice_overlay import patch_nodes
        nodes=[node('default',[node('speech_ext',[]),node('attachment_speaker_code','stock','CString')])]
        changes=patch_nodes(nodes,set(),set(),{})
        self.assertFalse(changes)
        self.assertEqual(nodes[0].value[1].value,'stock')

    def test_attachment_categories_and_paths_rewire_but_foreign_namespaces_do_not(self):
        from voice_overlay import patch_nodes
        def ref(name):return node('actor',[node('$PBGMAP','attachments\\attachment_lists','CString'),node('$PBGNAME',name,'CString')])
        nodes=[node('default',[ref('civilizations\\mongol\\female'),ref('foreign:female')])]
        patch_nodes(nodes,set(),set(),{('attachments','female'):'owner:private_female'})
        self.assertEqual(nodes[0].value[0].value[1].value,'owner:private_female')
        self.assertEqual(nodes[0].value[1].value[1].value,'foreign:female')

    def test_readback_checks_every_repeated_attachment_list(self):
        from voice_overlay import verify_speech_removed
        nodes=[node('default',[node('attachment_list',[node('attachment_speaker_code','','CString')]),
                               node('attachment_list',[node('attachment_speaker_code','surviving female','CString')])])]
        with self.assertRaises(RuntimeError):
            verify_speech_removed(nodes,set(),{'default/attachment_list/attachment_speaker_code'})


if __name__=='__main__':unittest.main()

"""Actual donor regression; frozen parent evidence is not a native refresh."""
import hashlib
import json
import sys
import unittest
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
import check_extension_inheritance as audit


class KoreaInheritanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ROOT/'tests/fixtures/korea'
        self.evidence = json.loads((self.fixture/'extension-parents.json').read_text())
        self.ledger = json.loads((ROOT/'docs/korea-import.json').read_text())
        self.before = (self.fixture/'before_identity_repair.xml').read_bytes()
        self.after = ROOT/'assets/attrib/instances'/Path(self.evidence['private'].replace('\\','/')+'.xml')

    def test_original_donor_reproduces_effective_inherited_duplicates(self):
        self.assertEqual(hashlib.sha256(self.before).hexdigest(), self.evidence['source_sha256'])
        record = audit.summarize(self.before)
        mapping = {row['source']: row['private'] for row in self.ledger['instances']}
        # Translate only the parent namespace to the destination. Keep the
        # actual pre-repair extension identities and every source value.
        for scope in record.values():
            parent = scope['parent']
            if parent and parent.get('value') in mapping:
                parent['value'] = mapping[parent['value']]
                parent['mod'] = self.ledger['destination_guid']
        records = {**self.evidence['local'], self.evidence['private']: record}
        errors = audit.Resolver(records, self.evidence['official']).audit()
        self.assertEqual(len(errors), 11)
        self.assertTrue(any(e.get('extension') == 'ebpextensions\\site_ext' for e in errors))

    def test_current_identity_overrides_remove_inherited_duplicates(self):
        records = {**self.evidence['local'], self.evidence['private']: audit.summarize(self.after.read_bytes())}
        self.assertEqual(audit.Resolver(records, self.evidence['official']).audit(), [])

    def test_identity_repair_preserves_numeric_gameplay_and_enums(self):
        def values(data):
            root = E.fromstring(data)
            return [(scope.get('name', 'default'), node.tag, node.get('name'), node.get('value'))
                    for scope in [root]+root.findall('variant')
                    for node in scope.iter()
                    if node.tag in ('float', 'int', 'bool', 'enum')]
        # Exercise the real identity repair against frozen parents. The live
        # editor also modernizes schema defaults, which is a separate audit.
        import import_korea
        roots = {}
        for key, record in self.evidence['local'].items():
            tree = E.Element('instance')
            for variant, scope in record.items():
                owner = tree if variant == 'default' else E.SubElement(tree, 'variant', name=variant)
                if scope['parent'] is not None:
                    E.SubElement(owner, 'instance_reference', scope['parent'])
                if scope['list'] is not None:
                    extensions = E.SubElement(owner, 'list', scope['list'])
                    for item in scope['items']:
                        E.SubElement(extensions, 'template_reference', item)
            roots[key] = tree
        tree = E.fromstring(self.before)
        mapping = {row['source']: row['private'] for row in self.ledger['instances']}
        for parent in tree.iter('instance_reference'):
            if parent.get('name') == 'parent_pbg' and parent.get('value') in mapping:
                parent.set('value', mapping[parent.get('value')])
                parent.set('mod', self.ledger['destination_guid'])
        roots[self.evidence['private']] = tree
        import_korea.repair_extensions(roots, self.evidence['official'])
        self.assertEqual(values(self.before), values(E.tostring(tree)))


if __name__ == '__main__':
    unittest.main()

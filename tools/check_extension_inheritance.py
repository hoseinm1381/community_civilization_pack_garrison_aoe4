"""Audit effective EBPS/SBPS extension identities, including official ancestors.

This is an inheritance check, not a substitute for a Content Editor burn.
The evidence cache is refreshed from the installed ReferenceAttributes archive;
tests may explicitly supply a frozen cache to reproduce historical failures.
"""
from pathlib import Path
import argparse, collections, ctypes, hashlib, json, sys, xml.etree.ElementTree as E, zlib

ROOT = Path(__file__).resolve().parents[1]
GUID = 'b7fcea91257b408fb9e8ae4d8bc402e1'

def summarize(data):
    root = E.fromstring(data)
    result = {}
    for node in [root, *root.findall('variant')]:
        parent = node.find("instance_reference[@name='parent_pbg']")
        extensions = node.find("list[@name='extensions']")
        result[node.get('name', 'default')] = {
            'parent': dict(parent.attrib) if parent is not None else None,
            'list': dict(extensions.attrib) if extensions is not None else None,
            'items': [dict(e.attrib) for e in extensions] if extensions is not None else [],
        }
    return result

def refresh(cache):
    import official_archive
    archive = official_archive.archive_path()
    records = {}
    for name,data in official_archive.members(archive, lambda name: name.startswith(('instances\\ebps\\','instances\\sbps\\')) and name.endswith('.xml')):
        records[name[len('instances\\'):-4]] = summarize(data)
    receipt = {'archive': str(archive), 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
               'records': records}
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(receipt, separators=(',', ':')), encoding='utf-8')
    return records

def load_local(root=ROOT):
    base = root / 'assets/attrib/instances'
    return {p.relative_to(base).with_suffix('').as_posix().replace('/', '\\'): summarize(p.read_bytes())
            for category in ['ebps', 'sbps'] for p in (base/category).rglob('*.xml')}

class Resolver:
    def __init__(self, local, official):
        self.local, self.official, self.cache = local, official, {}

    def scope(self, record, variant):
        default = record['default']
        scope = record.get(variant, default)
        return (scope['parent'] if scope['parent'] is not None else default['parent'],
                scope if scope['list'] is not None else default)

    def inherited(self, key, variant, private=True, trail=()):
        record = (self.local if private else self.official)[key]
        parent, scope = self.scope(record, variant)
        if not parent or not parent.get('value'): return []
        mod = parent.get('mod', '')
        if mod not in ('', GUID): raise ValueError('Unresolved foreign parent: ' + str(parent))
        return self.effective(parent['value'], variant, mod == GUID, trail)

    def effective(self, key, variant='default', private=True, trail=()):
        token = (key, variant, private)
        if token in self.cache: return self.cache[token]
        if token in trail: raise ValueError('Inheritance cycle: ' + str(token))
        record = (self.local if private else self.official)[key]
        _, scope = self.scope(record, variant)
        items = list(self.inherited(key, variant, private, trail + (token,)))
        settings = scope['list'] or {}
        if settings.get('overrideParent') == 'True': items = []
        removed = set(settings.get('removedIds', '').split(','))
        items = [i for i in items if i.get('List.ItemID') not in removed]
        for item in scope['items']:
            target = item.get('List.ParentItemID', item.get('List.ItemID'))
            found = next((i for i, old in enumerate(items) if old.get('List.ItemID') == target), None)
            if found is not None and item.get('List.ListAction') != 'Append': items[found] = item
            else: items.append(item)
        self.cache[token] = items
        return items

    def audit(self):
        errors = []
        for key, record in self.local.items():
            for variant in record:
                try:
                    parent, scope = self.scope(record, variant)
                    settings = scope['list'] or {}
                    # An explicit merge is not a full replacement list. Native
                    # compilation drops unmatched overrides instead of appending
                    # them (v8 farm2 readback). Audit before the duplicate model,
                    # which deliberately retains its older effective-list rules.
                    if settings.get('overrideParent') == 'False' and parent and parent.get('value'):
                        removed = set(settings.get('removedIds', '').split(','))
                        inherited_ids = {i.get('List.ItemID') for i in self.inherited(key, variant)
                                         if i.get('List.ItemID') not in removed}
                        for item in scope['items']:
                            target = item.get('List.ParentItemID', item.get('List.ItemID'))
                            if item.get('List.ListAction') != 'Append' and target not in inherited_ids:
                                errors.append({'blueprint': key, 'variant': variant,
                                    'extension': item.get('value'), 'target': target,
                                    'error': 'unmatched-extension-override'})
                    items = self.effective(key, variant)
                    counts = collections.Counter(i.get('value') for i in items)
                    for extension, count in counts.items():
                        if count > 1:
                            errors.append({'blueprint': key, 'variant': variant, 'extension': extension,
                                'items': [i for i in items if i.get('value') == extension]})
                except (KeyError, ValueError) as exc:
                    errors.append({'blueprint': key, 'variant': variant, 'unresolved': str(exc)})
        return errors

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official-cache', type=Path, default=ROOT/'.local/official-extensions.json')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    official = refresh(args.official_cache) if args.refresh or not args.official_cache.exists() else json.loads(args.official_cache.read_text(encoding='utf-8'))['records']
    local = load_local()
    errors = Resolver(local, official).audit()
    result = {'local_blueprints': len(local), 'official_blueprints': len(official), 'errors': errors}
    if args.output: args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
    sys.exit(bool(errors))

"""Verify storage and identity; optionally prove migration-only source preservation."""
import argparse
import json
from pathlib import Path
from workspace_support import ROOT, check_identity, check_preservation, check_storage, configuration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--storage-only', action='store_true')
    parser.add_argument('--preservation', action='store_true')
    parser.add_argument('--report', type=Path, help='Optional JSON under owned external output/provenance only.')
    args = parser.parse_args()
    config = configuration()
    result = {'status': 'passed', 'links': check_storage(ROOT, config)}
    if not args.storage_only:
        result['identity'] = check_identity(ROOT, config)
    if args.preservation:
        result['preservation'] = check_preservation(ROOT, config)
    if args.report:
        allowed = [Path(config['external_root']) / name for name in ('output', 'provenance')]
        path = args.report.resolve()
        if not any(path.is_relative_to(folder.resolve()) for folder in allowed):
            raise ValueError('Reports must be inside owned external output or provenance')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as error:
        print(json.dumps({'status': 'failed', 'error': str(error)}))
        raise SystemExit(1)

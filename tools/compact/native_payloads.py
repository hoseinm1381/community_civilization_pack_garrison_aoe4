"""Refresh compiled payloads from each completed native burn."""
from pathlib import Path


def refresh_native_member(archive, member, target, extractor):
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    fresh = target.with_name(target.name + '.extracting')
    if fresh.exists():
        raise ValueError('Inspect prior failed extraction before retrying: ' + str(fresh))
    extractor(archive, member, fresh)
    fresh.replace(target)
    return target

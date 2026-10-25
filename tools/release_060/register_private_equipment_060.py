"""Register the second, equipment-only native identity batch after lock handoff.

Reuses the guarded original-native clone proof from the first land batch. This
module does not run until explicitly invoked with prepare, cook, or readback.
"""
from __future__ import annotations

import argparse
import json

import register_private_land_identities_060 as batch
from common import OUT, STAGING, guard

batch.PLAN = OUT/'integration/private-equipment-graph/derive-plan-v1.json'
batch.EVIDENCE = OUT/'integration/private-equipment-identities/native-batch-v1'
batch.PROJECT = STAGING/'i/Mods/v6wc'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'cook', 'readback'))
    action = parser.parse_args().action
    guard()
    print(json.dumps({'prepare':batch.prepare, 'cook':batch.cook,
                      'readback':batch.readback}[action](), indent=2))

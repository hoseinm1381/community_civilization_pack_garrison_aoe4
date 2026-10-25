"""Finalize the read-only stealth diagnosis and native diagnostic handoff."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from workspace_support import configuration,check_storage

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    cfg=configuration(ROOT);check_storage(ROOT,cfg)
    out=Path(cfg['external_root'])/'output/release_052/stealth'
    recipe=ROOT/'art/recipes/release_052/stealth'
    inventory=json.loads((out/'inventory.json').read_text(encoding='utf-8'))
    trace=json.loads((out/'official/fort-trace.json').read_text(encoding='utf-8'))
    diagnostic=json.loads((recipe/'diagnostic.json').read_text(encoding='utf-8'))
    originals={str(x):sha(x) for x in (
        ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml',
        ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml',
        ROOT/'assets/scar/vietnam/landmarks.scar',
    )}
    assert inventory['villager_ability']['sha256']==originals[str(ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_forvills_vit.xml')]
    assert inventory['working_archer_control']['sha256']==originals[str(ROOT/'assets/attrib/instances/abilities/vietnam/vn_activate_stealth_for_archer.xml')]
    assert len(trace['objects'])>=10 and len(inventory['consumers'])==6
    receipt={'schema':'ccp.release052.stealth-preparation/v1','status':'native_diagnostic_required',
        'source_patch':None,'native_cook':None,'native_match':None,
        'unchanged_active_sources':originals,
        'inventory':str(out/'inventory.json'),'official_trace':str(out/'official/fort-trace.json'),
        'compiled_state_trace':str(out/'official/stealth-state-trees.json'),
        'compiled_state_summary':str(out/'official/stealth-state-summary.json'),
        'all_native_stealth_actions':str(out/'official/all-stealth-actions.json'),
        'spy_passive_details':str(out/'official/passive-spy-details.json'),
        'ability_activation_patterns':str(out/'official/ability-activation-patterns.json'),
        'fixture':{'file':str(recipe/'stealth_modifier_probe.scar'),'sha256':sha(recipe/'stealth_modifier_probe.scar')},
        'diagnostic':{'file':str(recipe/'diagnostic.json'),'sha256':sha(recipe/'diagnostic.json')},
        'conclusion':('The current always-on ability invokes a timed 10 s stealth state tree with 6 s recharge. '
            'The complete official simulation bundle has only three SetStealthAllowed roots: the timed Malian Entity tree, '
            'the Fort Entity aura with fixed 2D radius 32 and military-infantry filter, and the Spy DeferredEntity passive. '
            'The Spy graph responds to recent attacks but has no HQ proximity guard, and its root type differs from an ability entity_tree. '
            'No official always-on ability uses a deferred tree activation. None is a qualified drop-in 33 m villager fix.'),
        'next_gate':'A native diagnostic must first qualify a supported persistent ability/deferred-tree lifecycle, or a custom scoped state tree with 33 m villager eligibility; no production source patch is ready.',
        'acceptance_checks':diagnostic['native_observations'],
        'preserved_cache':'The task-owned 23.8 MB ReferenceAttributes upgrade and 5.8 MB Data SCAR extraction caches remain available for regeneration/inspection; cache cleanup command was rejected by automatic policy.'}
    target=out/'receipt.json';target.write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print('STEALTH052_PREPARED',receipt['status'],len(trace['objects']),len(inventory['consumers']),target)

if __name__=='__main__':main()

"""Package the qualified final053-based archive without recooking accepted assets."""
import argparse
import json
from pathlib import Path
import zipfile
from common import CFG, OUT, files, guard, owned, read, sha, write
from inspect_delivery_060 import CREDITS, EXPECTED_GATES, inspect_delivery
from pin_final053 import PIN, SGA_SHA, verify as verify_baseline


LIMITATIONS=[
    'Import, lobby selection, native appearance/gameplay and multiplayer are untested.',
    'Compatible mounted, elephant, siege and equipment remixes retain stock geometry and mechanisms; stronger source-only experiments are excluded.',
    'Custom worker-elephant crate geometry failed native group/palette preservation and is excluded. Actor 2 uses the complete stock Tughlaq worker model with material variation, as authorized; actor 1 retains its Sultanate owner.',
    'Rattan visual switching is deferred; editable art and the existing +1 ranged armor behavior are preserved.',
    'Human siege crew render consumers are unresolved in the static selector graph. Stock behavior is retained; no new human-crew redesign or runtime absence is claimed.',
    'Monk IV staff remains stock. Stock non-albedo material data and native animation owners are retained except the explicitly authorized actor 2 worker owner correction.',
    'New private actor/squad production dependencies are statically verified; recursive precache/spawn requires native testing.',
    'A plain editable-source Content Editor build does not reproduce final visuals. The pinned native/media overlay onto exact final053 is required.'
]


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--candidate-folder',type=Path,required=True)
    ap.add_argument('--archive-report',type=Path,required=True)
    ap.add_argument('--handoff',type=Path,required=True)
    ap.add_argument('--source-report',type=Path,required=True)
    ap.add_argument('--source-build-report',type=Path,required=True)
    ap.add_argument('--coverage',type=Path,required=True)
    ap.add_argument('--label',default='r1')
    args=ap.parse_args()
    guard();frozen=verify_baseline()
    candidate_folder=owned(args.candidate_folder)
    assembly=read(candidate_folder/'assembly.json')
    candidate=owned(assembly['candidate']);digest=sha(candidate)
    if digest!=assembly['candidate_sha256']:raise ValueError('Candidate changed')
    reports={
        'archive':args.archive_report,
        'source':args.source_report,
        'source_build':args.source_build_report,
        'bindings':args.handoff,
        'media':OUT/'integration/qualified-media-selection-r1.json',
        'coverage':args.coverage,
        'allowlist':candidate_folder/'allowlist.json',
        'producer_replay':OUT/'integration/private-land-graph/compiled-only-producer-replay-v1.json',
        'rattan':OUT/'rattan-probe/native-gate-v1/qualification.json',
    }
    data={key:read(owned(path)) for key,path in reports.items()}
    archive=data['archive'];source=data['source'];bindings=data['bindings'];media=data['media']
    if (archive['candidate_sha256']!=digest or not archive['protected053_resources_unchanged']
        or len(archive['changed'])!=62 or len(archive['added'])!=385 or archive['unchanged_count']!=749):
        raise ValueError('Final archive preservation gate failed')
    if (source['status']!='explicit_source_delta_and_preserved_normal_identities_prior_art_verified'
        or len(source['changed'])!=60 or len(source['added'])!=80
        or source['source_stage_sha256']!=sha(args.handoff)
        or files(Path(__file__).resolve().parents[2]/'assets',reject_links=True,exclude_release_060=False)!=source['active_assets']):
        raise ValueError('Current active source gate failed')
    if data['source_build']['status']!='editable_source_names_and_schemas_native_build_verified':raise ValueError('Source build gate failed')
    source_inputs=read(owned(args.source_build_report.parent/'source-inputs.json'))
    if sha(args.source_build_report.parent/'source-inputs.json')!=data['source_build']['source_inputs_sha256']:
        raise ValueError('Validated source input manifest changed')
    if source_inputs['assets']!=source['active_assets']:raise ValueError('Source build checked different editable bytes')
    if (bindings['status']!='offline_source_compiled_media_allowlist_and_native_inverse_verified'
        or bindings['payload_count']!=447 or bindings['source_row_count']!=140
        or bindings['media_selection_sha256']!=sha(reports['media'])
        or len(media['models'])!=57):raise ValueError('Final binding/media gate failed')
    # Independent coverage receipt has an explicit positive verdict, never inferred from file presence.
    if data['coverage'].get('static_coverage_verified') is not True:raise ValueError('Independent static coverage gate required')
    if (data['coverage'].get('schema')!='ccp-060-final-private-roster-coverage/v1'
        or data['coverage'].get('status')!='offline_candidate_media_graph_roster_coverage_verified'
        or data['coverage'].get('qualified_model_count')!=57
        or data['coverage'].get('private_rgd_count')!=80):raise ValueError('Unexpected static coverage scope')
    if data['coverage'].get('candidate_sha256')!=digest:raise ValueError('Coverage checked another candidate')
    if data['coverage'].get('handoff_sha256')!=sha(args.handoff):raise ValueError('Coverage checked another handoff')
    if data['coverage'].get('archive_audit_sha256')!=sha(reports['archive']):raise ValueError('Coverage checked another archive audit')
    if data['coverage'].get('media_registry_sha256')!=sha(reports['media']):raise ValueError('Coverage checked another media selection')
    if archive['allowlist_sha256']!=sha(reports['allowlist']):raise ValueError('Archive audit used another allowlist')
    expected={r['member']:(r['before_sha256'],r['sha256']) for r in bindings['payloads']}
    actual={r['member']:(r['before_sha256'],r['after_sha256']) for r in data['allowlist']['entries']}
    if expected!=actual or len(expected)!=447:raise ValueError('Candidate differs from exact final binding selection')
    for row in bindings['payloads']:
        if sha(row['path'])!=row['sha256']:raise ValueError('Final rebuild payload changed')
    with zipfile.ZipFile(PIN/'community_civilization_pack-0.5.3.zip') as old:
        manifest=json.loads(old.read('garrison.json'))
    key=CFG['package_key'];manifest['members']=[{'mod_key':key,'role':'tuning','path':key+'.sga','sha256':digest}]
    manifest['details'].update(version='0.6.0',author=CREDITS,updated='2026-10-18',
        summary='Vietnamese land-unit visuals and private native bindings',
        description='Vietnamese land-unit body designs and compatible stock material remixes across obtainable land tiers. Preserves final 0.5.3 gameplay and protected assets. See EVIDENCE.json for limitations and unrun native gates.',
        changelog='Added 57 private visual selections and isolated Vietnamese consumers. Corrected worker elephant 2 to the Tughlaq worker owner. Deferred custom cargo geometry and Rattan visual switching; existing ranged armor preserved.')
    evidence={'schema':'ccp.release060.evidence/v1','version':'0.6.0','is_final_release':True,
        'credits':CREDITS,'sga_sha256':digest,'baseline_sga_sha256':SGA_SHA,
        'gates':dict(EXPECTED_GATES,editable_source_build=True,active_source_preservation=True),
        'coverage_scope':'Static reachable land roster/model binding coverage, including compatible stock remixes; excludes Officials, ships, buildings, deferred Rattan overlay and unresolved human siege crew replacements. Not native full-roster acceptance.',
        'counts':{'models':57,'art_payloads':305,'payloads':447,'archive_members':1196,
                  'changed_baseline_members':62,'new_members':385,'unchanged_baseline_members':749,
                  'modified_source_files':60,'new_source_files':80},
        'protected053_resources':frozen['preserved053_resources'],
        'reports':{key:{'path':str(path),'sha256':sha(path)} for key,path in reports.items()},
        'limitations':LIMITATIONS,'rebuild_policy':'Exact frozen final053 SGA plus all447 pinned final binding-handoff payloads. Source compile alone is not equivalent.'}
    instructions='''Community Civilization Pack 0.6.0
Credits: hosein81 and chilly5

Import this ZIP through Garrison. Select Community Civilization Pack as both Game
Mode and Tuning Pack, start China and choose Vietnam through the normal pack flow.
Native import, lobby, appearance, gameplay and multiplayer tests remain yours.

Rollback: retain and import the exact final community_civilization_pack-0.5.3.zip.
Do not replace older source/art or delete prior releases.

This release contains qualified humanoid body geometry and compatible native stock
remixes for other families. Source-only geometry experiments are not activated.
Worker elephant 2 uses the complete stock Tughlaq worker model with material
variation; the custom crate geometry failed qualification and is excluded.
Rattan visual switching is deferred; existing +1 ranged armor remains unchanged.
Human siege crew render consumers remain unresolved; stock crew behavior is retained.

See EVIDENCE.json and tools/release_060/RELEASE_060_REPORT.md in the editable project
for precise scope, reproducible overlay steps, sources and native test checklist.
Plain Content Editor source builds require the retained native/media overlay.
'''
    import re
    if not re.fullmatch('[a-z0-9-]{1,20}',args.label):raise ValueError('Safe distinct packaging label required')
    folder=owned(OUT/('package-'+args.label));delivery=owned(OUT/(key+'-0.6.0.zip'))
    if folder.exists() or delivery.exists():raise FileExistsError('Preserve earlier packaging output')
    folder.mkdir(parents=True)
    write(folder/'garrison.json',manifest);write(folder/'EVIDENCE.json',evidence)
    (folder/'START-HERE.txt').write_text(instructions,encoding='utf-8')
    temporary=folder/delivery.name
    with zipfile.ZipFile(temporary,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in ('garrison.json','START-HERE.txt','EVIDENCE.json'):z.write(folder/name,name)
        z.write(candidate,key+'.sga')
    proof=inspect_delivery(temporary)
    if proof['sga_sha256']!=digest:raise ValueError('Wrong owning archive packaged')
    # Promote only a readable, verified ZIP; failed candidates stay in their labelled folder.
    temporary.replace(delivery)
    proof=inspect_delivery(delivery)
    write(OUT/'qualification/final-package-r1.json',proof)
    print(json.dumps(proof,indent=2))


if __name__=='__main__':main()

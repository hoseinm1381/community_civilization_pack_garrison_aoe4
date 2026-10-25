"""Write the delivery report only from hash-bound completed release receipts."""
import json
from pathlib import Path
from common import CONFIG, OUT, ROOT, guarded, read, sha


def report():
    guarded()
    package = read(OUT / 'package-verification.json')
    audit = read(OUT / 'archive-verification.json')
    checks = read(OUT / 'release-checks.json')
    assert package['status'] == audit['status'] == 'passed'
    assert checks['status'] == 'baseline-equivalent-with-known-failures'
    assert sha(package['zip']) == package['zip_sha256']
    assert sha(package['sga']) == package['sga_sha256'] == audit['sga_sha256'] == checks['sga_sha256']
    candidate_path = Path(package['candidate'])
    candidate = read(candidate_path)
    assert sha(candidate_path) == audit['candidate_sha256'] == checks['candidate_sha256']
    assert sha(candidate['archive']) == package['sga_sha256']
    assert checks['normal_files_unchanged'] == 484
    assert checks['accepted_010_art_files_unchanged'] == 214
    assert len(checks['tests']['failures']) == 2 and not checks['tests']['errors']
    summary = checks['static_summary']
    cleanup = read(OUT / 'cleanup-verification.json') if (OUT / 'cleanup-verification.json').exists() else None
    if cleanup is not None:
        assert cleanup['status'] == 'passed' and cleanup['apply'] is True
        assert Path(cleanup['candidate']).resolve() == candidate_path.resolve()
        assert cleanup['candidate_sha256'] == sha(candidate_path)
        assert cleanup['delivery_before'] == cleanup['delivery_after'] == {
            'zip': package['zip_sha256'], 'sga': package['sga_sha256']}
    cleanup_text = ('Cleanup has not run; required inputs and all current build evidence remain.' if cleanup is None
        else f"Verified cleanup removed {cleanup['bytes_reclaimed']} bytes of explicitly regenerable data; "
             'delivery hashes were checked before and after. Exact paths and restore commands are in '
             '`output/release_020/cleanup-verification.json`. Repeated cleanup totals are removal activity, '
             'not an assertion of cumulative net free space.')
    text = f'''# Community Civilization Pack 0.2.0 test release

Garrison edition: four barracks ages, four town-center ages, shared rice-paddy farm
boundaries, shared Hideout design with both native upgrade states, and a scratch
Economy Ministry hall, store and elephant-handling yard. Original UI names/icons,
research and elephant production are preserved. No lumber/mining camps were added.

## Delivery

- ZIP: `{package['zip']}`
- ZIP SHA-256: `{package['zip_sha256']}`
- Combined tuning/game-mode SGA: `{package['sga']}`
- SGA SHA-256: `{package['sga_sha256']}`
- GUID: `{CONFIG['project_guid']}`; key `community_civilization_pack`; version **0.2.0**.
- Exactly one strict `garrison.mod/v1` manifest and measured archive hashes.
- Candidate receipt: `{candidate_path}`.

## Editable sources and rebuild

Editable root: `{ROOT}`.
Blends and private textures: `art/authoring/buildings_020`.
Required exports: `art/exports/buildings_020`; recipes: `art/recipes/release_020`.
Native inventory and cook/reference receipts: `output/release_020`.
Donor caches and heavy generated data are under guarded F: storage; see `STORAGE.md`.
The separate accepted 0.1.0 rollback is `archives/release_010_user_accepted`.
Do not regenerate the immutable starting baseline from edited current source.

From the editable root:

```powershell
& .\\tools\\build_release_020.ps1 -VerifyOnly
& .\\tools\\build_release_020.ps1
```

The full command uses a new run label, fresh art cooks, isolated source compile,
native model reference validation and selective integration over the accepted
0.1.0 archive. Verification-only checks the existing delivery without a native cook.
Garrison-generated game-mode ownership and Live Reload remain off. Shared Blender
authoring and native cooks are serialized; unrelated live Blender work is untouched.

## Preservation and verification

- Normal edition: {checks['normal_files_unchanged']} original files unchanged.
- Accepted house/trap editable sources and exports: {checks['accepted_010_art_files_unchanged']} files unchanged.
- Frozen 0.1.0 source: only ten approved actor visual attachment references change;
  eleven private visual attachment identity stubs added. Gameplay XML and compiled
  actor comparisons allow no nonvisual changes.
- Archive: {audit['baseline_members']} accepted members -> {audit['final_members']} final;
  {len(audit['changed_existing_members'])} existing actor members changed,
  {audit['unchanged_existing_member_count']} existing members byte-identical,
  {len(audit['new_members'])} private members added. No original member removed.
- Native source compile validates {candidate['candidate_source_build']['native_validated_instances']} instances.
- Static validation: {summary['instances']} instances, {summary['errors']} errors,
  {summary['warnings']} warnings, {summary['info']} info. Instance-version warnings
  cover the seven accepted and eleven new private identity stubs; native compilation
  accepts their serialization. The informational stock-reference summary is retained.
- Raw unit suite: {checks['tests']['tests']} tests, exit {checks['raw_suite_exit_code']}, exactly two
  inherited weapon donor-comparison failures, no additional failures/errors/skips.
  Names: `vn_weapon_outpost_handcannon_bambo_alarm_chi` and
  `vn_weapon_outpost_handcannon_bambo_chi`. No gameplay or assertions changed to hide them.
- Final typed graph checks compiled actors, private lists/stamps/models/materials,
  textures and official terminals; all new members must be visited. Actual assembled
  media hashes are bound to successful native reference-cook inputs. CRC/member
  hashes and ZIP readability are checked independently.

Raw receipts: `source-preservation.json`, `release-checks.json`,
`archive-verification.json`, `package-verification.json` under `output/release_020`.

## Art evidence and limits

- Barracks/town-center source handoff and comparisons:
  `output/release_020/barracks_tc/ART_HANDOFF.md`. Eight donor remodels preserve
  topology/index/UV/owner-related bytes; source geometry and roof albedo changes
  are separately audited. Age I has textured comparisons; all four ages have
  solid donor/remodel comparisons. These are authoring views, not game screenshots.
- Ministry/farm/Hideout authoring evidence:
  `output/release_020/ministry_farm_hideout`. Shared farm edges retain native
  clearability; central rice crop, harvesting animator and terrain remain unchanged.
  Offline context previews may use labeled crop/terrain proxies, not the engine.
- Hideout preserves default/stone states and campaign scaffolding. Its added
  shelter uses a typed private native attachment-list graft; removing added nodes
  and reverting approved fields reproduces the original donor serialization.
- Historical material vocabulary draws on Thang Long timber/brick/tile evidence.
  The Ministry arrangement, elephant yard and age progression are artistic
  interpretations, not exact dated reconstructions. Later vernacular buildings
  are analogues. Requested percentages are qualitative visible redesign ranges.

References: [Thang Long excavation](https://hoangthanhthanglong.vn/en/initial-findings-of-the-excavation-of-the-kinh-thien-area/),
[Kinh Thien hall](https://hoangthanhthanglong.vn/en/kinh-thien-palace-the-heart-of-the-imperial-citadel-of-thang-long/),
[North Delta houses](https://journal.vnuf.edu.vn/vi/article/view/1397).

The user reported 0.1.0 tested and good; individual scenarios were not specified.
This new 0.2.0 ZIP has not been imported or tested in a native match by this build.
Native culling/LOD, flags/colours, animation/lifecycle presentation, firing origins,
elephant emergence and multiplayer behavior remain user-test gates. A successful
reference compile/readback does not prove engine rendering of every native state.

## Install and test

Close AoE4, import this ZIP into Garrison, enable it, and select both **Tuning Pack**
and **Game Mode: Community Civilization Pack**. Select China, then Vietnam in the
opening choice. Disable other editions for the initial isolated test.

- Existing/new barracks and all town-center variants through Ages I–IV.
- Construction, repair, cancel/delete, damage and destruction of all new visuals.
- Both farm variants: worker harvesting, isolated fields, adjacent fields and shared edges.
- Both Hideouts before/after upgrades: garrisoning, attacks, effects and scaffold states.
- Ministry: economic research, worker-elephant production and unobstructed visual emergence.
- Two player colours, near/far views, stock China isolation and 0.1.0 house/trap regression.

Roll back by using the preserved 0.1.0 ZIP; no client installation was performed.

## Cleanup

{cleanup_text}
'''
    destination = ROOT / 'docs/RELEASE_020_REPORT.md'
    destination.write_text(text, encoding='utf-8')
    return str(destination)


if __name__ == '__main__':
    print(report())

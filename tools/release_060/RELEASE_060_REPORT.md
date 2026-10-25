# Vietnamese land units 0.6.0

Credits: **hosein81 and chilly5**.

Release archive basis is the exact final 0.5.3 SGA, SHA256
`af202bcb644b4a8c74ff4a598a5374fff7c7a3df47457f3eee5c2195509b6456`.
Final candidate is `output/release_060/assembly/candidate-r2/community_civilization_pack.sga`,
SHA256 `204a889662e2b403b5c0caccb4b79f08bdf0654f90b5f9095ebebfd773b641c8`.
The strict delivery is `output/release_060/community_civilization_pack-0.6.0.zip`.
Its separate package receipt records the final ZIP hash; existence of this report
alone does not establish packaging success.

Delivery verification completed: ZIP SHA256
`913d5a8077aec36e8ce90ccfefcd06ccb39edb42f61bbbaf8667ac6168148ac9`,
90,297,410 bytes. All four expected ZIP members, strict version, exact credits,
manifest identity/content types, CRC/readability and embedded SGA hash passed.
The final release test suite passed **93 tests** in 17.048 seconds; exact command
and captured output are in `qualification/continuation-tests/run-005.json` and `.txt`.

Post-package cleanup removed only the complete candidate-r1 and candidate-r2
archive extraction directories: 2,392 files, **335,189,284 bytes** reclaimed.
Their member/hash inventories, candidate SGAs and regeneration commands remain.
The final ZIP, candidate-r2 SGA and exact 0.5.3 rollback hashes were unchanged after
cleanup. No failed diagnostic, editable input, model cook readback used by media
qualification, baseline extraction, source snapshot or earlier release was removed.

## Scope and evidence

The selected media registry has **57 model selections and 305 native art payloads**.
Twenty-five selections use qualified authored humanoid geometry: four spears,
three archers, two crossbows, handcannon, eight villagers, four men-at-arms bodies,
repeater crossbowman and two monks. Female villagers III–IV preserve their exact
58-bone skin palettes. Unchanged accepted exports were retained without recooking.

The other 32 selections use compatible stock geometry with qualified material
remixes: 16 mounted/trader bodies, three combat elephants, six siege/cart models,
six separately attached equipment models and one Tughlaq worker elephant. Native
anatomy, moving mechanisms and non-albedo material data are preserved. More extensive
editable geometry experiments are retained but excluded from these fallback assets.
The material changes can be modest at gameplay distance.

The archive has **1,196 members**. The explicit 447-member overlay changes 62
existing Vietnamese native resources and adds 385 private resources (305 art and
80 native identities). All **749 untouched baseline members** and the four
protected 0.5.3 payloads are byte-identical. Original native inverse-byte proofs
limit private clone edits to approved identities, visual references and the
authorized worker-owner correction. No foreign stock resource is overridden.
There are no new public gameplay interfaces. Statistics, abilities, production
behavior, voices, localization and project identity remain preservation requirements.

The active source has 60 changed existing Vietnamese XMLs and 80 private XML
identities. All 521 normal-edition files, 1,245 historical art files and project
identity files passed preservation checks. The isolated Content Editor source
build validated all 360 instances. That output is a name/schema check, **not**
the final visual archive. The 447 pinned native/media payloads remain necessary.

Authoritative receipts, relative to `output/release_060`:

- `integration/qualified-media-selection-r1.json`: selected source/art/cook provenance.
- `integration/final-binding-handoff-v3.json`: final source and native payloads,
  hashes, explicit before/after allowlist and inverse proofs.
- `qualification/final-archive-r2/receipt.json`: complete native archive readback.
- `qualification/final-source-r2.json`: current source, identities, older art and normal edition.
- `qualification/editable-source-build/r1/receipt.json`: isolated source compile.
- `qualification/final-coverage-r1.json`: scoped static model/consumer coverage.
- `qualification/final-package-r1.json`: ZIP readability, manifest, credits and embedded SGA hash.
- `qualification/cleanup-r1.json`: approved cache inventory and post-cleanup hashes.

Candidate-r1 and binding handoffs v1/v2 are superseded, retained checkpoints.
The final independent audit found Repeater IV still selecting its original body.
Handoff v3 corrects exactly its default, Cordoba and campaign private tier leaves
to the already registered private Repeater IV body list. Original inverse bytes
pass. The corrected candidate-r2 received a fresh complete archive audit.

## Limits and deferred work

- **Worker elephant:** the custom riderless crate/three-stick source is retained.
  Its native cook collapsed 24 groups into 18 and eight palettes into one, so it
  is excluded. Following the user's explicit authorization, actor
  `vn_unit_war_elephant_2_vit` changes from its cattle attachment to the complete
  native Tughlaq worker-elephant owner/model with material variation. Actor 1
  retains its Sultanate elephant owner. Cargo states and working animations need
  native testing; the custom crate is not activated.
- **Rattan:** one bounded exact-native attachment/schema gate found no qualified
  research-conditioned overlay preserving identity and actions. No Rattan cook
  was attempted without a viable schema/export. Visual activation is deferred;
  editable art and the existing +1 ranged armor implementation remain unchanged.
- **Siege crews:** common/Chinese human crew assets exist, but their runtime render
  consumer was not resolved from the active static selector graph. Stock crew
  behavior is retained. There is no claimed human-crew redesign or proof of runtime
  absence. Siege mechanisms/cart body material remixes are covered separately.
- **Equipment:** only the six qualified reached equipment selections are changed.
  Monk IV staff and other stock tools/attachments remain stock where no safe
  qualified replacement was established. The separately scoped coverage report
  must not be read as a redesign of every runtime attachment.
- **Precache:** new private actor/squad production dependencies are statically
  traced. Fresh-match loading and recursive precache remain native gates. Check
  new monk, trader and siege spawns for `This model has not been precached` warnings.
- Officials remain excluded. Ships and buildings are outside this art milestone.
  Previous accepted buildings, traps, landmarks and stealth are preserved.

## Rebuild and rollback

Run commands from the Garrison source root with Python 3.13. Keep the external
F: storage root and all seven configured junctions available. Scripts call the
storage guard and refuse to reuse build/audit output labels.

1. Run `py -3.13 -B tools/verify_workspace.py --storage-only`.
2. Retain `output/release_060/baseline/final053` and the exact final 0.5.3 ZIP/SGA.
   Never refresh old freezes to accept new changes.
3. Retain all selected payload files referenced by
   `integration/final-binding-handoff-v3.json`, native identity/cook archives,
   qualified media registry, source staging and recipes. The handoff's 447
   before/after records define the complete overlay; source-only XML compilation
   does not recreate final media or all inherited/private selector overrides.
4. Reassemble with
   `py -3.13 -B tools/release_060/assemble_payload_archive_060.py --stage <final-binding-handoff-v3.json> --label <new-label>`.
   This always starts from frozen final053 and verifies every selected payload.
5. Run `verify_archive_delta.py --candidate <new-sga> --allowlist <new-allowlist.json> --evidence <new-owned-audit-directory>`.
   It re-extracts all members, checks archive CRC/identity and exact unchanged bytes.
6. For editable-source revalidation use
   `validate_editable_source_build_060.py --handoff <v3-handoff> --label <new-short-label>`.
   This isolated build leaves active source alone. The compiled-only producer
   replay is recorded in `integration/private-land-graph/compiled-only-producer-replay-v1.json`;
   Repeater IV's three inherited tier selectors are likewise part of the final
   pinned native overlay. Do not substitute the source-build SGA for the final archive.
7. `apply_editable_source_060.py` applies the original v2 140-row source selection
   after its successful r1 source build. v3 has identical source bytes. The tool
   validates before/after states and supports resuming a recorded partial selection;
   unknown edits are rejected. The final read-only source verifier accepts the v3
   handoff and uses the full inventory, including private release_060 XMLs.
8. The package command takes explicit candidate-folder, archive-report, handoff,
   source-report, source-build-report and coverage arguments. It refuses mismatched
   evidence, stages a four-member ZIP, verifies it, then promotes it to the strict
   final filename. A different packaging label preserves failed attempts. Run
   `inspect_delivery_060.py <zip>` independently afterward.

This reproduction route is for exact 0.6.0 from exact final053. Future gameplay
changes need their own baseline/delta review; blindly replaying old native actors
onto a newer gameplay build could erase newer changes.

For in-game rollback, import the retained exact final
`community_civilization_pack-0.5.3.zip` and select its owning mode/tuning pack.
For editable-source rollback, use `baseline/final053/source/assets` plus the source
application allowlist: restore only the 60 changed XMLs and remove only the 80
verified release-owned additions after checking their current hashes. Preserve
0.6.0 sources, art, recipes and diagnostics as a separate checkpoint first.

## Editable delivery and native acceptance

Editable blends/media live under `art/authoring/release_060`, exports under
`art/exports/release_060`, and recipes under `art/recipes/release_060`. Integration,
qualification and package tools live under `tools/release_060`. Failed geometry,
earlier accepted variants, Rattan art, native diagnostics and all prior releases
remain available. External output paths are reached through the existing output
junction; they are project-owned rebuild inputs, not disposable temporary files.

Static tests, export, native cook/readback, archive assembly, editable-source build
and ZIP checks are separate gates. **Import, lobby selection, native appearance,
native gameplay and multiplayer have not been tested by this release process.**
Follow `NATIVE_TEST_CHECKLIST.md` for tier/gender/task/combat/death/LOD/player-color,
mount/crew, siege deployment, private spawn/precache and ordinary Chinese isolation.
User native testing remains the acceptance gate for the delivered visuals.

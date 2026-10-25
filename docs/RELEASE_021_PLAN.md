# 0.2.1 visual refinement release ledger

The user accepts 0.2.0 as good. This milestone replaces the two above-ground
stake visuals with distinct scratch pit traps and refines the Ministry with worn
surfaces and an outside yard with three full-size static stock worker elephants.
The user explicitly approved enlarging Ministry placement from 8x8 to 16x16 to
fit this compound. Terrain is not excavated. No production, cost, research,
trap trigger/duration or other mechanic changes. The prior missing-blueprint
report was a lobby selection mistake.

## Ownership and integration

- Accepted 0.2.0 ZIP/SGA and compact receipts: `archives/release_020_user_accepted`.
- New editable sources: `art/authoring/traps_021` and
  `art/authoring/buildings_021/ministry`; exports use the matching `art/exports`
  directories; recipes use `art/recipes/release_021`.
- Authoring/build helpers: `tools/release_021`; evidence and output:
  `output/release_021`, a guarded junction to the owned F: root.
- The three existing private model identities remain
  `art/scenario/cc010/t1/model`, `art/scenario/cc010/t2/model`, and
  `art/scenario/cc020/economy_ministry/model`.
- Their RGM, RRGEOM and material resources, plus newly cooked private
  `v021_*.rrtex` textures, may change. RGO lifecycle owners, native stamps,
  attribute bindings and PBG identities stay exact. The sole gameplay exception
  is the Ministry actor's site_ext footprint_scale x/y from 8 to 16 in normal
  and campaign variants; all other actor properties must remain exact.
  Obsolete prior textures remain for lossless rollback and accepted-byte parity.

## Build and verification

From the editable root, run `tools/build_release_021.ps1` for fresh Garrison art
registration, native cook, independent cook readback, native Reflect reference
validation, selective archive composition, archive/member comparison, static and
historical test gates, and a strict version 0.2.1 ZIP. Use `-Label r<unique>` to
retain append-only cook runs. `-VerifyOnly` verifies the current candidate and ZIP
without cooking. These commands require F: and expected junctions and never
create fallback storage on E:. Shared native builds use an exclusive file lock.

Fresh isolated Content Editor compilation supplies only the changed Ministry
actor. A typed comparison must restore only its footprint scalars and recover
the accepted compiled actor exactly. Every other compiled gameplay, mode,
localization and attachment member stays byte-identical to 0.2.0. Native art
cooks and exact-model reference validation are fresh, separate gates. Raw tests must retain exactly
the two inherited donor-comparison failures and introduce no failures/errors.

## Acceptance gates

| Gate | Evidence |
| --- | --- |
| Prior-source/normal/accepted art preservation | baseline-freeze.json and baseline verification |
| Authoring and contacts/materials | worker handoffs, recipes and previews |
| Fresh art cook and exact inputs | cook-pointer.json and input snapshot |
| Native model reference validation | integration/reference-cook.json |
| All changed and unchanged archive members | archive-verification.json |
| Static validation and historical tests | release-checks.json and logs |
| ZIP CRC, strict manifest and measured SGA | package-verification.json |
| Client import/lobby/native matches | user gate; not performed by build |

The in-game checklist covers both traps on varied terrain/slopes, upgrades,
construction, attack/destruction and four-second expiry; Ministry construction,
repair/damage/destruction, research, worker-elephant emergence, three-elephant
yard clearance, enlarged placement near neighbors and worker paths, two player
colours, near/far views, and unchanged Chinese buildings.

After verified delivery, remove only proven regenerable release-owned readbacks
or intermediate output, retain all authoring/exports/recipes/registered inputs,
native cook archives and logs, rollback artifacts, handoffs and hash receipts,
and rehash the ZIP/SGA. Record reclaimed bytes in cleanup-verification.json.

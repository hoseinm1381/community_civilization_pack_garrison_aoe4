# 0.5.1 execution ledger

The approved user plan limits this release to normal-edition trap completion logic,
both Castle landmarks and both monastery tiers. Siege workshops, keep and earlier
art are deferred. The normal edition was inspected as a donor and never written or
built. The exact 0.5.0 ZIP/SGA and the 0.4.0 rollback remain preserved.

Commands below ran from the active Garrison root using the configured Blender
Python runtime. Each run has separate `output/release_051` receipts and logs.

| Stage | Command or receipt | Result |
|---|---|---|
| Freeze | `freeze.py --verify` | Prior art/tools, normal files and identities preserved |
| Trap port | `traps.py apply` | Five source deltas; two private child identities and precache entries |
| Native source | `native.py compile rsrc01`, qualified by `finish rsrc01` | 280 instances; exact compiled parent parity and child passage/identity allowlist |
| Final composition | `release.py compose r05101` | 14 payloads, candidate SGA below |
| Archive comparison | `release.py verify` | 12 replacements, 2 additions, 797 unchanged byte-identical members |
| Native art reference | `reference.py rref02` | Seven exact candidate models; exit 0, no diagnostics |
| Package | `release.py package rpack02` | 73 tests, exactly two inherited weapon-parity failures; no new failures/errors/skips; strict ZIP verified |
| Dependency delta | `dependency_closure.py` | New children, parent/precache targets and seven model resource quartets resolved |
| Finalization | `finalize.py` | Only inventoried full-archive readback caches removed; delivery hashes rechecked |
| Human report | `report.py` | Detailed evidence, paths, hashes and pending user tests |

Final ZIP SHA-256:
`40a0dc66621dea0c66823a56d4c0a2479431db456cfcea3554e65e6853a11265`.
Final SGA SHA-256:
`c7da8e37d4ec3750ff9c9668a86a72384e2769a05eb69a699b55caf2c36e9444`.
Reclaimed readback bytes: **317,837,579**. The first unpublished ZIP is retained
under `packaging-history/rpack01`; rpack02 only synchronized art evidence metadata.

Monastery art decision: remove the erroneous added canopy/frame, restore coherent
donor-shaped roofs/selectors, retain smaller Vietnamese shrine/lotus/courtyard
details, and match default/Cordoba/campaign detail transforms to the native base.
Rejected suppression/canopy experiments remain isolated diagnostics. Corrected
editable details are OBJ plus deterministic native recipes; copied Blend/FBX files
are reference assets because background Blender startup timed out. The unrelated
open scene was preserved.

The first reference attempt had a run-root preflight failure; rref02 corrects its
isolated path. Native reference validation uses already-cooked geometry; no new
FBX cook or in-game rendering is claimed. The native decoder's non-finite-UV error
also occurs on the exact unchanged 0.5.0 model; those control logs remain available.
Installed native chunk/index readback separately checked corrected buffers.

Independent review checked final ZIP CRC, four members, manifest identity, embedded
SGA hash, bundled evidence, five current source hashes and final-candidate reference
binding. Import/lobby and native trap passage, landmark visibility/ruins/repair,
monastery appearance, player colours, production access and victory acceptance
remain pending user testing. See `RELEASE_051_REPORT.md` for the complete checklist.

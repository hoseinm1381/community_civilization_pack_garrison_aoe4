# Content Editor and Garrison ownership

The Vietnam gameplay was copied under an independent identity during preparation.
The accepted 0.1.0 houses/traps release is preserved as rollback; the user reported
it tested and good without specifying scenario coverage. Current 0.2.0 work authors
barracks, town centers, rice-paddy boundaries, Hideouts and a scratch Economy Ministry
through Garrison 0.1.4 and selectively integrates approved private visuals.
Preparation and 0.1.0 receipts remain historical; current receipts use
`output/release_020`. See `RELEASE_020_PLAN.md` and `RELEASE_020_LEDGER.md`.

The dedicated command is `tools/build_release_020.ps1`; `-VerifyOnly` checks the
current candidate/ZIP without cooking. A full build allocates a new run label and
freshly cooks registered art, compiles the isolated source, validates exact native
model references, and integrates only approved resources over accepted 0.1.0.
Do not refresh the frozen starting-source receipt from edited active source.

## Authoritative sources

| Surface | Owner / location |
| --- | --- |
| Gameplay, attribute instances, localization, mode RDO/SCAR | Content Editor source in `assets`; project `community_civilization_pack.aoe4mod` |
| Active editable blends/source media | `art/authoring` on E: |
| Retained qualified exports | `art/exports` on E: |
| Asset recipes, consumers, changed-resource allowlists | `art/recipes` on E: |
| Garrison project/registered source/recipes | `art/garrison_library/Mods/community_civilization_pack` -> F: |
| Donor cache | `art/stock_cache`, keyed by official donor identity/hash |
| Temporary candidates and readbacks | `staging` and `output`, on F: |
| Rollback deliveries | `archives`, on F: |

`workspace.json` records tools, identity, links and the retained Vietnam donor
location. Original PBG IDs, Reflect object IDs, localization IDs, Vietnam modules,
and all gameplay values remain. Never enable Garrison's generated game mode or
regenerate its scripts over the existing Vietnam source.

## What transfers from Berber

Berber's Content Editor project remains its gameplay authority. Its Garrison
projects register/cook art separately; explicit integration scripts admit only
approved resources and private visual bindings into the final owning archive.
Large working outputs are externally linked while active editable sources remain
on E:. This workspace adopts those ownership and preservation rules, not Berber
art, actors, binary mutations, release claims, or unfinished experimental routes.

The inspected reference surfaces were Berber's `AGENTS.md`, `STORAGE.md`,
`research/berber_050_project.py`, `research/berber_050_build.py`,
`research/berber_040_integrate_route.md`, and `research/berber_031_package.py`.
They demonstrate project settings, candidate cook ownership, resource inventories,
targeted bindings, preserved-member checks, and strict package hashing. Their
particular geometry/stamp procedures must be requalified for each future asset.

## Asset sequence

1. Verify storage and freeze the current accepted baseline hashes. Inventory the
   exact consumer chain: blueprint -> attachment/tier/stamp -> model/material,
   plus age variants, construction/destruction, sockets, animation, and owner colour.
   Define one asset's scope and expected resource changes before authoring.
2. Author only in owned E: sources using Blender/Garrison guidance. Retain blend,
   textures, recipe, donor identity/hash, transforms, and source dependencies. Add
   the asset to its owned Garrison family project through supported operations.
   Do not create unrelated placeholders just to make a cook run.
3. Run relevant Garrison preflight/export checks. Build/export source changes,
   then cook with Live Reload off. Pin configuration/source hashes, logs, output
   hash and latest successful cook record. An older SGA can survive a failed cook.
4. In an isolated candidate, use supported Content Editor serialization for
   private consumer bindings and stage the exact newly cooked resources required
   by reference validation. Preserve the civilization's animator, speaker,
   production/upgrade chains and gameplay. Generated prototype actors are not
   automatically suitable replacements.
5. Compile the candidate, then integrate only the admitted private bindings/media
   through a compatible verified archive tool if a separate art cook requires it.
   Keep the final pack GUID. Inventory archive members, read back changed members,
   verify reference closure and compare all untouched members against baseline.
   Never blindly merge the entire art archive or change archive identity alone.
6. Only after a fresh successful final archive and readback, create the strict
   `garrison.mod/v1` manifest with measured hashes. The expected final route is one
   `tuning` member containing both tuning-pack and game-mode content, matching the
   existing combined project and Berber pattern; verify actual content/roles before
   packaging. Package key/details.id is `community_civilization_pack`, display name
   is `Community Civilization Pack`, and the reserved first version is `0.1.0`.
   Do not hand-create a fake current `garrison.json` or package stale outputs.
7. Verify ZIP readability/members/SGA hash. A later authorized import must enable
   the new package and explicitly select both Tuning Pack and Game Mode in the
   lobby. Start a fresh match with the original China/Vietnam selection behavior.
   Test each affected age/action/construction/colour and regression scenario.
   Do not enable both edition identities as a substitute for coexistence testing.
8. Follow verified post-release cleanup rules while retaining all rebuild inputs
   and rollback files. Record exact remaining native/multiplayer gates.

## Current commands and gates

From the Garrison root, `tools/build_release.ps1` runs the complete 0.1.0 route:
verify storage/frozen authoring inputs, fresh serial Garrison art cooks, private
resource assembly, native reference validation, isolated source compile, exact
allowlist composition, independent source/archive/closure checks, strict package
verification, and bounded cleanup. `-VerifyOnly` checks the current delivery without
cooking or replacing it. Each full invocation uses a unique label and retains its
evidence under `output/release_010/integration/runs/<label>`. The current accepted
candidate pointer is `output/release_010/current-candidate.json`; delivery and
cleanup receipts are siblings. `docs/RELEASE_010_REPORT.md` is generated from those
receipts after a successful release command. No import/installation is performed.

From the Garrison root, `tools/prepare_garrison.ps1 -CheckOnly` inspects settings;
without the flag it reapplies preparation settings only. `tools/build.ps1
-ValidateOnly` validates the future Content Editor command without running it.
The plain build helper builds Content Editor source, not a final merged Garrison
release. Release-specific tools use the installed Garrison core and archive tool
with isolated native reference validation, matching Berber's selective route.
See the installed version-local `guide` and CLI
`mod-project cook --help` / `package --help` for future supported operations.

Cook/readback/package receipts do not prove import, lobby selection, or a native
match. The normal edition's earlier solo selection evidence is historical and
does not qualify this new GUID. Multiplayer, save/load, later ages, water,
precaching and long-match regression remain separate runtime gates.

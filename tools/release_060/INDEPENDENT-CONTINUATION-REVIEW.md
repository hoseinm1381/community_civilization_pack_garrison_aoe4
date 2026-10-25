# Independent continuation review: 0.6.0 graph and preservation tools

Scope was read-only review of the current inherited identity graph stage, exact final-0.5.3 baseline assumptions, and three release tools. No Blender, native build/cook, source mutation, or active archive assembly was performed.

## Findings

1. **The current graph stage is not directly consumable by the archive assembler.** `output/release_060/integration/private-inherited-graph-stage-r1/stage.json` has schema `ccp-060-private-inherited-graph-stage/v1`, status `identity_graph_and_vietnamese_consumer_references_staged_media_pending`, and 177 payload rows. It has no top-level `baseline_sga_sha256`; its payload rows use `baseline_before_sha256` (and in some rows `before_sha256`). `tools/release_060/assemble_payload_archive_060.py:45-47` requires `stage['baseline_sga_sha256']`, and `:25-26` requires a baseline hash on every row under `before_sha256`. Running that assembler against this named current stage therefore fails before assembly (missing stage key; and the intermediate r2 stage also lacks the required final payload fields). This is consistent with the stage's pending status, but a merged, explicitly pinned final payload-stage artifact is a required handoff before assembly.

2. **Three inherited producer overrides remain compiled-only and need a pinned replay/readback handoff.** The current stage records three overrides with `direct_source_match_count: 0`: the 0.4.0 Vietnamese market actor's default trader squad, plus default and campaign religious-control monk squads. Their target private 0.6.0 squad members and before/after values are explicit. They alter compiled producer references without corresponding direct source elements in this stage. The stage's rebuild policy itself says Content Editor output must be followed by the original-native compiled overlay and qualified media. Keep that overlay as an explicit, hashed recipe and verify its exact output against the pinned before/after values and final archive readback before treating source preservation or production closure as complete. The market actor mapping also needs the existing mechanical-equivalence evidence to accompany the visual identity change; this review did not establish runtime equivalence.

3. **No direct hash or duplicate-member fault was found in the staged rows.** All 177 payload paths existed and matched recorded SHA-256 and byte counts; there were zero case-insensitive duplicate member names. All 97 staged source paths existed and matched their `staged_sha256` values. The stage reports 34 Vietnamese stock-consumer changes and 28 private-native graph records; those counts are stage inventory only, not final archive or roster acceptance.

## Tool review and checks

- `assemble_payload_archive_060.py` checks owned payload paths, duplicate names, before hashes, namespace boundaries, and pinned payload bytes, and creates an isolated candidate plus allowlist. It intentionally leaves full archive readback to a separate gate. It should consume only the eventual merged final payload stage, not the current intermediate graph stage.
- `verify_active_source_delta_060.py` compares the complete active `assets` tree to the frozen final-0.5.3 source with an explicit allowlist, and checks original identities, the normal-edition tree, and earlier editable art. The 97-row graph stage's row shape is compatible with its `source_rows` parser; however, its stated exclusions and preservation results have not yet been verified by running this final gate against the final merged source selection.
- `inspect_delivery_060.py` verifies ZIP names/CRC, version, credits, embedded SGA hash, final-0.5.3 baseline identity, and explicit unrun native gates. Its own qualification limit correctly requires separate archive, bindings, and roster evidence.
- Focused regression tests: `test_payload_archive_060`, `test_source_preservation_060`, and `test_delivery_060` — **11 passed** using the configured bundled Python (`python.exe -B -m unittest ...`). This confirms fixtures, not completion of the current release gates.

## Limits

No final merged payload stage, active-source delta receipt, final archive/readback, ZIP, import, lobby, appearance, gameplay, or multiplayer result was qualified in this review. The identity graph is staged and hash-consistent, but this is not release acceptance.

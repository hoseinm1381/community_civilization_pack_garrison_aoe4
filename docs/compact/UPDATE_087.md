# Compact 0.8.7 update — 2026-10-25

Requested scope: update the existing GitHub working folder from the accepted main-workspace 0.8.7 release with minimal additional data. No push or game installation.

The latest “Generate 0.8.4 unit voices” handoff records independent per-unit 5s/8s/15s cooldowns, Phổ Minh Tower resource drop-off and separate Skirmisher selection groups. The final package contains exactly eight changed archive members since 0.8.4; all audio and art are unchanged.

## Implementation

- Keep all 171 original packs and the original 0.8.4 index byte-identical.
- Layer a 3,793-byte index and one 1,192,813-byte pack over the baseline. Include the four edited XMLs, source recipes/tests, seven compiled RGD replacements, dispatcher, release metadata and compact source/native evidence.
- Reuse the retained 0.8.4 ZIP rather than storing a new full ZIP/SGA. Apply the dispatcher then the seven typed deltas with their original data mount policy. Preserve ZIP entry metadata to reproduce the exact original package.
- Retain existing current artwork, Ogg bank, compiled-only resources and contributor tooling. New release source/native checks are available in the restored `output/release_085` tree. Historical one-time owner scripts remain provenance; the supported portable command is `rebuild-087` or `release` with `--archive-tool`.

## Exact targets

- SGA SHA-256: `c910eaa6e4c1da3e18aee6fc261cd1bb173f100efe573198cfe7398765099a99`.
- ZIP SHA-256: `13911d70f58bd818699179ceb7ddf16fe46cabb401168f06542ad7bdd5cd37f1`.
- ZIP size: 284,924,620 bytes.
- 11,973 member hashes and all mounts must match final verification.

## Validation gates

The main release records completed Content Editor compilation of 377 instances, inheritance/tuning checks and full archive proof. This sync runs independent package reconstruction with original owner roots blocked, fresh archive extraction, source regressions and compact/contributor tests. Current results are recorded in `docs/compact/evidence/update-087.json` when complete. No fresh native compilation, art cook, speech synthesis, game import, drop-off/pathing, selection UI, save/load or multiplayer test is claimed by this sync.

## Verified result

Exact 0.8.7 SGA and ZIP hashes match the delivered release. Fresh extraction verified all 11,973 members and mounts. Original authoring roots were blocked during reconstruction, with zero attempted access. All 172 pack hashes and 42 changed/new virtual files passed verification. Ten compact tests, fifteen contributor tests and three source regressions passed (28 total); 436 asset files were restored for the source checks. An independent read-only review found no blockers.

The optional Lua suite could not rerun because `lupa` is absent in the checked runtimes; no dependency installation was performed. Main-release tests/native compilation remain separately recorded upstream evidence. The four XMLs preserve the main authoring bytes; its line-ending rewrite makes Git's ordinary line diff larger, while `git diff --ignore-space-at-eol -- assets` shows only the 60 authorized added lines. No fresh art/audio generation or game acceptance is claimed.

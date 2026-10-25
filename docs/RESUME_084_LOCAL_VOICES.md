# Resume Garrison 0.8.4 local Vietnamese voices

## Completed package — 2026-10-25

**Final ZIP verified: 284,922,388 bytes (284.92 MB), below 400 MB.** All 9,702 spoken jobs and 568 pools are accounted for, including 128 user-approved minor speech exceptions. No generation remains. See [delivery evidence and remaining native acceptance](RELEASE_084_DELIVERY.md) and `local/WRAP_UP_CHECKPOINT.json`. Successful logs are `local/wrap-up-v2`; earlier unfinished status and counts below are historical. The extra large download is stopped. Do not restart synthesis/downloads or rerun immutable release labels.

## Wrap-up supersedes generation continuation — 2026-10-25

The user requested no additional tool download and accepted minor imperfections in the remaining spoken lines. The large model download is stopped and partial files retained. No more synthesis or downloads are authorized for this wrap-up. The saved medium recheck was intentionally stopped; its continuation's failed status records that interruption, not lost recordings.

Current accepted delivery: **9,702 / 9,702 spoken jobs**, including **128 explicitly attested minor speech exceptions**. Fifteen accepted synthetic efforts are archived and excluded; the delivery retains stock effort media. Read `local/minor-speech-exceptions.json` before interpreting any word-screen failures. STOP remains present to prevent generation continuation.

The finishing chain is compression, complete compressed bank, reversible overlay and ordinary ZIP verification. Follow `local/wrap-up-v1/status.txt`, `bank.log`, `overlay.log` and `package.log`. Completed delivery proof belongs at `output/release_084/delivery/final-v1/verification.json`; its existence and current hashes, rather than this narrative, establish package completion. Native game acceptance remains independent. Offline checks: **111 passed**.

## Resumed after reboot: 2026-10-25

**Latest checkpoint (UTC about 08:35):** the initial dialogue retakes finished with 9,426 accepted spoken jobs. The second medium-ASR pass checked 800 saved originals and recovered 36 more, leaving **9,462 / 9,702 spoken jobs** accepted, plus 15 archived custom efforts outside delivery. Native editable reference compilation has actually completed: **397 instances, 20 new identities**, with namespace verification and a separately fresh extraction/provenance proof in `local/native-reference-fresh-proof.json`. Native receipt: `integration/native-reference-v2/receipt.json`. Do not rerun the immutable cook output paths.

An active foreground continuation is running from `tools/release_084/CONTINUE_SPOKEN_084.ps1`. Its current status/logs are under `local/continuations/20261025t083522236z/`. It waits for the earlier ASR worker, then runs dialogue with an explicit **five-attempt ceiling**, medium recheck through attempt five, compression and full bank verification. This is a foreground job, with no scheduled automation. The script honors `generation/STOP` between phases and retains failures. To resume a later phase, pass `-StartPhase recheck`, `compress` or `verify`. Avoid duplicate GPU/native jobs and duplicate compression writers.

The default per-job ceiling remains three. The optional two extra LOCAL retakes keep the actor/model and every approved word unchanged, introducing a comma after the first word to aid clarity. Original attempts are never reset or overwritten. New requests record exact synthesis text/recipe, and new completed state binds request SHA-256; unprompted word checks are unchanged. Explicit commands are `RESUME_LOCAL_084.ps1 -Phase dialogue -AttemptCeiling 5` and `-Phase recheck -AttemptCeiling 5`. Custom effort generation is rejected under the approved spoken-only scope. Latest offline suite: **107 tests passed**, including bounded extended retakes, source-word preservation and request hash integrity; read-only review found no important defects.

The strict assembler uses local Python 3.11 for audio and delegates its storage/preservation checks to configured Python 3.12; its actual local-runtime storage preflight passed. Native RGD/provenance work continues to require Blender Python 3.13. This avoids the `Path.is_junction` compatibility gap.

**Latest scope change:** the user explicitly chose “Preserve stock pain/death sounds and scope 0.8.4 to custom spoken dialogue.” `local/delivery-scope.json` freezes this approval without changing any original manifest/recording IDs or historical attempt limits. Custom delivery requires 9,702 dialogue recordings. Do not start further custom-effort synthesis. The 15 accepted local effort candidates and prior rejected attempts remain archived.

`integration/stock-effort-inventory-v1/inventory.json` traces 67 consumers to 19 available Chinese stock profiles; `stock-efforts-v1/receipt.json` contains 827 decoded/compressed original stock media sources. `stock_export.py` is resumable and never modifies the game. Portable vgmstream r2117 was downloaded from its official GitHub release to F:; its release metadata, ZIP and tool hashes are retained. The generic read-only SPD parser handles the actual Chinese female villager record with 67 media entries; the older Donso parser's 64-entry limit and failed inventory diagnostic remain untouched. `manatarmsFemale` has no corresponding Chinese stock profile: the receipt explicitly aliases that custom female infantry assignment to stock `villagerFemale` efforts. Exact original assignment and native scheduling are not claimed.

The bank/overlay/assembler now verify stock effort source/recipe/audio hashes and bind the exact stock receipt. SCAR routes stock light/heavy pain and death independently of spoken cooldowns, with local effort arbitration. Native playback/quality and the female fallback need acceptance. Latest offline suite: 104 tests passed. Full source-reference compilation is queued after the current dialogue worker exits; it must not overlap GPU models.

Latest size projection, including 9,702 dialogue jobs, 9,815,249 bytes of stock efforts and a 10 MB assembly margin: **326,259,299 bytes**, below the 400,000,000-byte limit. `local/package-size-projection.json` records the measured sample. This is an estimate, not a completed ZIP.

This section supersedes the historical shutdown counts below. The user approved leaving the changed `art/authoring/release_081/buffalo/r4/model.blend` untouched and using the exact released 0.8.3 buffalo assets. `local/approved-authoring-deviation.json` records both hashes. Use `tools/release_084/check_preservation.py` rather than refreshing the historical freeze: 7,846 protected files matched and the one approved authoring deviation was retained.

The first full compression snapshot completed: 8,717 clips, 97,358,251 encoded bytes. The full-coverage size projection is 323,947,300 bytes including a 10 MB margin. Recompute with `size_projection.py` after subsequent compression. The user requires a popup notification if the projection or actual ZIP exceeds 400,000,000 bytes; do not silently deliver an oversized package.

The medium ASR recovery is running in `local/recheck-after-reboot.log`; its live progress is `local/generation/recheck-medium-checkpoint.json`. It has recovered more than 230 saved recordings without synthesis. Wait for its final checkpoint before starting another memory-heavy job. Dialogue resumed briefly and accepted 34 additional recordings, then stopped cooperatively so ASR could run. The STOP marker remains until explicit dialogue/effort resumption. Refresh all counts from state rather than using the historical shutdown snapshot.

Interpreter correction: **native RGD tools require `workspace.json`'s `blender_python`, Python 3.13**, because `garrison_shared` is a CPython 3.13 native module. Use it for `prepare_voice_identities.py`, `audit_voice_identities.py`, `prepare_voice_source.py`, `compile_voice_reference.py`, `native_reference_proof.py` and `voice_overlay.py`. Use configured Python 3.12 for storage/inheritance/tuning/offline checks and the F: Python 3.11 environment for synthesis/compression/audio validation/assembly. The older instruction below saying configured Python for every identity helper is superseded.

Typed reversible voice overlays, lifecycle/precache patches and a strict final assembler are now implemented in `voice_overlay.py`, `voice_lifecycle.py` and `assemble_release.py`. They have not been applied. Full output remains gated on complete coverage and all 20 audited private identities. The assembler recomposes routing and checks current compressed payload hashes, independently audits actual native reference provenance through fresh RGD extraction, preserves all untouched 0.8.3 members/mounts, checks namespace before/after assembly, and verifies ZIP CRC and embedded hashes. This is preparation, not package or runtime proof. Actual full voice native compilation, decoder playback, audible quality, save/load and multiplayer remain unverified. Latest offline suite: 95 tests passed (`local/offline-tests-integration.log`), with a separate read-only review of the new release gates.

Paused at the user's request for laptop shutdown on 2026-10-25, UTC 05:17:35. Read this file, `docs/RELEASE_084_LOCAL.md`, `STORAGE.md`, `workspace.json` and `output/release_084/local/SHUTDOWN_CHECKPOINT.json` before resuming. No automation was created. The cooperative `generation/STOP` marker remains present.

## Latest user requirements

- Complete playable human unit voices, both available genders and all available AoE ages, including naval crews. Northern Đại Việt characterization, stable actor per role across ages, six alternatives × three independent performances per supported pool.
- Local generation is authorized. All downloaded models, portable dependencies, caches, temporary files and media belong on the owned F: project storage. Existing cloud credits were exhausted; make no further paid API calls. Credentials are not needed for the local continuation and are not recorded in this handoff.
- **The final ordinary Garrison mod ZIP must not exceed 400,000,000 bytes, and voice lines must be compressed.** The user explicitly corrected the earlier opposite size statement. Preserve original recordings and canonical mono 48 kHz PCM16 masters on F:; distribute compressed playback files. Measure actual final ZIP size.
- Preserve normal edition, 0.8.3 final-v2, all gameplay/art/buffalo animations, identity, bundle key and rollback. No installation into the game, publication, deletion, purchases, billing changes or scheduled automation.
- A full 0.8.4 mod release requires complete required coverage. Earlier listening packages remain explicitly partial pilots. Word checks do not certify acting, historical pronunciation, native-speaker approval or in-game behavior.

## Exact stopped state

`output/release_084/local/generation/state.json` holds **8,717 accepted recordings: 8,702 dialogue + 15 nonverbal efforts**. Required: 9,702 dialogue + 684 efforts = 10,386 unique jobs, addressing 12,348 directed slots and 686 pools. **1,000 dialogue + 669 efforts remain missing; 246 pools are complete.** Every dialogue job has been started. At shutdown, 90 missing dialogue jobs had reached their three-attempt ceiling; the other missing jobs retain eligible retakes. Resume never resets attempts.

The main worker log `local/bulk-worker-resume3.log` ends `COOPERATIVE_STOP`, then `LOCAL_BATCH_FINISHED 8717 new accepted 6326 synthesized 7679`. It exited normally. Do not restart completed jobs or overwrite originals. `shutdown-checkpoints/20261025T051735Z/` contains hash-verified copies of state, attempts, manifest, generation checkpoint and input fingerprint, plus `remaining-jobs.json`. The last six accepted playback hashes were checked at shutdown. Full-bank validation remains to be refreshed after generation.

The compression pilot produced **20 verified per-clip receipts totaling 191,390 encoded bytes**. It was stopped during its post-limit scan, after encoding had finished. Those receipts/audio are valid and resumable. Its old loaded code scanned remaining sources unnecessarily after hitting the 20-new-clip limit; the source now breaks promptly at that limit. The pilot did not finish `compressed-v1/index.json`; rerunning compression rebuilds it from receipts without re-encoding valid exports. Preserve the empty scan-created directories and existing evidence.

## Local runtime and voices

Physical runtime: `F:\aoe_4_temp\Community_civilization_pack_garrison_temp\tool-cache\local-voices-084`. All seven expected workspace junctions must pass storage preflight. Do not replace missing junctions with ordinary E: directories. GPU is RTX 5050 Laptop 8 GB; portable Python 3.11 + Torch 2.8.0+cu128 work. The established workspace guard needs configured Python 3.12; `local_guard()` delegates to it. `local_env.ps1` places caches/TMP on F: and clears HF tokens/telemetry.

VieNeu SDK revision `04044e1b8f822f946bafb2c88b716459f4164152`, v3 Turbo model revision `61b85e3d937fbbacb387714180e8182823512523`, synthesis fingerprint `130c52597bc9198050ced7c533bf8caf5f741840527b26386025685a2e4375e2`. `local_inputs.py` rechecks actual SDK/model/dependency bytes. The frozen production manifest contains selected actors; preserve it. GUNNER and NAVAL_TRANSPORT were recast to Minh Đức and Quốc Tuấn before production. The older `VOICES` constant retains the initial audition actors intentionally; do not regenerate the production manifest from that constant.

Whisper large-v3-turbo and PhoWhisper-small are installed and used. **PhoWhisper-medium also finished downloading**, including the 3,055,754,969-byte weights, and publisher SHA-256 verification. Its pinned revision is `55a7e3eb6c906de891f8f06a107754427dd3be79`. The final download log is `local/download-medium-resume2.log`; earlier interrupted downloads/logs are retained. The downloader now bounds stalled transfers with curl's 60-second low-speed timeout.

`local_recheck.py` has not run. It rechecks saved rejected dialogue with unprompted medium ASR, preserves earlier disagreements, validates recipes/original/playback/model provenance and never synthesizes or relaxes effort screening. A medium recheck sidecar is hash-bound to accepted state and rechecked on validation/export. Future review may need to examine rare legacy certified request handling if such a pending request is encountered; never invent an input fingerprint.

Efforts remain weak candidates. The pilot attempted 228 first takes and accepted 15 under the strict technical screen. Both original recognizers must positively return allowed nonlexical sounds; empty transcripts and tone-distinct Vietnamese words fail. Do not substitute sigh/laughter for death or speak English direction tags. Acting is unapproved. VieNeu v3 ignores natural-language style directions; retain this limitation rather than claiming expressive delivery from text checks.

## Resume commands

From the Garrison root, use `tools/release_084/RESUME_LOCAL_084.ps1`. Its default `-Phase status` only reads the shutdown checkpoint after storage preflight. Explicit dialogue/effort phases archive the STOP marker before resuming. Generation, ASR and native cook helpers share the memory-heavy lock; serialize them. Overlapping a native cook with GPU models previously caused a real allocation failure. Existing user applications remain untouched.

```powershell
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase status
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase dialogue
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase effort
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase recheck
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase compress
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase verify
.\tools\release_084\RESUME_LOCAL_084.ps1 -Phase listen
```

Run phases one at a time and inspect failures before continuing. Dialogue/effort synthesis has a global maximum of three attempts per job, with explicit per-run budgets. Recheck only revisits originals, including exhausted dialogue jobs; no new synthesis. Compression may be repeated after recovery to add newly accepted jobs. Verification must be current before building/exporting the bank. Listening export uses all verified compressed recordings, a new immutable timestamp label, ZIP CRC and embedded hash checks, plus a 400,000,000-byte size guard. It remains a listening pilot, not an installable mod.

## Compression and native format qualification

`local_compress.py` exports mono 48 kHz, nominal 64 kbps **Ogg Vorbis** with a hash-verified portable FFmpeg copy in F:/.../tools. Original/PCM bytes remain unchanged. Each receipt records source/encoder/encoded hashes, source recipe, full local decode, PCM decode hash, rate/channels, duration, RMS and clipping checks. Final export reloads and decodes compressed files, rejects changed/duplicate performances, and uses `.ogg` paths. `voice_bank.py --compressed --partial-preview --label bank-compressed-preview-v2` can prepare a disabled preview after fresh bank verification and identity audits. Earlier `bank-partial-preview` remains historical evidence.

The installed backend contains rodio 0.17.3 Vorbis decoder code. Own-helper-PID probes `codec-probe-v1/v2` read an isolated tiny SGA and used zero/nearly-zero gain. They **did not produce the deliberate invalid-control decoder error**, so their lack of error is inconclusive. Do not claim native decoder/playback success. Compressed route qualification remains independent of encoding/full local decoding. No game was launched or modified by these probes. The 0.8.3 ZIP is 197,948,355 bytes; preliminary compressed sizes appear compatible with the final 400 MB cap, but only an actual assembled ZIP proves it.

Compression/routing/listening integration additions have passed unit checks but have not yet completed an end-to-end compressed listening export. The 57-clip PCM representative pilot is already verified at `local/delivery/representative-v1/LISTEN.html`, with its ZIP and proof alongside it. Preserve it.

## Remaining native preparation and packaging

The current production graph has 67 human squad consumers, including one inherited stock monk from the private Pagoda's default spawner. Speaker closure v3: 303 resources, zero unresolved donors. Production routes v3: 161 resources, zero unresolved, plus three extra squads (that monk and two animals). Tier upgrade squad/entity targets are followed; associated/requirement references are excluded. Existing MONK age-III/IV recordings explicitly cover the monk; no new synthesis jobs. Wildlife/elephant animal calls stay untouched; human elephant dialogue was not admitted without a verified channel.

Eighteen private voice-owner identities are already Garrison-derived and audited, including naval pairs, siege actors and female attachment lists. This involved an empty native base cook with **zero instances**, followed by derivation, and is not compilation of 18 XMLs or the full voice pack. After GPU workers exit, run these with configured Python:

1. `tools/release_084/prepare_voice_identities.py --monk-extra` — separate two-identity monk cook and combined 20-identity receipt.
2. `tools/release_084/audit_voice_identities.py --complete` — exact donor-delta/undo and current official/private PBG collision proof.
3. `tools/release_084/prepare_voice_source.py` — separate `F:/.../staging/release_084/source-draft-v2`, preserving v1 and active source.
4. Refresh `tools/check_extension_inheritance.py --refresh --root <source-draft-v2> --official-cache output/release_084/integration/current-official-extensions.json --output output/release_084/integration/source-draft-v2-inheritance.json`.
5. Run installed `C:/Users/RS/.codex/skills/modify-aoe4-tuning-packs/scripts/validate_tuning_pack.py <source-draft-v2> --json output/release_084/integration/source-draft-v2-tuning.json`; parse XML with .NET too. V1 had 395 instances, zero tuning/inheritance errors and 149 retained version-format warnings; v2 should add two instances.
6. `tools/release_084/compile_voice_reference.py` — actual staged editable-identity reference compilation and fresh identity readbacks, not a complete voice release. It preserves diagnostics, checks archive namespace, and serializes native work.

Actual speech suppression, private production/AI/upgrade reference overlays, loading/precache and lifecycle activation are still unfinished. Do not mute partially covered consumers or package the raw reference cook as the final mod. Final assembly must retain the 0.8.3 compiled-only owning-resource overlays and untouched member bytes/mounts, then add approved speech/routing/audio changes. Preserve GUID `b7fcea91-257b-408f-b9e8-ae4d8bc402e1`, archive namespace `b7fcea91257b408fb9e8ae4d8bc402e1`, and bundle key `community_civilization_pack`. Check burnproj identity and `tools/release_073/check_identity.py --archive <final.sga>` before/after assembly; freshly extract and verify hashes and mounts, ZIP CRC, actual ZIP size and compressed voice presence.

Baseline `output/release_084/baseline.json` protects 7,847 files. It was fully rechecked earlier; rerun `tools/release_084/freeze.py` before final work/delivery. 0.8.3 final-v2 SGA SHA-256 `85abef75f6c0ea5ccb1236140e97895232b061fbf1e50db81d7edc90252ac034`; ZIP SHA-256 `08f7129c7f200b47f83b48a8a33bc1a46a4923c70c01b9237d4fa91da8cccd2c`. No active assets were changed by this continuation.

## Verification boundaries

Latest offline suite: **82 tests passed**, log `local/offline-tests-compression.log`. Dispatcher source check v2: 56 calls, no low-confidence APIs or missing locdb IDs; 13 known local/Garrison/keyword resolutions. Latest full audio snapshot validated 6,485 clips with zero invalid files; all later producer clips had per-take checks, but a new full-bank pass remains mandatory. Native reference compile, final archive/package proof, import, audible acting/pronunciation, correct age/gender routing, stock overlap, save/load and multiplayer remain separate gates. See `docs/RELEASE_084_NATIVE_ACCEPTANCE.md`. No full 0.8.4 mod ZIP has been assembled, installed or published.

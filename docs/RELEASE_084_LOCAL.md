# 0.8.4 local voice production

**Paused for laptop shutdown:** read [the current resume handoff](RESUME_084_LOCAL_VOICES.md) and `output/release_084/local/SHUTDOWN_CHECKPOINT.json`. All voice workers stopped; 8,702 dialogue and 15 effort clips saved. Explicit resume commands are in the handoff.

## Final delivery size constraint

The user's corrected requirement is a final ordinary Garrison ZIP **at most 400,000,000 bytes**, including compressed voice lines. The earlier statement that it should exceed 400 MB was explicitly corrected. The 0.8.3 final-v2 ZIP is 197,948,355 bytes. Preserve original recordings and canonical mono 48 kHz PCM16 masters on F:, while preparing separate mono 48 kHz, nominal 64 kbps Ogg Vorbis playback exports with `local_compress.py`. Each export retains its PCM hash, encoder hash, full decode checks, duration/level checks and encoded hash. Measure the actual assembled final ZIP against the limit before delivery; size estimates do not prove compliance.

The installed backend contains rodio's Vorbis decoder, but the own-helper-PID codec probes have not yet established decoder execution: their deliberately invalid control did not generate an error. Their lack of error is inconclusive. Keep compressed route qualification separate from successful encoding/full local decoding.

The user authorized local generation and downloads on F: after all existing cloud credits were exhausted. This continues the approved 0.8.4 scope. No new paid API calls, purchases, billing changes, Google generation, installation into the game, publication, deletion or automation are included.

All new portable runtime, model, dependency, cache and temporary files live under:

`F:\aoe_4_temp\Community_civilization_pack_garrison_temp\tool-cache\local-voices-084`

The existing project output junction places candidates under the owned F: output root. Normal, the 0.8.3 final-v2 delivery and all 926 accepted cloud recordings remain the baseline. Local job identities, casting and state are separate in `output/release_084/local`. A local role must be complete before replacing a cloud role; no mid-role provider substitution is permitted.

## Pinned inputs

| Input | Revision |
|---|---|
| VieNeu SDK 3.8.3 | `04044e1b8f822f946bafb2c88b716459f4164152` |
| VieNeu v3 Turbo | `61b85e3d937fbbacb387714180e8182823512523` |
| MOSS Audio Tokenizer Nano | `6aa02b01e445cc585582cf0ba480bc3ea6c8dd68` |
| Whisper large-v3-turbo | `41f01f3fe87f28c78e2fbf8b568835947dd65ed9` |
| VinAI PhoWhisper-small | `a86b604c346caf7148c37512eafe783a16420adb` |
| VinAI PhoWhisper-medium, saved-dialogue recovery only | `55a7e3eb6c906de891f8f06a107754427dd3be79` |
| PyTorch CUDA wheel | 2.8.0+cu128; SHA-256 `34c55443aafd31046a7963b63d30bc3b628ee4a704f826796c865fdfd05bb596` |

Publisher metadata and verified per-file SHA-256 receipts accompany downloaded models. Retain SDK LICENSE and model README files. Public model downloads require no account token. Synthesis and transcription explicitly use offline local paths after download. Actual CUDA availability and generated PCM must be verified; a dependency installation alone is not a working voice engine.

The optional medium Vietnamese recognizer rechecks existing rejected dialogue after generation exits. `local_recheck.py` does no synthesis and uses no expected-text prompt. It retains both previous recognizers' disagreements, binds new sidecars to the original/playback/model hashes, and accepts only exact normalized words with Vietnamese tones retained. It does not relax the two-positive-recognizer requirement for nonverbal efforts. This remains an automatic word screen, not pronunciation or acting approval. The synthesis fingerprint and selected actors do not change when this verifier is added.

## Qualification

The candidate cast uses only presets labelled Northern (`Bắc`) by the current SDK. Age changes use the same actor. Shared preset actors across some roles are explicitly listed in the local manifest; their audio requests remain independent.

VieNeu v3 Turbo ignores the deprecated `style` argument. Audition intent labels therefore do not prove whispered, shouted or historical delivery. Test calm, urgent, quiet and effort probes, with three separately seeded generations each. Preserve float originals and mono 48 kHz, 16-bit PCM candidates. Local unprompted PhoWhisper checks the actual words, with Whisper large-v3-turbo checking mismatches. Neither establishes acting or native-speaker approval.

Do not send English nonverbal directions such as `[groan]` to ordinary dialogue synthesis. Effort probes need separate qualification. Keep incomplete or unqualified output labelled a partial listening pilot. Do not suppress existing native voices, assemble a full 0.8.4 ZIP or claim release readiness based on the local manifest alone.

## Commands

Run from the Garrison root. `tools/release_084/local_env.ps1` sets process-only F: cache paths. The isolated interpreter is `...\local-voices-084\venv\Scripts\python.exe`.

1. `tools/release_084/install_local.ps1 -Stage base`
2. Resume the recorded CUDA wheel URL with `curl.exe -C -`; retain incomplete data, then run `tools/release_084/install_local.ps1 -Stage cuda` (verifies publisher SHA-256).
3. Run `tools/release_084/download_local_models.py` with configured Python. It resumes pinned downloads and checks publisher LFS hashes.
4. Run `tools/release_084/local_audition.py --prepare-only` to verify the isolated manifest and Northern cast.
5. Run the audition script with isolated Python and `--limit 1000`, then `tools/release_084/local_check.py` with the same environment.

The local runtime is an authoring tool on F:, not a player-facing dependency. Integration, actual native compilation, archive/ZIP proof, import, audible quality, age routing, original-voice overlap, save/load and multiplayer remain separate gates.

## Local production and integrity

The selected cast is recorded in `output/release_084/local/casting-selected.json`. Gunner uses Minh Đức and Transport uses Quốc Tuấn after the initial candidates failed the automatic word screen. These roles had no production requests before selection; every age of each role uses the same selected preset.

Use `local_batch.py --kind dialogue --limit 10000 --max-attempts 30000` with the isolated interpreter. It serializes model batches of at most six same-actor, same-age and same-take requests. Different takes are independent model calls. Failed performances count against the work cap, and each job has at most three immutable attempt folders. Original float WAVs, request receipts, model fingerprints and transcription diagnostics are retained. A `generation/STOP` file requests a safe checkpoint between batches; preserve it as a named receipt before resuming.

Local GPU workers and new native cook helpers share `memory-heavy-job.lock`. The 16 GiB authoring machine exhausted Windows allocation headroom when the native editor and voice models overlapped. The interrupted four-clip batch kept its originals for zero-synthesis recovery; new helpers reject overlapping heavy jobs. Existing user applications and system memory settings are untouched.

The separate `--kind effort` pilot uses six nonlexical vocalization cues, never English `[grunt]` or `[groan]` directions as speech. Both recognizers must positively pass the short nonlexical screen. Empty transcripts and lexical tone variants such as `ở`, `hạ` and `hư` remain unresolved. This technical screen does not qualify acted pain or death.

`local_bank_validation.py` checks the retained source recipes, all pool/alias references, six alternatives × three takes, playback and float-original hashes, model identity, distinct performance bytes and word/nonlexical evidence. `--require-complete` fails for any missing or invalid recording. It reports technical coverage separately from audible quality, native compilation and package proof. The cloud manifest and originals remain unchanged.

## Integration preparation

`inventory/speaker-closure-v2/audit.json` records a recursive audit of 301 squad/entity/attachment resources, including inactive human owners for ownership review. It selectively extracted 32 additional official donors and resolved every active actor/list edge. Inactive audit roots do not authorize new generation or native suppression.

The subsequent default production audit (`inventory/production-routes-v2/audit.json`) follows actual construction targets, loadouts, spawners and tier targets through 161 resources. The first broad diagnostic graph is preserved under v1; it wrongly followed `associated_ebps` metadata into a Mongol roster and is not availability evidence. Regression tests now exclude associated/requirement references. The corrected audit found one additional human consumer: the inherited stock Chinese monk in the private Pagoda's default spawner. It reuses the already recorded MONK age-III/IV role explicitly; no extra synthesis jobs or art/gameplay replacement is intended. The two other additional squads are animals and remain excluded. The Dock's campaign-only scout ship is outside ordinary default-mode coverage.

`inventory/consumers-complete.json` now records 67 admitted human squad consumers. `speaker-closure-v3/audit.json` includes the stock monk: 303 resources, zero unresolved actor/list donors, and no extra attachment-speaker override for that monk. Its stock SBPS/EBPS pair still needs private identities. `prepare_voice_identities.py --monk-extra` performs that isolated cook after GPU generation ends, then writes an explicit 20-identity combined receipt. `audit_voice_identities.py --complete` checks the combined proof; `prepare_voice_source.py` stages a separate v2 source draft without overwriting v1.

The 18 shared resources used by active consumers have isolated Garrison-derived identities: seven naval squads, seven naval actors, two land siege actors and two female-soldier lists. The Garrison CLI ran a real native base cook with **zero attribute instances**, then produced derived compiled payloads. This is not native compilation of 18 editable XML instances or the complete 0.8.4 pack. Retain the native logs, derived payload receipts, exact-delta/undo audit and current-official identity collision check. No voice suppression or active source change has been applied.

The v1 staged source passed validation for 395 instances with zero errors. All 149 warnings are `UNSEEN_INSTANCE_VERSION` for the project's proven version-2 inherited children (18 are newly added). The refreshed current-official inherited-extension check covered 214 private and 5,758 official blueprints with zero errors; .NET XmlReader also parsed all 395 staged instances. `compile_voice_reference.py` is the separate guarded native reference entrypoint. It has not yet run; it must never overlap GPU models. Its output is reference evidence, not a release archive: final assembly must retain every required compiled-only 0.8.3 owning resource.

The 57-clip representative listening pilot is under `local/delivery/representative-v1`. It includes one complete selection phrase in three independent performances for every selected role. Its ZIP CRC and all embedded WAV SHA-256 values were checked. It contains no Garrison manifest, executable or installer and is explicitly not an installable mod. `local_listening_package.py --all --label <new-label>` can later package every currently verified recording as another partial listening artifact; it preserves prior packages and does not bypass full-release coverage gates.

# Vietnamese unit voices — 0.8.0 preparation

Prepared **18 October 2026 (Asia/Tehran)** for Community Civilization Pack. Credits: **hosein81 and chilly5**.

Historical research and complete **creative script drafts** for Northern Đại Việt, approximately AD 700–1700: land and naval roles, four chronological banks, six phrases per semantic pool and three fresh takes per phrase. No audio was generated, and no mod files were edited or built.

**Start with [SAMPLE_LINES.md](SAMPLE_LINES.md), then [HISTORY_AND_LANGUAGE.md](HISTORY_AND_LANGUAGE.md).** Native Vietnamese editorial review and historical-pronunciation approval remain pending. Complete sentences are original adaptations; source citations do not make them attested ancient speech. Earlier whole-sentence pronunciation is unresolved and has not been fabricated.

## Contents

| Read | Purpose |
|---|---|
| [HISTORY_AND_LANGUAGE.md](HISTORY_AND_LANGUAGE.md) | Four historical ranges, language evidence, role vocabulary, regional conflicts and editorial choices |
| [SOURCES.md](SOURCES.md) | Eighteen stable scholarly/institutional/production/local evidence entries with links, locators and access limits |
| [UNIT_COVERAGE.md](UNIT_COVERAGE.md) | Source roster, inherited naval queue, starts, production and unresolved consumers |
| [UNIT_INVENTORY.json](UNIT_INVENTORY.json) | Source paths, evidence lines, speaker metadata and hashes |
| [UNIT_VOICE_MAP.json](UNIT_VOICE_MAP.json) | Every inventoried consumer/reference assigned a proposed profile, exclusion or unresolved status |
| [CASTING_AND_DELIVERY.md](CASTING_AND_DELIVERY.md) | Eighteen proposed actor identities, age continuity, six phrases/three takes and performance rules |
| [VOICE_SCRIPTS.md](VOICE_SCRIPTS.md) | Complete readable dialogue and effort bank |
| [VOICE_SCRIPTS.json](VOICE_SCRIPTS.json) | Full structured bank with stable IDs, meanings, sources, tone aids, take directions and reuse groups |
| [PRONUNCIATION_LEXICON.json](PRONUNCIATION_LEXICON.json) | Bounded historical forms and explicitly modern rehearsal examples |
| [SCRIPT_ACCOUNTING.md](SCRIPT_ACCOUNTING.md) | Exact counts and the difference between unique wording, expanded rows and a final recording order |
| [NATIVE_CONTEXT_MAPPING.json](NATIVE_CONTEXT_MAPPING.json) | Every context in seven decoded stock profiles, preserving raw suffixes and unqualified semantic proposals |
| [SPEECH_CONSUMERS.json](SPEECH_CONSUMERS.json) | Literal local speech fields and squad references; inherited/cooked attachment limits retained |
| [RECORDING_HANDOFF.md](RECORDING_HANDOFF.md) | Review/session workflow, filenames, eventual recording and listening gates |
| [TECHNICAL_PREPARATION.md](TECHNICAL_PREPARATION.md) | Future route options and separate native acceptance requirements |
| [VALIDATION.json](VALIDATION.json) | Original 0.7.0 offline checks and protected-source hash comparison; retained as historical evidence |
| [REVIEW.md](REVIEW.md) | Independent artifact review, addressed findings and remaining qualification limits |

Content checks passed; the **strict source-preservation gate detected drift** in existing release-tool scripts during preparation. [PREPARATION_REPORT.md](PREPARATION_REPORT.md) separates the results. The immutable before-snapshot was retained, and those scripts were neither restored nor edited by this preparation.

This dossier moved from `0.7.0` to `0.8.0` without new recordings or audio integration. Existing `VN070_` phrase IDs and authored text remain stable. The original folder is archived under `output/release_070/voices`; the historical validation and preservation receipts in this folder retain their original bytes and failed preservation result. Future runs of `verify_preparation.py` write `VALIDATION_080.json`, `CONTENT_VALIDATION_080.json` and `SOURCE_PRESERVATION_AFTER_080.json` so they do not replace those receipts.

## Important distinctions

- Four age banks are **writing/research capacity**, not evidence that every unit exists in every age. Real unlock requirements and native chronology scheduling still need qualification.
- Age-sensitive wording covers shared commands and fourteen additional role/task pools. Other concrete task phrases intentionally recur across ages; [AGE_VARIATION_AUDIT.json](AGE_VARIATION_AUDIT.json) quantifies that reuse. Historical sound progression remains an unapproved research target.
- Six phrases × three takes applies to each authored pool. Shared generic and role/weapon pools are alternatives for one event, not extra simultaneous speech. Repeated text is explicitly accounted for.
- The full expanded bank includes conditional/dormant content and human effort copies across ages. It is **not** an instruction to record every row. Choose verified consumers/events and intentional aliases before commissioning audio.
- Stock delivery labels are preserved. T1/T2/T3 do **not** mean `iNorm/iHigh/iStealth`. No native delivery/age mapping is implemented.
- The confirmed Dock queue contains seven stock ship families. Fishing uses `tradeShip`; transport uses `scoutShip`; military ships use `ship`/`warShip`; fireships use `fireShip`. Proposed new roles can deliberately split/share those original actors.
- Effective inherited land ages/gender attachments and unexamined native speech profiles remain explicitly unresolved. No “all native slots replaced” claim is made.
- Only human dialogue/efforts are planned. Sheep, animal calls, hull/engine/weapon effects and unrelated civilization speech remain outside this preparation.

## Reproduce preparation checks

Run from the project parent in PowerShell using the configured bundled Python:

```powershell
& 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'Community_civilization_pack_garrison\tools\verify_workspace.py' --storage-only
& 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'Community_civilization_pack_garrison\0.8.0\research_tools\verify_preparation.py'
```

To regenerate only the structured/readable scripts, accounting, source-consumer crosswalks and preview after editing draft dialogue:

```powershell
& 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' 'Community_civilization_pack_garrison\0.8.0\research_tools\make_scripts.py'
```

That helper writes **only within this 0.8.0 folder**. It runs no mod build, cook or game process. Re-run validation after regeneration. Retain selected stock metadata, official attribute readbacks and their hashes as research provenance; they contain no supplied audio recordings. `SOURCE_PRESERVATION_BEFORE.json` records its precise protected-file scope and exclusions rather than claiming a complete art/output freeze.

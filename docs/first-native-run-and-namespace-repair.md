# First user-operated native run and source repair

2026-10-14. User built the project and reported no popup or gameplay effect. No build or test was executed by Codex during diagnosis or repair.

## Observed evidence

- Content Editor screenshot: zero errors, four warnings stating `Property bag group [ebps] [v2_probe_*] not found` in the mode RDO. The custom EBPS appear in the Attribute Editor tree under `Vietnam_v2`.
- User-built `archives/Vietnam_v2.sga`: 1,726,967 bytes, written 19:46:44 local client time. Read-only archive inspection found all seven private RGDs and all three SCAR sources, including the unchanged unqualified lookup code. No compiled RGD properties were inferred or edited.
- Game `warnings.log`, 19:53:36: selected `vietnam_v2_gm`; both `WinConditionExtensionPackPart` and `TuningExtensionPackPart` mounted for `a743d7d1d7534cf78817e29d8ded7366`; human civilization `chinese`.
- Game log, 19:53:50: `LoadWinCondition: - [winconditions\VietnamMode] succeeded.` The game exited normally. Ordinary SCAR print markers, including stock core markers, are absent from that log. Marker absence cannot establish callback execution or non-execution.

## Diagnosis and narrow source change

Private entities were requested without their project namespace in both the reflected precache references and SCAR blueprint lookups. This is inconsistent with GUID-owned private instances and with the GUID-qualified custom lookup pattern found in other editable mode sources. The four editor warnings establish unresolved precache names; the same naming mistake in `EBP_Exists` is a candidate explanation for taking the missing-blueprint branch. The exact runtime branch was not captured, so removal of the missing-popup symptom remains unverified.

- Qualify four existing RDO `m_fileName` values as `a743d7d1d7534cf78817e29d8ded7366:v2_probe_*`. Preserve existing reflected object IDs and graph.
- Qualify the four SCAR `EBP_Exists` names and three initialization entity/squad lookup names with the same GUID.
- Keep stock Chinese names unqualified and official attribute parents unchanged.
- Add initialization/eligibility branch markers and visible system-message diagnostics for the no-eligible-human and missing-qualified-blueprint branches.
- Synchronize the foundation generator and regression fixture source with the naming contract. Do not execute them under the user's testing boundary.
- Focused fresh read-only review found no additional confirmed startup blocker or cleanup regression. Its diagnostic wording findings were corrected: unavailable blueprints do not establish missing tuning, and README lists the new branch markers.

Official evidence: installed ScarDoc signatures for `EBP_Exists`, `BP_GetEntityBlueprint`, `BP_GetSquadBlueprint`, `UI_SystemMessageShow`, and `UIWarning_Show`; read-only current native core registration/delegate and player-table functions. Secondary naming example: editable Company of Heroes mode uses `BP_GetEntityBlueprint("cc8b94b55c6f42dd9da034d4fb9f43d7:building_open_pit_mine_small_gold")`. This is serialization/call-shape evidence, not proof of Vietnam's runtime behavior.

## Next user gate

Reopen the edited source and build. Confirm the four precache warnings are gone. Start a Chinese-human Dark Age match with this mode and tuning. Report whether the selection/countdown appears, a diagnostic message appears, or there is still no visible response. XAML is not yet established as the cause or required repair; selection initialization and qualified loading must be established first. Do not activate the China-replacement fallback from this failed opening alone.

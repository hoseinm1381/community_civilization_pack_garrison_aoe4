# Vietnam runtime repair — completed source verification 2026-10-16

> Superseded for trap/tunneling by `native-trap-tunnel-restoration.md` at the user's request on 2026-10-16. The dynasty UI repair remains active. The SCAR tunnel/area-damage design and its diagnostic instructions below are historical.

Source revision: `20261015-trap-tunnel-dynasty-r1`.

Dynasty and tunneling source repairs are implemented. The original native trap failure is **not yet diagnosed or claimed fixed**. No Content Editor build, installation, publication, or native match was performed by Codex.

## Implementation and official evidence

- Dynasty: collapse the existing `DynastyUI` presenter locally for Vietnam and disable hit testing. Close the dropdown; if the stock controller helper refuses to toggle without a selected Town Center, clear its verified global local-UI flag and remove its specific Cancel handler. Restore the presenter for other player views, retaining the stock race visibility rules. Existing refresh/local-player/restore hooks reapply it.
- The installed `UI.sga` resource `ui/resources/hudresources.xaml:871-893` ORs `[is_ui_visible]` with Chinese race IDs. Official `gameplay/chi/current_dynasty_ui.scar` defines the presenter, show/dropdown helpers, global `_dynasty.data_context.is_dropdown_visible`, and `HUDPageBase.Cancel` handler. `UI_SetPropertyValue` and `UI_RemoveEventHandler` are documented APIs; official `combat_mode.scar` demonstrates property updates.
- Tunneling: the internal `entity_id_v1` payload is `sorted,squad,ids|destinationEntityID`. Local `Misc_IsMouseOverEntity`/`Misc_GetMouseOverEntity` identify the clicked building, following official `scarutil.scar` usage. The registered network callback resolves it in the sender's owned entities and validates life, completion, destination type, Citadel, squad ownership/life/ability, siege/hold exclusions, source distance, and landing. Only validated relocation spends the 120-second cooldown. Reject malformed, duplicate, over-64, and inexact numeric IDs with reason-coded logs. The old coordinate payload is intentionally incompatible; start a fresh match with the rebuilt package.
- Ability XML: clear only `requirements_target`, which previously excluded landmarks. Keep the existing position-targeted modal activation; SCAR owns destination validation. Click the building itself; ground clicks are rejected. All other XML semantics and identities are unchanged.
- Traps: retain SCAR as the sole damage owner and preserve existing gameplay conditions, damage/research, delay, blast position, cancellation, and Roller construction behavior. Add at most 192 diagnostic lines per match and six samples per entity/stage, with five-second spacing for unchanged samples. Existing tracked/armed/detonated gameplay markers remain. No native weapon was restored.
- Temporary query groups are destroyed; the existing `Player_GetSquads` observer is engine-owned and must not be destroyed. Local UI/mouse state never directly moves squads or consumes cooldown.

## Verification

All 77 source tests passed, including 32 focused repair/package fixtures. Both skill self-tests passed. Results are recorded in `runtime-repair-tests-green.txt`, `runtime-repair-full-tests.txt`, and `runtime-repair-static.txt`; final MCP results are in `runtime-repair-mcp.json`. Fixtures are offline evidence, not engine proof.

Coverage includes all 15 private tunnel destinations; local UI recreation/view changes and the controller dropdown guard; ownership, malformed payloads, source/landing boundaries, non-finite landing results, cooldown, and group cleanup; both trap types, enemy presence at completion, fixed-position delayed damage, friendly immunity, research, lethal damage, destruction/disappearance cancellation, log limits, and abandoned versus progressing Roller construction.

Tuning validation finds 237 instances, zero errors/warnings, and the existing informational summary of 1,036 externally supplied reference values. No reference value was added. Semantic comparison with the rollback confirms only the tunnel target list changed. The baseline hash inventory confirms exactly four assets changed; all building-time definitions, localization, manifests, RDO, and private identities are preserved.

MCP found no unresolved new engine calls. It reports the draft-local helpers `moveSquad`, `nearCitadel`, `reject`, `validID`, and `diagnostic` as unknown, plus tokenizer false positives `and`/`or`; each is defined locally or a Lua keyword. Retained low-confidence usage classifications have exact official API declarations: `Player_GetEntitiesEGroup`, `UI_ClearModalAbilityPhaseCallback`, `UI_MessageBoxHide`, and `UI_MessageBoxReset`. Static warnings concern the engine-owned squad observer, guarded despawned-squad enumeration, and imported `VietnamSelectionCore` table methods.

The deployed SGA's archive GUID was verified. Its three repaired SCAR files differ from current source, as expected before rebuilding; see `runtime-repair-package-check.txt`. This is **not** a current-package pass. The read-only package helper compares all SCAR sources and hashes, normalizing BOM/line endings; it does not validate compiled tuning.

Remaining native contracts: hover-target availability at `TP_Issued`, Visibility property conversion, presenter recreation timing, passable landing placement, multiplayer host/client behavior, and the original trap failure. Save/load, later-age starts, and Vietnamese AI remain outside this milestone.

## Next user-owned build and match

1. Save/build/package `Vietnam_v2.aoe4mod` in Content Editor and inspect its Error List.
2. From this project directory, verify the installed package without extracting or modifying it:

```powershell
& 'C:\Users\RS\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' tools/verify_runtime_package.py --package 'C:\Users\RS\Documents\My Games\Age of Empires IV\mods\extension\local\Vietnam_v2\Vietnam_v2.sga' --runtime 'E:\age of empires 4 mods\07_Subscribed_Mods\Subscribed_Mods\Current\subscribed_mods\.aoe4-sga-v10-runtime'
```

Expect the correct archive identity and **zero SCAR mismatches**. Retain any archive-reader error rather than treating it as a comparison pass.

3. Start a fresh Dark Age custom match and choose Vietnam. Confirm:

```text
VIETNAM_V2_SOURCE revision=20261015-trap-tunnel-dynasty-r1 tunnel_protocol=entity_id_v1 trap_diagnostics=1
```

4. Confirm the dynasty button is absent. In a separate China-choice match, check its normal button, dropdown, bonuses, and roster. Controller users should also test an open dropdown after deselecting the TC.
5. Finish Imperial Citadel, place an eligible squad within 16 units, activate Tunneling, and click each owned completed TC/keep/landmark. Expect a request with `destination=...`, followed by `VIETNAM_V2_TUNNEL squad=... destination=...`. An immediate repeat should report `reason=cooldown`. Check incomplete/foreign destinations and siege/garrisoned squads; failures must not spend cooldown.
6. Test each trap with an enemy villager already nearby at completion, then separately walk an enemy into range. Keep a friendly villager as control. Expect completion/ready/query diagnostics, `TRAP_ARMED`, then `TRAP_DAMAGE ... applied=1` and `TRAP_DETONATED` after one second. Check research and destruction cancellation separately. Preserve the full fresh `warnings.log` if anything fails.
7. Diagnostic interpretation: absent `TRAP_SCAN_PLAYER_*` means the update entry needs investigation; `MISSING` identifies loss from the player group; eligibility shows construction/life rejection; query counts show empty results or filtered candidates; damage counts distinguish immunity and applied damage. Repair the proven failing boundary and repeat this native test before declaring the trap fixed.
8. Recheck House 15s/faster House 7.5s, Farm 6s, Market 20s, secondary TC 150s, and the working tower gate/timing. Their source definitions were unchanged.

## Execution record

- Ruling: use the requested non-Git source root with a focused rollback ZIP and baseline hash inventory. Cost: rollback uses the archive rather than Git.
- Ruling: close the controller dropdown through its verified global local-UI field and specific handler when the official helper's selection guard prevents closure. Cost if official UI changes: review this adapter; simulation authority is unaffected.
- One independent read-only review found that controller issue. Its regression failed before the correction and passed afterward. Review's extra boundary and Roller scenarios were added. No other demonstrated Important/Critical findings remained.
- `runtime-repair-baseline.json` records the integrity-checked rollback ZIP, SHA-256, and the pre-repair hashes of all 272 assets.

# Full Persia import into Normal

The user confirmed opening selection works and authorized the full import on
2026-10-26. That result establishes selection; the newly imported roster and
landmark mechanics still need the native acceptance below.

## Implemented source

- All 280 non-army source instances are private under `*/persia/ps_*`: 113
  entities, 79 squads, 52 weapons, 18 abilities and 18 technologies. The extra
  private upgrade is an eligibility signal with no gameplay bonus of its own.
- All 1,803 source-local references were translated, including relocated
  stock-path aliases, parents, build/production menus, tier replacement units,
  projectiles, naval dependencies, batch squads and upgrades. All 27 original
  icons retain their bytes under a private UI directory. Custom localization
  uses separate destination IDs. The source Persia project is unchanged.
- Current official inheritance was resolved for all authored default/campaign
  scopes. There are 516 extension-identity normalizations, with all original
  scalar/statetree gameplay values preserved. The original source also audits
  without duplicate extensions; this is migration normalization, not a claim
  that 516 existing source bugs were repaired. See `persia-preservation.json`.
- Private Persian Town Center/villager/scout definitions replace the probe.
  Entity and squad conversion remain preflighted and postchecked. Both pairs
  share one 30-second deadline; timeout keeps the original civilization. AI
  remains native. Normal's GUID, mode entry, RDO IDs and existing Vietnam
  attribute/gameplay bytes are preserved.
- Gundeshapur now supplies a private functioning-landmark signal. Il-Khanid's
  existing OR permits either Castle Age or that signal, retaining the preceding
  dynasty and self/queued guards. A completed, active, living owned Gundeshapur
  qualifies; foundations, ruins and lost ownership do not. Repeated updates and
  multiple sources do not stack. Completed dynasty/economic research is never
  removed. Counts refresh every 0.5 seconds after native deferred state changes.
- Native Divan supervision, Caravanserai abilities, dynasty/veterancy tiers,
  Wynguard-style Ali Qapu batches, costs and weapons remain source-owned.
  Their ongoing effects and persistent repairable ruin owners were preserved.

## Important native limit

The original source notes that some landmark benefits can persist while ruined.
The donor effects live inside compiled native statetrees, whose teardown cannot
be established from editable XML or the available official source index. This
import preserves those mechanisms and adds explicit functioning-landmark
eligibility; it does **not** claim to have repaired unverified donor-effect
teardown. Do not add a second scripted bonus or blanket-disable action/construction
extensions to conceal that uncertainty. Test each effect below, then diagnose any
surviving benefit through its actual native contract. No native ruin entity is
replaced or respawned.

Grand Caravanserai's tooltip advertises 33% cheaper Traders, while source Trader
base costs are 60 Wood/60 Gold and the discount is not explicit in its tuning
tiers. A compiled donor effect may implement it. Source costs were preserved;
changing that discrepancy requires the user's individual decision after native
measurement. Two unused localization rows containing pasted XML were repaired
to the label they explicitly referenced; this changes no gameplay.

## Native acceptance

Build `Community_Civilization_Pack_Normal.aoe4mod` with the owned Content Editor,
after reloading the project so old probe instances are not retained. The source
GUID and archive NiceName remain `a743d7d1d7534cf78817e29d8ded7366`. Verify a real
completed burn, the final SGA namespace and source readback before import.

1. Fresh Dark Age, standard resources: select Chinese humans and Delhi humans,
   mix China/Vietnam/Delhi/Persia, include multiple Persians and native AI.
   Check timeout, early completion, disconnects, host/client, teams and FFA.
2. Confirm one TC, six villagers, one scout, unchanged resources and no duplicate
   sheep. Check old and newly trained villagers, all builder menus and future
   production; no native Delhi or Vietnam data may change.
3. Play every age and landmark route. Check all unique units, replacements,
   weapons/abilities, naval units and simultaneous dynasty upgrades. Compare
   costs, research, population and visuals with the original source behavior.
4. With the preceding dynasty researched, verify Il-Khanid in Feudal is locked
   without a functioning Gundeshapur, unlocked when complete, revoked while
   ruined, and restored after full repair. Research already completed must stay.
   Exercise two sources and ownership changes without stacked/unintended effects.
5. Test each landmark alive, destroyed, partially repaired and fully repaired:
   Gundeshapur supervision/Feudal availability; Grand Caravanserai Trader aura
   and discount; economy Divan supervision; vision/Assassin abilities; Ali Qapu
   batches; siege-landmark production. Check ongoing benefits stop and return
   correctly. This is an unverified native acceptance gate, not a passed fix.
6. For Ali Qapu, preserve and verify the dummy-plus-five-additional-squad contract,
   costs, produced quantities, population accounting, cancellation and rally.
   Supervision must not stack unexpectedly across simultaneous Divans.

No Persian AI, Nomad, later-age start, save/load or new artwork is implemented.
Content Editor compilation, final package/readback, import, full native behavior
and multiplayer have not been run by this source handoff.

## GitHub and recovery

This folder is the independent `normal` branch, with a fresh history separate
from Garrison. The baseline commit `48a1897c3790aefc1ca68bda3c2cd8e14e63aeb4`
preserves the user-accepted selection test. Source editing/building needs no
external project or cache. The original Persia project is needed only to rerun
the one-time importer, not to edit or compile the imported mod.

Current tests live under `tests/current`; old fixtures/tests are retained under
`tests/legacy`. Work, archives, editor caches, machine settings and generated
outputs are ignored and stay local. No large Garrison development store or
Garrison history was copied into this branch. Git retains the accepted baseline
and final source. The clean staged export passed verification with a fresh Lupa
dependency and without local caches or configuration. Automatic approval review
blocked deletion of the temporary verification copies; their local paths are
recorded in the handoff and ignored work receipts. No new preservation ZIP was made.

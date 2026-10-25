# Vietnamese land units 0.6.0 — user native test checklist

Status: **not run**. Export, cook/readback, binding, archive and ZIP checks are
separate evidence. This checklist does not mark any native gate as passed.

Keep the exact final 0.5.3 ZIP for rollback. Record the 0.6.0 delivery ZIP SHA256,
game/Garrison versions, selected mode and tuning pack, map and player colors.

## Import and lobby

- Close AoE4, import the strict 0.6.0 ZIP into Garrison, and confirm the displayed
  version and credits `hosein81 and chilly5`.
- Select Community Civilization Pack as both Game Mode and Tuning Pack. Start
  China, select Vietnam through the pack's normal flow, and confirm normal start.
- Separately start China without selecting Vietnam. Stock Chinese units, monks,
  traders and siege must keep their Chinese visuals and normal behavior.

## Roster and appearance

Check existing units through age changes and newly produced units after each age.
Check ordinary, discounted, free, landmark and ability-spawned consumers where
available. Officials are excluded; ships and buildings are outside this art release.

- Spears I–IV, including fire variants; archers II–IV; crossbows III–IV; handcannon
  IV; repeater crossbow IV; male/female men-at-arms III–IV.
- Male and female villagers I–IV; monks III–IV; traders II–IV.
- Male and female scouts I–IV; horsemen II–IV; knights III–IV. Check the rider and
  mount together rather than interpreting an unposed Blender rest view as gameplay.
- Both worker elephant consumers. Actor 1 retains its Sultanate elephant owner;
  actor 2 now selects the complete Tughlaq worker model with material variation.
  The custom wooden crate/three-stick geometry failed its cook and is excluded.
  Check every resource cargo state and all conditional carry attachments.
- All combat elephant consumers, handcannon crews, free variants, howdahs and weapons.
- Obtainable siege engines, siege carts, crews, carried equipment and alternate
  render consumers. Check both deployed and mobile/packed states where supported.
  Human siege crew consumers remain unresolved in the static selector graph;
  their stock behavior is retained, without a claimed human-crew redesign.

At close and normal gameplay distance, inspect silhouette, material placement,
weapons/grips, cloth/tack/armor, team-color readability, ground contact, clipping
and missing/black parts. Move the camera across every LOD transition. Test at least
red and blue owners, including selected/highlighted units and multiple units together.
Compatible stock remixes retain native geometry; do not expect source-only geometry
experiments listed as excluded in the coverage/limitation report.

## Tasks, combat and lifecycle

- Villagers: construct, repair, farm, hunt, gather each resource, carry/deposit,
  garrison/ungarrison, idle and move. Retain the existing automatic stealth behavior.
- Monks: heal, convert and collect/carry/deposit relics. Traders: establish, move
  and complete trade routes with normal cargo and income.
  Test fresh production of private monks, traders and siege in a new match and
  inspect warnings for `This model has not been precached`. The native factory
  dependency graph is verified; recursive loading/precache is not runtime-proven.
- Infantry/ranged: idle, move, attack, attack-move, charge/brace where applicable,
  torch buildings, switch targets, garrison, die and leave the normal corpse.
- Cavalry/elephants: idle, turn, move, charge, attack with each weapon/crew, take
  damage, die and show the normal mount/crew lifecycle.
- Siege: construct, crew where applicable, pack/deploy, turn, move, aim, fire,
  reload, repair, die and show native destruction. Inspect moving mechanisms and
  projectile origins while operating; a static preview cannot prove these states.
- Check costs, build time, production choices, population, upgrades, statistics,
  voices, abilities and unit identity/actions against final 0.5.3.

## Rattan and regression

The final limitation report determines whether the optional visual switch was
qualified or deferred. In either case, verify the existing +1 ranged armor behavior
on all six ranged consumers, without losing health, orders or unit identity.
Test research before/after unit production and before/after tier upgrades.

Verify the preserved landmarks, villager stealth, traps and monastery still behave
as in final 0.5.3. Their accepted art and unrelated gameplay are preservation gates,
not new art work in this release.

## Multiplayer and recording results

Multiplayer remains a separate test: use the exact same ZIP/hash for all players,
include Vietnam and ordinary China in one match, exercise upgrades and the unit
families above, and check for synchronization problems and cross-civilization art.

For a failure, record unit/tier/gender and spawn route, task/state, map/color,
camera distance, reproduction steps, screenshots/video and the relevant warning
log interval. Distinguish import, lobby, appearance, behavior and multiplayer results.

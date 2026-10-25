# 0.6.1 fresh native acceptance checklist

No native match has been run for this artifact. Static, native asset cook/readback,
archive and ZIP evidence are separate from this checklist.

1. Close AoE4, import the full `community_civilization_pack-0.6.1.zip`, confirm
   version/credits and select the owning pack as both Game Mode and Tuning Pack.
   Start a **fresh** China-to-Vietnam match. A saved 0.6.0 match is not a clean test.
2. Produce spearmen I–IV (including fire variants), archers II–IV, crossbows
   III–IV, handcannons IV, repeater IV, men-at-arms III–IV, both villager/scout
   genders and ages, horsemen II–IV, knights III–IV, monks III–IV, traders II–IV,
   both worker elephants, combat elephants and all obtainable siege/cart consumers.
   Check existing units after tier upgrades as well as newly produced ones.
3. Check visible bodies and equipment at near/far distance, LOD transitions,
   idle/move/attack/charge/brace/death, mounts/crews, garrisoning, resources/cargo,
   relics/trade and siege mobile/deployed states. Look for invisible or black parts.
   Inspect warnings for missing blueprints/assets or unprecached private actors.
4. In separate matches build **Imperial Citadel** and **Resistance Headquarters**.
   Inspect foundation, intermediate construction and completed 5,000/5,000 HP
   appearance **without relying on selection outlines**. Check near/far views and
   two player colours. Full dynamic tint may differ with object-PBR materials.
5. Damage each Castle landmark, destroy it, select the persistent ruin and repair
   it back to completion. Test interrupted/resumed repairs, selection, footprint,
   access, garrison/production and landmark victory. Native owners and actors are
   preserved, but these actual runtime transitions are not verified by the cook.
6. Confirm ordinary Chinese units and buildings remain unchanged, including a
   Chinese opponent in the same match. Check prior traps, monastery, Feudal
   landmarks, activated archer stealth and automatic villager stealth.
7. Check costs/stats/abilities/production/upgrades/voices/localization and unit
   identity. Rattan keeps its existing +1 armor and no visual research switch;
   custom worker-elephant crate remains excluded; human siege crews remain stock.
8. Multiplayer is a separate acceptance gate. All participants must use this
   exact ZIP/hash. Exercise upgrades, simultaneous combat and Vietnam/China
   isolation and watch for desynchronization.

Record game/Garrison versions, artifact SHA256, unit/tier/gender, task/state,
camera distance, player colour, screenshots and the matching warnings.log interval.
Retain the exact failed 0.6.0 and earlier 0.5.3 ZIPs as historical rollback evidence;
neither is claimed as a proven fallback for the Castle visibility problem.

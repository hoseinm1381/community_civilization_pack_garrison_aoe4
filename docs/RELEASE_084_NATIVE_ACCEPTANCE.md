# 0.8.4 voice acceptance gates

This is a pending acceptance matrix, not evidence that the game has been run. No installation or publication is authorized by this document. The local listening ZIP is media for review and must not be imported as a Garrison mod.

## Scope and proof

Current default-mode reconciliation contains 67 human squad consumers and 19 recording roles. The inherited stock monk in the private Pagoda shares the MONK age-III/IV voice bank explicitly, while retaining its stock artwork and gameplay. The campaign-only stock scout ship is outside default-mode coverage. Buffalo and elephant calls remain native; no elephant human channel has been verified.

The user changed scope after reboot: **custom spoken dialogue only; preserve stock pain/death sounds**. Required custom audio is now 9,702 dialogue jobs. The historical 684 custom effort recipes, attempts and 15 accepted candidates remain archived and are excluded from delivery; generation state and original manifests are unchanged. `local/delivery-scope.json` records approval and the generation-manifest hash.

Stock pain, heavy pain and death media are replayed through the same Garrison audio route because native dialogue/efforts share one speaker binding. The inventory contains 827 original media sources across 19 Chinese speaker profiles. Original WEMs and decoded masters are retained, while playback is mono 48 kHz Vorbis. This preserves stock sound media, **not original native scheduling**. The dispatcher observes HP loss/death and admits efforts separately from dialogue cooldowns. A missing Chinese `manatarmsFemale` profile is explicitly aliased to existing stock `villagerFemale` efforts; exact original female infantry behavior has not been established. Test that fallback and damage/death timing audibly before acceptance.

Offline tests exercise the actual Lua dispatcher with mocks. Audio checks establish file format, hash/recipe integrity and conservative word/nonlexical screens. Neither proves expressive acting, native pronunciation, stock-voice suppression or a working game session. VieNeu v3 Turbo ignores the `style` parameter; urgency and quiet intent labels are not acting approval. Historical pronunciation is a creative approximation.

| Gate | Required evidence | Current state |
|---|---|---|
| Generation | Every required spoken job, six alternatives × three distinct performances per supported dialogue pool; explicit stock effort aliases | Dialogue retakes in progress; 827 stock effort sources exported |
| Source/static | Current donor/parent checks, identity collision checks, typed semantic undo, local routing tests | Preparation checks passed; final integration pending |
| Native compilation | Completed Content Editor log for exact staged inputs, fresh identity readbacks and archive namespace | Editable identity reference build completed: 397 validated instances and 20 fresh identity readbacks. Full voice post-cook integration/native playback remain separate and unverified |
| Final SGA/package | Before/after namespace checks, fresh extraction, untouched bytes/mounts, compressed audio hashes, one manifest and ZIP integrity; at most 400,000,000 bytes | Full release not assembled |
| Import/listening | Actual ordinary Garrison import and fresh-process audible tests | Not run |
| Save/load | Actual restored-match voice behavior and clean session restart | Not run |
| Multiplayer | Actual two-client ownership, isolation, repeated commands and long-match behavior | Not run |

## Native test cases

| Case | Expected result |
|---|---|
| Opening army versus newly trained Villagers | Both appearances respond; test the six converted starting units separately from freshly trained units. No stock/custom overlap or unintended silence. |
| Ages I–IV | Civilian, Scout, monk and crew banks follow available player ages. Military fixed-tier voices follow the actual upgraded blueprint. Test advancing age without researching the unit upgrade, then researching it. |
| Training variations | Ordinary and tower/discount routes, male/female branches, skirmishers and siege families retain their existing art, costs, abilities and gameplay. |
| Monks | Test the inherited stock-art monk produced by the default Pagoda separately from the private Vietnamese-art monk routes. Both use the same selected MONK character. |
| Naval crews | Test fishing, trade, transport, combat ship, war galley, warship and fire ship, at every available age and after relevant upgrades. Check AI production and research compatibility independently. |
| Selection and groups | Holding selection does not repeat; mixed groups have one responder. Include wildlife, buffalo, foreign stock units and private captured units. |
| Orders | Repeat move, attack, attack-move, stop, hold, retreat, work/build, trade, garrison/load/unload and available abilities. Generic default orders use acknowledgement without inventing a target discriminator. |
| Variation | Repeated admissions rotate different phrases before another performance of the same words; all three performances are independently generated. Duration/cooldown gating prevents a chorus. |
| Damage/death | Original stock light/heavy pain and death recordings dispatch during custom dialogue, with separate local effort cooldowns; distant responses fade. Check the documented female infantry stock fallback. Dead or recycled IDs never trigger another actor's speech. Native event parity is not claimed. |
| Ownership | Capture/conversion, local-player changes and observer transitions remove stale handlers and route only the intended locally owned consumers. Check rapid capture/death timing natively. |
| Teardown | Pause/resume, menu return, second match in one process and full restart leave no orphan rules, stale cooldowns or continuing backend playback. |
| Save/load | Reload a save with selected mixed units, combat and changed ages; verify fresh playback session, routing and repetition state. |
| Audio balance | Check audible clarity, urgent and quiet delivery, no clipping/overlap, and native-slider versus external-backend volume behavior. No new player configuration is introduced. |
| Multiplayer | Two clients, Vietnamese/other civilization combinations, ownership changes and repeated commands. Audio state must not affect simulation RNG or gameplay decisions. |

## Observable-event limits

The controller observes supported squad commands, selection-set changes, HP changes and selected activity edges. Work and combat activity are inferred; they are not native dialogue-tree context parity. Generic default orders are acknowledged, without guessing whether an unexposed target means repair, trade, healing or conversion. Ability replies are generic. Heal/convert success/failure, relic pickup/drop-off, production completion, diplomacy and other dossier-only contexts are not implemented by this adapter. Repeated or queued orders and transitions during a busy response require native timing checks.

Final integration must trace private naval/monk identity references through production, relevant upgrades, AI aliases and prematch precache. Do not globally mute shared stock owners, replace the raw 0.8.3 owning archive with a source-only cook, or count an unchanged-source reference compile as a complete voice release.

Read-only preservation review scanned all 395 baseline RGDs: 94 typed incoming rewires across ten resources; excluded buffalo and elephant paths reach none of the 115 directly suppressed baseline human resources. Remaining unresolved animal leaves are unchanged official attachments. This is graph evidence, not an audible animal test. `integration/overlay-preservation-review-v1.json` also records inactive human exceptions: the unused cheap culverin has two loadout rewires, and unused archers II–IV plus cheap tower handcannons share muted human EBPS. They have no current incoming production/start route. Current playable coverage does not promise unchanged speech for these unused cheat-spawned consumers.

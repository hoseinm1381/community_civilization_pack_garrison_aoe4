# Casting and delivery — preparation draft

**Northern Đại Việt / Red River cultural center; proposed casting, no actors booked and no audio generated.** `VOICE_SCRIPTS.json` contains the authoritative profile IDs and exact directions. Sources establish background, not how every historical person sounded.

## Proposed voice identities

| Profile | Actor ID | Roles sharing this identity | Vocal character |
|---|---|---|---|
| CIV_M | VM01 | Male villager, bamboo-worker and eligible civilian variants | Warm adult middle baritone; capable, practical |
| CIV_F | VF01 | Female variants of the same civilian occupations | Grounded adult lower mezzo; equal authority and task coverage |
| SCOUT | VM02 | Verified male mounted scout | Alert light tenor, good quiet breath control |
| INFANTRY | VM03 | Spearmen, fire-lance and men-at-arms variants | Firm middle baritone; change equipment-specific words, not identity |
| ARCHER | VM04 | Vietnamese bow-armed foot units | Focused upper baritone, precise short calls |
| CROSSBOW | VM05 | Crossbow tiers | Patient compact middle register |
| GUNNER | VM06 | Handgunner and discounted variants | Centered baritone, deliberate readiness |
| CAVALRY | VM07 | Horseman and knight tiers | Open middle register, mobile controlled projection |
| MONK | VM08 | Human religious actors | Gentle mature low tenor; conversational, never a fake ritual accent |
| OFFICIAL | VM09 | Official and eligible inherited tax collectors | Measured diction; literate without comic pomp |
| TRADER | VM10 | Land trader variants | Conversational middle tenor, reliable and observant |
| ELEPHANT | VM11 | Human handler/crew caller on elephant variants | Low middle voice, patient rhythmic coordination |
| SIEGE | VM12 | Confirmed human siege crew caller | Broad middle baritone, coordinated labor |
| NAVAL_FISH | VM13 | Fishing-vessel caller | Economical weathered tenor, no pirate voice |
| NAVAL_TRADE | VM14 | Naval trader caller | Even middle register, clear cargo/navigation language |
| NAVAL_MILITARY | VM15 | Combat ship, war galley, combat warship | Projected baritone, clear coordinated calls |
| NAVAL_TRANSPORT | VM16 | Transport-vessel caller | Steady low tenor, clear boarding instructions |
| NAVAL_FIRE | VM17 | Demolition-vessel caller | Tense focused middle voice, restrained warnings |

These are **18 proposed distinct identities**, not 18 confirmed historical social dialects. Male defaults for many donor-male military roles are production choices. A different approved gender need not change the language or competence of a role. An installed female Scout speech profile is inventory evidence; its presence does not prove that the Vietnamese Scout selects it. If the effective gender branch is unresolved, keep it unresolved rather than silently adding an obtainable unit. Do not reuse a female civilian performance as a female scout by merely renaming files.

**ELEPHANT is blocked from recording and integration until a human speech owner is verified.** The current `warelephant` code is not sufficient evidence of a human handler channel. VM11 is a creative casting proposal only; every associated JSON row carries that hard recording gate. Preserve animal calls.

## Stable identity and variation

Keep one actor/voice identity across that profile's ages. Age banks represent language chronology, not a child becoming an elderly adult. Avoid changing pitch, accent or persona randomly between ages. Related variants explicitly share the profile above. Actor consolidation across profiles is not assumed: one performer may later portray several distinct identities, but that casting decision needs separate auditions and accounting.

Each applicable **profile × semantic pool × age** has six distinct phrases. Each phrase has three fresh performances with identical text. The bank supplies specific T1/T2/T3 directions. For ordinary acknowledgements these vary readiness and rhythm; attacks vary supported urgency; concealed lines remain quiet and intelligible. All three must retain the same lexical tone categories. Do not count a duplicate waveform, time stretch, pitch shift, EQ change or filename alias as a fresh take.

Short task vocabulary is intentionally reused across ages and sometimes roles. Identical text is **not** additional unique wording. The JSON's SHA-256 reuse groups make this visible. Different actors reading the same sentence are separate performances. Nonverbal directions are also shared deliberately. No audio files exist yet, so no waveform uniqueness or actor consistency has been tested.

`select` and `role_select` are alternative six-phrase pools for **one selection event**. Likewise generic `attack`/`move` and weapon/family-specific pools are alternatives, not successive lines. The final route chooses one pool per event/consumer. Do not play every mapped bank when the same command fires. `attack_move` deliberately can use attack wording; its native command semantics remain distinct.

## AoE4-style direction

Target roughly 0.6–2.2 seconds for ordinary responses and usually under 3 seconds for urgent calls. These are **editorial timing targets**, not documented engine limits. Let native timing and semantic clarity win; duration cannot be measured until recording. Avoid announcer projection, long exposition, booming fantasy growls or modern military-radio speech.

Keep spontaneous human texture, clear intended action and recognizable role timbre. Fear is not comedy; pain/death are nonverbal human efforts. Animal and machinery sound design remains separate. A ship's speaker may be an abstract crew caller; that does not prove an individually simulated crew actor exists.

The raw stock labels `iNorm`, `iHigh`, `iStealth` are preserved in the native crosswalk. **Three takes are not these three labels.** Their scheduling and meaning have not been established for the current Vietnamese consumers. A later route may require additional delivery sessions. Do not treat T1/T2/T3 as a ready-made native delivery mapping.

## Pronunciation and review

Use a native Northern Vietnamese performer and native-language director for readable drafts. A historical-linguistics reviewer must approve any period target separately. The developer interview's cultural consultation and native casting provide the model for that approach. [G01](https://news.xbox.com/en-us/2021/04/10/age-of-empires-4-interview/)

For every revision, record the stable line ID, old/new Vietnamese, English meaning, lexical rationale, source locator and pronunciation approval. Preserve source forms in the research lexicon. No universal phoneme conversion or full-sentence historical IPA has been invented. Modern orthographic tone breakdowns in JSON are rehearsal aids only.

Review occupational expressions as well as grammar: bow versus crossbow, mining versus panning, ship versus land movement, gun versus mechanical artillery, relic custody versus conversion, and combat versus building/repair. Do not infer commands from an inferred animation or call a fictional command a documented historical phrase.

## Suggested audition sequence for a future recording phase

No auditions are produced now. A later session should compare the same actor's selection, movement, work/attack, concealed delivery where supported, and nonverbal efforts. Review A1 and A4 together for stable identity with distinct approved language targets. Then review a civilian pair, ranged pair, official/monk pair and naval roles at game listening distance. Written approval is not audible acceptance.

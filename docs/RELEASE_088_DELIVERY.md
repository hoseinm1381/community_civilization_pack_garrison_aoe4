# Garrison 0.8.8 — Castle landmark crash and Phổ Minh drop-off

Delivery: `output/release_085/final-v2/community_civilization_pack-0.8.8.zip`.
The existing delivery folder is reused. 087 was replaced only after complete
candidate verification; independent 084 rollback, prior metadata and compact
replaced-member rollback ZIPs remain. No duplicate art/audio bank was created.

- ZIP: **284,935,545 bytes**, below 400,000,000 bytes.
- ZIP SHA-256: `ca7ff19b1da774666f6f8e1dc3d6d9a4357dc8aa97dc99578dc5f776f9d63e2a`.
- SGA SHA-256: `a341dfb4ceec21c42f795502de5e3017a490ac83c66a7056eb8aa33d81c6b09a`.
- Exactly two changed members among 11,973; no added/deleted members or changed
  mounts. All other 11,971 member bytes, including art, dialogue, voice cooldowns
  and Skirmisher selection grouping, match 087.

## Reported failure and scoped changes

The supplied screenshot and warnings log report `Entity BP did not have
moving_ext!` at flooded_citadel.scar:46 (eligible), called from Update:131 and
lifecycle.scar:59 when the Castle landmark becomes active. The accessor is
BP_GetEntityBPDefaultSpeed, not an arbitrary entity speed getter. Its current
installed ScarDoc explicitly requires moving_ext. A player-wide entity observer
also contains nonmoving visual/emplacement actors; ordinary unit tags do not
prove mobility (current stock visual actors can carry worker/cavalry tags).

The script now admits the native speed accessor only for names whose effective
current private/official parent chains and variants contain moving_ext. Unknown
and nonmoving records are cached as ineligible, without attempting the asserting
call. An inline generated set contains 1,938 names, including GUID-qualified
private/voice-derived units. No new engine API, error-catching bypass, motion test,
local-player branch or simulation RNG is introduced. Unmodified positive base
speed, 0.7 multiplier, footprint/range, overlap, removal and lifecycle code remain
identical. New units/game updates require regenerating this set from fresh data.

The generator normalizes comma-space removedIds in a working copy of current
ReferenceAttributes records. The historical identity auditor splits IDs without
trimming whitespace; leaving that unchecked falsely admitted four stock visual/
placeholder records whose movement extension was removed. Frozen historical
source/evidence stays unchanged. Current compiled default EBPS cross-check has
zero admitted records without moving_ext after normalization.

Phổ Minh's 087 resource flags already match the Hideout, including accepting food,
wood, gold and stone. Both also lacked an explicit resource_drop_off interaction.
Current Town Center/lumber-camp donors supply that interaction. Add exactly its
native group to Phổ Minh's existing interactive_object_ext/type_list in default
and campaign, preserving repair/construct/shelter, art, footprint and every other
value. No singleton extension is added. Only two fresh local group IDs are used;
PBG identities and archive namespace/bundle/GUID are preserved.

## Verification gates

- Real Lua fixtures: three original fatal-probe failures reproduced, then fixed;
  a further removed-inherited-extension failure reproduced, then fixed. Twelve
  source/Lua regressions pass, including positive stock/private/voice-derived
  coverage, unmodified-speed cache, zero-speed/exclusions and structural undo of
  both edited source files against 088-before-source.zip.
- Existing chatter/storage suite: 45 passed. SCAR validator: zero errors, one
  existing loader/PLAYERS import warning. MCP: no low-confidence APIs or missing
  localization; the sole unknown token is Lua `and`.
- Fresh official/private extension identity check: 198 local / 5,758 official,
  zero errors. Tuning validator: 377 instances, zero errors, 131 existing corpus
  version warnings. .NET XML parse is a separate source gate.
- Actual completed Content Editor tuning reference compilation: 377 instances,
  archive copied and identity checked. Final tower node matches the freshly
  compiled donor interaction; serialized typed undo reconstructs every original
  byte. Final SCAR received the normalized admission set after staging; that
  source-only delta is recorded separately, with no native SCAR execution claim.
- Full fresh NTFS extraction, all member hashes/mounts, namespace before/after
  assembly, ZIP CRC/exact entries/embedded SGA hash and 400 MB cap passed.

Native game acceptance remains unrun: fresh-match Castle completion/active field,
nearby foreign units and visual actors, 30% slow/removal/overlap; Phổ Minh manual
and automatic food/wood/gold/stone returns, pathing, repaired landmark state;
save/load and multiplayer. No installation, publication, synthesis or download.

## Rebuild and contributor handoff

Tools live under tools/release_088. generate_mobility.py needs the current 088
reference cache (refresh with check_extension_inheritance.py), local EBPS sources
and retained voice identity metadata. Unknown newly added blueprints fail closed
until regeneration. No voice masters, AI models or credentials are needed.
compile.py is the isolated actual tuning build. package.py is the guarded one-time
two-member overlay. Historical scripts/receipts are not overwritten to accept it.

Keep output/release_085/088-* source/native receipts and rollback inputs. The
local contributor/GitHub checkout update is explicitly authorized by the owner.
Its supported compact route must reuse existing immutable packs and 087 metadata,
add only the changed source/resources and sparse 088 verification, and reproduce
the exact current ZIP without accessing this owner workspace. No full ZIP/SGA or
unchanged sound/art is added there. Report local push readiness; do not push.

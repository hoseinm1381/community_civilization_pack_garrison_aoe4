> Superseded by 0.8.7 in the same final-v2 folder. This is historical 086 evidence;
> use RELEASE_087_DELIVERY.md for current delivery and compact 086 reconstruction.

# Garrison 0.8.6 — independent unit voice cooldowns

Current delivery: `output/release_085/final-v2/community_civilization_pack-0.8.6.zip`.
The 085 directory is deliberately reused at the owner's request. No permanent
086 output/authoring directory or duplicate audio bank was created. The superseded
085 ZIP and raw SGA were replaced only after complete candidate verification.
Independent 084 rollback and compact compressed 085 metadata/source remain.

- ZIP: **284,922,930 bytes**, below 400,000,000 bytes.
- ZIP SHA-256: `e1fec0c54d639f1f8c258896fd0eb4a831b7c8a72306eddafd38c8fc7e98030e`.
- SGA SHA-256: `8c7f52762713133da67ed4e8dece0219b5c963b797714914dad03a34231120d8`.
- All 11,973 archive members and mounts freshly verified;
  exactly one changed member: `scar/vietnam/voices_084.scar`. No added/deleted members.

## Minimal behavior change

Each individual unit now owns its own 5-second selection/order/activity timer,
8-second movement/default-acknowledgement timer, and 15-second under-attack timer.
A scout's cooldown cannot silence a villager or another scout. The current spoken
clip still finishes before another unit replies, preserving the existing short
global playback arbitration. No queuing, interruption or broader improvisation
was added. Existing command/activity duplicate suppression remains unchanged.
All pain/death sounds, effort scheduling, spoken media, gameplay and art are exact.

Source: `tools/release_085/voices_086.scar`. Original 085 dispatcher remains at
`tools/release_085/voices.scar`. The functional change moves three cooldown fields
from global state S to the actor record r; actor lifetime/retracking remains intact.

## Verification

20 dispatcher tests passed, including five observed failures against 085 before
the fix. Full 085/086 helper/dispatcher suite: 44 passed; inherited 084 suite:
112 passed, for 156 offline tests. Current-package recovery guard also passed an
observed failing-then-passing 086 filename regression. SCAR validation has zero
errors and eight existing integration/lifecycle warnings. MCP reported no
low-confidence APIs or missing localization; reported unknown names are existing
local helpers, Lua tokens and Garrison methods. No new game-engine call was added.

Fresh extraction used an owned temporary NTFS directory and was removed afterward,
avoiding the earlier exFAT readback footprint. Namespace/GUID/bundle, every member
hash and mount, ZIP CRC/exact members, manifest version and embedded SGA hash
passed. Post-replacement integrity is `output/release_085/086-final-integrity.json`.
The one-time owner upgrade is `tools/release_085/upgrade_086.py`; it refuses to
rerun after replacement. For future reconstruction, overlay `voices_086.scar` at
its stable mounted path using the retained 084 owning archive and supported
`set-members --alias data` route, then compare the current verification map and
manifest. Do not use historical `build.py` to rebuild current 086: it emits 085.

No new native compilation or 086 native game acceptance is claimed. The owner
confirmed that 085's cooldowns worked in gameplay, but wanted independent timers.
086 import, audible feel, save/load and multiplayer remain separate checks.
No synthesis, download, billing, installation or publication was performed.
The GitHub update was canceled/held by the owner; no new GitHub-folder changes
were made. Cold recovery bundles and the compact workspace remain intact.

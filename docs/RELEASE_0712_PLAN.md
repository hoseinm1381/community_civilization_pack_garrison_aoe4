# Garrison 0.7.12

User scope, 2026-10-24: skirmisher wind-up +0.25 seconds with the same amount
removed from reload; clickable buffalo count cycling; substantially larger
work marker. Later steering adds influence display +2 metres, explicitly
authorizes actual influence +2 metres if the display cannot be separated,
and requires ground-click tunnel destinations within 8 metres of a building.
The user clarified that direct building clicks work but nearby ground clicks fail.

## Decisions

- Three existing private skirmisher weapons: wind-up0.25 ->0.50 and both reload
  duration bounds1.375 ->1.125. Other timing/damage/range values stay intact.
- Resolve the local player by stable native player ID. Explicitly publish click
  availability from presentation state; clicking selects and focuses the next
  living owned buffalo in stable ID order. No orders are issued.
- Increase the existing steady marker from14px to48px (40px image), opacity
  from0.65 to0.95. Preserve owner/replay/work-end cleanup and camera visibility.
- Increase every positive effective private Vietnamese district-generator range
  by2m:36 blueprints/74 variant scopes. Existing inherited extensions are overridden
  using their exact native IDs. Increase scripted tunnel graph reach by2m too.
- Keep the native position-target ability, cooldown and transit mechanics.
  Measure the destination allowance from the footprint edge. Choose the nearest
  eligible completed owned connected building within8m; an invalid closer
  foundation or unrelated unknown building must not steal a valid destination.

## Evidence and preservation

Freeze exact delivered0.7.11 and source/normal hashes. Use release_0712 tools,
staging and receipts. Current official inheritance and weapon schema are checked
before edits; native scalar readback must confirm every authorized value.
Final compiled attribute integration clones accepted actor documents and copies
only native-verified float changes, preserving compiled-only overlays and metadata.

No model edits, installation, publication or cleanup. Preserve normal edition,
GUID/bundle/archive identity, prior editable assets and rollback evidence.
Static/source, native source compile, final archive/ZIP, fresh-match UI and
transport behavior, save/load and multiplayer remain separate acceptance gates.

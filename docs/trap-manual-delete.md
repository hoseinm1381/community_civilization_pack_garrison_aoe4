# Trap manual delete — 2026-10-16

The user reports that the restored native trap/tunnel changes work in game. This follow-up adds only the native player Delete/Scuttle option to both trap blueprints, in their root and campaign variants.

Restored `abilities\timed_abilities\civ_core\core_building_scuttle` from the corresponding original `Real_Vietnam_1` ability-list entries, preserving their original per-list IDs. No new identity or script was added. Weapon behavior, tunneling, four-second automatic destruction, construction times, and dynasty changes are unchanged.

Verification parsed all four ability lists and confirmed that removing the new entries yields exactly the pre-edit XML semantics. Tuning validation passed with zero errors/warnings. Rollback/hash evidence is in `trap-manual-delete-audit.json`.

Rebuild/package in Content Editor and check the native Delete/Scuttle command on each trap. This follow-up has not been built or run in game by Codex.

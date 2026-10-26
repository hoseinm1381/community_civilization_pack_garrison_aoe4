# Community Civilization Pack — Garrison

**[Download Garrison 0.8.8 — installable ZIP (284.94 MB)](https://github.com/hoseinm1381/community_civilization_pack_garrison_aoe4/releases/download/v0.8.8/community_civilization_pack-0.8.8.zip)**

Self-contained current development handoff for **0.8.8**. Includes editable art, gameplay source, native recipes, exact shipped Ogg voices and rebuild inputs. The compact data store is approximately **5.96 GB**; Git also stores committed data locally. No LFS, separate asset download, API key or AI model is needed to use the existing assets or reproduce the package.

```powershell
python -B -m unittest discover -s tools/compact -p "test_*.py"
python -B tools/compact/portable.py verify
python -B tools/compact/portable.py verify-audio
python -B tools/compact/portable.py release --archive-tool "C:/path/to/sga-archiver.exe" --destination .local/delivery-088
```

Start with [the contributor guide](docs/COMPACT_DEVELOPMENT.md). It covers restoring/editing sources, configuring locally installed tools, fixing Blender paths, native source builds, selective integration, optional new local voices, and milestone updates. Verification and restoration use Python 3.12+. Exact package reconstruction also uses the installed Garrison archive tool.

The delivered ZIP is **284,935,545 bytes**. Its existing **10,529 Ogg clips total 118,761,135 bytes**, including 9,702 spoken takes. WAV production originals, rejected takes, old deliveries and generated readbacks are omitted from the upload. Omitted material is not required by this checkout. Shipped sound bytes are unchanged.

Install compatible Blender/Garrison and an owned AoE4 Content Editor for their respective authoring/build tasks. Optional new local voice production uses the documented pinned environment; ordinary mod development does not require it.

See [publishing verification](docs/compact/READINESS.md), [delivery evidence](docs/RELEASE_088_DELIVERY.md), [discoveries](docs/DISCOVERIES.md), and [rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md). Package reproduction, native compilation, art cooking and in-game acceptance are reported separately.

0.8.8 fixes the Flooded Citadel movement-extension crash and adds Phổ Minh’s explicit resource-return interaction. Existing per-unit voice cooldowns, Skirmisher selection groups, sound and art are preserved. It reuses all 172 prior packs and adds a 158,426-byte input pack plus a small index.

Credits: **hosein81 and chilly5**.

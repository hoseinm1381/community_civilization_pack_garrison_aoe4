# Community Civilization Pack — Garrison

Self-contained current development handoff for **0.8.7**. Includes editable art, gameplay source, native recipes, exact shipped Ogg voices and rebuild inputs. The compact data store is approximately **5.96 GB**; Git also stores committed data locally. No LFS, separate asset download, API key or AI model is needed to use the existing assets or reproduce the package.

```powershell
python -B -m unittest discover -s tools/compact -p "test_*.py"
python -B tools/compact/portable.py verify
python -B tools/compact/portable.py verify-audio
python -B tools/compact/portable.py release --archive-tool "C:/path/to/sga-archiver.exe" --destination .local/delivery-087
```

Start with [the contributor guide](docs/COMPACT_DEVELOPMENT.md). It covers restoring/editing sources, configuring locally installed tools, fixing Blender paths, native source builds, selective integration, optional new local voices, and milestone updates. Verification and restoration use Python 3.12+. Exact package reconstruction also uses the installed Garrison archive tool.

The delivered ZIP is **284,924,620 bytes**. Its existing **10,529 Ogg clips total 118,761,135 bytes**, including 9,702 spoken takes. WAV production originals, rejected takes, old deliveries and generated readbacks are omitted from the upload. Omitted material is not required by this checkout. Shipped sound bytes are unchanged.

Install compatible Blender/Garrison and an owned AoE4 Content Editor for their respective authoring/build tasks. Optional new local voice production uses the documented pinned environment; ordinary mod development does not require it.

See [publishing verification](docs/compact/READINESS.md), [delivery evidence](docs/RELEASE_087_DELIVERY.md), [discoveries](docs/DISCOVERIES.md), and [rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md). Package reproduction, native compilation, art cooking and in-game acceptance are reported separately.

0.8.7 adds independent per-unit 5s/8s/15s reply cooldowns, resource drop-off at Phổ Minh Tower, and separate Skirmisher selection groups. All sound and art bytes are unchanged. The update reuses all 171 original packs and adds about 1.2 MB of packed changes.

Credits: **hosein81 and chilly5**.

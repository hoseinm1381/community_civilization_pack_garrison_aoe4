# Community Civilization Pack — Garrison

Self-contained current development handoff for **0.8.4**. Includes editable art, gameplay source, native recipes, exact shipped Ogg voices and rebuild inputs. The compact data store is approximately **5.96 GB**; Git also stores committed data locally. No LFS, separate asset download, API key or AI model is needed to use the existing assets or reproduce the package.

```powershell
python -B -m unittest discover -s tools/compact -p "test_*.py"
python -B tools/compact/portable.py verify
python -B tools/compact/portable.py verify-audio
python -B tools/compact/portable.py release --destination .local/delivery
```

Start with [the contributor guide](docs/COMPACT_DEVELOPMENT.md). It covers restoring/editing sources, configuring locally installed tools, fixing Blender paths, native source builds, selective integration, optional new local voices, and milestone updates. Python 3.12+ is enough for the offline commands above.

The delivered ZIP is **284,922,388 bytes**. Its existing **10,529 Ogg clips total 118,761,135 bytes**, including 9,702 spoken takes. WAV production originals, rejected takes, old deliveries and generated readbacks are omitted from the upload. The owner preserves them separately. Shipped sound bytes are unchanged.

Install compatible Blender/Garrison and an owned AoE4 Content Editor for their respective authoring/build tasks. Optional new local voice production uses the documented pinned environment; ordinary mod development does not require it.

See [publishing verification](docs/compact/READINESS.md), [delivery evidence](docs/RELEASE_084_DELIVERY.md), [discoveries](docs/DISCOVERIES.md), and [rights and attribution](docs/RIGHTS_AND_ATTRIBUTION.md). Package reproduction, native compilation, art cooking and in-game acceptance are reported separately.

Credits: **hosein81 and chilly5**.

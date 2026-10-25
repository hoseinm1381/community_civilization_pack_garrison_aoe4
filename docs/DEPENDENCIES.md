# Dependencies and local setup

No installed tool, model weight, CUDA environment or API credential is required to
read the source, verify the shared store, export the delivered ZIP or reassemble it
with a supported archive tool. No dependency is downloaded automatically.

| Purpose | Required locally | Preserved recipe/evidence |
| --- | --- | --- |
| Restore/verify shared inputs | Python 3.12+ | `tools/collaboration`, standard library only |
| Edit art | Blender; qualified owner used 5.2 | editable `.blend`, exports, recipes |
| Garrison cook/package/archive | compatible installed Garrison extension/core/archive CLI | workflow guides and release logs |
| Native compile | owned AoE4 and its Content Editor | isolated project sources, native logs and receipts |
| Predictive buffalo encoder | appropriate Python plus pinned scientific/Havok dependencies | `external/resources_082_animation/requirements.lock.txt`, wheels, manifest; `tools/release_082_animation` |
| New local speech production (optional) | Python 3.11, CUDA-capable runtime, pinned TTS/codec/ASR models | `tools/release_084/install_local.ps1`, download recipes, SDK revision, lockfiles and publisher receipts |

The author's environment used Torch `2.8.0+cu128`, torchaudio `2.8.0+cu128`,
Transformers `4.57.6`, VieNeu `3.8.3`. Completed speech is included; installing this
environment or regenerating all speech is unnecessary for ordinary development.
The PhoWhisper-large download was stopped and is not a ready dependency. Do not
resume it automatically. Keep third-party software/model terms and hardware needs
separate from the mod's own source license.

Historical helpers can contain `C:/Users/RS`, E: and F: paths and imports from a
personal skills directory. Configure a restored copy, use bundled workflow/validator
sources and adapt the specific command deliberately. Preserve frozen receipts.
Full historical preservation tests may require separately owned normal-edition/donor
trees; this Garrison repository does not distribute unrelated projects. Those tests
are not the portable contributor smoke suite.

`docs/ai/workflows` includes the authoring/validation guide sources used for this
handoff and a hash provenance file. Installed official game schema/data and the
installed Garrison guide remain authoritative for version-sensitive operations.

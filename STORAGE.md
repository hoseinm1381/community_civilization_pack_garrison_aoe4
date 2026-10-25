# Compact storage ownership

`development-data/current-084-v1` is a self-contained immutable input store, approximately 5.96 GB. It preserves editable masters and required rebuild resources. Store packs are not caches. Do not edit or delete them directly. Restore working inputs using tools/compact/portable.py.

This checkout owns no links to the original authoring workspace. Configuration creates links only inside an explicitly restored workspace. `.local` holds regenerable verification outputs and is not tracked. The old historical repository copy was deleted on 2026-10-25 at the owner's explicit request after verifying all 171 retained input packs and independent active-workspace links. This checkout does not depend on that archive. Omitted WAV originals, old deliveries and diagnostics are not part of the compact checkout.

Git stores committed input data in its own database in addition to the working tree. Report upload content, Git size and restored working size separately. Future milestone binaries grow history.

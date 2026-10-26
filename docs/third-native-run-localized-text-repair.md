# Third user-operated run: localized text contract repair

2026-10-14. The user's screenshots show the native China/Vietnam popup and working localized labels. warnings.log at 20:20:45 reports:

```text
data+17:scar\winconditions\VietnamMode.scar:161: attempt to concatenate a utf8_mt value
```

The failing statement composes the countdown using `text(1003) .. ...`, where `text` returns `Loc_GetString`. AoE4 supplies a localized engine value (`utf8_mt`), which cannot participate in Lua string concatenation. An equivalent source mistake also exists in the no-eligible-player diagnostic composition.

## Source repair

- Add `messageText(id)` to convert the localized value through `Loc_ToAnsi` before composing a Lua string. This first-release probe declares English only.
- Use it for countdown, missing-blueprint, and no-eligible-player system messages. Store and hide the same plain composed message, preserving module-owned cleanup.
- Keep native localized values for the popup title, body, and button labels; those displayed successfully.
- Shorten English ID 1007 to `30 seconds to choose. Default: China.` because the user's native popup clips the previous long instructions. Synchronize the foundation generator.
- Tighten the mock source: localized values now have a concatenation-rejecting metatable, explicit conversion returns plain text, and system-message calls require plain strings. Add fallback-message regression cases. Do not execute them under the user's testing boundary.

Official evidence: current installed `cardinal.scar:447` composes a Lua string using `Loc_ToAnsi(objective.Title)`; extracted read-only under `.tools/official`. ScarDoc documents localized return from `Loc_GetString` and string system-message parameters. A focused read-only reviewer found no remaining localized-object concatenation in the patched module and no confirmed integration defect.

No build or test was performed by Codex. Native countdown, choice delivery, conversion, unlock, timeout, and multiplayer coexistence remain pending. The displayed popup establishes that a custom XAML replacement is not required simply to present the current choice.

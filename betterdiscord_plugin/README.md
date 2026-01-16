## VocabReplacer (BetterDiscord plugin)

Purpose
- Replace message text in Discord using a JSON rule list.
- Applies to message content and embed descriptions.

Install
1) Copy `betterdiscord_plugin/VocabReplacer.plugin.js` into your BetterDiscord plugins folder.
2) Reload Discord or toggle the plugin on.
3) If prompted, allow the BDFDB library plugin download.

Rules JSON schema
- Paste either:
  - A JSON array of rule objects, or
  - A full dataset JSON exported from the GUI (uses its `rules` array).
- Each rule is an object with:
  - `source_phrase` (string): phrase to match (words only, spaces allowed).
  - `replacement` (string): replacement text.
  - `priority` (number, optional): higher wins on conflicts; default 0.
  - `case_policy` (string, optional): `match`, `as-is`, `lower`, `upper`, `title`.
  - `enabled` (boolean, optional): default true.

Example rules
```json
[
  {"source_phrase":"twilight","replacement":"gloaming","priority":10},
  {"source_phrase":"stunned into silence","replacement":"overawed","case_policy":"match"}
]
```

Notes
- Only whitespace is allowed between words inside a phrase; punctuation breaks a match.
- Matching is case-insensitive by default; `case_policy` controls output casing.
- Share code supports Short (CJK) and Safe (URL) modes; import accepts either.

Development
- Source modules live in `betterdiscord_plugin/src/`.
- Build the single-file plugin:
  - `node betterdiscord_plugin/build_plugin.js`
- Watch and rebuild on save:
  - `node betterdiscord_plugin/watch_plugin.js`
- Sync to your BetterDiscord plugins folder:
  - `node betterdiscord_plugin/sync_plugin.js`
  - Override location with `BD_PLUGINS_DIR`.

End-to-end example
1) Install the plugin by copying `betterdiscord_plugin/VocabReplacer.plugin.js` into your BetterDiscord plugins folder.
2) Enable the plugin in BetterDiscord.
3) Open the plugin settings and paste this JSON into the rules box:
```json
[
  {"source_phrase":"twilight","replacement":"gloaming","priority":10},
  {"source_phrase":"stunned into silence","replacement":"overawed","case_policy":"match"}
]
```
4) Click Save. The plugin parses the JSON and stores it via `BDFDB.DataUtils.save`.
5) Send or view a message containing those phrases:
   - Input: `At twilight, she was stunned into silence.`
   - Output: `At gloaming, she was overawed.`

What the code does
- Settings panel stores JSON rules and rebuilds the trie (see `getSettingsPanel` in `betterdiscord_plugin/VocabReplacer.plugin.js`).
- Message replacement runs in `processMessages` and `parseMessage`, applying `replaceText` to message content and embeds.
- The trie matcher uses word tokenization and only allows whitespace between words in a phrase.

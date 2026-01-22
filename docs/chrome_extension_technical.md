# LexiShift Chrome Extension: Technical Notes

Overview
- The extension runs a content script on all frames and replaces visible text using a ruleset.
- The codebase is modularized into small, focused modules loaded in a strict order by the manifest.
- Settings are stored in `chrome.storage.local` and shared between the content script and options page.

Module layout
- `apps/chrome-extension/shared/settings_defaults.js`
  - Central default settings used by both the options UI and content script.
  - Avoids drift when new settings are added.
- `apps/chrome-extension/content/tokenizer.js`
  - Tokenization utilities (word/space/punct) and normalization helpers.
  - Exposes `tokenize`, `normalize`, `textHasToken`, `computeGapOk`.
- `apps/chrome-extension/content/matcher.js`
  - Builds a phrase trie from rules and resolves longest-match tokens.
  - Applies case policy (`match`, `as-is`, `lower`, `upper`, `title`).
  - Normalizes rule objects to a consistent shape.
- `apps/chrome-extension/content/replacements.js`
  - Builds a `DocumentFragment` with replacement spans for a text node.
  - Filters matches based on settings (max-one-per-block, allow-adjacent).
  - Keeps optional replacement detail logs for debug mode.
- `apps/chrome-extension/content/ui.js`
  - Handles highlight styles, click-to-toggle behavior, and cleanup.
  - Separates DOM mutation concerns from parsing and matching.
- `apps/chrome-extension/content/utils.js`
  - Logging helpers: element descriptors, codepoint snippets, node traversal.
- `apps/chrome-extension/content_script.js`
  - Orchestrator: loads settings, builds trie, scans DOM, observes changes.
  - Provides debug logging and focus word diagnostics.

Manifest ordering
- `apps/chrome-extension/manifest.json` loads modules before `content_script.js`.
- Load order is required to populate `globalThis.LexiShift` with module APIs.
- The options page also loads `shared/settings_defaults.js` before `options.js`.

Settings flow
- Defaults come from `globalThis.LexiShift.defaults` in `shared/settings_defaults.js`.
- Options page writes values to `chrome.storage.local`.
- Content script reads settings on boot and reacts to `chrome.storage.onChanged`.
- Highlight/visual settings apply immediately; rules changes trigger a rescan.

Replacement pipeline (content script)
1. Load and normalize settings from storage.
2. Normalize rules and build a trie of word tokens.
3. Collect all text nodes using a TreeWalker.
4. For each node:
   - Skip if empty, whitespace-only, in editable fields, excluded tags, or already replaced.
   - Tokenize and find longest matches via the trie.
   - Optionally filter matches:
     - `maxOnePerTextBlock`: keep only the first match in the text node.
     - `allowAdjacentReplacements=false`: skip back-to-back word matches.
   - Replace the node with a fragment containing spans and text nodes.
5. Track processed nodes in a `WeakMap` to avoid repeated replacements.

Observer strategy
- A MutationObserver watches for added/edited nodes and rescans only the new content.
- `ensureObserver` rebinds if the document body changes.
- A lightweight rescan runs on window load and after a post-load timeout.

Debug tooling
- `debugEnabled` controls console logs across all modules.
- `debugFocusWord` highlights whether the word appears as:
  - substring in a node,
  - exact word token,
  - replaced or skipped.
- Detail logs are capped to avoid flooding the console.

Settings added for replacement behavior
- `maxOnePerTextBlock` (default: false)
  - Limits each text node to a single replacement.
- `allowAdjacentReplacements` (default: true)
  - When disabled, prevents replacements that occur on immediately adjacent words.

Known issue (not fixed yet)
- The act of replacing text nodes splits the original text into multiple nodes.
- This means `maxOnePerTextBlock` can no longer refer to the original text block,
  because the subsequent scan sees newly created nodes and treats them as separate.
- This is a behavior-level bug; do not fix yet.

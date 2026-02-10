# LexiShift App Size Reduction Notes

## Scope
This document captures practical ways to reduce installed app size for the macOS desktop build.

## Current observations (local build/install)
- Installed size is dominated by two apps:
  - `/Applications/LexiShift.app`
  - `/Applications/LexiShift Helper.app`
- Main + helper together are roughly the same order as the reported `~1.24 GB`.
- The packaging flow currently includes both app bundles in the DMG.

## Main size drivers
1. Two bundled apps (main + helper), each carrying Python/PySide6/Qt runtime payload.
2. Symlink flattening during DMG staging:
   - `scripts/build/installer.py` uses `shutil.copytree(...)` for `.app` bundles.
   - If symlinks are not preserved, shared files become duplicated real files.
3. Heavy runtime dependencies:
   - PySide6/Qt frameworks.
   - Python runtime + dynamic modules.
4. Large lexical assets:
   - `simplemma` dictionary data (many language files).

## High-impact, low-effort changes
1. Preserve symlinks when staging app bundles for DMG.
   - Update `scripts/build/installer.py` copy logic to keep symlinks in `.app` contents.
   - Expected impact: significant reduction in installed footprint when duplicated framework/resource files are currently materialized.
2. Re-evaluate whether both apps must be independently installed.
   - If helper can be embedded/optional, users may avoid installing a second full runtime.
3. Prune unneeded bundled assets.
   - Keep only required dictionaries/languages and nonessential resources.

## Medium-effort changes
1. Split helper into a lightweight tray process without full PySide6 runtime.
   - Current helper app likely inherits most framework cost from GUI stack.
2. Reduce PyInstaller payload via explicit module/data exclusions.
   - Remove unused Qt modules/plugins/translations and unused Python modules.
3. Minimize duplicate resource placement in spec/runtime layout.
   - Ensure the same payload is not copied into multiple bundle locations unnecessarily.

## Higher-effort structural changes
1. Move from dual-bundle runtime model to a single bundle with internal helper launch path.
2. Revisit packaging stack (if needed) for better shared-library deduplication characteristics.

## Measurement checklist (use after each change)
1. Compare installed app totals:
   - `du -sh /Applications/LexiShift.app /Applications/'LexiShift Helper.app'`
2. Inspect bundle sections:
   - `du -sh /Applications/LexiShift.app/Contents/* | sort -h`
   - `du -sh /Applications/'LexiShift Helper.app'/Contents/* | sort -h`
3. Identify largest files:
   - `find /Applications/LexiShift.app -type f -exec stat -f '%z %N' {} + | sort -nr | head -n 40`
4. Check symlink preservation:
   - `find /Applications/LexiShift.app -type l | wc -l`
   - `find /Applications/'LexiShift Helper.app' -type l | wc -l`
5. Compare with pre-install dist artifacts:
   - `find apps/gui/dist/LexiShift.app -type l | wc -l`
   - `find apps/gui/dist/'LexiShift Helper.app' -type l | wc -l`

## Recommended execution order
1. Fix symlink preservation in DMG staging.
2. Rebuild + reinstall + remeasure.
3. If still too large, prioritize helper-runtime split and asset pruning.

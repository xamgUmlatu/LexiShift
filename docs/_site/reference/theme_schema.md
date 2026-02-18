# LexiShift Theme Schema (Draft)

This schema describes user-provided themes for the GUI. It is not wired yet, but it is the target format for future customization.

## Theme object (draft)
```json
{
  "id": "night_slate_custom",
  "name": "Night Slate Custom",
  "version": 1,
  "colors": {
    "bg": "#151A1F",
    "panel_top": "#1E242B",
    "panel_bottom": "#12171C",
    "panel_border": "#2B333C",
    "text": "#E3E8EE",
    "muted": "#9AA5B1",
    "accent": "#7CA6C8",
    "accent_soft": "#1F2C36",
    "primary": "#2B3947",
    "primary_hover": "#344454",
    "table_bg": "#171C22",
    "table_sel_bg": "#233040"
  },
  "background": {
    "image_path": "themes/night_slate/bg.png",
    "opacity": 0.18,
    "position": "center",
    "size": "cover",
    "repeat": "no-repeat",
    "blend_mode": "multiply"
  },
  "notes": "Optional free-form notes."
}
```

## Field notes
- `id`: stable identifier used in settings.
- `name`: display name in the theme selector.
- `version`: schema version for forward compatibility.
- `colors`: required palette keys. These map to Settings UI styling and will later apply app-wide.
- `background`: optional background image config. If present, the GUI should layer the image behind panels.

## Theme folder structure (recommended)
Store each theme in its own folder so assets are grouped with the theme JSON.

```
themes/
  harbor_glow.json
  moe_pastel/
    theme.json
    ocean.jpg
    forest.jpg
    clouds.jpg
```

Notes:
- The loader accepts `.json` files directly in `themes/`, or a `theme.json` inside a subfolder.
- Image paths in `theme.json` are resolved relative to that file’s folder.
- A shared `themes/sample_images/` folder can be used for example assets; themes can reference it via `../sample_images/...`.
- The app seeds `themes/sample_images/` from bundled resources on first run (if the files are missing).

## Screen overrides (planned)
Themes should be able to override colors and backgrounds per GUI screen. This keeps a consistent base palette
while allowing each screen to feel purpose-built and readable. The suggested structure below is additive
to the base `colors` and `background` fields above.

```json
{
  "screen_overrides": {
    "main_window": {
      "colors": { "...": "..." },
      "background": { "...": "..." }
    },
    "profiles_dialog": {
      "colors": { "...": "..." },
      "background": { "...": "..." }
    }
  }
}
```

### Main Window (Ruleset Editor)
Elements to define:
- Window background (entire screen)
- Primary panel backgrounds (rules table, replacement list, preview/log)
- Panel borders + dividers
- Section headers and labels
- Table header + row background
- Table selection background + text
- Inline action buttons (add/remove/save)
- Tag/chip colors for rule tags
- Highlight color for replacements (if enabled)
- Status text + muted helper text

Background image (entire screen):
- Optional image behind the main window panels with opacity control.

### Profiles / Manage Dialog
Elements to define:
- Window background
- Profile list background + selected row
- Ruleset list background + selected row
- Action buttons (new, reveal, duplicate, delete)
- Section headers + descriptions
- Borders/dividers

Background image (entire screen):
- Optional image behind the dialog container.

### Settings Dialog
Elements to define:
- Window background
- Tab header background + selected tab
- Form field background + border
- Toggle/checkbox accent
- Primary buttons + hover
- Section headers + helper text

Background image (entire screen):
- Optional image behind the settings tabs (current implementation applies to Settings only).

### Code / Import-Export Dialogs
Elements to define:
- Window background
- Code editor background + selection
- Monospace text color
- Action buttons (copy/save/import)
- Warning/notice text

Background image (entire screen):
- Optional image behind the dialog container.

### First-Run / Welcome Dialog
Elements to define:
- Window background
- Title text + subtitle text
- Primary call-to-action button + hover
- Illustration/container panel background

Background image (entire screen):
- Optional image behind the dialog container.

## Background keys (planned)
- `image_path`: local path (relative to theme pack or absolute). Future plan: allow http(s) with caching.
- `opacity`: 0.0 to 1.0.
- `position`: CSS-like position (`center`, `top`, `left`, etc.).
- `size`: `cover`, `contain`, or explicit percent.
- `repeat`: `no-repeat`, `repeat`, `repeat-x`, `repeat-y`.
- `blend_mode`: `normal`, `multiply`, `screen`, etc.

## Validation (planned)
- All `colors` keys are required.
- Hex colors must be `#RRGGBB`.
- `opacity` must be numeric in `[0.0, 1.0]`.
- Unknown keys should be ignored for forward compatibility.

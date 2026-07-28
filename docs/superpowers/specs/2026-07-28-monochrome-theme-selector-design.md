# Monochrome HUD theme selector

## Goal

Replace the fixed multi-hue Cyberpunk Neon palette with a switchable **single-hue** theme system: the whole page (all metric cards, gauges, service icons, live indicator) uses exactly one accent color at a time, chosen from 4 presets via a toggle button next to the existing language toggle. Multi-entry sections (disks, network interfaces) that used to get one hue each now get tonal (lightness) variants of that one theme color instead.

This also incidentally fixes a known limitation from the previous palette: with 7+ disks, distinct hues started repeating (see disk-color testing in this same project). Tonal shades are now generated per-render for however many entries actually exist, so they never hit a hard repeat ceiling.

## Themes (4 presets, cycled by clicking the toggle)

| Theme | Base hex |
|---|---|
| Cyan (default) | `#55ead4` |
| Phosphor Green | `#3ef25a` |
| Amber | `#ffb000` |
| Red | `#ff3b30` |

Cyan is the default so first load after this ships looks the same as the just-shipped neon cyan CPU color - no jarring change for existing visitors.

## Mechanics

- Applying a theme sets all six existing role variables (`--blue`, `--leaf`, `--sun`, `--red`, `--teal`, `--mint`) on `:root` to the *same* hex via inline style (`documentElement.style.setProperty`). Every CSS rule in the file already reads color through one of these six variables, so no selector needs to change - the whole page (including service-row icons, which read `accent` from `config.json` through the same variable names) becomes monochrome automatically.
- A new `--accent-glow` variable replaces the currently-hardcoded green `rgba(88, 189, 139, 0.45)` in `.live-dot`'s `box-shadow`, computed from the active theme's hex at apply-time so the glow always matches.
- Choice persists in `localStorage` (same pattern as the language toggle), independent of language.
- Toggle button sits next to the language button in the topbar, styled with `color: var(--blue)` (now the live theme color) so its own text color previews the active theme; click cycles cyan -> green -> amber -> red -> cyan. Tooltip names the theme, translated via the existing i18n dictionary.

## Tonal shades for disks and network cards

Replace the fixed 6-color `DISK_COLORS` pool with a function that generates exactly as many shades as there are entries to render, by varying HSL lightness of the active theme's hue (hue/saturation held constant, lightness spread evenly across a legible range, e.g. 32%-78%). Called separately for the disk bar/legend and for network card accents, sized to `disks.length` / `networks.length` respectively at render time - never a fixed-size pool, so it scales cleanly with however many real entries a given machine has.

## Out of scope

- No change to layout, typography, background tones, or the borderless card convention.
- `config.json`'s per-service `accent` field stays in the schema (harmless, forward-compatible) but has no visible effect while a monochrome theme is active, by explicit user choice - simpler than maintaining two coexisting color systems.

## Verification

Same as prior changes to this repo: local mock-data browser check (cycle all 4 themes, confirm every card/icon/glow follows; confirm disk and network tonal cycling with edge-count mocks like 0/1/7 entries), then redeploy `index.html` to the live Pi (bind-mounted, no rebuild) for the user's own visual confirmation.

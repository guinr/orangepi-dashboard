# Cyberpunk Neon accent palette

## Goal

Restyle the dashboard's accent colors to a "neo-militarism cyberpunk" HUD vibe, without touching layout, typography, or the dark background - a pure color-variable swap on top of the existing design system.

## Scope

Only the six accent CSS custom properties in `www/index.html`'s `:root` change. Everything else (card shapes, spacing, fonts, background tones, borderless convention, gauge/bar mechanics) stays exactly as-is. This preserves the dashboard's established "compact, flat, no clutter" visual language (see project memory `orangepi-portal-dashboard`) while giving it a bolder, high-saturation accent identity inspired by Cyberpunk 2077's official UI palette and real tactical-HUD color conventions (cyan/green readouts, amber/red alerts).

## Palette mapping

| Variable | Role | Old | New |
|---|---|---|---|
| `--blue` | CPU card | `#7aa7d9` | `#55ead4` (electric cyan) |
| `--leaf` | RAM card | `#8fbf6f` | `#9fe64d` (acid green) |
| `--sun` | Disk card + 2nd disk-cycle color | `#d7a84a` | `#f3e600` (neon yellow) |
| `--red` | Temperature card | `#d37668` | `#c5003c` (Cyberpunk 2077 red) |
| `--teal` | Network card + 5th disk-cycle color | `#4db6ac` | `#ff2079` (neon magenta) |
| `--mint` | Live-dot glow + camera service accent + 6th disk-cycle color | `#58bd8b` | `#b026ff` (neon violet) |

Six distinct, fully-saturated hues, no repeats - deliberately chosen so the disk-color-cycling logic (`DISK_COLORS`, reused for network card accents) still produces 6 visually distinct colors before repeating.

## Out of scope (explicitly deferred, not part of this change)

- Typography, corner shapes, scanline/grid textures, glow effects beyond the existing live-dot shadow, alert-threshold color logic - all considered and explicitly rejected in favor of the "subtle, colors-only" intensity level the user chose.
- Background/surface tone shift (the "Night-Ops + tinted background" option) - user picked the option that keeps the background untouched.

## Verification

Apply the same way every prior change to this repo was verified: local mock-data render in the browser preview (confirm all six cards + disk legend + service icons render with the new hues, contrast is still readable at the existing small font sizes), then redeploy `index.html` to the live Pi (bind-mounted, no rebuild needed) and spot-check via the already-established curl/API checks.

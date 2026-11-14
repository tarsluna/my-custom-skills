# Design system

The deck is deliberately quiet: one idea, centered, on a dark field, with one accent color. Nothing competes with the speaker.

**May change:** the eight colors, the logo or wordmark, the words.
**Stays:** fonts, type scale, layout, spacing, timings, diagrams.

## Color tokens

Eight values in `brand.json`. Every border, tint and glow derives from them with `color-mix`, so a palette swap recolors everything.

| Token | Role | Default |
| --- | --- | --- |
| `bg` | Page background | `#0d0c0a` |
| `fg` | Main text | `#efe9dd` |
| `soft` | Diagram labels, secondary text | `#cfc8bb` |
| `mut` | Captions, counters | `#9a9386` |
| `accent` | Keywords, figures, active strokes, progress bar | `#e9c48f` |
| `node` | Fill of cards and pills | `#161411` |
| `panel` | Notes and help popovers | `#201d17` |
| `on_accent` | Text on an accent fill | `#14120e` |

Derived tints: `--f12`, `--f18`, `--f20` from `fg`, and `--a08`, `--a12`, `--a15`, `--a33`, `--a47`, `--a53` from `accent`.

The build refuses a palette that fails these contrast ratios: `fg` on `bg` 7:1, `soft` on `bg` 4.5:1, `mut` on `bg` 3:1, `accent` on `bg` 4.5:1, `on_accent` on `accent` 4.5:1, `accent` on `panel` 3:1. `palettes.json` has four sets that pass: `ink-gold` (default), `midnight-mint`, `ember`, and a light one, `paper`.

Choosing your own: keep one accent only. Derive `node` and `panel` by lifting `bg` slightly. Make `soft` about 15% of the way from `fg` to `bg`, and `mut` about 40%. Keep the warmth of the neutrals consistent with the accent.

## Type

Two families, both under the SIL Open Font License and embedded in the file. Licenses are in `template/assets/`.

| Family | Use |
| --- | --- |
| Jost | Spoken line, headline, figures, diagram titles |
| Instrument Sans | Interface, labels, captions |

| Element | Size | Weight / line height |
| --- | --- | --- |
| Spoken line | `clamp(28px, 3.7vw, 56px)`, max 30ch | 350 / 1.3, tracking -.012em |
| Spoken line beside a diagram or stat | `clamp(23px, 2.8vw, 42px)`, max 34ch | 350 / 1.3 |
| Headline (screen mode) | `clamp(40px, 6.4vw, 96px)`, max 19ch | 350 / 1.1, tracking -.018em |
| Headline beside a diagram | `clamp(34px, 4.4vw, 66px)` | 350 / 1.1 |
| Stat value | `clamp(52px, 7.4vw, 112px)` | 350 / 1, tracking -.02em |
| Stat value (screen mode) | `clamp(68px, 10.5vw, 168px)` | 350 / 1 |
| Stat label | `clamp(14px, 1.35vw, 20px)` | 400 / 1.35 |
| Eyebrow (FAQ question) | 13px uppercase, tracking .09em | 400 |
| Context line | `clamp(12px, 1.1vw, 15px)` uppercase, tracking .09em | 400 |
| Diagram title / label / caption / big | 24px / 17px / 15px / 60px | Jost 400 / Instrument / Instrument / Jost 350 |

All text uses `text-wrap: balance`. Keywords switch color only, never weight or style.

## Layout

A three-row grid fills the viewport: 66px header, stage, footer.

- **Header:** logo 118px wide, 30px side padding.
- **Stage:** content centered both ways, max width 1120px, side padding 6vw. Vertical gap between elements `clamp(14px, 2.6vh, 28px)`.
- **Slide order:** eyebrow, headline or spoken line, diagram, stats, context, CTA pill.
- **Diagrams:** width up to 760px in reading mode, 1040px in screen mode. All drawn in a 720 by 240 box.
- **Footer:** previous and next, counter, time marker, part menu, tools.
- **Progress:** a 2px accent bar at the very top.

Responsive rules: below 700px width everything tightens and secondary labels hide. Below 760px height on desktop, the type and diagrams scale down. `verify.cjs` tests 1440x900, 1280x720 and 390x844.

## Three modes

| Mode | Purpose | Shows |
| --- | --- | --- |
| Reading (default) | Teleprompter | The full spoken line word for word, the FAQ eyebrow, diagram, stats |
| Screen (`L`) | What viewers see | Big `key` line and a larger diagram. Stats alone, giant |
| Presenter (`P`) | Second window | Spoken line, next line, notes, part marker. Stays in sync through BroadcastChannel |

The notes panel (`N`) shows the framework position, the question and production notes. Viewers never see these.

## Behavior

- When the mouse stops for 2.4 seconds, the toolbar and progress bar fade and the cursor hides. The frame stays clean to film.
- Keyboard: arrows, Space, PageUp and PageDown, Home, End, `L`, `N`, `P`, `F`, `A`.
- The URL carries the slide number, so `deck.html#14` opens slide 14.
- One self-contained file. No network request, no external font, no script.
- Accessibility: `aria-live` on the slide, labeled controls, visible focus, `prefers-reduced-motion` honored, a manual animation switch.
- Print: the deck prints plainly, and `script.html` has a print layout with a spoken-only view.

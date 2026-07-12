# Template — Master-prompt GPT Image 2 (par cellule)

Remplir les `{{placeholders}}` depuis `client-brand-profile.json` + la cellule de
`variation-matrix.json` + le style choisi (`frameworks/01`). Le prompt final va dans
`cells[].prompt`. Les 7 blocs sont **obligatoires** (cf. framework 01 §1).

---

## Gabarit (anglais — GPT Image 2 suit mieux l'anglais pour l'art-direction)

```
[FORMAT]
A {{platform}} ad creative, {{aspect_ratio}} aspect ratio, designed for {{format_name}}.
Mobile-first, fully legible at thumbnail size.

[STYLE]
Visual style: {{design_style_name}} — {{design_style_seed}}.
{{#style_ref}}Use the composition, lighting and energy of the reference image as
inspiration ONLY; the brand, colors, product and text must be 100% {{brand_name}},
never the reference's brand.{{/style_ref}}

[SCENE]
{{scene_description}}
{{#brand_assets}}Match the product/brand shown in the reference images; do not invent
a different logo or product.{{/brand_assets}}

[PALETTE]
Background {{bg_role}} {{bg_hex}}, text {{text_role}} {{text_hex}},
single accent color {{accent_hex}} used ONLY on the call-to-action.
{{secondary_hex}} for the secondary tonal line. High-end, editorial color grading.

[TEXT]
The headline text reads exactly: «{{hook}}» — placed {{hook_placement}},
large and high-contrast, in a {{type_voice}} type style.
{{#sub}}A smaller secondary line reads: «{{sub}}».{{/sub}}
The call-to-action button text reads exactly: «{{cta}}», on a rounded pill in the accent color, near the bottom.
Keep ALL text short, correctly spelled, and perfectly legible. Do not add any other text.

[COMPOSITION]
{{brand_name}} logo small in the top-left. Single focal point. Generous negative space
(editorial breathing room). Strict vertical rhythm: logo top, headline upper third,
CTA lower area. Keep the bottom 15% clear of critical text (Meta safe zone).
{{#story}}Keep the top 220px and bottom 220px clear of text (Instagram UI).{{/story}}

[QUALITY]
Premium {{render_quality}} rendering, crisp focus, natural light, magazine-grade finish.
NEGATIVE: no watermark, no extra gibberish text, no misspelled words, no distorted hands,
no fake or duplicated logos, no lorem ipsum, no duplicated UI chrome, no border frame.
```

---

## Exemple rempli (studease — angle white-space « coût réorientation », style S7 data-viz, Feed 4:5)

```
[FORMAT]
A Meta Feed ad creative, 4:5 aspect ratio, designed for Instagram/Facebook feed.
Mobile-first, fully legible at thumbnail size.

[STYLE]
Visual style: Data-Viz / Chart — clean data visualization, single big number,
upward chart, financial UI aesthetic, brand accent on key metric.

[SCENE]
A clean editorial chart showing the rising cost of a wasted academic year, one giant
number dominating the upper area, subtle grid lines, no clutter.

[PALETTE]
Background deep navy #0F2A3F, text off-white #F6F1E7, single accent color #F25C2A used
ONLY on the call-to-action. Warm cream #E7DBC6 for the secondary tonal line.
High-end, editorial color grading.

[TEXT]
The headline text reads exactly: «Une année ratée coûte 10 000 €.» — placed in the
upper third, large and high-contrast, in a confident serif type style.
A smaller secondary line reads: «Une mauvaise orientation aussi.»
The call-to-action button text reads exactly: «Faire le point», on a rounded pill in
the accent color, near the bottom. Keep ALL text short, correctly spelled, perfectly
legible. Do not add any other text.

[COMPOSITION]
studease logo small in the top-left. Single focal point (the big number). Generous
negative space. Strict vertical rhythm: logo top, headline upper third, CTA lower area.
Keep the bottom 15% clear of critical text.

[QUALITY]
Premium photoreal/editorial rendering, crisp focus, magazine-grade finish.
NEGATIVE: no watermark, no extra gibberish text, no misspelled words, no distorted
hands, no fake or duplicated logos, no lorem ipsum, no duplicated UI chrome, no border frame.
```

---

## Notes
- Garde le **hook ≤ 7 mots** et le **CTA ≤ 4 mots** : au-delà, GPT Image 2 déforme le texte.
- Le **body** (primary text Meta) ne va PAS dans l'image — il est livré à part dans le copy pack.
- Si la cellule a un `style_ref` et/ou des `brand_assets`, ils sont passés par `build_variations.py` en `input_images` (le bloc `{{#...}}` correspondant doit alors être présent dans le prompt).
- Après génération, si le texte rendu est flou ou mal orthographié → `brand_lock_pass.py` réincruste hook/CTA en PIL avec les fonts exactes.

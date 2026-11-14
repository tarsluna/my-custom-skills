# Content format

A deck is two files: `brand.json` holds what is specific to the brand, `content.py` holds the script. `vsl.py`, `build.py`, `player.html` and `verify.cjs` do not change between decks.

## brand.json

| Key | Purpose |
| --- | --- |
| `slug` | File name of the deck, lowercase with hyphens |
| `name` | Brand name, used in the page title and for screen readers |
| `wordmark` | Text shown top left when there is no logo |
| `logo` | Path to an SVG, or `null`. Use `fill="currentColor"` so it follows the palette |
| `lang` | `fr` or `en`. Sets the part names, interface labels, punctuation and default banned words |
| `format` | `long` (6 to 10 loops, 1200 to 1800 words) or `short` (3 to 5 loops, 450 to 750 words) |
| `voice` | Who speaks |
| `wpm` | Reading speed. 138 is a fair start, measure a real read |
| `colors` | Eight tokens, see [04-design-system.md](04-design-system.md) |
| `mechanism` | The name exactly as spoken, for example `méthode Relais` |
| `cta.button` | Button label |
| `cta.question` | The personalization question, asked word for word in the CTA |
| `cta.reminder` | A word the last slide must contain, case-insensitive, for example `Réservez` |
| `verbatims` | Exact customer phrases. At least two must appear word for word in the spoken `text`. `key` and notes do not count |
| `banned` | Words to refuse for this market, added to the defaults |
| `allow` | Default banned words this market legitimately uses |
| `proof_inventory` | Each `{value, label, source}`. A stat must match a `value` exactly, spacing included: `4.9 / 5` is not `4.9/5`. Only `stats` are checked, so trace figures in `text` and `key` by hand |

## content.py

Five lists: `INTRO`, `OLD_NEW`, `FAQ`, `CTA`, `PROOF`. Helpers come from `vsl.py`.

### s(text, key, v, note, stats, who, context)

One slide.

| Field | Shown | Rules |
| --- | --- | --- |
| `text` | Reading mode, spoken word for word | 27 words at most. `*asterisks*` color a phrase |
| `key` | Screen mode, the big line | 9 words at most |
| `v` | Animated diagram | `v('type', ...)`, see [05-animations.md](05-animations.md) |
| `note` | Notes panel and script only | Sources, legal flags, filming directions |
| `stats` | Giant figures | Up to two `(value, label)` pairs |
| `who` | Proof line | Name of the client or person |
| `context` | Proof line | Sector or source. Required with any stat and on every proof-salad slide, testimonials included |

### b(role, *slides)

A block of slides. Roles by part:

- `INTRO`: `hook` (first), `promise`, `pain`, `proof`, `plan`, `picture`.
- `OLD_NEW`: `old`, `why`, optional `shift`, `new` (last).
- `CTA`: `action`, `question`.
- `PROOF`: `salad`.

Any other role string is accepted and displayed as written.

### q(title, think, wrong, right, proof, kind)

One FAQ loop. The four stages are lists of slides. `kind` is `offer`, `price`, `guarantee`, or any label you choose.

### Example

```python
from vsl import s, b, q, v

CTX = 'Car repair, private clients'

FAQ = [
    q('What if it does not work?',
      [s('“What if I commit and nothing happens?”', 'What if it fails?')],
      [s('In this market the risk is usually yours. Here it is ours.', 'The risk is ours.')],
      [s('The target is written down: *three contracts in ninety days*.', 'Three contracts. 90 days.',
         v=v('deadline', start='Day 1', end='Day 90', title='Three contracts signed', sub='Within the criteria set at the start')),
       s('*If none is signed, you pay us nothing.*', 'You pay nothing.', note='Have counsel review this before broadcast.')],
      [s('One family-run garage: *forty requests in two months*.', '40 requests.',
         stats=[('40', 'requests in 2 months')], context=CTX)],
      kind='guarantee'),
]
```

## Build checks

`python3 build.py` reports every failure at once. Fix the copy. Do not edit the check to get past it.

| Message | Meaning | Fix |
| --- | --- | --- |
| `missing block` | An intro, part 2, CTA or proof block is absent | Write it |
| `first block must be "hook"` | The video opens on something else | Move the hook first |
| `the last block must be "new"` | Part 2 does not end on the mechanism | Reorder |
| `mechanism ... never named` | The `new` block does not say the name | Name it exactly as in `brand.json` |
| `FAQ: n loops` | Too few or too many for the format | Add, merge, or change `format` |
| `all four stages` | A loop is missing a stage | Write the stage |
| `proof stage needs a figure` | A loop ends without proof | Add real proof, or a placeholder in draft |
| `no loop with kind` | Offer, price or guarantee is missing | Add the loop and set `kind` |
| `named n times` | Mechanism under or over repeated in the FAQ | Rephrase the "what is right" stages |
| `question ... word for word` | CTA does not ask the exact question | Quote it |
| `only proof after the CTA` | An argument slipped into the salad | Move it to the FAQ |
| `missing context` | Proof without a sector or source | Add `context` |
| `must remind the single action` | The deck ends elsewhere | End on the action |
| `unbalanced asterisks` | Odd number of `*` | Close the phrase |
| `words, one idea per slide` | Slide too long | Split it |
| `screen line too long` | `key` is over nine words | Shorten |
| `figure ... not in proof_inventory` | Number without a declared source | Declare it with its source, or delete it |
| `figure without context` | A stat with no sector | Add `context` |
| `proof does not belong` | Proof in part 2 | Move it to a loop |
| `proof placeholder left` | `[PROOF NEEDED]` in a final build | Get the proof, or build with `--draft` |
| `visual ...` | Unknown type, missing parameter, label too long | See the visual's limits |
| `banned expression` | A forbidden word | Rewrite. Use `allow` only if it is the market's own word |
| `"it is not X, it is Y"` | More than two | Rewrite |
| `customer verbatim` | Fewer than two exact quotes | Quote from the research |
| `n words` | Above the format's maximum | Cut. Below the minimum is a warning only: do not pad, see `02-copywriting.md` |
| `contrast too low` | Palette is hard to read | Adjust the color named |

Warnings do not block. They flag part shares outside the target range.

## Draft mode

`python3 build.py --draft` accepts `[PROOF NEEDED: ...]` placeholders and figures outside the inventory, so a speaker can rehearse. Report the draft status clearly. The content report shows `"draft": true`.

## Language

`fr` and `en` are built in. To add one, copy a block in `I18N` in `build.py` and translate the parts, stages, roles, interface labels, script labels and banned words. Non-breaking French punctuation is handled by the player.

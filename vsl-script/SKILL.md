---
name: vsl-script
description: Write a complete Video Sales Letter on Alex Hormozi's 5-part framework and compile it into one self-contained, animated HTML presentation you can read from and film. Includes a word-by-word teleprompter mode, a big-keyword screen mode, a synced presenter window, 23 animated diagrams, blocking framework and copy checks, and browser QA. Use for "VSL", "video sales letter", "sales video script", "VSL presentation", "script VSL", "présentation VSL", "vidéo de vente", or to rebrand or update a deck built with this skill. Not for short ads, and not for editing the finished video.
---

# VSL Script

Turn an offer and its proof into a VSL script, then stage that script as a single HTML file the speaker reads from and films. The default language is the user's language. The template ships in French and English.

Read these before writing. They are the skill, not background:

| File | Read it for |
| --- | --- |
| [references/01-framework.md](references/01-framework.md) | The five parts, slide by slide |
| [references/02-copywriting.md](references/02-copywriting.md) | Research, big idea, mechanism, FAQ loops, sentence rules, review pass |
| [references/03-content-format.md](references/03-content-format.md) | `brand.json`, `content.py`, every build check and how to fix it |
| [references/04-design-system.md](references/04-design-system.md) | Tokens, type scale, layout, modes, what may change |
| [references/05-animations.md](references/05-animations.md) | Motion rules and the 23 diagrams |
| [references/06-beat-map.md](references/06-beat-map.md) | The pacing of a full 104-slide VSL |

## Four rules that do not bend

1. **Five parts, in order.** Intro, old way vs new way, FAQ loops, small CTA, proof salad. No other section. The offer, price, guarantee and urgency are answers to FAQ questions. `build.py` assembles the parts itself, so the order cannot drift.
2. **Real proof only.** Never invent a figure, client, quote or result. Every stat on screen must match an entry in `proof_inventory`, which records its source, and carries a context line naming the sector, so a result from another trade never reads as one from the viewer's. The build can only check stats. Figures spoken in `text` or written in `key` are yours to trace in the review pass. If proof is missing, ask for it. For a rehearsal draft, write `[PROOF NEEDED: what is missing]` and build with `--draft`. A draft is never a deliverable.
3. **The design is locked.** Change the eight colors, the logo and the words. Keep the fonts, type scale, layout, timings and diagrams. If a client wants a different layout, this is the wrong skill.
4. **Local by default.** Build and verify on the machine. Publishing the deck, sending it, or wiring it to a booking tool needs its own explicit request.

## What you deliver

```text
my-vsl/
├── BRIEF.md                      Frozen strategy
├── brand.json                    Colors, logo, mechanism, CTA, verbatims, proof inventory
├── content.py                    The script, slide by slide
└── dist/
    ├── <slug>.html               The deck. One file, fonts and data embedded
    ├── script.html               Script to read or print, with a spoken-only view
    ├── script.md, script.txt     Same script as text
    └── verification/             Content report, browser report, captures
```

## Workflow, from A to Z

### 1. Read what exists, ask only what blocks

Look for research, offer documents, testimonials, past scripts and brand files first. Ask only for what you cannot find and cannot responsibly assume:

- who the video is for, and what you want them to do at the end;
- the offer: result, delay, what is included, price logic, guarantee;
- the proof: figures with their source, client names you may use, testimonials;
- the person speaking, the language, long (8 to 12 min) or short (3 to 5 min);
- brand colors and logo.

### 2. Extract the market

Follow "Research" in [02-copywriting.md](references/02-copywriting.md). The output is a working list: five pains in the buyer's own words, every objection, what they already tried and why it failed, the awareness and sophistication levels. If no research exists, say so, work from what the user knows, and mark assumptions in `BRIEF.md`.

### 3. Freeze the strategy

Copy `template/BRIEF.md` and fill all of it: hook, big idea, promise, picture, old mechanisms and their shared flaw, the turning point, the named mechanism and its three pillars, the offer, the client's own effort, price, guarantee, CTA with its personalization question, allowed proof, banned words. Everything after this point obeys the brief. This is what keeps a 100-slide script consistent.

### 4. Start the project

```bash
cp -R "<skill-dir>/template" ./my-vsl
cd my-vsl
npm install        # puppeteer-core, for browser QA only
```

`<skill-dir>` is the folder holding this `SKILL.md`. Python 3.9+ has no other dependency. Edit `brand.json`: slug, name, wordmark or logo, `lang`, `format`, voice, colors (`palettes.json` has four tested sets), mechanism, CTA, verbatims, banned words, proof inventory.

### 5. Write the script

Replace every line of `content.py`. Its example is fictional: do not carry any of it over. Write in this order, because each part depends on the one before:

1. the `new` block of part 2, where the mechanism is named;
2. the rest of part 2;
3. the FAQ loops, starting with offer, price and guarantee;
4. the intro, once you know what you are promising and can prove;
5. the CTA and the proof salad.

One slide carries one idea, 27 spoken words at most. `text` is written for the ear, numbers spelled out as they are said. `key` is the line on screen, nine words at most, digits welcome. Mark the phrase to remember with `*asterisks*`, on about two slides out of three.

If the material is thin, make a shorter video. See "When the material is thin" in [02-copywriting.md](references/02-copywriting.md). Never add a fact to reach a word count.

### 6. Stage it

Open [05-animations.md](references/05-animations.md) and pick a diagram wherever a mechanism, comparison, sequence or offer is easier to see than to hear. Roughly one slide in three carries one. Use two-state reveals: the same diagram on consecutive slides, with more lit on the second. Leave pure emotion and short punchlines as text alone. Never restate the `key` inside the diagram.

### 7. Build

```bash
python3 build.py
```

It lists every problem at once and refuses to produce a deck until they are fixed. [03-content-format.md](references/03-content-format.md) explains each message. Fix the copy, never the check. Warnings about part balance do not block, but read them.

### 8. Verify in a real browser

```bash
node verify.cjs
```

It walks every slide in three viewports and both modes, tests every control and the synced presenter window, and captures each diagram type plus the key slides, in both modes, into `dist/verification/captures/`, with a mobile capture and the presenter window. Then **open the captures and look at them**. The script catches overflow and broken controls. It cannot tell whether a diagram explains anything.

### 9. Review the copy

Run the review pass at the end of [02-copywriting.md](references/02-copywriting.md): read the whole script aloud, trace every claim to the brief, attack it as a skeptical buyer, cut 10%. Rebuild and re-verify after any change.

### 10. Deliver

State plainly: the deck path, script path, word count and estimated duration, the mechanism and the CTA question, what was checked, and what still needs a human decision. That last list usually holds legal review of the guarantee, amounts not yet set, deliverables that must stay true (a free bonus, a deadline), adding the CTA question to the real booking form, objections left out because no known fact answers them, any market fact you could not source, and every mechanism description or image you wrote yourself and the owner must confirm. Tell the user how to drive the deck: `L` reading or screen, `N` notes, `P` presenter, `F` full screen, `A` animations, arrows to move.

## Editing a deck built with this skill

Edit `content.py` or `brand.json` only, then rebuild and re-verify. Never patch `dist/`, which is overwritten. A figure the owner changes goes through `proof_inventory` too. If the owner states a figure that their own source does not support, apply their decision and say so in one line.

## Failure modes this skill was built against

- **Self-undermining copy.** Hedges on screen ("we are just starting", "no guarantee", "planned diagram") kill the sale. Say only what is true, say it plainly, and keep caveats in production notes. An honest gap can become the argument: "you would be among the first, which is why we carry the risk".
- **Empty proof slots.** A deck full of `[PROOF NEEDED]` is a draft. Do not present it as finished.
- **A separate offer section.** It breaks the loop. Offer, price and guarantee are FAQ questions.
- **Results without a sector.** "40 requests in two months" reads as a result in the viewer's trade unless the slide says otherwise.
- **Internal labels on screen.** Framework names, "proof", "slide 12" belong in the notes.
- **Machine prose.** Serial "it is not X, it is Y", hollow triplets, exclamation marks, emoji.
- **A CTA question that does not exist.** It must be asked by the real booking form.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compile brand.json + content.py into a self-contained VSL deck and its scripts.

Usage: python3 build.py [--draft]

Every framework and copy rule below is blocking. All failures are listed at once.
--draft allows [PROOF NEEDED: ...] placeholders and proof figures missing from the inventory,
so a first version can be read and rehearsed. A draft is never a deliverable.
"""
from pathlib import Path
from html import escape
import base64, json, re, sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from vsl import VISUALS, COUNTS, ICONS, ICON_USES
import content as C

DRAFT = '--draft' in sys.argv
DIST = HERE / 'dist'
errors, warnings = [], []
err = errors.append
warn = warnings.append

I18N = {
    'fr': dict(
        parts=['1. Intro', '2. Ancienne méthode contre nouvelle', '3. FAQ', '4. CTA', '5. Preuves'],
        stages=['Ce qu’il pense', 'Pourquoi c’est faux', 'Ce qui est vrai', 'Preuve'],
        roles=dict(hook='Accroche', promise='Promesse', pain='Douleur', proof='Preuve', plan='Plan', picture='Projection',
                   old='Ancienne méthode', why='Pourquoi ça ne suffit plus', shift='Le déclic', new='Nouvelle méthode, nommée',
                   action='Action unique', question='Question de personnalisation', salad='Preuves'),
        ui=dict(prev='Diapositive précédente', next='Diapositive suivante', part='Choisir une partie', screen='Mode écran', reading='Mode lecture',
                motion='Animations', notes='Notes', presenter='Présentateur', full='Plein écran', shortcuts='Raccourcis clavier',
                help='← → : changer de page · Espace : suivante · L : lecture / écran · N : notes · P : présentateur · F : plein écran · A : animations',
                readAll='Lire tout le script', frameTag='Repère du cadre :', question='Question :', nextLine='Ensuite :', estimated='estimées',
                fullHint='Utilisez le plein écran du navigateur.'),
        script=dict(voice='Voix', words='mots', est='estimées', slides='diapositives', title='Le script, mot à mot.', screen='À l’écran', anim='animation',
                    production='Production', open='Ouvrir la présentation', plain='Texte brut', spoken='Texte parlé seul', print='Imprimer',
                    legend='Les mots entre astérisques sont les mots clés mis en couleur à l’écran.', spoken_only='TEXTE PARLÉ SEUL.'),
        banned=['!', '—', 'incroyable', 'révolutionnaire', 'révolutionner', 'game changer', 'boostez', 'booster', 'machine à cash', 'leads', 'funnel',
                'tunnel de vente', 'closing', 'scaler', 'mindset', 'prédictabilité', 'sans garantie'],
        not_but=r"n['’]est pas[^.?!]{0,70}?(?:c['’]est|mais)",
    ),
    'en': dict(
        parts=['1. Intro', '2. Old way vs new way', '3. FAQ', '4. CTA', '5. Proof'],
        stages=['What they think', 'Why it is wrong', 'What is right', 'Proof'],
        roles=dict(hook='Hook', promise='Promise', pain='Pain', proof='Proof', plan='Plan', picture='Picture',
                   old='Old way', why='Why it stopped working', shift='The turning point', new='New way, named',
                   action='One action', question='Personalization question', salad='Proof'),
        ui=dict(prev='Previous slide', next='Next slide', part='Jump to a part', screen='Screen mode', reading='Reading mode',
                motion='Animations', notes='Notes', presenter='Presenter', full='Full screen', shortcuts='Keyboard shortcuts',
                help='← → : change slide · Space : next · L : reading / screen · N : notes · P : presenter · F : full screen · A : animations',
                readAll='Read the full script', frameTag='Framework:', question='Question:', nextLine='Next:', estimated='estimated',
                fullHint='Use your browser’s full screen.'),
        script=dict(voice='Voice', words='words', est='estimated', slides='slides', title='The script, word for word.', screen='On screen', anim='animation',
                    production='Production', open='Open the deck', plain='Plain text', spoken='Spoken text only', print='Print',
                    legend='Words between asterisks are the keywords colored on screen.', spoken_only='SPOKEN TEXT ONLY.'),
        banned=['!', '—', 'game changer', 'game-changer', 'revolutionary', 'unbelievable', 'skyrocket', 'supercharge', 'no guarantee'],
        not_but=r"\b(?:isn['’]t|is not)\b[^.?!]{0,70}?\b(?:it['’]s|it is|but)\b",
    ),
}
FORMATS = {
    'long': dict(faq=(6, 10), words=(1200, 1800), mechanism=(4, 6)),
    'short': dict(faq=(3, 5), words=(450, 750), mechanism=(2, 4)),
}
PART_SHARE = [(10, 17), (15, 22), (40, 55), (2, 6), (10, 25)]
MAX_WORDS_SLIDE, MAX_WORDS_KEY = 27, 9
PLACEHOLDER = re.compile(r'\[(?:PREUVE|PROOF)\b', re.I)
INTERNAL = re.compile(r'\b(?:TODO|TBD|FIXME|lorem)\b', re.I)
EMOJI = re.compile('[\U0001F300-\U0001FAFF☀-➿]')
COLORS = ['bg', 'fg', 'soft', 'mut', 'accent', 'node', 'panel', 'on_accent']

brand = json.loads((HERE / 'brand.json').read_text(encoding='utf8'))
lang = brand.get('lang', 'fr')
if lang not in I18N:
    sys.exit(f'brand.json: lang must be one of {sorted(I18N)}')
L = I18N[lang]
fmt = brand.get('format', 'long')
if fmt not in FORMATS:
    sys.exit(f'brand.json: format must be one of {sorted(FORMATS)}')
F = FORMATS[fmt]
WPS = brand.get('wpm', 138) / 60
PARTS, STAGES = L['parts'], L['stages']


def plain(t): return t.replace('*', '')
def words(t): return len(re.findall(r"[\wÀ-ÿ0-9]+(?:[’'-][\wÀ-ÿ0-9]+)*", plain(t)))
def clock(n): n = int(round(n)); return f'{n // 60}:{n % 60:02}'
def role_label(r): return L['roles'].get(r, r)
def low(t): return plain(t).replace("'", '’').lower()


# Colors -----------------------------------------------------------------------------------------
def lum(hexa):
    vals = [int(hexa[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    r, g, b = [v / 12.92 if v <= .03928 else ((v + .055) / 1.055) ** 2.4 for v in vals]
    return .2126 * r + .7152 * g + .0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)


colors = brand.get('colors', {})
for c in COLORS:
    if not re.fullmatch(r'#[0-9a-fA-F]{6}', colors.get(c, '')):
        err(f'brand.json colors.{c}: need a #rrggbb value')
if not errors:
    for a, b_, need in [('fg', 'bg', 7), ('soft', 'bg', 4.5), ('mut', 'bg', 3), ('accent', 'bg', 4.5), ('on_accent', 'accent', 4.5), ('accent', 'panel', 3)]:
        ratio = contrast(colors[a], colors[b_])
        if ratio < need:
            err(f'contrast too low: {a} on {b_} is {ratio:.1f}:1, need {need}:1')
scheme = 'dark' if not errors and lum(colors['bg']) < .4 else 'light'

# Structure --------------------------------------------------------------------------------------
SECTIONS = [
    dict(title=PARTS[0], blocks=C.INTRO), dict(title=PARTS[1], blocks=C.OLD_NEW), dict(title=PARTS[2], questions=C.FAQ),
    dict(title=PARTS[3], blocks=C.CTA), dict(title=PARTS[4], blocks=C.PROOF),
]
SLIDES = []
for sec in SECTIONS:
    if 'questions' in sec:
        for j, q in enumerate(sec['questions'], 1):
            for k, stage in enumerate(q['stages']):
                for sl in stage:
                    SLIDES.append(dict(sl, plain=plain(sl['text']), section=sec['title'], role=f'Q{j} · {STAGES[k]}', faq=q['title']))
    else:
        for bl in sec['blocks']:
            for sl in bl['slides']:
                SLIDES.append(dict(sl, plain=plain(sl['text']), section=sec['title'], role=role_label(bl['role']), faq=''))
t = 0
for sl in SLIDES:
    d = max(words(sl['text']) / WPS, 2.2)
    if sl['stats'] and sl['section'] == PARTS[4]:
        d = max(d, 7)
    sl['start'] = t
    sl['duration'] = d
    t += d
SECONDS = t
WORDS = sum(words(s['text']) for s in SLIDES)


def need_roles(name, blocks, required):
    have = [bl['role'] for bl in blocks]
    for r in required:
        if r not in have:
            err(f'{name}: missing block "{r}" ({role_label(r)})')
    return have


intro_roles = need_roles('Intro', C.INTRO, ['hook', 'promise', 'pain', 'proof', 'plan', 'picture'])
if intro_roles and intro_roles[0] != 'hook':
    err('Intro: the first block must be "hook"')
old_roles = need_roles('Old way vs new way', C.OLD_NEW, ['old', 'why', 'new'])
if old_roles and old_roles[-1] != 'new':
    err('Old way vs new way: the last block must be "new", which names the mechanism')
need_roles('CTA', C.CTA, ['action', 'question'])
need_roles('Proof', C.PROOF, ['salad'])

mechanism = brand.get('mechanism', '')
if not mechanism:
    err('brand.json: mechanism is required')
else:
    new_text = ' '.join(low(sl['text']) for bl in C.OLD_NEW if bl['role'] == 'new' for sl in bl['slides'])
    if low(mechanism) not in new_text:
        err(f'Old way vs new way: the mechanism "{mechanism}" is never named in the "new" block')

lo, hi = F['faq']
if not lo <= len(C.FAQ) <= hi:
    err(f'FAQ: {len(C.FAQ)} loops, the {fmt} format needs {lo} to {hi}')
for q in C.FAQ:
    if len(q['stages']) != 4 or not all(st and all(sl['text'] for sl in st) for st in q['stages']):
        err(f'FAQ "{q["title"]}": all four stages need at least one slide')
    elif not any(sl['stats'] or sl['who'] or PLACEHOLDER.search(sl['text']) for sl in q['stages'][3]):
        err(f'FAQ "{q["title"]}": the proof stage needs a figure, a named client or a [PROOF NEEDED: ...] placeholder')
kinds = [q.get('kind') for q in C.FAQ]
for k in ('offer', 'price', 'guarantee'):
    if k not in kinds:
        err(f'FAQ: no loop with kind="{k}". Offer, price and guarantee are answers to FAQ questions')

mech_n = sum(low(sl['text']).count(low(mechanism)) for q in C.FAQ for st in q['stages'] for sl in st) if mechanism else 0
lo, hi = F['mechanism']
if not lo <= mech_n <= hi:
    err(f'FAQ: the mechanism is named {mech_n} times, the {fmt} format needs {lo} to {hi}')

cta_brand = brand.get('cta', {})
for k in ('button', 'question', 'reminder'):
    if not cta_brand.get(k):
        err(f'brand.json: cta.{k} is required')
cta_text = ' '.join(low(sl['text']) for bl in C.CTA for sl in bl['slides'])
if cta_brand.get('question') and low(cta_brand['question']) not in cta_text:
    err('CTA: the personalization question from brand.json must be asked word for word')

proof_slides = [sl for bl in C.PROOF for sl in bl['slides']]
if proof_slides:
    for sl in proof_slides[:-1]:
        if not (sl['stats'] or sl['who'] or PLACEHOLDER.search(sl['text'])):
            err(f'Proof: only proof after the CTA, this slide has no data: {sl["text"]}')
        if not sl['context'] and not PLACEHOLDER.search(sl['text']):
            err(f'Proof: missing context (sector or source): {sl["text"]}')
    if cta_brand.get('reminder') and low(cta_brand['reminder']) not in low(proof_slides[-1]['text']):
        err('Proof: the last slide must remind the single action')
else:
    err('Proof: no slide')

# Per slide --------------------------------------------------------------------------------------
inventory = {str(p['value']).strip() for p in brand.get('proof_inventory', [])}
for p in brand.get('proof_inventory', []):
    if not p.get('source'):
        err(f'proof_inventory "{p.get("value")}": every figure needs a source')
for n, sl in enumerate(SLIDES, 1):
    tag = f'slide {n}'
    if sl['text'].count('*') % 2:
        err(f'{tag}: unbalanced asterisks: {sl["text"]}')
    if words(sl['text']) > MAX_WORDS_SLIDE:
        err(f'{tag}: {words(sl["text"])} words, one idea per slide means {MAX_WORDS_SLIDE} at most: {sl["plain"]}')
    if words(sl['key']) > MAX_WORDS_KEY:
        err(f'{tag}: screen line too long ({words(sl["key"])} words, max {MAX_WORDS_KEY}): {sl["key"]}')
    if len(sl['stats']) > 2:
        err(f'{tag}: two stats at most')
    if sl['stats'] and not sl['context']:
        err(f'{tag}: a figure without context reads as a result in the viewer’s own sector: {sl["plain"]}')
    if (sl['who'] or sl['stats']) and sl['section'] == PARTS[1]:
        err(f'{tag}: proof does not belong in the old way vs new way part')
    for val, _ in sl['stats']:
        if str(val).strip() not in inventory and not DRAFT:
            err(f'{tag}: figure "{val}" is not in proof_inventory. Add it with its source, or remove it')
    if PLACEHOLDER.search(sl['text'] + sl['key']) and not DRAFT:
        err(f'{tag}: proof placeholder left in a final build: {sl["plain"]}')
    v = sl['v']
    if v:
        kind = v.get('type')
        if kind not in VISUALS:
            err(f'{tag}: unknown visual "{kind}"')
            continue
        if kind in COUNTS:
            field, mn, mx = COUNTS[kind]
            count = len(v.get(field, []))
            if not mn <= count <= mx:
                err(f'{tag}: visual {kind} needs {mn} to {mx} {field}, got {count}')
                continue
        try:
            for text, limit in VISUALS[kind](v):
                if len(text) > limit:
                    err(f'{tag}: visual {kind}: "{text}" is {len(text)} characters, the drawing holds {limit}')
            for ic in ICON_USES.get(kind, lambda p: [])(v):
                if ic not in ICONS:
                    err(f'{tag}: unknown icon "{ic}"')
        except (KeyError, IndexError, TypeError) as e:
            err(f'{tag}: visual {kind} is missing a parameter: {e}')

# Copy -------------------------------------------------------------------------------------------
spoken = ' '.join(s['plain'] for s in SLIDES)
screen = ' '.join(s['key'] + ' ' + ' '.join(v + ' ' + l for v, l in s['stats']) + ' ' + s['context'] + ' ' + s['who'] for s in SLIDES)
visible = spoken + ' ' + screen
for w in L['banned'] + brand.get('banned', []):
    if w in brand.get('allow', []):
        continue
    hit = w in visible if not re.match(r'\w', w) else re.search(r'(?<![\wÀ-ÿ])' + re.escape(w) + r'(?![\wÀ-ÿ])', visible, re.I)
    if hit:
        err(f'banned expression on screen or in the script: "{w}"')
if EMOJI.search(visible):
    err('emoji found in the visible text')
if INTERNAL.search(visible):
    err('internal marker (TODO, TBD, lorem) in the visible text')
not_but = len(re.findall(L['not_but'], spoken, re.I))
if not_but > 2:
    err(f'{not_but} "it is not X, it is Y" constructions. Two at most, they read as machine prose')
verbatims = brand.get('verbatims', [])
found = [x for x in verbatims if low(x) in low(spoken)]
if len(found) < 2:
    err(f'{len(found)} customer verbatim(s) quoted, at least 2 from brand.json are required')
lo, hi = F['words']
if WORDS > hi:
    err(f'{WORDS} words, the {fmt} format holds {hi} at most. Cut, or change format')
elif WORDS < lo:
    warn(f'{WORDS} words, below the {fmt} range ({lo} to {hi}). Do not pad: add real material, or set format to short')
shares = {p: round(sum(s['duration'] for s in SLIDES if s['section'] == p) / SECONDS * 100, 1) if SECONDS else 0 for p in PARTS}
for p, (lo, hi) in zip(PARTS, PART_SHARE):
    if not lo <= shares[p] <= hi:
        warn(f'{p}: {shares[p]}% of the running time, target {lo} to {hi}%')
if brand.get('wpm', 138) < 110 or brand.get('wpm', 138) > 170:
    warn('wpm outside 110 to 170. Measure a real read-through')

if errors:
    print(f'BUILD REFUSED: {len(errors)} problem(s)\n', file=sys.stderr)
    for e in errors:
        print(' - ' + e, file=sys.stderr)
    sys.exit(1)


# Output -----------------------------------------------------------------------------------------
def b64(name): return base64.b64encode((HERE / 'assets' / name).read_bytes()).decode()


JOST, INSTRUMENT = b64('Jost-latin.woff2'), b64('InstrumentSans-latin.woff2')
DIST.mkdir(exist_ok=True)
(DIST / 'verification').mkdir(exist_ok=True)
slug, name = brand['slug'], brand['name']
TITLE = brand.get('title', f'{name} · VSL')

if brand.get('logo'):
    logo = (HERE / brand['logo']).read_text(encoding='utf8')
    logo = re.sub(r'<\?xml.*?\?>|<!--.*?-->|<title>.*?</title>|<script.*?</script>', '', logo, flags=re.S).strip()
else:
    logo = f'<span class="wm">{escape(brand.get("wordmark", name))}</span>'

deck = dict(id=slug, title=TITLE, lang=lang, seconds=round(SECONDS), words=WORDS, slides=SLIDES, parts=PARTS, ui=L['ui'],
            cta=dict(button=cta_brand['button'], question=cta_brand['question']))
html = (HERE / 'player.html').read_text(encoding='utf8')
for token, value in [('__TITLE__', escape(TITLE)), ('__LANG__', lang), ('__BRAND__', escape(name, quote=True)), ('__SCHEME__', scheme),
                     ('__JOST__', JOST), ('__INSTRUMENT__', INSTRUMENT), ('__LOGO__', logo)] + [(f'__{c.upper()}__', colors[c]) for c in COLORS]:
    html = html.replace(token, value)
if re.search(r'__[A-Z_]+__', html.replace('__DATA__', '').replace('__deckState', '')):
    sys.exit('player.html: unresolved token')
html = html.replace('__DATA__', json.dumps(deck, ensure_ascii=False).replace('</', '<\\/'))
(DIST / f'{slug}.html').write_text(html, encoding='utf8')
(DIST / 'deck.json').write_text(json.dumps(deck, ensure_ascii=False, indent=1), encoding='utf8')

W = L['script']
md = [f'# {TITLE}\n\n{W["voice"]}: {brand.get("voice", "")}. {WORDS} {W["words"]}. {clock(SECONDS)} {W["est"]} ({brand.get("wpm", 138)} wpm).\n{W["legend"]}\n']
txt = [f'{TITLE.upper()}. {W["spoken_only"]}', '']
body = [f'<p class="meta">{escape(TITLE).upper()}</p><h1>{W["title"]}</h1><p class="meta">{W["voice"]} : {escape(brand.get("voice", ""))} · {WORDS} {W["words"]} · {clock(SECONDS)} {W["est"]} · {len(SLIDES)} {W["slides"]}</p>']


def gold(t): return re.sub(r'\*(.+?)\*', r'<b>\1</b>', escape(t, quote=False))


def line(sl):
    anim = f' · {W["anim"]} {sl["v"]["type"]}' if sl['v'] else ''
    md.append(sl['text'] + '\n')
    md.append(f'_{W["screen"]}: {sl["key"]}{anim}_\n')
    if sl['note']:
        md.append(f'> {W["production"]}: {sl["note"]}\n')
    txt.extend([plain(sl['text']), ''])
    body.append(f'<p class="spoken">{gold(sl["text"])}</p><p class="screenline">{W["screen"]} : {escape(sl["key"])}</p>')
    if sl['note']:
        body.append(f'<p class="production">{escape(sl["note"])}</p>')


for sec in SECTIONS:
    md.append('\n## ' + sec['title'] + '\n')
    txt.extend([sec['title'].upper(), ''])
    body.append('<h2>' + escape(sec['title']) + '</h2>')
    if 'questions' in sec:
        for j, q in enumerate(sec['questions'], 1):
            md.append(f'\n### Q{j} · {q["title"]}\n')
            body.append(f'<h3>Q{j} · {escape(q["title"])}</h3>')
            for k, stage in enumerate(q['stages']):
                md.append(f'**{STAGES[k]}**\n')
                body.append(f'<p class="label">{escape(STAGES[k])}</p>')
                for sl in stage:
                    line(sl)
    else:
        for bl in sec['blocks']:
            label = role_label(bl['role'])
            md.append(f'**{label}**\n')
            body.append(f'<p class="label">{escape(label)}</p>')
            for sl in bl['slides']:
                line(sl)
(DIST / 'script.md').write_text('\n'.join(md), encoding='utf8')
(DIST / 'script.txt').write_text('\n'.join(txt), encoding='utf8')

c = colors
CSS = (f"@font-face{{font-family:Jost;src:url(data:font/woff2;base64,{JOST}) format('woff2');font-weight:100 900}}"
       f"@font-face{{font-family:Instrument;src:url(data:font/woff2;base64,{INSTRUMENT}) format('woff2');font-weight:100 900}}"
       f":root{{color-scheme:{scheme};--ink:{c['bg']};--stone:{c['fg']};--mut:{c['mut']};--accent:{c['accent']};--line:color-mix(in srgb,{c['fg']} 14%,transparent);--a47:color-mix(in srgb,{c['accent']} 47%,transparent)}}"
       "*{box-sizing:border-box}body{margin:0;background:var(--ink);color:var(--stone);font:18px/1.75 Instrument,Arial,sans-serif}main{max-width:820px;margin:60px auto;padding:0 30px 100px}a{color:var(--accent)}nav{display:flex;gap:18px;align-items:center;flex-wrap:wrap;padding:14px 30px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--ink);font-size:13px}h1{font:350 clamp(36px,6vw,58px)/1.15 Jost,sans-serif;letter-spacing:-.015em;margin:18px 0}h2{font:400 31px/1.3 Jost,sans-serif;margin-top:70px;border-top:1px solid var(--line);padding-top:28px}h3{font:400 24px/1.4 Jost,sans-serif;margin-top:40px}p{margin:0 0 14px}b{color:var(--accent);font-weight:inherit}.meta{font-size:13px;color:var(--mut)}.spoken{font-size:22px;line-height:1.6;margin-bottom:6px}.label{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-top:24px}.production{border-left:2px solid var(--a47);padding:6px 16px;color:var(--mut);font-size:13px}.screenline{font-size:12px;color:var(--mut);margin-bottom:16px}button{background:none;border:1px solid var(--line);border-radius:6px;color:var(--stone);padding:7px 12px;cursor:pointer;font:inherit;font-size:13px}.clean .label,.clean .production,.clean .screenline,.clean .meta,.clean h3{display:none}.clean .spoken{font-size:27px;margin-bottom:22px}.clean h2{margin-top:50px}@media print{body{color:#111;background:#fff}nav{display:none}main{margin:0;max-width:none}.production,.screenline,.meta{color:#555}.label{color:#555}b{color:#000;font-weight:600}.spoken{font-size:12.5pt}.clean .spoken{font-size:14pt}h2,h3{break-after:avoid}}")
nav = (f'<nav><a href="{slug}.html">{W["open"]}</a><a href="script.txt">{W["plain"]}</a>'
       f'<button onclick="document.body.classList.toggle(\'clean\')">{W["spoken"]}</button><button onclick="print()">{W["print"]}</button></nav>')
(DIST / 'script.html').write_text(
    f'<!doctype html><html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(TITLE)} · Script</title><style>{CSS}</style></head><body>{nav}<main>{"".join(body)}</main></body></html>',
    encoding='utf8')

report = dict(draft=DRAFT, format=fmt, words=WORDS, duration=clock(SECONDS), slides=len(SLIDES), faq_loops=len(C.FAQ), mechanism_in_faq=mech_n,
              verbatims_quoted=len(found), part_share_percent=shares, visuals_used=sorted({s['v']['type'] for s in SLIDES if s['v']}),
              slides_with_visual=sum(1 for s in SLIDES if s['v']), longest_slide_words=max(words(s['text']) for s in SLIDES), warnings=warnings)
(DIST / 'verification' / 'content-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(report, ensure_ascii=False, indent=1))

# -*- coding: utf-8 -*-
"""Slide helpers and the visual catalogue. Imported by content.py and build.py."""


def s(text, key, v=None, note='', stats=None, who='', context=''):
    """One slide carries one idea.

    text     spoken word for word. *asterisks* mark the phrase shown in the accent color.
    key      the big line of screen mode. Digits welcome here.
    v        an animated diagram, built with v('type', ...).
    note     production note. Only visible in the notes panel and in script.md.
    stats    up to two (value, label) pairs. Every value must be in proof_inventory.
    who      a named client or person for a proof slide.
    context  the sector or source line. Required on every number and every proof.
    """
    return dict(text=text, key=key, v=v, note=note, stats=stats or [], who=who, context=context)


def b(role, *slides):
    """A block of slides sharing a role (hook, promise, pain, proof, plan, picture, ...)."""
    return dict(role=role, slides=list(slides))


def q(title, think, wrong, right, proof, kind=''):
    """One FAQ loop: four lists of slides, in the framework order.

    kind marks what the loop answers. The offer, price and guarantee loops are mandatory.
    """
    return dict(title=title, stages=[think, wrong, right, proof], kind=kind)


def v(type, **params):
    """An animated diagram. See references/05-animations.md for every type."""
    return dict(type=type, **params)


ICONS = ['photo', 'form', 'phone', 'chart', 'person', 'check', 'lock', 'pin', 'eye', 'hand',
         'house', 'search', 'grid', 'web', 'coin', 'clock']

# For each visual: the (text, max characters) pairs that must fit its drawing.
VISUALS = {
    'bars': lambda p: [(p['a']['label'], 40), (p['a']['value'], 18), (p['b']['label'], 40), (p['b']['value'], 40)],
    'board': lambda p: [(c[0], 13) for c in p['cards']] + [(c[1], 14) for c in p['cards']] + [(p.get('tag', ''), 12)],
    'pills': lambda p: [(x, 16) for x in p['items']],
    'fanout': lambda p: [(p['from'], 22), (p['you'], 10)],
    'shift': lambda p: [(p['left'], 22), (p['right'], 22), (p['a'], 14), (p['b'], 14)],
    'journey': lambda p: [(x[1], 13) for x in p['steps']],
    'curves': lambda p: [(p['slow'], 18), (p['fast'], 18), (p['axis'], 12)],
    'numbers': lambda p: [(x, 18) for x in p['items']],
    'road': lambda p: [],
    'pillars': lambda p: [(x[0], 11) for x in p['items']],
    'card': lambda p: [(p['title'], 30), (p.get('tag', ''), 12)] + [(r[0], 16) for r in p['rows']] + [(r[1], 26) for r in p['rows']],
    'phone': lambda p: [(p['notif'][0], 9), (p['notif'][1], 9), (p['big'], 5), (p['caption'], 30)],
    'filter': lambda p: [(p['label'], 22)],
    'owned': lambda p: [(x, 19) for x in p['items']] + [(p['caption'], 30)],
    'contract': lambda p: [(x, 34) for x in p['lines']],
    'twin': lambda p: [(p['a'][0], 20), (p['a'][1], 32), (p['a'][2], 32), (p['b'][0], 20), (p['b'][1], 32), (p['b'][2], 32)],
    'deadline': lambda p: [(p['start'], 12), (p['end'], 12), (p['title'], 44), (p['sub'], 52)],
    'install': lambda p: [(p['big'], 11)] + [(x, 14) for x in p['steps']],
    'dashboard': lambda p: [(x, 13) for x in p['items']],
    'split': lambda p: [(p['left']['title'], 12), (p['right']['title'], 12)] + [(x, 32) for x in p['left']['items'] + p['right']['items']],
    'stack': lambda p: [(x, 30) for x in p['items']],
    'cards': lambda p: [(x[1], 19) for x in p['items']] + [(x[2], 24) for x in p['items']],
    'cta': lambda p: [(p.get('question', ''), 70), (p.get('button', ''), 30)],
}

# Visuals drawn for a fixed number of items: field, minimum, maximum.
COUNTS = {
    'board': ('cards', 3, 3), 'pills': ('items', 2, 4), 'journey': ('steps', 3, 4), 'numbers': ('items', 3, 3),
    'pillars': ('items', 3, 3), 'card': ('rows', 4, 4), 'phone': ('notif', 2, 2), 'owned': ('items', 3, 3),
    'contract': ('lines', 2, 2), 'install': ('steps', 3, 3), 'dashboard': ('items', 4, 4), 'stack': ('items', 3, 6),
    'cards': ('items', 3, 3),
}

# Icon names used by a visual, so a typo fails the build instead of drawing nothing.
ICON_USES = {
    'pills': lambda p: [p['icon']] if p.get('icon') else [],
    'shift': lambda p: [x for x in (p.get('ia'), p.get('ib')) if x],
    'journey': lambda p: [x[0] for x in p['steps']],
    'pillars': lambda p: [x[1] for x in p['items']],
    'owned': lambda p: [p['icon']] if p.get('icon') else [],
    'cards': lambda p: [x[0] for x in p['items']],
}

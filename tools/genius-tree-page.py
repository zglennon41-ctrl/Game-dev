#!/usr/bin/env python3
"""The whole genius tree as one page to read: every base, its three paths, their prongs and
finishes, the play that earns each, and (with --shots) a picture of every form as the game
draws it.

  python3 tools/genius-tree-page.py --out build/genius-tree
  python3 tools/genius-tree-page.py --out build/genius-tree --shots DIR

DIR holds what the game writes, one folder a base:

  godot --path . --resolution 3200x1800 -- --sheet=wolf --shots=DIR/sheet-wolf
  godot --path . -- --lineage=wolf --shots=DIR/life-wolf

The page is a fragment (no <html> or <body>), with its pictures beside it in img/.
"""
import argparse
import html
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLASSES = [('animal', 'Animals', 'Animal'), ('monster', 'Monsters', 'Monster'), ('creature', 'Magical creatures', 'Magical creature'),
           ('item', 'Items of power', 'Item of power'), ('weapon', 'Weapons', 'Weapon'), ('armor', 'Armors', 'Armor')]
# what a player does, for each line of the leans
WORDS = {
    'range.close': 'fighting close', 'range.mid': 'fighting at mid range', 'range.far': 'striking from far off',
    'orders.guard': 'keeping it on Guard', 'orders.hunt': 'sending it to Hunt', 'orders.hold': 'setting it to Hold', 'orders.free': 'leaving it Free',
    'shape.anchor': 'Anchor techniques', 'shape.turn': 'Turn techniques', 'shape.cast': 'Cast techniques', 'shape.read': 'Read techniques',
    'shape.bind': 'Bind techniques', 'shape.make': 'Make techniques',
    'fights.parries': 'parrying', 'fights.blocks': 'blocking', 'fights.hurts': 'taking the blow', 'fights.dodges': 'dodging',
    'company.alone': 'going out alone', 'company.party': 'going out with a party',
    'ground.line': 'working the line', 'ground.wild': 'running the wild', 'ground.water': 'going by water', 'ground.ruin': 'running the ruins',
    'ground.night': 'going out at night', 'ground.quiet': 'keeping to the quiet places',
    'pattern.fires': 'firing your Pattern often', 'pattern.sworn': 'a sworn Pattern',
    'bonds.classmate': 'standing by a classmate', 'bonds.shade': 'speaking with shades', 'bonds.named': 'felling named beasts',
    'quests.linework': 'linework', 'quests.salvage': 'salvage', 'quests.hunt': 'hunts', 'quests.escort': 'escorts', 'quests.writ': 'writs',
    'quests.deep-run': 'deep runs',
}
# the hybrids written by hand (data/genius-hybrids.json, pairs), which the page shows as examples
HYBRIDS = [tuple(k.split('+')) for k in json.load(open(os.path.join(ROOT, 'data', 'genius-hybrids.json')))['pairs']]


def e(s):
    return html.escape(str(s))


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)


def leans(d):
    flat = sorted(((float(w), '%s.%s' % (line, k)) for line, ks in d.items() for k, w in ks.items()), key=lambda t: -t[0])
    return ', '.join(WORDS.get(k, k) for _, k in flat[:3])


def order_of(base):
    """The ids of a base's forms in the order the game's sheet stands them (Data.tree_of)."""
    ids = [base['settled']['id']]
    ids += [p['id'] for p in base['paths']]
    ids += [q['id'] for p in base['paths'] for q in p['prongs']]
    ids += [f['id'] for p in base['paths'] for q in p['prongs'] for f in q['finishes']]
    return ids


def pictures(shots, out, bases):
    """Cut the game's shots down for the page. Returns {base: {form id: cell}}, {base: (w, h)} of the life rows."""
    from PIL import Image
    os.makedirs(os.path.join(out, 'img'), exist_ok=True)
    cells, lives, extra = {}, {}, {}
    names = [b['id'] for b in bases] + ['%s+%s' % h for h in HYBRIDS]
    for b in names:
        d = os.path.join(shots, 'sheet-' + b)
        if os.path.exists(os.path.join(d, 'sheet.json')):
            with open(os.path.join(d, 'sheet.json')) as f:
                sheet = json.load(f)
            im = Image.open(os.path.join(d, '01-sheet.png')).convert('RGB').resize((2400, 1350), Image.LANCZOS)
            im.save(os.path.join(out, 'img', b.replace('+', '-') + '.jpg'), quality=84, optimize=True)
            cells[b] = {fid: i for i, fid in enumerate(sheet['forms'])}
            extra[b] = (sheet['cols'], sheet['rows'])
        p = os.path.join(shots, 'life-' + b, '01-lineage-life.png')
        if os.path.exists(p):
            im = Image.open(p).convert('RGB').crop((0, 150, 1600, 610))
            im.save(os.path.join(out, 'img', b + '-life.jpg'), quality=84, optimize=True)
            lives[b] = im.size
    return cells, lives


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--shots', default='')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    folder = os.path.join(ROOT, 'data', 'genius-bases')
    bases = [load(os.path.join('data', 'genius-bases', f)) for f in sorted(os.listdir(folder)) if f.endswith('.json')]
    homes = {k: v for k, v in load('data/genius-homes.json').items() if not k.startswith('$')}
    seeds = load('data/seeds.json')
    seeds = seeds['seeds'] if isinstance(seeds, dict) else seeds
    seed_text = {s['id']: (s.get('text') or s.get('name') or s['id'].replace('-', ' ')) for s in seeds}
    blood_name = {b['id']: b['name'] for b in load('data/bloods.json')}
    by_id = {b['id']: b for b in bases}
    cells, lives = pictures(args.shots, args.out, bases) if args.shots else ({}, {})
    baby = False
    if args.shots and os.path.exists(os.path.join(args.shots, 'sheet-baby', '01-sheet.png')):
        from PIL import Image
        im = Image.open(os.path.join(args.shots, 'sheet-baby', '01-sheet.png')).convert('RGB')
        im.crop((0, 0, im.size[0] // 8, im.size[1] // 4)).resize((300, 338), Image.LANCZOS).save(os.path.join(args.out, 'img', 'baby.jpg'), quality=86, optimize=True)
        baby = True

    def pic(base_id, fid, name):
        if base_id not in cells or fid not in cells[base_id]:
            return ''
        i = cells[base_id][fid]
        return '<button type="button" class="pic" style="--c:%d;--r:%d" data-n="%s" aria-label="Look at the %s"></button>' % (i % 8, i // 8, e(name), e(name))

    def detail(n):
        return ('<details class="more"><summary>the detail</summary><p>%s</p><dl><dt>Its sign</dt><dd>%s</dd><dt>Its habit</dt><dd>%s</dd></dl></details>'
                % (e(n['text']), e(n['sign']), e(n['habit'])))

    def form(base_id, n, level, tag):
        of = '<p class="of">%s</p>' % e(n['of']) if 'of' in n else ''
        ln = '<p class="comes">comes of %s</p>' % e(leans(n['leans'])) if n.get('leans') else ''
        words = ' '.join([n['name'], n.get('of', ''), n['text'], n['sign'], n['habit']]).lower()
        return ('<div class="form l%d" data-s="%s">%s<div class="txt"><%s class="fname">%s</%s>%s%s%s</div></div>'
                % (level, e(words), pic(base_id, n['id'], n['name']), tag, e(n['name']), tag, of, ln, detail(n)))

    def node(base_id, n, level, col, span, pos, kids):
        cls = 'node n%d %s%s' % (level, pos, ' kids' if kids else '')
        return ('<div class="%s" style="grid-column:%d/span %d;grid-row:%d">%s<span>%s</span>%s</div>'
                % (cls, col + 1, span, level + 1, pic(base_id, n['id'], n['name']), e(n['name']), '<i></i>' if kids else ''))

    def chart(b):
        """The whole line at a glance, as an evolution chart: one column a Final."""
        bid = b['id']
        cells = ['<span class="lab" style="grid-row:%d">%s</span>' % (i + 1, t) for i, t in enumerate(('Baby', 'Starter', 'Paths', 'Advancements', 'Finals'))]
        # everyone's is the same before the rite
        babe = '<img src="img/baby.jpg" width="300" height="338" loading="lazy" alt="The Baby: a small round thing of light with a face">' if baby else '<b class="mote"></b>'
        cells.append('<div class="node n0 only" style="grid-column:2/span 18;grid-row:1">%s<span>Baby</span><i></i></div>' % babe)
        cells.append(node(bid, b['settled'], 1, 1, 18, 'solo', True))
        where = ('first', 'mid', 'last')
        for pi, p in enumerate(b['paths']):
            cells.append(node(bid, p, 2, 1 + 6 * pi, 6, where[pi], True))
            for qi, q in enumerate(p['prongs']):
                cells.append(node(bid, q, 3, 1 + 6 * pi + 2 * qi, 2, where[qi], True))
                for fi, f in enumerate(q['finishes']):
                    cells.append(node(bid, f, 4, 1 + 6 * pi + 2 * qi + fi, 1, ('first', 'last')[fi], False))
        return '<div class="chartwrap"><div class="chart" role="group" aria-label="The %s line, from its Starter to its Finals">%s</div></div>' % (e(b['name']), ''.join(cells))

    nav, out, css = [], [], []
    for cid, cname, one in CLASSES:
        group = [b for b in bases if b['class'] == cid]
        nav.append('<div class="navgroup"><span class="navlabel">%s</span>%s</div>'
                   % (e(cname), ''.join('<a href="#%s">%s</a>' % (b['id'], e(b['name'])) for b in group)))
        for b in group:
            bid = b['id']
            if bid in cells:
                css.append('#%s.seen .pic{background-image:url(img/%s.jpg)}' % (bid, bid))
            hl = sorted(((v[bid], h) for h, v in homes.items() if bid in v), reverse=True)
            homes_line = ', '.join('%s (×%s)' % (h.capitalize(), ('%g' % m)) for m, h in hl) or 'no home in particular'
            calls = b['calls']
            top = lambda d: [k for k, _ in sorted(d.items(), key=lambda t: -t[1])]
            seeds_line = ', '.join('“%s”' % e(seed_text.get(k, k)) for k in top(calls.get('seed', {})))
            shapes = ', '.join(k.capitalize() for k in top(calls.get('shape', {})))
            bloods = ', '.join(e(blood_name.get(k, k)) for k in top(calls.get('blood', {})))
            s = b['settled']
            sec = ['<section class="base" id="%s"><header class="bhead"><p class="eyebrow">%s</p><h2>%s</h2><p class="soul">%s</p>'
                   % (bid, e(one), e(b['name']), e(b['soul']))]
            sec.append('<div class="facts"><div><h3>The spark</h3><p>%s</p></div>' % e(b['spark']))
            sec.append('<div><h3>Its Starter</h3><div class="settled">%s<div class="txt"><p><strong>%s.</strong> %s</p><p class="sub"><em>Its sign.</em> %s</p><p class="sub"><em>Its habit.</em> %s</p></div></div></div>'
                       % (pic(bid, s['id'], s['name']), e(s['name']), e(s['text']), e(s['sign']), e(s['habit'])))
            sec.append('<div><h3>Who it comes to</h3><p class="sub">Seeds: %s</p><p class="sub">Shapes: %s</p><p class="sub">Bloods: %s</p><p class="sub">Likelier for children of %s</p><p class="sub">In a hybrid it is the <strong>%s</strong> half: %s</p></div></div></header>'
                       % (seeds_line, e(shapes), bloods, e(homes_line), e(b['hybrid']['adj']), e(b['hybrid']['text'])))
            if bid in lives:
                p0 = b['paths'][0]
                q0 = p0['prongs'][0]
                f0 = q0['finishes'][0]
                w, h = lives[bid]
                sec.append('<figure class="life"><img loading="lazy" src="img/%s-life.jpg" width="%d" height="%d" alt="Six ages of one %s, each beside its partner, from the %s to the %s at its apex."><figcaption>One life in the game, beside its partner, down the first road: %s, %s, %s, %s, then the %s grown great, and at its apex. The partner wears its echo.</figcaption></figure>'
                           % (bid, w, h, e(b['name']), e(s['name']), e(f0['name']), e(s['name']), e(p0['name']), e(q0['name']), e(f0['name']), e(f0['name'])))
            if bid in cells:
                sec.append(chart(b))
            sec.append('<div class="paths">')
            for p in b['paths']:
                sec.append('<div class="path">' + form(bid, p, 2, 'h3'))
                for q in p['prongs']:
                    sec.append('<div class="prong">' + form(bid, q, 3, 'h4') + '<div class="finishes">')
                    sec.append(''.join(form(bid, f, 4, 'h5') for f in q['finishes']))
                    sec.append('</div></div>')
                sec.append('</div>')
            sec.append('</div></section>')
            out.append(''.join(sec))

    hyb = []
    for a, b2 in HYBRIDS:
        key = '%s+%s' % (a, b2)
        if key in cells and a in by_id and b2 in by_id:
            name = load('data/genius-hybrids.json')['pairs'][key].get('name') or '%s %s' % (by_id[b2]['hybrid']['adj'], by_id[a]['name'])
            hyb.append('<figure class="life"><img loading="lazy" src="img/%s-%s.jpg" width="2400" height="1350" alt="The thirty-one forms of the %s."><figcaption><strong>%s.</strong> A %s that turned toward the %s at its first refinement: its settled form, three paths, nine prongs and eighteen finishes, in that order.</figcaption></figure>'
                       % (a, b2, e(name), e(name), e(by_id[a]['name']), e(by_id[b2]['name'])))
    hybrids = ('<section class="base" id="hybrids"><header class="bhead"><p class="eyebrow">Two bases in one</p><h2>Hybrids</h2><p class="soul">A partner who changes how they play after the rite and before the first refinement may be offered a turning: their genius takes a second base into itself, and grows down a tree made of both.</p></header>%s</section>'
               % ''.join(hyb)) if hyb else ''
    if hyb:
        nav.append('<div class="navgroup"><span class="navlabel">Also</span><a href="#hybrids">Hybrids</a></div>')

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genius-tree-page.html')) as f:
        page = f.read()
    seen = ('Each picture is the form as the game draws it today, brought up close; tap one to look closer. '
            'The row under each base shows one life at its true sizes. '
            'Most forms still wear their base\'s body with the parts their features give them.') if cells else ''
    page = (page.replace('__NAV__', ''.join(nav)).replace('__BODY__', '\n'.join(out) + hybrids).replace('__SPRITES__', ''.join(css))
            .replace('__SEEN__', seen).replace('__TOTAL__', str(31 * len(bases))).replace('__NBASE__', str(len(bases))))
    with open(os.path.join(args.out, 'genius-tree.html'), 'w') as f:
        f.write(page)
    print('%d bases, %d forms, %d with pictures, %d life rows, %d hybrids -> %s'
          % (len(bases), 31 * len(bases), sum(len(v) for k, v in cells.items() if '+' not in k), len(lives), len(hyb), os.path.join(args.out, 'genius-tree.html')))


if __name__ == '__main__':
    main()

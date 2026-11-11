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
    ap.add_argument('--worn', default='', help='a folder of pictures of a genius in the hand or worn, named for its base (blade.png, coat.png) or companion.png')
    ap.add_argument('--check', nargs=2, metavar=('BEFORE', 'AFTER'), default=None,
                    help="the line check's numbers before and after the second pass (tools/genius-line-check.py --json)")
    ap.add_argument('--moving', default='', help='a folder of moving portraits, <base>.webp (tools/genius-moving.py), each with a <base>.txt naming the forms shown')
    ap.add_argument('--new', default='', help='the ids of the bases that are new, comma separated')
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

    kinds = load('data/genius-types.json')
    ramps = load('data/style.json')['ramps']

    def path_colour(node):
        """A Path's own colour (docs/genius-lines.md, "A Path's colour"), as the page shows it."""
        r = (node.get('body') or {}).get('accent')
        return ramps[r][3] if r in ramps else ''
    kind_of = {c: k for k, v in kinds['types'].items() if isinstance(v, dict) for c in v['classes']}
    worn = {}
    if args.worn and os.path.isdir(args.worn):
        from PIL import Image
        os.makedirs(os.path.join(args.out, 'img'), exist_ok=True)
        for f in sorted(os.listdir(args.worn)):
            key, ext = os.path.splitext(f)
            if ext.lower() in ('.png', '.jpg') and (key in by_id or key == 'companion'):
                im = Image.open(os.path.join(args.worn, f)).convert('RGB')
                im.thumbnail((640, 640), Image.LANCZOS)
                im.save(os.path.join(args.out, 'img', 'worn-%s.jpg' % key), quality=86, optimize=True)
                worn[key] = im.size

    new = {x for x in args.new.split(',') if x}
    moving = {}
    if args.moving and os.path.isdir(args.moving):
        from PIL import Image
        import shutil
        os.makedirs(os.path.join(args.out, 'img'), exist_ok=True)
        names = {n['id']: n['name'] for b in bases for n in
                 [b['settled']] + b['paths'] + [q for p in b['paths'] for q in p['prongs']] + [f for p in b['paths'] for q in p['prongs'] for f in q['finishes']]}
        for f in sorted(os.listdir(args.moving)):
            key, ext = os.path.splitext(f)
            if ext.lower() == '.webp' and key in by_id:
                src = os.path.join(args.moving, f)
                shutil.copyfile(src, os.path.join(args.out, 'img', '%s-moving.webp' % key))
                im = Image.open(src)
                im.seek(0)
                im.convert('RGB').save(os.path.join(args.out, 'img', '%s-moving.jpg' % key), quality=84, optimize=True)   # for one who has asked for less motion
                txt = os.path.join(args.moving, key + '.txt')
                ids = open(txt).read().replace('\n', ',').split(',') if os.path.exists(txt) else []
                moving[key] = (im.size, [names[i.strip()] for i in ids if i.strip() in names])

    def beside(b):
        """What this base does beside its partner (data/genius-types.json), for its header."""
        bid, k = b['id'], kind_of.get(b['class'], '')
        t = kinds['types'].get(k, {})
        if k == 'weapon' and bid in kinds['weapon']['bases']:
            w = kinds['weapon']['bases'][bid]
            return ('<div><h3>Beside you: a weapon</h3><p class="sub">G takes it in hand in place of the weapon you carry, and lets it go again.</p><p class="sub"><em>In the hand.</em> %s</p></div>'
                    % e(w['inHand']))
        if k in ('defense', 'ritual') and bid in kinds['items']:
            it = kinds['items'][bid]
            return ('<div><h3>Beside you: a %s</h3><p class="sub"><em>Always, %s.</em> %s</p><p class="sub"><em>G, %s.</em> %s</p></div>'
                    % (e(t['name'].lower()), e(it['always']['name'].lower()), e(it['always']['text']), e(it['use']['name'].lower()), e(it['use']['text'])))
        if k == 'companion' and bid in kinds['companions']:
            r = kinds['roles'][kinds['companions'][bid]['role']]
            return ('<div><h3>Beside you: a companion</h3><p class="sub"><strong>%s.</strong> %s It supplies %s.</p><p class="sub"><em>%s.</em> %s</p></div>'
                    % (e(r['name']), e(r['does']), e(r['supplies']), e(r['own']['name']), e(r['own']['text'])))
        return ''

    def in_fight(b, n):
        """What a Path makes of that, in a line."""
        bid, k = b['id'], kind_of.get(b['class'], '')
        if k == 'weapon':
            d = kinds['weapon']['bases'].get(bid, {}).get('paths', {}).get(n['id'])
            return '<p class="fight"><b>%s.</b> %s</p>' % (e(d['name']), e(d['text'])) if d else ''
        if k in ('defense', 'ritual'):
            d = kinds['items'].get(bid, {}).get('paths', {}).get(n['id'])
            return '<p class="fight"><b>In a fight.</b> %s</p>' % e(d['text']) if d else ''
        d = kinds['companions'].get(bid, {}).get('paths', {}).get(n['id'])
        return '<p class="fight"><b>%s at heart.</b> %s</p>' % (e(kinds['roles'][d['shade']]['name']), e(d['text'])) if d else ''

    def pic(base_id, fid, name):
        if base_id not in cells or fid not in cells[base_id]:
            return ''
        i = cells[base_id][fid]
        return '<button type="button" class="pic" style="--c:%d;--r:%d" data-n="%s" aria-label="Look at the %s"></button>' % (i % 8, i // 8, e(name), e(name))

    def detail(n):
        return ('<details class="more"><summary>the detail</summary><p>%s</p><dl><dt>Its sign</dt><dd>%s</dd><dt>Its habit</dt><dd>%s</dd></dl></details>'
                % (e(n['text']), e(n['sign']), e(n['habit'])))

    def form(base_id, n, level, tag, fight=''):
        of = '<p class="of">%s</p>' % e(n['of']) if 'of' in n else ''
        ln = '<p class="comes">comes of %s</p>' % e(leans(n['leans'])) if n.get('leans') else ''
        words = ' '.join([n['name'], n.get('of', ''), n['text'], n['sign'], n['habit']]).lower()
        return ('<div class="form l%d" data-s="%s">%s<div class="txt"><%s class="fname">%s</%s>%s%s%s%s</div></div>'
                % (level, e(words), pic(base_id, n['id'], n['name']), tag, e(n['name']), tag, of, ln, fight, detail(n)))

    def node(base_id, n, level, col, span, pos, kids, pc=''):
        cls = 'node n%d %s%s%s' % (level, pos, ' kids' if kids else '', ' pc' if pc else '')
        return ('<div class="%s" style="grid-column:%d/span %d;grid-row:%d%s">%s<span>%s</span>%s</div>'
                % (cls, col + 1, span, level + 1, ';--pc:' + pc if pc else '', pic(base_id, n['id'], n['name']), e(n['name']), '<i></i>' if kids else ''))

    def chart(b):
        """The whole line at a glance, as a chart of its stages: one column a Final."""
        bid = b['id']
        cells = ['<span class="lab" style="grid-row:%d">%s</span>' % (i + 1, t) for i, t in enumerate(('Baby', 'Starter', 'Paths', 'Advancements', 'Finals'))]
        # everyone's is the same before the rite
        babe = '<img src="img/baby.jpg" width="300" height="338" loading="lazy" alt="The Baby: a small round thing of light with a face">' if baby else '<b class="mote"></b>'
        cells.append('<div class="node n0 only" style="grid-column:2/span 18;grid-row:1">%s<span>Baby</span><i></i></div>' % babe)
        cells.append(node(bid, b['settled'], 1, 1, 18, 'solo', True))
        where = ('first', 'mid', 'last')
        for pi, p in enumerate(b['paths']):
            pc = path_colour(p)
            cells.append(node(bid, p, 2, 1 + 6 * pi, 6, where[pi], True, pc))
            for qi, q in enumerate(p['prongs']):
                cells.append(node(bid, q, 3, 1 + 6 * pi + 2 * qi, 2, where[qi], True, pc))
                for fi, f in enumerate(q['finishes']):
                    cells.append(node(bid, f, 4, 1 + 6 * pi + 2 * qi + fi, 1, ('first', 'last')[fi], False, pc))
        return '<div class="chartwrap"><div class="chart" role="group" aria-label="The %s line, from its Starter to its Finals">%s</div></div>' % (e(b['name']), ''.join(cells))

    nav, out, css = [], [], []
    for cid, cname, one in CLASSES:
        group = [b for b in bases if b['class'] == cid]
        nav.append('<div class="navgroup"><span class="navlabel">%s</span>%s</div>'
                   % (e(cname), ''.join('<a href="#%s"%s>%s</a>' % (b['id'], ' class="new"' if b['id'] in new else '', e(b['name'])) for b in group)))
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
            sec = ['<section class="base" id="%s"><header class="bhead"><p class="eyebrow">%s%s</p><h2>%s</h2><p class="soul">%s</p>'
                   % (bid, '<b class="newmark">New</b> ' if bid in new else '', e(one), e(b['name']), e(b['soul']))]
            sec.append('<div class="facts"><div><h3>The spark</h3><p>%s</p></div>' % e(b['spark']))
            sec.append('<div><h3>Its Starter</h3><div class="settled">%s<div class="txt"><p><strong>%s.</strong> %s</p><p class="sub"><em>Its sign.</em> %s</p><p class="sub"><em>Its habit.</em> %s</p></div></div></div>'
                       % (pic(bid, s['id'], s['name']), e(s['name']), e(s['text']), e(s['sign']), e(s['habit'])))
            sec.append('<div><h3>Who it comes to</h3><p class="sub">Seeds: %s</p><p class="sub">Shapes: %s</p><p class="sub">Bloods: %s</p><p class="sub">Likelier for children of %s</p><p class="sub">In a hybrid it is the <strong>%s</strong> half: %s</p></div></div></header>'
                       % (seeds_line, e(shapes), bloods, e(homes_line), e(b['hybrid']['adj']), e(b['hybrid']['text'])))
            sec[-1] = sec[-1].replace('</div></header>', beside(b) + '</div></header>')
            if bid in lives:
                p0 = b['paths'][0]
                q0 = p0['prongs'][0]
                f0 = q0['finishes'][0]
                w, h = lives[bid]
                sec.append('<figure class="life"><img loading="lazy" src="img/%s-life.jpg" width="%d" height="%d" alt="Six ages of one %s, each beside its partner, from the %s to the %s at its apex."><figcaption>One life in the game, beside its partner, down the first road: %s, %s, %s, %s, then the %s grown great, and at its apex. The partner wears its echo.</figcaption></figure>'
                           % (bid, w, h, e(b['name']), e(s['name']), e(f0['name']), e(s['name']), e(p0['name']), e(q0['name']), e(f0['name']), e(f0['name'])))
            if bid in moving:
                (w, h), shown = moving[bid]
                who = ', '.join(shown[:-1]) + (' and ' if len(shown) > 1 else '') + shown[-1] if shown else 'a few of its forms'
                sec.append('<figure class="life"><picture><source media="(prefers-reduced-motion: reduce)" srcset="img/%s-moving.jpg"><img loading="lazy" src="img/%s-moving.webp" width="%d" height="%d" alt="%s, moving as the game moves them."></picture><figcaption>As the game moves them: %s. What blinks, beats, sways and gutters does so on its own; nothing here is a drawn animation.</figcaption></figure>'
                           % (bid, bid, w, h, e(who), e(who)))
            if bid in cells:
                sec.append(chart(b))
            sec.append('<div class="paths">')
            for p in b['paths']:
                pc = path_colour(p)
                sec.append('<div class="path"%s>' % (' style="--pc:%s"' % pc if pc else '') + form(bid, p, 2, 'h3', in_fight(b, p)))
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
            hyb.append('<figure class="life"><img loading="lazy" src="img/%s-%s.jpg" width="2400" height="1350" alt="The thirty-one forms of the %s."><figcaption><strong>%s.</strong> A %s that turned toward the %s at its first refinement: its Starter, three Paths, nine Advancements and eighteen Finals, in that order. It keeps the body of its first base and wears the gift of its second.</figcaption></figure>'
                       % (a, b2, e(name), e(name), e(by_id[a]['name']), e(by_id[b2]['name'])))
    hybrids = ('<section class="base" id="hybrids"><header class="bhead"><p class="eyebrow">Two bases in one</p><h2>Hybrids</h2><p class="soul">A partner who changes how they play after the rite and before the first refinement may be offered a turning: their genius takes a second base into itself, and grows down a tree made of both.</p></header>%s</section>'
               % ''.join(hyb)) if hyb else ''
    if hyb:
        nav.append('<div class="navgroup"><span class="navlabel">Also</span><a href="#hybrids">Hybrids</a></div>')

    def shot(key, cap):
        if key not in worn:
            return ''
        w, h = worn[key]
        return '<figure><img loading="lazy" src="img/worn-%s.jpg" width="%d" height="%d" alt="%s"><figcaption>%s</figcaption></figure>' % (key, w, h, e(cap), e(cap))

    def kind(k, title, lead, shots, rows):
        return ('<div class="kind"><h3>%s</h3><p>%s</p>%s<dl>%s</dl></div>'
                % (e(title), lead, '<div class="worn">%s</div>' % ''.join(shots) if any(shots) else '', ''.join('<dt>%s</dt><dd>%s</dd>' % r for r in rows)))

    T, W, I, R = kinds['types'], kinds['weapon']['bases'], kinds['items'], kinds['roles']
    named = lambda ids: [by_id[i] for i in ids if i in by_id]
    weapons = named(W)
    defs = [b for b in bases if kind_of.get(b['class']) == 'defense' and b['id'] in I]
    rits = [b for b in bases if kind_of.get(b['class']) == 'ritual' and b['id'] in I]
    comps = kinds['companions']
    item_row = lambda b: ('<a href="#%s">%s</a>' % (b['id'], e(b['name'])),
                          '<em>Always:</em> %s <em>G, %s:</em> %s' % (e(I[b['id']]['always']['text']), e(I[b['id']]['use']['name'].lower()), e(I[b['id']]['use']['text'])))
    role_row = lambda rid: ('%s' % e(R[rid]['name']),
                            '%s %s <span class="who">%s</span>' % (e(R[rid]['does']), e(R[rid]['lacks']),
                                                                   ', '.join('<a href="#%s">%s</a>' % (b['id'], e(b['name'])) for b in bases if comps.get(b['id'], {}).get('role') == rid)))
    types = ('<section class="base types" id="types"><header class="bhead"><p class="eyebrow">What it does beside you</p><h2>Three types of genius</h2>'
             '<p class="soul">One key means a different thing for each: G takes a weapon in hand, uses an item, gives a companion its order.</p></header><div class="kinds">%s%s%s%s</div></section>'
             % (kind('weapon', 'Weapon', e(T['weapon']['says']),
                     [shot(b['id'], 'The %s in the hand' % b['name']) for b in weapons],
                     [('<a href="#%s">%s</a>' % (b['id'], e(b['name'])), e(W[b['id']]['inHand'])) for b in weapons]),
                kind('defense', 'Defensive item', e(T['defense']['says']),
                     [shot(b['id'], 'The %s, worn' % b['name']) for b in defs], [item_row(b) for b in defs]),
                kind('ritual', 'Ritual item', e(T['ritual']['says']),
                     [shot(b['id'], 'The %s, carried' % b['name']) for b in rits], [item_row(b) for b in rits]),
                kind('companion', 'Companion', e(T['companion']['says']),
                     [shot('companion', 'A companion at its post')],
                     [role_row(rid) for rid in R if isinstance(R[rid], dict) and 'name' in R[rid]])))
    measured = ''
    if args.check:
        with open(args.check[0]) as f:
            was = json.load(f)
        with open(args.check[1]) as f:
            now = json.load(f)
        def cell(b0, b1, key, pct=False):
            show = (lambda v: '%d%%' % round(v * 100)) if pct else (lambda v: '%d' % v)
            met = (b1[key] >= 0.9) if pct else (b1[key] == 0)
            before = '<s>%s</s> ' % show(b0[key]) if b0 is not None else ''
            return '<td class="%s">%s<b>%s</b></td>' % ('met' if met else 'unmet', before, show(b1[key]))
        rows, tot = [], {'was': [0, 0, 0.0, 0], 'now': [0, 0, 0.0, 0]}
        for b in sorted(bases, key=lambda b: ([c[0] for c in CLASSES].index(b['class']), b['name'])):
            bid = b['id']
            if bid not in now:
                continue
            b0, b1 = was.get(bid), now[bid]
            for k, v in (('was', b0), ('now', b1)):
                if v is not None:
                    tot[k][0] += v['alike']; tot[k][1] += v['dark']; tot[k][2] += v['colour']; tot[k][3] += 1
            rows.append('<tr><th scope="row"><a href="#%s">%s</a>%s</th>%s%s%s</tr>'
                        % (bid, e(b['name']), ' <i>new</i>' if b0 is None else '', cell(b0, b1, 'alike'), cell(b0, b1, 'dark'), cell(b0, b1, 'colour', True)))
        if rows:
            w, n = tot['was'], tot['now']
            pct = lambda t: '%d%%' % round(100 * t[2] / max(1, t[3]))
            sums = ('<dl class="sums"><div><dt>Pairs of forms too alike in outline</dt><dd><s>%d</s> <b>%d</b></dd></div>'
                    '<div><dt>Forms too dark to read</dt><dd><s>%d</s> <b>%d</b></dd></div>'
                    '<div><dt>Paths told apart by colour alone</dt><dd><s>%s</s> <b>%s</b></dd></div></dl>' % (w[0], n[0], w[1], n[1], pct(w), pct(n)))
            measured = ('<section class="base" id="measured"><header class="bhead"><p class="eyebrow">The second pass</p><h2>Every line, looked at again</h2>'
                        '<p class="soul">Each line is held to three questions a stranger could answer from across a room: are two of its forms the same black shape, is any too dark to read by lamplight, and can its three Paths be told apart by colour alone.</p></header>'
                        '%s<div class="tablewrap"><table class="meas"><thead><tr><th scope="col">Line</th><th scope="col">Too alike</th><th scope="col">Too dark</th><th scope="col">Paths by colour</th></tr></thead><tbody>%s</tbody></table></div>'
                        '<p class="sub">Struck through is the number before the pass; beside it, the number now. The aim for every line is none alike, none dark, and nine forms in ten landing on their own Path by colour. The check counts %d lines now and counted %d before.</p></section>'
                        % (sums, ''.join(rows), n[3], w[3]))
            nav.insert(0, '<div class="navgroup"><a href="#measured">The second pass</a></div>')
    nav.insert(0, '<div class="navgroup"><span class="navlabel">First</span><a href="#types">The three types</a></div>')

    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'genius-tree-page.html')) as f:
        page = f.read()
    seen = ('Each picture is the form as the game draws it today, brought up close; tap one to look closer. '
            'The row under each base shows one life at its true sizes. '
            'Every form has a body of its own: no two on a line are the same shape.') if cells else ''
    page = (page.replace('__NAV__', ''.join(nav)).replace('__BODY__', types + measured + '\n'.join(out) + hybrids).replace('__SPRITES__', ''.join(css))
            .replace('__SEEN__', seen).replace('__TOTAL__', str(31 * len(bases))).replace('__NBASE__', str(len(bases))))
    with open(os.path.join(args.out, 'genius-tree.html'), 'w') as f:
        f.write(page)
    print('%d bases, %d forms, %d with pictures, %d life rows, %d hybrids -> %s'
          % (len(bases), 31 * len(bases), sum(len(v) for k, v in cells.items() if '+' not in k), len(lives), len(hyb), os.path.join(args.out, 'genius-tree.html')))


if __name__ == '__main__':
    main()

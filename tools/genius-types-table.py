#!/usr/bin/env python3
"""The three types of genius as tables, from data/genius-types.json and the bases
(docs/genius-types.md has them; print them again after a change to the data):

  python3 tools/genius-types-table.py            every base: its type, what it does, what its key does, its three paths
  python3 tools/genius-types-table.py --check    only say whether every base and path is written
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        return json.load(f)


def main():
    T = load('data/genius-types.json')
    folder = os.path.join(ROOT, 'data', 'genius-bases')
    bases = [load(os.path.join('data', 'genius-bases', f)) for f in sorted(os.listdir(folder)) if f.endswith('.json')]
    type_of = {}
    for tid, t in T['types'].items():
        if tid.startswith('$'):
            continue
        for c in t['classes']:
            type_of[c] = tid
    problems = []
    rows = {'weapon': [], 'defense': [], 'ritual': [], 'companion': []}
    for b in bases:
        tid = type_of.get(b['class'], '')
        names = {p['id']: p['name'] for p in b['paths']}
        if tid == 'weapon':
            w = T['weapon']['bases'].get(b['id'])
            if not w:
                problems.append('%s: a weapon with nothing written' % b['id'])
                continue
            for pid in names:
                if pid not in w['paths']:
                    problems.append('%s: path %s not written' % (b['id'], pid))
            rows[tid].append((b, w))
        elif tid in ('defense', 'ritual'):
            it = T['items'].get(b['id'])
            if not it:
                problems.append('%s: an item with nothing written' % b['id'])
                continue
            for pid in names:
                if pid not in it['paths']:
                    problems.append('%s: path %s not written' % (b['id'], pid))
            rows[tid].append((b, it))
        elif tid == 'companion':
            c = T['companions'].get(b['id'])
            if not c:
                problems.append('%s: a companion with no role' % b['id'])
                continue
            for pid in names:
                if pid not in c['paths']:
                    problems.append('%s: path %s not written' % (b['id'], pid))
            rows[tid].append((b, c))
        else:
            problems.append('%s: no type takes the class %s' % (b['id'], b['class']))
    if '--check' in sys.argv:
        print('%d bases, %d problems' % (len(bases), len(problems)))
        for p in problems:
            print('  ' + p)
        sys.exit(1 if problems else 0)

    print('### Weapons\n')
    print('| Base | In the hand | Its paths, and the one property each gives it |')
    print('|---|---|---|')
    for b, w in rows['weapon']:
        paths = '<br>'.join('**%s** (%s): %s' % (p['name'], w['paths'][p['id']]['name'], w['paths'][p['id']]['text']) for p in b['paths'] if p['id'] in w['paths'])
        print('| **%s** | %s Each blow costs it %s of its Will. | %s |' % (b['name'], w['inHand'], ('%g' % w['willPerBlow']), paths))
    for tid, title in (('defense', 'Defensive items'), ('ritual', 'Ritual items')):
        print('\n### %s\n' % title)
        print('| Base | Always | The key | Its paths, and how each bends it |')
        print('|---|---|---|---|')
        for b, it in rows[tid]:
            paths = '<br>'.join('**%s**: %s' % (p['name'], it['paths'][p['id']]['text']) for p in b['paths'] if p['id'] in it['paths'])
            u = it['use']
            print('| **%s** (%s) | **%s.** %s | **%s.** %s Every %g seconds, for %g of its Will. | %s |' % (
                b['name'], it['wornAs'].lower(), it['always']['name'], it['always']['text'], u['name'], u['text'], u['wait'], u['will'], paths))
    print('\n### Companions\n')
    print('| Base | Role | Its paths, and the role each leans toward |')
    print('|---|---|---|')
    for b, c in rows['companion']:
        paths = '<br>'.join('**%s** (%s): %s' % (p['name'], 'keeps to the ' + T['roles'][c['role']]['name'] if c['paths'][p['id']]['shade'] == c['role'] else 'toward the ' + T['roles'][c['paths'][p['id']]['shade']]['name'], c['paths'][p['id']]['text'])
                           for p in b['paths'] if p['id'] in c['paths'])
        print('| **%s** | %s | %s |' % (b['name'], T['roles'][c['role']]['name'], paths))
    if problems:
        print('\nNot written:')
        for p in problems:
            print('  ' + p)


if __name__ == '__main__':
    main()

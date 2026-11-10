#!/usr/bin/env python3
"""Bring the colours the data names onto the game's one style (data/style.json; docs/style.md).

  python3 tools/style-conform.py            says what is off and what it would become
  python3 tools/style-conform.py --write    and writes it

The game moves a colour onto its ramp when a material is made, so nothing on screen depends
on this. It is for the data to say what the game shows: after a ramp is changed, run it and
the hair colours, each zone's night and the creator's lights follow. What it holds:

  data/creation.json   look.hairColors on the coat's ramps; stage.lights: a cool light is the
                       moon's cast (the warm key is left: it was tuned on every face)
  data/zones.json      light.moonColor no bluer than a cast may be; light.ambient no more
                       coloured than an ambient may be
"""
import colorsys
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools', 'blender'))
import style  # noqa: E402

MOON_CAP = 0.23       # the most saturated a cool light's cast may be
AMBIENT_CAP = 0.3     # and an ambient


def r3(c):
    return [round(float(x), 3) for x in c[:3]]


def desaturate(c, cap):
    h, s, v = colorsys.rgb_to_hsv(*c[:3])
    return list(colorsys.hsv_to_rgb(h, min(s, cap), v))


def cool(c):
    h, s, v = colorsys.rgb_to_hsv(*c[:3])
    return s > 0.05 and 0.45 < h < 0.78


def load(path):
    with open(os.path.join(ROOT, path)) as f:
        text = f.read()
    d = json.loads(text)
    same = json.dumps(d, indent=2, ensure_ascii=False) + '\n' == text
    return d, same


def main():
    write = '--write' in sys.argv
    changes = []

    creation, same_c = load('data/creation.json')
    for name, c in creation['look']['hairColors'].items():
        to = r3(style.conform_srgb(c, 'coat'))
        if to != r3(c):
            changes.append('hair %s: %s -> %s' % (name, style.to_hex(c), style.to_hex(to)))
            creation['look']['hairColors'][name] = to
    moon = r3(style.rgb(style.data()['lights']['moon']['cast']))
    for name, l in creation.get('stage', {}).get('lights', {}).items():
        if cool(l['color']) and r3(l['color']) != moon:
            changes.append("the creator's %s light: %s -> %s (the moon's cast)" % (name, style.to_hex(l['color']), style.to_hex(moon)))
            l['color'] = moon

    zones, same_z = load('data/zones.json')
    for z in zones:
        L = z.get('light')
        if not L:
            continue
        if 'moonColor' in L and cool(L['moonColor']) and style.saturation(L['moonColor']) > MOON_CAP:
            to = r3(desaturate(L['moonColor'], MOON_CAP - 0.03))
            changes.append("zone %s: its moon %s -> %s" % (z['id'], style.to_hex(L['moonColor']), style.to_hex(to)))
            L['moonColor'] = to
        if style.saturation(L['ambient']) > AMBIENT_CAP:
            to = r3(desaturate(L['ambient'], AMBIENT_CAP - 0.04))
            changes.append("zone %s: its ambient %s -> %s" % (z['id'], style.to_hex(L['ambient']), style.to_hex(to)))
            L['ambient'] = to

    for c in changes:
        print(c)
    if not changes:
        print('the data is on the style: nothing to change')
        return
    if not write:
        print('\n%d to change. Run with --write to change them.' % len(changes))
        return
    for path, d, same in (('data/creation.json', creation, same_c), ('data/zones.json', zones, same_z)):
        if not same:
            print('NOT written: %s is not in the plain two-space form this tool writes; change it by hand.' % path)
            continue
        with open(os.path.join(ROOT, path), 'w') as f:
            f.write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
        print('wrote', path)


if __name__ == '__main__':
    main()

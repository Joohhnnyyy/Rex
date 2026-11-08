"""Build Rex's chosen mascot logo; Python standard library only."""
from pathlib import Path
import math
import json
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
MASTERS = ROOT / 'masters'
K = 4 * (math.sqrt(2) - 1) / 3


def capsule(x, y, w, h, angle=0):
    """Rounded rectangle as cubic paths, with the rotation baked into coordinates."""
    r = min(w, h) / 2
    cx, cy = x + w / 2, y + h / 2
    theta = math.radians(angle)
    def point(a, b):
        return f'{cx+(a-cx)*math.cos(theta)-(b-cy)*math.sin(theta):.3f} {cy+(a-cx)*math.sin(theta)+(b-cy)*math.cos(theta):.3f}'
    commands = [('M', [(x+r, y)]), ('L', [(x+w-r, y)]),
        ('C', [(x+w-r+K*r,y),(x+w,y+r-K*r),(x+w,y+r)]),
        ('L',[(x+w,y+h-r)]),('C',[(x+w,y+h-r+K*r),(x+w-r+K*r,y+h),(x+w-r,y+h)]),
        ('L',[(x+r,y+h)]),('C',[(x+r-K*r,y+h),(x,y+h-r+K*r),(x,y+h-r)]),
        ('L',[(x,y+r)]),('C',[(x,y+r-K*r),(x+r-K*r,y),(x+r,y)])]
    return ''.join(cmd+' '.join(point(*p) for p in points) for cmd,points in commands)+'Z'


def mark(expression, small=False, reverse=False):
    # Exact capsule replaces the sampled 64-segment animation outline.
    body = capsule(24,66,208,124)
    extra = 0.7 if reverse else 0
    if expression == 'confused':
        w, h = (24, 44) if small else (20, 44)
        rw, rh = (30, 24) if small else (28, 18)
        eyes = capsule(100-w/2-extra,116-h/2-extra,w+2*extra,h+2*extra,-15)
        eyes += capsule(156-rw/2-extra,124-rh/2-extra,rw+2*extra,rh+2*extra,30)
    else:
        eyes = capsule(77-extra,100-extra,40+2*extra,56+2*extra,-15)
        eyes += capsule(139-extra,100-extra,40+2*extra,56+2*extra,15)
    return body+eyes


def svg(body, title, width=256, height=256):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img"><title>{title}</title>{body}</svg>\n'


def path(d, color, rule='evenodd'):
    return f'<path fill="{color}" fill-rule="{rule}" d="{d}"/>'


def art(expression, tone='red', small=False):
    color = {'red':'#FF4055','black':'#141418','white':'#FFFFFF'}[tone]
    d = mark(expression, small, reverse=tone=='white')
    result = path(d, color)
    if tone == 'red':
        result += path(d[len(capsule(24,66,208,124)):], '#FFFFFF')
    return result


# Quiet, rounded custom lettering. All artwork uses outlines, no font dependency.
word = capsule(12,65,18,126)
word += 'M21 118A53 53 0 0 1 74 65H84V83H74A35 35 0 0 0 39 118Z'
word += 'M225 137H116A46 46 0 0 0 197.3 156.3L210.6 168.5A64 64 0 1 1 225 128ZM206 119A46 46 0 0 0 116 119Z'
word += capsule(266,57,18,142,-30)+capsule(266,57,18,142,30)
for expression in ['confused','excited']:
    for tone,color in [('red','#FF4055'),('black','#141418'),('white','#FFFFFF')]:
        d=mark(expression, reverse=tone=='white')
        (MASTERS/f'rex-{expression}-{tone}.svg').write_text(svg(art(expression,tone),f'Rex / {expression} / {tone}'))
        lock=art(expression,tone)+f'<g transform="translate(272 0)">{path(word,"#FFFFFF" if tone=="white" else "#141418","nonzero")}</g>'
        (MASTERS/f'rex-{expression}-horizontal-{tone}.svg').write_text(svg(lock,f'Rex / {expression} / horizontal',610))
        stack=f'<g transform="translate(32 0)">{art(expression,tone)}</g><g transform="translate(0 174)">{path(word,"#FFFFFF" if tone=="white" else "#141418","nonzero")}</g>'
        (MASTERS/f'rex-{expression}-stacked-{tone}.svg').write_text(svg(stack,f'Rex / {expression} / stacked',320,410))
    (MASTERS/f'rex-{expression}-small.svg').write_text(svg(art(expression,small=True),f'Rex / {expression} / small-size'))
(MASTERS/'rex-wordmark.svg').write_text(svg(path(word,'#141418','nonzero'),'Rex / outlined wordmark',340))
# Simple geometry checks double as a reproducible export self-check.
for f in MASTERS.glob('*.svg'):
    ET.fromstring(f.read_text())
    assert not any(token in f.read_text() for token in ['NaN','Infinity','<text','<mask','<filter','<image'])
assert mark('confused') != mark('excited')
assert mark('confused',True) != mark('confused')

# A compact review board with actual assets and authentic small-size examples.
parts=['<rect width="1440" height="1150" fill="#0c0c0e"/>',
 '<text x="60" y="76" fill="white" font-family="Arial,sans-serif" font-size="42" font-weight="700">Rex / curious by default. Excited by possibility.</text>',
 '<text x="60" y="116" fill="#aaaab4" font-family="Arial,sans-serif" font-size="20">Two expressions. One identity. Refined from your current mascot.</text>']
for i,(expression,label,caption) in enumerate([('confused','Confused / primary','The curious, playful everyday face.'),('excited','Excited / companion','For greetings, wins and moments of discovery.')]):
    x=60+i*680
    parts += [f'<rect x="{x}" y="160" width="640" height="440" rx="28" fill="#17171b"/>',f'<g transform="translate({x+140} 155) scale(1.4)">{art(expression)}</g>',f'<text x="{x+32}" y="522" fill="white" font-family="Arial,sans-serif" font-size="27" font-weight="700">{label}</text>',f'<text x="{x+32}" y="562" fill="#aaaab4" font-family="Arial,sans-serif" font-size="19">{caption}</text>']
# Lockup on paper, reversed mark, and app icon on ink.
parts += ['<rect x="60" y="630" width="640" height="210" rx="22" fill="#f6f3ee"/>',f'<g transform="translate(85 630) scale(.93)">{art("confused")}<g transform="translate(272 0)">{path(word,"#141418","nonzero")}</g></g>', '<rect x="740" y="630" width="300" height="210" rx="22" fill="#242429"/>', f'<g transform="translate(785 630) scale(.82)">{path(mark("confused",reverse=True),"#FFFFFF")}</g>', '<rect x="1080" y="630" width="300" height="210" rx="22" fill="#17171b"/>', '<rect x="1158" y="663" width="144" height="144" rx="32" fill="#090A0D"/>',f'<g transform="translate(1158 663) scale(.5625)">{art("confused",small=True)}</g>']
parts += ['<text x="60" y="900" fill="white" font-family="Arial,sans-serif" font-size="23">Small-size cut / real pixels</text>']
for i,size in enumerate([16,24,32,48,64]):
    x=60+i*112
    parts += [f'<g transform="translate({x} 930) scale({size/256})">{art("confused",small=True)}</g>',f'<text x="{x}" y="1038" fill="#aaaab4" font-family="Arial,sans-serif" font-size="16">{size}px</text>']
for i,(color,name) in enumerate([('#FF4055','Rex red'),('#141418','Ink'),('#F6F3EE','Paper')]):
    x=800+i*190
    parts += [f'<rect x="{x}" y="925" width="160" height="64" rx="12" fill="{color}" stroke="#3a3a40"/>',f'<text x="{x}" y="1020" fill="#aaaab4" font-family="Arial,sans-serif" font-size="16">{name} / {color}</text>']
parts += ['<text x="60" y="1110" fill="#777780" font-family="Arial,sans-serif" font-size="17">Filled paths. White eyes in colour; transparent counters in mono. Optical small-size and reversed cuts. No gradients or shadows.</text>']
(ROOT/'review/identity-board.svg').write_text(svg(''.join(parts),'Rex / mascot logo identity',1440,1150))
spec={'brand':'Rex','brief':'Multilingual AI voice operator with a playful, expressive personality. Use the established mascot as the identity.','adjectives':['curious','capable','playful'],'industry':'consumer-app','brand_color':'#FF4055','tile_color':'#090A0D','greyscale':False,'final':True,'concepts':[{'name':'Curious Rex','symbol':'masters/rex-confused-red.svg','lockup':'masters/rex-confused-horizontal-red.svg','stacked':'masters/rex-confused-stacked-red.svg','symbol_on_tile':'masters/rex-confused-red.svg','symbol_on_dark':'masters/rex-confused-red.svg','lockup_on_dark':'masters/rex-confused-horizontal-white.svg','idea':'A curious face for a capable companion.','rationale':['Confused is the primary expression; Excited supports greetings and success.','Exact capsule and transparent eye counters.','Enlarged small-size eyes retain the expression.']}],'recommendation':'Use Confused consistently for recognition; use Excited for celebratory moments.'}
(ROOT/'presentation-spec.json').write_text(json.dumps(spec,indent=2))

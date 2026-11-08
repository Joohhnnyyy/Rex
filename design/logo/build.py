"""Rex logo concepts, built from explicit geometry (python3 build.py writes the SVGs next to this file).

Shared detail: an eyelid cut at an exact 15 degrees, the inner corner lower: Rex's unimpressed look.
"""

import math
from pathlib import Path

OUT = Path(__file__).parent
T15 = math.tan(math.radians(15))


def f(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def lidded_eye(cx, cy, r, slope, drop):
    """Path for the part of a circle below a lid line through (cx, cy - drop) with the given slope."""
    a, b, c = 1 + slope**2, -2 * slope * drop, drop**2 - r**2  # (u)^2 + (slope*u - drop)^2 = r^2
    disc = math.sqrt(b * b - 4 * a * c)
    u1, u2 = (-b - disc) / (2 * a), (-b + disc) / (2 * a)
    p1 = (cx + u1, cy - drop + slope * u1)
    p2 = (cx + u2, cy - drop + slope * u2)
    large = 1 if drop > 0 else 0  # lid above centre: the visible part is more than half
    return f"M{f(p1[0])} {f(p1[1])}L{f(p2[0])} {f(p2[1])}A{f(r)} {f(r)} 0 {large} 1 {f(p1[0])} {f(p1[1])}Z"


def circle(cx, cy, r):
    return f"M{f(cx - r)} {f(cy)}A{f(r)} {f(r)} 0 1 0 {f(cx + r)} {f(cy)}A{f(r)} {f(r)} 0 1 0 {f(cx - r)} {f(cy)}Z"


def rrect(x, y, w, h, r):
    return (
        f"M{f(x + r)} {f(y)}H{f(x + w - r)}A{f(r)} {f(r)} 0 0 1 {f(x + w)} {f(y + r)}V{f(y + h - r)}"
        f"A{f(r)} {f(r)} 0 0 1 {f(x + w - r)} {f(y + h)}H{f(x + r)}A{f(r)} {f(r)} 0 0 1 {f(x)} {f(y + h - r)}"
        f"V{f(y + r)}A{f(r)} {f(r)} 0 0 1 {f(x + r)} {f(y)}Z"
    )


def svg(w, h, paths, title):
    body = "\n  ".join(f'<path fill="#000" fill-rule="evenodd" d="{d}"/>' for d in paths)
    head = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img">'
    return f"{head}<title>{title}</title>\n  {body}\n</svg>\n"


# ---- A: Lidded squircle (mascot). Body 216x184 rounded rect, eyes r=30 with 15-degree lids, side-eye pupils.
def concept_a(pupils=True):
    body = rrect(20, 36, 216, 184, 72)
    # heavy lids: a flat line just below the eye's centre (sloped lids read as angry or sad without brows)
    eyes = [lidded_eye(86, 128, 34, 0, -6), lidded_eye(170, 128, 34, 0, -6)]  # flat, heavy: deadpan
    paths = [body + "".join(eyes)]
    if pupils:
        paths.append(circle(96, 146, 12) + circle(180, 146, 12))  # both glance right, half-hidden by the lid
    return paths


# ---- B: Lid-eye R (letterform). Stroke 32: stem, bowl (outer r=64, counter r=32), 45-degree leg.
def concept_b(pupil=True):
    stem = "M48 36H80V220H48Z"
    outer = "M64 36H140A64 64 0 0 1 140 164H64Z"  # starts inside the stem so the two overlap cleanly
    # counter = the eye: the part of the D-shaped counter below a 15-degree lid through (110, 96)
    m, x0, y0 = T15, 110, 96
    # intersect lid line with the counter's arc (centre 140,100 r 32): y = y0 + m(x - x0)
    k = y0 - m * x0 - 100
    qa, qb, qc = 1 + m * m, 2 * (m * k - 140), 140 * 140 + k * k - 32 * 32
    xi = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
    yi = y0 + m * (xi - x0)
    yl = y0 + m * (80 - x0)
    counter = f"M80 {f(yl)}L{f(xi)} {f(yi)}A32 32 0 0 1 140 132H80Z"
    leg = "M96 148H141L213 220H168Z"
    paths = [stem, outer + counter, leg]
    if pupil:
        paths.append(circle(126, 118, 9))
    return paths


# ---- C: "rex" wordmark. x-height 64..192, stroke 30; the e's bar tilts 15 degrees like a lid.
def concept_c(offset=0):
    o = offset
    r_stem = f"M{f(16 + o)} 64H{f(46 + o)}V192H{f(16 + o)}Z"
    r_arm = f"M{f(31 + o)} 128A64 64 0 0 1 {f(95 + o)} 64H{f(110 + o)}V94H{f(95 + o)}A34 34 0 0 0 {f(61 + o)} 128Z"
    cx, cy, R, ri = 194 + o, 128, 64, 34

    def pt(rad, deg):
        t = math.radians(deg)
        return cx + rad * math.cos(t), cy + rad * math.sin(t)

    a0 = 40  # aperture: the ring runs clockwise from 52 degrees (lower right) round to 0 degrees
    p_o0, p_o1 = pt(R, a0), pt(R, 360)
    p_i1, p_i0 = pt(ri, 360), pt(ri, a0)
    ring = (
        f"M{f(p_o0[0])} {f(p_o0[1])}A{R} {R} 0 1 1 {f(p_o1[0])} {f(p_o1[1])}"
        f"L{f(p_i1[0])} {f(p_i1[1])}A{ri} {ri} 0 1 0 {f(p_i0[0])} {f(p_i0[1])}Z"
    )

    # tilted bar: band of half-thickness 14 through the centre, slope +tan15, ending on the outer circle
    def edge_hit(off):
        k = off  # y - cy = m*(x - cx) + k
        m = -T15
        qa, qb, qc = 1 + m * m, 2 * m * k, k * k - R * R
        u = (-qb + math.sqrt(qb * qb - 4 * qa * qc)) / (2 * qa)
        return cx + u, cy + m * u + k

    top_r, bot_r = edge_hit(-14), edge_hit(14)
    xl = cx - 50
    top_l = (xl, cy - 14 - T15 * (xl - cx))
    bot_l = (xl, cy + 14 - T15 * (xl - cx))
    bar = (
        f"M{f(top_l[0])} {f(top_l[1])}L{f(top_r[0])} {f(top_r[1])}A{R} {R} 0 0 1 {f(bot_r[0])} {f(bot_r[1])}"
        f"L{f(bot_l[0])} {f(bot_l[1])}Z"
    )
    x0 = 274 + o
    h = 30 / math.sin(math.radians(60))
    run = 128 / math.tan(math.radians(60))
    d1 = f"M{f(x0)} 64H{f(x0 + h)}L{f(x0 + h + run)} 192H{f(x0 + run)}Z"
    d2 = f"M{f(x0 + run)} 64H{f(x0 + h + run)}L{f(x0 + h)} 192H{f(x0)}Z"
    return [r_stem, r_arm, ring, bar, d1, d2], math.ceil(x0 + h + run + 16 - o)


def write(name, w, h, paths, title):
    (OUT / f"{name}.svg").write_text(svg(w, h, paths, title))


write("a-symbol", 256, 256, concept_a(), "Rex: lidded squircle")
write("a-symbol-small", 256, 256, concept_a(pupils=False), "Rex: lidded squircle, small sizes")
write("b-symbol", 256, 256, concept_b(), "Rex: lid-eye R")
word, ww = concept_c()
write("c-wordmark", f(ww), 256, word, "Rex wordmark")
# lockups: symbol + 32 gap + wordmark (letters span y 64..192, centred on the 256 symbol)
for key, sym in (("a", concept_a()), ("b", concept_b())):
    w2, wwid = concept_c(offset=288)
    write(f"{key}-lockup", f(wwid + 288), 256, sym + w2, f"Rex lockup {key}")
write("c-lockup", f(ww), 256, word, "Rex wordmark")
print("written:", sorted(p.name for p in OUT.glob("*.svg")))

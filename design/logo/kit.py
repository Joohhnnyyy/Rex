"""Rex logo kit masters (direction A, "Deadpan"). python3 kit.py writes kit/masters/*.svg.

Geometry comes from build.py so the kit and the approved concept can never drift apart.
Colours: Rex Red #FF4055 (face), Paper #FFFFFF (eyes), Ink #141418 (pupils, wordmark on light),
Night #090A0D (dark backgrounds).
"""

from pathlib import Path

from build import circle, concept_a, concept_c, f, lidded_eye, rrect

OUT = Path(__file__).parent / "kit" / "masters"
RED, PAPER, INK = "#FF4055", "#FFFFFF", "#141418"

BODY = rrect(20, 36, 216, 184, 72)
EYES = [lidded_eye(86, 128, 34, 0, -6), lidded_eye(170, 128, 34, 0, -6)]
PUPILS = circle(96, 146, 12) + circle(180, 146, 12)
# Small-size cut (16-32 px): bigger, simpler eyes and no pupils, which blur into specks at favicon size.
SMALL_EYES = [lidded_eye(80, 130, 36, 0, -8), lidded_eye(176, 130, 36, 0, -8)]  # 24-unit gap: 1.5 px at 16 px


def doc(w, h, body, title):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img">'
        f"<title>{title}</title>\n{body}</svg>\n"
    )


def p(d, fill, evenodd=False):
    rule = ' fill-rule="evenodd"' if evenodd else ""
    return f'  <path fill="{fill}"{rule} d="{d}"/>\n'


def symbol_black():
    return "".join(p(d, "#000", True) for d in concept_a())


def symbol_color():
    return p(BODY, RED) + p("".join(EYES), PAPER) + p(PUPILS, INK)


def small_black():
    return p(BODY + "".join(SMALL_EYES), "#000", True)


def small_color():
    return p(BODY, RED) + p("".join(SMALL_EYES), PAPER)


def wordmark(fill, offset=0):
    paths, width = concept_c(offset=offset)
    return "".join(p(d, fill, True) for d in paths), width


def write(name, w, h, body, title="Rex logo"):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{name}.svg").write_text(doc(w, h, body, title))


def main():
    write("rex-symbol", 256, 256, symbol_black())
    write("rex-symbol-color", 256, 256, symbol_color())
    write("rex-symbol-small", 256, 256, small_black(), "Rex logo (small sizes)")
    write("rex-symbol-small-color", 256, 256, small_color(), "Rex logo (small sizes)")

    word, ww = wordmark("#000")
    write("rex-wordmark", ww, 256, word, "Rex wordmark")
    write("rex-wordmark-ink", ww, 256, wordmark(INK)[0], "Rex wordmark")

    # Horizontal: symbol, a gap of 32 (half an eye), wordmark whose x-height is centred on the face.
    for name, sym, ink in (
        ("rex-horizontal", symbol_black(), "#000"),
        ("rex-horizontal-color", symbol_color(), INK),
        ("rex-horizontal-color-dark", symbol_color(), PAPER),
    ):
        w2, wwid = wordmark(ink, offset=288)
        write(name, f(wwid + 288), 256, sym + w2)

    # Stacked: symbol centred over the wordmark, 24 apart; the wordmark's letters span y 64..192.
    x_sym = round((ww - 256) / 2)
    for name, sym, ink in (
        ("rex-stacked", symbol_black(), "#000"),
        ("rex-stacked-color", symbol_color(), INK),
        ("rex-stacked-color-dark", symbol_color(), PAPER),
    ):
        body = (
            f'<g transform="translate({x_sym} 0)">\n{sym}</g>\n'
            f'<g transform="translate(0 216)">\n{wordmark(ink)[0]}</g>\n'
        )
        write(name, ww, 408, body)
    print("masters:", sorted(x.name for x in OUT.glob("*.svg")))


if __name__ == "__main__":
    main()

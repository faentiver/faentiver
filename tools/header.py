"""Erzeugt assets/header.svg: Pixel-Landschaft mit Parallax, Ringen, Komet und Titelkarte."""

from pathlib import Path

from font import outlined_text, text_width
from pixel import Grid, svg_rects
from sprites import COLORS, cloud, comet, palm, ring

P = 4  # Bildschirmpixel pro Spielpixel
W, H = 210, 60  # Spielpixel
GROUND = 46


DEFS = []


def tile_svg(grid, x_offsets, y=0, name=None):
    """Definiert die Kachel einmal in <defs> und setzt sie per <use> an alle Positionen."""
    name = name or f"t{len(DEFS)}"
    DEFS.append(f'<g id="{name}">{svg_rects(grid, 1, COLORS)}</g>')
    return "".join(f'<use xlink:href="#{name}" x="{x}" y="{y}"/>' for x in x_offsets)


def mountains():
    g = Grid(W, 20)
    for cx, h, w in ((20, 14, 26), (62, 18, 30), (110, 12, 24), (150, 17, 28), (195, 13, 26)):
        for dx in (-W, 0, W):
            g.poly([(cx + dx - w, 20), (cx + dx, 20 - h), (cx + dx + w, 20)], "m1")
            g.poly([(cx + dx - 3, 20 - h + 3), (cx + dx, 20 - h), (cx + dx + 3, 20 - h + 3)], "m2", only=("m1",))
    return g


def hills():
    g = Grid(W, 22)
    for cx, rx, ry in ((18, 26, 9), (75, 34, 11), (140, 24, 8), (190, 30, 10)):
        for dx in (-W, 0, W):
            g.ellipse(cx + dx, 22, rx, ry, "h2")
    for y in range(22):
        for x in range(W):
            if g.px[y][x] == "h2":
                above = g.get(x, y - 1)
                if above is None or above == "h3" and y > 0 and g.get(x, y - 2) is None:
                    g.px[y][x] = "h3"
                elif (x // 6 + y // 3) % 2 and y > 16:
                    g.px[y][x] = "h1"
    for px_ in (48, 168):
        p = palm(22)
        g.paste(p, px_ - 10, 0)
    return g


def ground_tile():
    g = Grid(10, H - GROUND + 1)
    for x in range(10):
        g.set(x, 1, "g1")
        g.set(x, 2, "g1")
        g.set(x, 3, "g2")
    for x in (2, 3, 7):
        g.set(x, 0, "g1")
    for y in range(4, g.h):
        for x in range(10):
            light = ((x // 5) + ((y - 4) // 5)) % 2 == 0
            g.set(x, y, "e1" if light else "e2")
            if light and x % 5 == 0 and (y - 4) % 5 == 0:
                g.set(x, y, "e3")
    return g


def build():
    css = """
    .clouds{animation:scroll 90s linear infinite}
    .mount{animation:scroll 40s linear infinite}
    .hills{animation:scroll 16s linear infinite}
    .ground{animation:groundscroll .35s linear infinite}
    .rmove{animation:ringmove 7.2s linear infinite}
    .spin{animation:spin 1s infinite;transform-box:fill-box;transform-origin:center}
    .comet{animation:comet 6s linear infinite}
    .cf1{animation:flick .16s step-end infinite}
    .cf0{animation:flick .16s step-end infinite reverse}
    .blink{animation:blink 1.2s step-end infinite}
    @keyframes scroll{from{transform:translateX(0)}to{transform:translateX(-840px)}}
    @keyframes groundscroll{from{transform:translateX(0)}to{transform:translateX(-40px)}}
    @keyframes ringmove{from{transform:translateX(0)}to{transform:translateX(-960px)}}
    @keyframes spin{0%{transform:scaleX(1)}25%{transform:scaleX(.55)}50%{transform:scaleX(.15)}75%{transform:scaleX(.55)}100%{transform:scaleX(1)}}
    .spin{animation-timing-function:steps(1,end)}
    @keyframes comet{0%{transform:translateX(-140px)}24%{transform:translateX(980px)}100%{transform:translateX(980px)}}
    @keyframes flick{0%{opacity:1}50%{opacity:0}}
    @keyframes blink{0%{opacity:1}55%{opacity:0}}
    """
    DEFS.clear()
    parts = ['<g clip-path="url(#r)">']
    # Himmel in Bändern
    bands = [("s1", 0, 10), ("s2", 10, 20), ("s3", 20, 30), ("s4", 30, 38), ("s5", 38, GROUND)]
    for col, y0, y1 in bands:
        parts.append(f'<rect x="0" y="{y0 * P}" width="840" height="{(y1 - y0) * P}" fill="{COLORS[col]}"/>')

    sc = f'transform="scale({P})"'
    # Wolken
    DEFS.append(f'<g id="cloud">{svg_rects(cloud(), 1, COLORS)}</g>')
    cloud_pos = [(x + dx, y) for dx in (0, W) for x, y in ((14, 4), (78, 12), (130, 3), (176, 9))]
    cloud_tile = "".join(f'<use xlink:href="#cloud" x="{x}" y="{y}"/>' for x, y in cloud_pos)
    parts.append(f'<g class="clouds"><g {sc}>{cloud_tile}</g></g>')
    # Berge
    parts.append(f'<g class="mount"><g {sc}>{tile_svg(mountains(), (0, W), 22, 'mount')}</g></g>')
    # Hügel mit Palmen
    parts.append(f'<g class="hills"><g {sc}>{tile_svg(hills(), (0, W), GROUND - 22, 'hills')}</g></g>')
    # Boden
    gt = ground_tile()
    parts.append(f'<g class="ground"><g {sc}>{tile_svg(gt, range(0, W + 20, 10), GROUND - 1, 'ground')}</g></g>')

    # Ringe, die mit dem Boden vorbeiziehen
    DEFS.append(f'<g id="ring">{svg_rects(ring(10), 1, COLORS)}</g>')
    for x, y in ((0, 35), (14, 32), (28, 31), (42, 32), (56, 35)):
        parts.append(
            f'<g transform="translate({880 + x * P},{y * P})"><g class="rmove">'
            f'<g class="spin"><g {sc}><use xlink:href="#ring"/></g></g></g></g>'
        )

    # Komet, der alle paar Sekunden durchschießt
    c0, c1 = svg_rects(comet(0), 1, COLORS), svg_rects(comet(1), 1, COLORS)
    parts.append(
        f'<g transform="translate(0,{24 * P})"><g class="comet"><g transform="scale(6)">'
        f'<g class="cf0">{c0}</g><g class="cf1">{c1}</g></g></g></g>'
    )

    # Titelkarte rechts
    right = 812
    name = "FATIH COŞKUN"
    parts.append(outlined_text(name, right - text_width(name, 4), 46, 4, "#ffffff", COLORS["navy"]))
    sub = "IOS DEVELOPER · STUTTGART"
    parts.append(outlined_text(sub, right - text_width(sub, 2), 96, 2, COLORS["Y"], COLORS["navy"]))
    start = "▶ PRESS START"
    parts.append(f'<g class="blink">{outlined_text(start, right - text_width(start, 2), 126, 2, "#ffffff", COLORS["navy"])}</g>')

    parts.append("</g></svg>")
    head = [
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 840 240" width="840" height="240" shape-rendering="crispEdges" role="img">',
        "<title>Fatih Coşkun · iOS Developer · Stuttgart</title>",
        f"<style>{css}</style>",
        '<defs><clipPath id="r"><rect width="840" height="240" rx="18"/></clipPath>' + "".join(DEFS) + "</defs>",
    ]
    return "".join(head + parts)


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "assets" / "header.svg"
    out.write_text(build())
    print(f"{out} ({out.stat().st_size // 1024} KB)")
